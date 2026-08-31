"""Evaluate dialogue control without retrieval or ranking.

The Dialogue Control Pass Rate (DCPR) is the share of scripted sessions that
simultaneously satisfy intent, state-transition, and question-policy rules.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Iterable, Mapping

from starter.constraints import parse_constraints
from starter.dialogue_policy import QuestionPolicy
from starter.intent import DialogueIntent, recognize_intent
from starter.state import SessionState


DEFAULT_CASES_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "dialogue_control_cases.jsonl"
)
DEFAULT_ANSWERS_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "contextual_answer_cases.jsonl"
)
DEFAULT_CANDIDATE_QUESTIONS_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "candidate_question_cases.jsonl"
)
POLICY_MODES = {"legacy", "adaptive"}


def load_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_answer_cases(path: str | Path = DEFAULT_ANSWERS_PATH) -> list[dict]:
    return load_cases(path)


def load_candidate_question_cases(
    path: str | Path = DEFAULT_CANDIDATE_QUESTIONS_PATH,
) -> list[dict]:
    return load_cases(path)


def _candidate_products(case: Mapping[str, object]) -> list[dict]:
    attribute = str(case.get("expected_attribute", ""))
    left = case.get("left")
    right = case.get("right")
    products: list[dict] = []
    for side, value in (("L", left), ("R", right)):
        for index in range(5):
            product = {
                "parent_asin": f"{case.get('case_id', '')}_{side}{index}",
                "title": "Candidate product",
                "features": [],
                "store": "",
                "price": None,
            }
            if attribute == "brand":
                product["store"] = str(value)
            elif attribute == "budget":
                product["price"] = float(value)
            else:
                product["features"] = [str(value)]
            products.append(product)
    return products


def evaluate_candidate_question_selection(
    cases: Iterable[Mapping[str, object]],
    *,
    dynamic: bool,
) -> dict:
    case_list = list(cases)
    passed = 0
    failures: list[dict] = []
    for case in case_list:
        state = SessionState.create(str(case.get("case_id", "")), {})
        state.apply([_constraint({"attribute": "category", "value": "Shoes"})], turn=1)
        decision = QuestionPolicy().decide(
            state,
            intent=DialogueIntent.BROWSING,
            candidate_products=_candidate_products(case) if dynamic else (),
        )
        expected = str(case.get("expected_attribute", ""))
        contrastive = " or " in decision.message.casefold()
        if decision.ask_attribute == expected and contrastive:
            passed += 1
        else:
            failures.append({
                "case_id": str(case.get("case_id", "")),
                "expected_attribute": expected,
                "actual_attribute": decision.ask_attribute,
                "contrastive": contrastive,
            })
    rate = passed / len(case_list) if case_list else 0.0
    return {
        "case_count": len(case_list),
        "passed_case_count": passed,
        "candidate_question_utility_rate": round(rate, 6),
        "failed_cases": failures,
    }


def evaluate_answer_utilization(
    cases: Iterable[Mapping[str, object]],
    *,
    contextual_fallback: bool,
) -> dict:
    case_list = list(cases)
    expected_count = 0
    captured_count = 0
    failures: list[dict] = []
    for case in case_list:
        attribute = str(case.get("last_asked_attribute", ""))
        expected = [str(value) for value in case.get("expected_values", [])]
        constraints = parse_constraints(
            str(case.get("message", "")),
            last_asked_attribute=attribute,
            enable_contextual_fallback=contextual_fallback,
        )
        actual = {
            str(item.get("value", "")).casefold()
            for item in constraints
            if str(item.get("attribute", "")) == attribute
        }
        missing = [value for value in expected if value.casefold() not in actual]
        expected_count += len(expected)
        captured_count += len(expected) - len(missing)
        if missing:
            failures.append({
                "case_id": str(case.get("case_id", "")),
                "missing_values": missing,
            })
    rate = captured_count / expected_count if expected_count else 0.0
    return {
        "case_count": len(case_list),
        "expected_value_count": expected_count,
        "captured_value_count": captured_count,
        "answer_utilization_rate": round(rate, 6),
        "failed_cases": failures,
    }


def _constraint(item: Mapping[str, object]) -> dict[str, object]:
    value = item.get("value")
    return {
        "attribute": str(item.get("attribute", "")),
        "value": value,
        "kind": str(item.get("kind", "hard")),
        "confidence": float(item.get("confidence", 0.95)),
        "source": "fixture_setup",
        "raw_text": str(value),
    }


def _contains_expected(actual: Mapping[str, object], expected: Mapping[str, object]) -> bool:
    for key, value in expected.items():
        actual_value = actual.get(key)
        if isinstance(value, list):
            if not isinstance(actual_value, list) or any(item not in actual_value for item in value):
                return False
        elif actual_value != value:
            return False
    return True


def _expected_last_action(expected: Mapping[str, object], decisions: list[dict]) -> bool:
    wanted = expected.get("last_ask", "unspecified")
    if wanted == "unspecified":
        return True
    actual = decisions[-1]["ask_attribute"] if decisions else None
    if wanted == "present":
        return isinstance(actual, str) and bool(actual)
    return actual == wanted


def evaluate_case(case: Mapping[str, object], *, policy_mode: str) -> dict:
    if policy_mode not in POLICY_MODES:
        raise ValueError(f"unsupported policy mode: {policy_mode}")

    case_id = str(case.get("case_id", ""))
    scenario = str(case.get("scenario", ""))
    state = SessionState.create(case_id, {})
    setup_constraints = [
        _constraint(item)
        for item in case.get("setup_constraints", [])
        if isinstance(item, Mapping)
    ]
    if setup_constraints:
        state.apply(setup_constraints, turn=1)
    for attribute in case.get("setup_asked", []):
        state.mark_asked(str(attribute))

    policy = QuestionPolicy()
    decisions: list[dict] = []
    observed_intents: list[str] = []
    changed_by_turn: list[set[str]] = []
    start_turn = 2 if setup_constraints else 1
    turns = case.get("turns", [])
    for offset, turn_spec in enumerate(turns):
        if not isinstance(turn_spec, Mapping):
            continue
        message = str(turn_spec.get("message", ""))
        constraints = parse_constraints(
            message,
            last_asked_attribute=state.last_asked_attribute,
        )
        intent = recognize_intent(message, constraints)
        observed_intents.append(intent.intent.value)
        state.apply(constraints, turn=start_turn + offset)
        changed = {
            str(item.get("attribute", ""))
            for item in constraints
            if str(item.get("kind", "")) in {"neutral", "override"}
        }
        changed_by_turn.append(changed)
        if policy_mode == "adaptive":
            decision = policy.decide(
                state,
                intent=intent.intent,
                changed_attributes=changed,
            )
        else:
            decision = policy.decide(state)
        decisions.append({
            "ask_attribute": decision.ask_attribute,
            "message": decision.message,
        })
        if decision.ask_attribute is not None:
            state.mark_asked(decision.ask_attribute)

    expected = case.get("expected", {})
    if not isinstance(expected, Mapping):
        expected = {}
    failures: list[str] = []
    expected_intents = [
        str(item.get("expected_intent", ""))
        for item in turns
        if isinstance(item, Mapping)
    ]
    if observed_intents != expected_intents:
        failures.append("wrong_intent")
    if not _contains_expected(state.current_slots, expected.get("current_slots", {})):
        failures.append("current_slot_mismatch")
    if not _contains_expected(state.hard_constraints, expected.get("hard_constraints", {})):
        failures.append("hard_constraint_mismatch")
    if not _contains_expected(state.invalidated_slots, expected.get("invalidated_slots", {})):
        failures.append("invalidated_slot_mismatch")
    neutral = {str(item) for item in state.neutral_attributes}
    if any(str(item) not in neutral for item in expected.get("neutral_contains", [])):
        failures.append("neutral_attribute_missing")

    asked = [item["ask_attribute"] for item in decisions if item["ask_attribute"] is not None]
    forbidden = {str(item) for item in expected.get("forbidden_asks", [])}
    if any(attribute in forbidden for attribute in asked):
        failures.append("forbidden_question")
    minimum = int(expected.get("min_questions", 0))
    maximum = int(expected.get("max_questions", len(decisions)))
    if not minimum <= len(asked) <= maximum:
        failures.append("question_count")
    if not _expected_last_action(expected, decisions):
        failures.append("wrong_stop_or_ask")

    if scenario == DialogueIntent.BUYING.value and len(asked) > 2:
        failures.append("buying_over_asking")
    if scenario == DialogueIntent.BROWSING.value and not asked:
        failures.append("browsing_premature_stop")
    if scenario == DialogueIntent.BOUNDARY.value:
        changed = set().union(*changed_by_turn) if changed_by_turn else set()
        if len(asked) > 1 or any(attribute in changed for attribute in asked):
            failures.append("boundary_handling")
    if scenario == DialogueIntent.INTENT_OVERRIDE.value:
        changed = set().union(*changed_by_turn) if changed_by_turn else set()
        if len(asked) > 1 or any(attribute in changed for attribute in asked):
            failures.append("override_recovery")

    unique_failures = list(dict.fromkeys(failures))
    return {
        "case_id": case_id,
        "scenario": scenario,
        "passed": not unique_failures,
        "failures": unique_failures,
        "observed_intents": observed_intents,
        "decisions": decisions,
        "final_state": state.to_dict(),
    }


def evaluate_cases(cases: Iterable[Mapping[str, object]], *, policy_mode: str) -> dict:
    results = [evaluate_case(case, policy_mode=policy_mode) for case in cases]
    grouped: dict[str, list[dict]] = defaultdict(list)
    failures: Counter[str] = Counter()
    for result in results:
        grouped[result["scenario"]].append(result)
        failures.update(result["failures"])

    def pass_rate(items: list[dict]) -> float:
        return round(sum(int(item["passed"]) for item in items) / len(items), 6) if items else 0.0

    return {
        "policy_mode": policy_mode,
        "case_count": len(results),
        "dialogue_control_pass_rate": pass_rate(results),
        "scenario_pass_rate": {
            scenario: pass_rate(items)
            for scenario, items in sorted(grouped.items())
        },
        "failure_reasons": dict(sorted(failures.items())),
        "failed_cases": [
            {"case_id": item["case_id"], "failures": item["failures"]}
            for item in results
            if not item["passed"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate intent-aware dialogue control in isolation")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--answers", default=str(DEFAULT_ANSWERS_PATH))
    parser.add_argument("--candidate-questions", default=str(DEFAULT_CANDIDATE_QUESTIONS_PATH))
    parser.add_argument("--policy-mode", choices=["legacy", "adaptive", "both"], default="both")
    parser.add_argument("--details", action="store_true", help="include every failed case")
    args = parser.parse_args()
    cases = load_cases(args.cases)
    answer_cases = load_answer_cases(args.answers)
    candidate_question_cases = load_candidate_question_cases(args.candidate_questions)
    modes = ["legacy", "adaptive"] if args.policy_mode == "both" else [args.policy_mode]
    reports = {mode: evaluate_cases(cases, policy_mode=mode) for mode in modes}
    if not args.details:
        reports = {
            mode: {key: value for key, value in report.items() if key != "failed_cases"}
            for mode, report in reports.items()
        }
    answer_reports = {
        "legacy": evaluate_answer_utilization(
            answer_cases,
            contextual_fallback=False,
        ),
        "adaptive": evaluate_answer_utilization(
            answer_cases,
            contextual_fallback=True,
        ),
    }
    if not args.details:
        answer_reports = {
            mode: {key: value for key, value in report.items() if key != "failed_cases"}
            for mode, report in answer_reports.items()
        }
    candidate_question_reports = {
        "static": evaluate_candidate_question_selection(
            candidate_question_cases,
            dynamic=False,
        ),
        "dynamic": evaluate_candidate_question_selection(
            candidate_question_cases,
            dynamic=True,
        ),
    }
    if not args.details:
        candidate_question_reports = {
            mode: {key: value for key, value in report.items() if key != "failed_cases"}
            for mode, report in candidate_question_reports.items()
        }
    payload: dict[str, object] = {
        "dialogue_control_reports": reports,
        "answer_utilization_reports": answer_reports,
        "candidate_question_reports": candidate_question_reports,
    }
    if args.policy_mode == "both":
        payload["dialogue_control_pass_rate_delta"] = round(
            reports["adaptive"]["dialogue_control_pass_rate"]
            - reports["legacy"]["dialogue_control_pass_rate"],
            6,
        )
    payload["answer_utilization_rate_delta"] = round(
        answer_reports["adaptive"]["answer_utilization_rate"]
        - answer_reports["legacy"]["answer_utilization_rate"],
        6,
    )
    payload["candidate_question_utility_rate_delta"] = round(
        candidate_question_reports["dynamic"]["candidate_question_utility_rate"]
        - candidate_question_reports["static"]["candidate_question_utility_rate"],
        6,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
