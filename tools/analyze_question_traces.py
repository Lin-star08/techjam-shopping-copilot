"""Summarize clarification-question yield and outcome from debug traces."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Iterable, Mapping


def _is_answer(message: str) -> bool:
    return message.casefold().lstrip().startswith("for that, what matters is:")


def _is_contrastive(message: str) -> bool:
    lowered = message.casefold()
    return "to narrow these down" in lowered and " or " in lowered


def summarize_sessions(sessions: Iterable[Mapping[str, object]]) -> dict:
    per_attribute: dict[str, Counter[str]] = defaultdict(Counter)
    sequence_counts: Counter[str] = Counter()
    misses: list[dict] = []
    session_list = list(sessions)

    for session in session_list:
        turns = [turn for turn in session.get("turns", []) if isinstance(turn, Mapping)]
        asked_sequence: list[str] = []
        for index, turn in enumerate(turns):
            attribute = turn.get("ask_attribute")
            if not isinstance(attribute, str) or not attribute:
                continue
            asked_sequence.append(attribute)
            stats = per_attribute[attribute]
            stats["asked"] += 1
            if _is_contrastive(str(turn.get("agent_message", ""))):
                stats["contrastive"] += 1
            next_turn = turns[index + 1] if index + 1 < len(turns) else None
            if next_turn is not None:
                next_message = str(next_turn.get("user_message", ""))
                if _is_answer(next_message):
                    stats["answered"] += 1
                elif "no preference" in next_message.casefold():
                    stats["declined"] += 1
                if next_turn.get("eligible_for_hit") and next_turn.get("target_rank") is not None:
                    stats["next_turn_hit"] += 1
            if session.get("hit"):
                stats["eventual_hit"] += 1
        sequence_counts[" > ".join(asked_sequence) or "<none>"] += 1
        if not session.get("hit"):
            misses.append({
                "sample_id": str(session.get("sample_id", "")),
                "scenario": str(session.get("scenario_type", "")),
                "asked_sequence": asked_sequence,
                "intent_card": session.get("intent_card", {}),
            })

    attribute_report: dict[str, dict] = {}
    for attribute, stats in sorted(per_attribute.items()):
        asked = stats["asked"]
        attribute_report[attribute] = {
            **dict(stats),
            "answer_yield": round(stats["answered"] / asked, 6) if asked else 0.0,
            "next_turn_hit_rate": round(stats["next_turn_hit"] / asked, 6) if asked else 0.0,
            "eventual_hit_rate": round(stats["eventual_hit"] / asked, 6) if asked else 0.0,
        }
    return {
        "session_count": len(session_list),
        "hit_count": sum(int(bool(session.get("hit"))) for session in session_list),
        "miss_count": len(misses),
        "attribute_report": attribute_report,
        "top_question_sequences": sequence_counts.most_common(15),
        "misses": misses,
    }


def compare_results(baseline: Mapping[str, object], current: Mapping[str, object]) -> dict:
    baseline_hits = {
        str(item.get("sample_id", "")): bool(item.get("hit"))
        for item in baseline.get("sessions", [])
        if isinstance(item, Mapping)
    }
    current_hits = {
        str(item.get("sample_id", "")): bool(item.get("hit"))
        for item in current.get("sessions", [])
        if isinstance(item, Mapping)
    }
    shared = sorted(set(baseline_hits) & set(current_hits))
    return {
        "shared_sample_count": len(shared),
        "gained_hits": [sample_id for sample_id in shared if not baseline_hits[sample_id] and current_hits[sample_id]],
        "lost_hits": [sample_id for sample_id in shared if baseline_hits[sample_id] and not current_hits[sample_id]],
        "unchanged_hits": sum(baseline_hits[item] and current_hits[item] for item in shared),
        "unchanged_misses": sum(not baseline_hits[item] and not current_hits[item] for item in shared),
    }


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze per-turn clarification traces")
    parser.add_argument("trace")
    parser.add_argument("--baseline")
    parser.add_argument("--current")
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    trace = _load(args.trace)
    report = summarize_sessions(trace.get("sessions", []))
    if not args.details:
        report.pop("misses", None)
    payload: dict[str, object] = {"question_trace_report": report}
    if args.baseline and args.current:
        payload["version_comparison"] = compare_results(
            _load(args.baseline),
            _load(args.current),
        )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
