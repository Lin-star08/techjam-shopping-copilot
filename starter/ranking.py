from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import inf
from typing import Any


DEFAULT_RANKING_CONFIG: dict[str, Any] = {
    "rrf_k": 60.0,
    "route_weights": {},
    "default_route_weight": 1.0,
}


def _valid_route_rank(value: object) -> int | None:
    """Return a positive integer route rank, or None when it is unusable."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _merged_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    """Merge and validate the small set of supported ranking parameters."""
    merged = {
        **DEFAULT_RANKING_CONFIG,
        **(dict(config) if config is not None else {}),
    }
    rrf_k = merged["rrf_k"]
    default_weight = merged["default_route_weight"]
    route_weights = merged["route_weights"]
    if isinstance(rrf_k, bool) or not isinstance(rrf_k, (int, float)) or rrf_k < 0:
        raise ValueError("rrf_k must be a non-negative number")
    if (
        isinstance(default_weight, bool)
        or not isinstance(default_weight, (int, float))
        or default_weight < 0
    ):
        raise ValueError("default_route_weight must be a non-negative number")
    if not isinstance(route_weights, Mapping):
        raise TypeError("route_weights must be a mapping")
    for route, weight in route_weights.items():
        if not isinstance(route, str):
            raise TypeError("route_weights keys must be strings")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
            raise ValueError("route weights must be non-negative numbers")
    return merged


def aggregate_candidates(candidates: Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    """Group retrieval candidates by parent_asin without losing route evidence."""
    aggregated: dict[str, dict[str, Any]] = {}
    for candidate in candidates or ():
        if not isinstance(candidate, Mapping):
            continue
        parent_asin = str(candidate.get("parent_asin") or "").strip()
        if not parent_asin:
            continue

        item = aggregated.setdefault(
            parent_asin,
            {
                "parent_asin": parent_asin,
                "route_evidence": [],
                "matched_terms": [],
                "debug_reasons": [],
            },
        )
        route = str(candidate.get("route") or "unknown").strip() or "unknown"
        terms = candidate.get("matched_terms")
        clean_terms = (
            [str(term) for term in terms if str(term)]
            if isinstance(terms, (list, tuple))
            else []
        )
        reason = candidate.get("debug_reason")
        evidence = {
            "route": route,
            "route_rank": _valid_route_rank(candidate.get("route_rank")),
            "route_score": candidate.get("route_score"),
            "matched_terms": list(dict.fromkeys(clean_terms)),
        }
        if reason not in (None, ""):
            evidence["debug_reason"] = str(reason)
        item["route_evidence"].append(evidence)

        for term in clean_terms:
            if term not in item["matched_terms"]:
                item["matched_terms"].append(term)
        if reason not in (None, "") and str(reason) not in item["debug_reasons"]:
            item["debug_reasons"].append(str(reason))

    return list(aggregated.values())


def reciprocal_rank_fusion_score(
    aggregated_candidate: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> float:
    """Calculate RRF using the best valid rank contributed by each route."""
    ranking_config = _merged_config(config)
    best_rank_by_route: dict[str, int] = {}
    evidence_records = aggregated_candidate.get("route_evidence", [])
    if not isinstance(evidence_records, list):
        return 0.0
    for evidence in evidence_records:
        if not isinstance(evidence, Mapping):
            continue
        route = str(evidence.get("route") or "unknown")
        route_rank = _valid_route_rank(evidence.get("route_rank"))
        if route_rank is None:
            continue
        best_rank_by_route[route] = min(route_rank, best_rank_by_route.get(route, route_rank))

    weights = ranking_config["route_weights"]
    default_weight = float(ranking_config["default_route_weight"])
    rrf_k = float(ranking_config["rrf_k"])
    return sum(
        float(weights.get(route, default_weight)) / (rrf_k + route_rank)
        for route, route_rank in best_rank_by_route.items()
    )


def rerank_candidates(
    candidates: Iterable[Mapping[str, Any]] | None,
    state: object = None,
    top_k: int = 10,
    config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate, rank with RRF, deterministically sort, and return Top K."""
    del state  # Reserved for a later, contract-compatible preference stage.
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 0:
        raise ValueError("top_k must be a non-negative integer")
    ranking_config = _merged_config(config)
    ranked = aggregate_candidates(candidates)
    for item in ranked:
        valid_ranks = [
            evidence["route_rank"]
            for evidence in item["route_evidence"]
            if evidence["route_rank"] is not None
        ]
        item["best_route_rank"] = min(valid_ranks, default=None)
        item["final_score"] = reciprocal_rank_fusion_score(item, ranking_config)

    ranked.sort(
        key=lambda item: (
            -item["final_score"],
            item["best_route_rank"] if item["best_route_rank"] is not None else inf,
            item["parent_asin"],
        )
    )
    return ranked[:top_k]
