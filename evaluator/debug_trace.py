from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

from evaluator.local_evaluator import (
    MAX_TURNS,
    TOP_K,
    catalog_index,
    coarse_category,
    customer_reply,
    initial_message,
    load_jsonl,
    materialize_hidden_fields,
    normalize_recommendations,
)
from starter.agent import Agent


def _fallback_response() -> dict:
    return {"message": "", "ask_attribute": None, "recommendations": []}


def trace_session(
    agent: Agent,
    sample: dict,
    catalog_ids: set[str],
    categories: dict[str, list[str]],
    products: dict[str, dict],
) -> dict:
    sample_id = str(sample["sample_id"])
    session_id = f"debug_{sample_id}"
    target = str(sample["ground_truth"]["parent_asin"])
    trace: list[dict] = []
    reset_error: dict | None = None

    try:
        agent.reset(session_id, sample["user_profile"])
    except Exception as exc:  # Debug output intentionally preserves the exception.
        reset_error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }

    effective_intent_card, effective_behavior = materialize_hidden_fields(sample, products)
    effective_sample = {
        **sample,
        "intent_card": effective_intent_card,
        "behavior": effective_behavior,
    }
    disclosed: set[str] = set()
    boundary_used = False
    override_applied = sample["scenario_type"] != "intent_override"
    user_message = initial_message(effective_sample, coarse_category(categories.get(target, [])), disclosed)
    hit_turn: int | None = None
    best_rank: int | None = None

    for turn in range(1, MAX_TURNS + 1):
        started = time.perf_counter()
        response_error: dict | None = None
        raw_response: object
        try:
            raw_response = agent.respond(session_id, user_message, turn, TOP_K)
        except Exception as exc:  # The official evaluator converts this to an empty response.
            raw_response = None
            response_error = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        latency_ms = round((time.perf_counter() - started) * 1000.0, 3)

        response_valid = isinstance(raw_response, dict) and isinstance(raw_response.get("message"), str)
        effective_response = raw_response if response_valid else _fallback_response()
        ranked = normalize_recommendations(effective_response.get("recommendations"), catalog_ids)
        target_rank = ranked.index(target) + 1 if target in ranked else None
        eligible_for_hit = override_applied

        trace.append({
            "turn": turn,
            "user_message": user_message,
            "response_valid": response_valid,
            "response_error": response_error,
            "agent_message": effective_response.get("message", ""),
            "ask_attribute": effective_response.get("ask_attribute"),
            "recommendations": ranked,
            "target_rank": target_rank,
            "eligible_for_hit": eligible_for_hit,
            "disclosed_constraints": sorted(disclosed),
            "latency_ms": latency_ms,
            "usage": effective_response.get("usage"),
        })

        if eligible_for_hit and target_rank is not None:
            hit_turn = turn
            best_rank = target_rank
            break
        if turn == MAX_TURNS:
            break

        override = effective_behavior.get("override") or {}
        if not override_applied and turn + 1 == int(override.get("turn", 3)):
            override_applied = True
            new_value = str(override.get("new_value", ""))
            if new_value:
                disclosed.add(new_value)
            user_message = str(override.get("message", "Actually, please ignore my earlier preference."))
        else:
            user_message, boundary_used = customer_reply(
                effective_sample,
                effective_response.get("ask_attribute"),
                disclosed,
                boundary_used,
            )

    return {
        "sample_id": sample_id,
        "scenario_type": sample["scenario_type"],
        "session_id": session_id,
        "target_parent_asin": target,
        "reset_error": reset_error,
        "hit": hit_turn is not None,
        "first_hit_turn": hit_turn,
        "best_rank": best_rank,
        "reciprocal_rank": 0.0 if best_rank is None else 1.0 / best_rank,
        "intent_card": effective_intent_card,
        "behavior": effective_behavior,
        "turns": trace,
    }


def _select_samples(samples: list[dict], sample_ids: list[str], scenario: str | None, all_rows: bool, limit: int) -> list[dict]:
    if sample_ids:
        requested = set(sample_ids)
        selected = [sample for sample in samples if sample["sample_id"] in requested]
        missing = requested - {sample["sample_id"] for sample in selected}
        if missing:
            raise ValueError(f"unknown sample_id(s): {', '.join(sorted(missing))}")
        return selected
    selected = [sample for sample in samples if scenario is None or sample["scenario_type"] == scenario]
    return selected if all_rows else selected[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay sessions with per-turn debug traces")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--dataset", default="data/public_set.jsonl")
    parser.add_argument("--output", default="debug_traces.json")
    parser.add_argument("--sample-id", action="append", default=[])
    parser.add_argument("--scenario", choices=["buying", "browsing", "intent_override", "boundary"])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--all", action="store_true", help="Trace all matching sessions")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    samples = load_jsonl(args.dataset)
    selected = _select_samples(samples, args.sample_id, args.scenario, args.all, args.limit)
    catalog_ids, categories, products = catalog_index(args.catalog)
    agent = Agent(args.catalog)
    sessions = [trace_session(agent, sample, catalog_ids, categories, products) for sample in selected]
    payload = {
        "catalog": args.catalog,
        "dataset": args.dataset,
        "sample_count": len(sessions),
        "hits": sum(int(session["hit"]) for session in sessions),
        "sessions": sessions,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "sessions"}, indent=2))


if __name__ == "__main__":
    main()
