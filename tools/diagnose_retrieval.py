from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import (
    MAX_TURNS,
    TOP_K,
    coarse_category,
    customer_reply,
    initial_message,
    load_jsonl,
    materialize_hidden_fields,
)
from starter.agent import Agent
from starter.constraints import apply_hard_filters, hard_filter_diagnostics, parse_constraints
from starter.retrieval import candidate_recall


def _target_candidate_info(candidates: list[dict], target_parent_asin: str) -> dict:
    target = str(target_parent_asin)
    for index, candidate in enumerate(candidates, start=1):
        if str(candidate.get("parent_asin") or "") == target:
            return {
                "target_candidate_rank": index,
                "target_best_route": candidate.get("route"),
                "target_route_hits": candidate.get("route_hits", 1),
                "target_routes": [route.get("route") for route in candidate.get("routes", [])],
            }
    return {
        "target_candidate_rank": None,
        "target_best_route": None,
        "target_route_hits": 0,
        "target_routes": [],
    }


def classify_failure(before: dict, after: dict, filters: dict, top_k: int = TOP_K) -> str:
    if filters.get("target_filtered_out"):
        return "filter_failure"
    position = after.get("target_position") or before.get("target_position")
    if position is None:
        return "recall_failure"
    if int(position) > top_k:
        return "rerank_failure"
    return "top_k_hit"


def diagnose(catalog_path: str | Path, dataset_path: str | Path) -> dict:
    agent = Agent(catalog_path)
    samples = load_jsonl(dataset_path)
    scenario_summary: dict[str, Counter] = defaultdict(Counter)
    missed_category_summary: dict[str, Counter] = defaultdict(Counter)
    misses: list[dict] = []

    for sample in samples:
        session_id = f"diag_{sample['sample_id']}"
        agent.reset(session_id, sample["user_profile"])
        target = str(sample["ground_truth"]["parent_asin"])
        product = agent.retriever.product_lookup[target]
        effective_card, effective_behavior = materialize_hidden_fields(
            sample,
            agent.retriever.product_lookup,
        )
        effective_sample = {**sample, "intent_card": effective_card, "behavior": effective_behavior}
        disclosed: set[str] = set()
        boundary_used = False
        override_applied = sample["scenario_type"] != "intent_override"
        user_message = initial_message(
            effective_sample,
            coarse_category([str(value) for value in product.get("categories") or []]),
            disclosed,
        )
        best: dict | None = None

        for turn in range(1, MAX_TURNS + 1):
            state = agent._sessions[session_id]
            constraints = parse_constraints(user_message, last_asked_attribute=state.last_asked_attribute)
            state.apply(constraints, turn)
            user_profile = agent._profiles.get(session_id, {})
            fallback = agent.retriever.fallback_candidates(user_message, limit=max(50, TOP_K))
            candidates = agent.retriever.retrieve_all_routes(
                state,
                user_profile,
                user_message,
                constraints,
                fallback_candidates=fallback,
                limit=100,
            )
            filtered = apply_hard_filters(
                candidates,
                state.hard_constraints,
                agent.retriever.product_lookup,
                min_results=TOP_K,
            )
            before = candidate_recall(candidates, target, cutoffs=(50, 100))
            after = candidate_recall(filtered, target, cutoffs=(50, 100))
            filters = hard_filter_diagnostics(candidates, filtered, target)
            target_info = _target_candidate_info(candidates, target)
            failure_type = classify_failure(before, after, filters, TOP_K)
            if best is None or (
                after["target_position"] is not None
                and (
                    best["after"]["target_position"] is None
                    or int(after["target_position"]) < int(best["after"]["target_position"])
                )
            ):
                best = {
                    "turn": turn,
                    "message": user_message,
                    "before": before,
                    "after": after,
                    "filters": filters,
                    "target_info": target_info,
                    "failure_type": failure_type,
                }
            if override_applied and after["recall_at_50"]:
                break
            if turn == MAX_TURNS:
                break
            override = effective_sample.get("behavior", {}).get("override") or {}
            if not override_applied and turn + 1 == int(override.get("turn", 3)):
                override_applied = True
                new_value = str(override.get("new_value", ""))
                if new_value:
                    disclosed.add(new_value)
                user_message = str(override.get("message", "Actually, please ignore my earlier preference."))
            else:
                user_message, boundary_used = customer_reply(
                    effective_sample,
                    None,
                    disclosed,
                    boundary_used,
                )

        assert best is not None
        scenario = str(sample["scenario_type"])
        if best["before"]["recall_at_50"]:
            scenario_summary[scenario]["candidate_recall_at_50"] += 1
        if best["before"]["recall_at_100"]:
            scenario_summary[scenario]["candidate_recall_at_100"] += 1
        if best["after"]["recall_at_50"]:
            scenario_summary[scenario]["post_filter_recall_at_50"] += 1
        if best["after"]["recall_at_100"]:
            scenario_summary[scenario]["post_filter_recall_at_100"] += 1
        if best["filters"].get("target_filtered_out"):
            scenario_summary[scenario]["target_filtered_out"] += 1
        scenario_summary[scenario][best["failure_type"]] += 1
        if not best["after"]["recall_at_100"]:
            scenario_summary[scenario]["not_recalled"] += 1
            for category in product.get("categories") or []:
                missed_category_summary[scenario][str(category)] += 1
            if len(misses) < 20:
                misses.append({
                    "sample_id": sample["sample_id"],
                    "scenario_type": scenario,
                    "target_parent_asin": target,
                    "best_turn": best["turn"],
                    "best_message": best["message"],
                    "target_candidate_rank": best["target_info"]["target_candidate_rank"],
                    "target_best_route": best["target_info"]["target_best_route"],
                    "target_route_hits": best["target_info"]["target_route_hits"],
                    "target_routes": best["target_info"]["target_routes"],
                    "target_after_filter": best["after"]["target_position"] is not None,
                    "failure_type": best["failure_type"],
                    "target_title": product.get("title"),
                    "target_categories": product.get("categories"),
                })

    summary = {}
    scenario_counts = Counter(str(sample["scenario_type"]) for sample in samples)
    for scenario, counter in sorted(scenario_summary.items()):
        count = scenario_counts[scenario]
        summary[scenario] = {
            "sample_count": count,
            "candidate_recall_at_50": round(counter["candidate_recall_at_50"] / count, 6),
            "candidate_recall_at_100": round(counter["candidate_recall_at_100"] / count, 6),
            "post_filter_recall_at_50": round(counter["post_filter_recall_at_50"] / count, 6),
            "post_filter_recall_at_100": round(counter["post_filter_recall_at_100"] / count, 6),
            "target_filtered_out": counter["target_filtered_out"],
            "recall_failure": counter["recall_failure"],
            "rerank_failure": counter["rerank_failure"],
            "filter_failure": counter["filter_failure"],
            "top_k_hit": counter["top_k_hit"],
            "not_recalled": counter["not_recalled"],
        }
    missed_categories = {
        scenario: counter.most_common(12)
        for scenario, counter in sorted(missed_category_summary.items())
    }
    return {
        "scenario_summary": summary,
        "missed_category_summary": missed_categories,
        "example_not_recalled": misses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose retrieval recall on the public development set.")
    parser.add_argument("--catalog", default="data/catalog.jsonl")
    parser.add_argument("--dataset", default="data/public_set.jsonl")
    args = parser.parse_args()
    print(json.dumps(diagnose(args.catalog, args.dataset), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
