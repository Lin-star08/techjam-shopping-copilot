from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from math import inf
from typing import Any


RANKING_CONFIG_ENV = "RANKING_CONFIG_NAME"
DEFAULT_NAMED_RANKING_CONFIG = "mild_evidence_light"
RETRIEVAL_ROUTES = (
    "current_message",
    "current_state",
    "category",
    "title",
    "field_category",
    "field_attribute",
    "category_requirement",
    "field_requirement",
    "same_category_popular",
    "field_brand",
    "relaxed",
    "attribute_profile",
    "browsing_profile",
    "popular_category",
    "fallback_bm25",
    "fallback_catalog",
)
HARD_EVIDENCE_ATTRIBUTES = {"category", "color", "material", "brand"}
EXPLICIT_EVIDENCE_ATTRIBUTES = HARD_EVIDENCE_ATTRIBUTES | {"use_case", "feature"}
DEFAULT_RANKING_CONFIG: dict[str, Any] = {
    "rrf_k": 60.0,
    "route_weights": {},
    "default_route_weight": 1.0,
    "hard_evidence_weight": 0.0,
    "soft_evidence_weight": 0.0,
    "max_evidence_boost": 0.0,
}


def _evidence_counts(matched_attributes: Mapping[str, list[str]] | None) -> dict[str, int]:
    attributes = matched_attributes or {}
    explicit_terms = {
        term
        for attribute in EXPLICIT_EVIDENCE_ATTRIBUTES
        for term in attributes.get(attribute, [])
    }
    hard_terms = {
        term
        for attribute in HARD_EVIDENCE_ATTRIBUTES
        for term in attributes.get(attribute, [])
    }
    return {
        "explicit_match_count": len(explicit_terms),
        "hard_match_count": len(hard_terms),
        "matched_attribute_count": sum(1 for values in attributes.values() if values),
    }
RANKING_CONFIGS: dict[str, dict[str, Any]] = {
    "equal": {
        "rrf_k": 60.0,
        "route_weights": {route: 1.0 for route in RETRIEVAL_ROUTES},
        "default_route_weight": 1.0,
    },
    "mild": {
        "rrf_k": 60.0,
        "route_weights": {
            "current_message": 1.15,
            "current_state": 1.10,
            "category": 1.0,
            "category_requirement": 1.05,
            "field_requirement": 0.95,
            "same_category_popular": 0.90,
            "attribute_profile": 0.95,
            "browsing_profile": 0.90,
            "popular_category": 0.80,
            "fallback_bm25": 1.0,
            "fallback_catalog": 0.75,
        },
        "default_route_weight": 1.0,
    },
    "stronger": {
        "rrf_k": 60.0,
        "route_weights": {
            "current_message": 1.30,
            "current_state": 1.15,
            "category": 1.0,
            "category_requirement": 1.10,
            "field_requirement": 0.95,
            "same_category_popular": 0.85,
            "attribute_profile": 0.90,
            "browsing_profile": 0.80,
            "popular_category": 0.65,
            "fallback_bm25": 0.90,
            "fallback_catalog": 0.65,
        },
        "default_route_weight": 1.0,
    },
    "mild_evidence_light": {
        "rrf_k": 60.0,
        "route_weights": {
            "current_message": 1.15,
            "current_state": 1.10,
            "category": 1.0,
            "category_requirement": 1.05,
            "field_requirement": 0.95,
            "same_category_popular": 0.90,
            "attribute_profile": 0.95,
            "browsing_profile": 0.90,
            "popular_category": 0.80,
            "fallback_bm25": 1.0,
            "fallback_catalog": 0.75,
        },
        "default_route_weight": 1.0,
        "hard_evidence_weight": 0.025,
        "soft_evidence_weight": 0.01,
        "max_evidence_boost": 0.12,
    },
    "mild_evidence_tiny": {
        "rrf_k": 60.0,
        "route_weights": {
            "current_message": 1.15,
            "current_state": 1.10,
            "category": 1.0,
            "category_requirement": 1.05,
            "field_requirement": 0.95,
            "same_category_popular": 0.90,
            "attribute_profile": 0.95,
            "browsing_profile": 0.90,
            "popular_category": 0.80,
            "fallback_bm25": 1.0,
            "fallback_catalog": 0.75,
        },
        "default_route_weight": 1.0,
        "hard_evidence_weight": 0.015,
        "soft_evidence_weight": 0.005,
        "max_evidence_boost": 0.08,
    },
    "mild_evidence_medium": {
        "rrf_k": 60.0,
        "route_weights": {
            "current_message": 1.15,
            "current_state": 1.10,
            "category": 1.0,
            "category_requirement": 1.05,
            "field_requirement": 0.95,
            "same_category_popular": 0.90,
            "attribute_profile": 0.95,
            "browsing_profile": 0.90,
            "popular_category": 0.80,
            "fallback_bm25": 1.0,
            "fallback_catalog": 0.75,
        },
        "default_route_weight": 1.0,
        "hard_evidence_weight": 0.04,
        "soft_evidence_weight": 0.015,
        "max_evidence_boost": 0.20,
    },
}


def ranking_config_from_environment() -> dict[str, Any]:
    """Return the selected named config, defaulting to the frozen V2 settings."""
    name = os.environ.get(RANKING_CONFIG_ENV, DEFAULT_NAMED_RANKING_CONFIG).strip()
    name = name or DEFAULT_NAMED_RANKING_CONFIG
    if name not in RANKING_CONFIGS:
        choices = ", ".join(sorted(RANKING_CONFIGS))
        raise ValueError(f"unknown {RANKING_CONFIG_ENV}={name!r}; choose one of: {choices}")
    selected = RANKING_CONFIGS[name]
    return {
        **selected,
        "route_weights": dict(selected["route_weights"]),
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
    for key in ("hard_evidence_weight", "soft_evidence_weight", "max_evidence_boost"):
        value = merged[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{key} must be a non-negative number")
    return merged


def _state_dict(state: object) -> Mapping[str, Any]:
    if isinstance(state, Mapping):
        return state
    to_dict = getattr(state, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
        return value if isinstance(value, Mapping) else {}
    return {}


def _flatten_strings(value: object) -> list[str]:
    if isinstance(value, Mapping):
        return [str(item).casefold() for item in value.values()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).casefold() for item in value]
    return [str(value).casefold()] if value not in (None, "") else []


def evidence_boost_breakdown(
    aggregated_candidate: Mapping[str, Any],
    state: object = None,
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a small product-evidence multiplier with state safety guards."""
    ranking_config = _merged_config(config)
    state_data = _state_dict(state)
    neutral = {str(value) for value in state_data.get("neutral_attributes", []) or []}
    invalidated = state_data.get("invalidated_slots", {})
    invalidated_by_attribute = {
        str(attribute): set(_flatten_strings(values))
        for attribute, values in invalidated.items()
    } if isinstance(invalidated, Mapping) else {}

    attributes = aggregated_candidate.get("matched_attributes", {})
    hard_terms: set[tuple[str, str]] = set()
    soft_terms: set[tuple[str, str]] = set()
    if isinstance(attributes, Mapping):
        for attribute, values in attributes.items():
            attribute_name = str(attribute)
            if attribute_name in neutral or not isinstance(values, (list, tuple, set)):
                continue
            blocked = invalidated_by_attribute.get(attribute_name, set())
            for value in values:
                term = str(value).casefold()
                if not term or term in blocked:
                    continue
                target = hard_terms if attribute_name in HARD_EVIDENCE_ATTRIBUTES else soft_terms
                target.add((attribute_name, term))

    raw_boost = (
        len(hard_terms) * float(ranking_config["hard_evidence_weight"])
        + len(soft_terms) * float(ranking_config["soft_evidence_weight"])
    )
    boost = min(raw_boost, float(ranking_config["max_evidence_boost"]))
    return {
        "hard_evidence_count": len(hard_terms),
        "soft_evidence_count": len(soft_terms),
        "evidence_boost": boost,
        "evidence_multiplier": 1.0 + boost,
    }


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
                "query_terms": [],
                "matched_terms": [],
                "matched_attributes": {},
                "soft_matched_terms": [],
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
        query_terms = candidate.get("query_terms")
        clean_query_terms = (
            [str(term) for term in query_terms if str(term)]
            if isinstance(query_terms, (list, tuple))
            else []
        )
        matched_attributes = candidate.get("matched_attributes")
        clean_matched_attributes: dict[str, list[str]] = {}
        if isinstance(matched_attributes, Mapping):
            for attribute, values in matched_attributes.items():
                if not isinstance(values, (list, tuple, set)):
                    continue
                clean_values = list(dict.fromkeys(str(value) for value in values if str(value)))
                if clean_values:
                    clean_matched_attributes[str(attribute)] = clean_values
        soft_terms = candidate.get("soft_matched_terms")
        clean_soft_terms = (
            [str(term) for term in soft_terms if str(term)]
            if isinstance(soft_terms, (list, tuple))
            else []
        )
        reason = candidate.get("debug_reason")
        evidence = {
            "route": route,
            "route_rank": _valid_route_rank(candidate.get("route_rank")),
            "route_score": candidate.get("route_score"),
            "query_terms": list(dict.fromkeys(clean_query_terms)),
            "matched_terms": list(dict.fromkeys(clean_terms)),
        }
        evidence.update(_evidence_counts(clean_matched_attributes))
        if clean_matched_attributes:
            evidence["matched_attributes"] = clean_matched_attributes
        if clean_soft_terms:
            evidence["soft_matched_terms"] = list(dict.fromkeys(clean_soft_terms))
        if reason not in (None, ""):
            evidence["debug_reason"] = str(reason)
        item["route_evidence"].append(evidence)

        for term in clean_query_terms:
            if term not in item["query_terms"]:
                item["query_terms"].append(term)
        for term in clean_terms:
            if term not in item["matched_terms"]:
                item["matched_terms"].append(term)
        for term in clean_soft_terms:
            if term not in item["soft_matched_terms"]:
                item["soft_matched_terms"].append(term)
        for attribute, values in clean_matched_attributes.items():
            existing = item["matched_attributes"].setdefault(attribute, [])
            for value in values:
                if value not in existing:
                    existing.append(value)
        if reason not in (None, "") and str(reason) not in item["debug_reasons"]:
            item["debug_reasons"].append(str(reason))

    for item in aggregated.values():
        item.update(_evidence_counts(item["matched_attributes"]))

    return list(aggregated.values())


def reciprocal_rank_fusion_score(
    aggregated_candidate: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> float:
    """Calculate RRF using the best valid rank contributed by each route."""
    return sum(
        item["contribution"]
        for item in reciprocal_rank_fusion_contributions(aggregated_candidate, config)
    )


def reciprocal_rank_fusion_contributions(
    aggregated_candidate: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return per-route contributions used by the production RRF score."""
    ranking_config = _merged_config(config)
    best_rank_by_route: dict[str, int] = {}
    evidence_records = aggregated_candidate.get("route_evidence", [])
    if not isinstance(evidence_records, list):
        return []
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
    contributions: list[dict[str, Any]] = []
    for route in sorted(best_rank_by_route):
        route_rank = best_rank_by_route[route]
        route_weight = float(weights.get(route, default_weight))
        contributions.append(
            {
                "route": route,
                "route_rank": route_rank,
                "route_weight": route_weight,
                "contribution": route_weight / (rrf_k + route_rank),
            }
        )
    return contributions


def ranking_score_breakdown(
    aggregated_candidate: Mapping[str, Any],
    config: Mapping[str, Any] | None = None,
    *,
    state: object = None,
) -> dict[str, Any]:
    """Expose the production RRF contribution calculation for internal debugging."""
    contributions = reciprocal_rank_fusion_contributions(aggregated_candidate, config)
    valid_ranks = [item["route_rank"] for item in contributions]
    rrf_score = sum(item["contribution"] for item in contributions)
    evidence = evidence_boost_breakdown(aggregated_candidate, state, config)
    return {
        "parent_asin": str(aggregated_candidate.get("parent_asin") or ""),
        "rrf_score": rrf_score,
        "final_score": rrf_score * evidence["evidence_multiplier"],
        "contributions": contributions,
        "best_route_rank": min(valid_ranks, default=None),
        **evidence,
    }


def rerank_candidates(
    candidates: Iterable[Mapping[str, Any]] | None,
    state: object = None,
    top_k: int = 10,
    config: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Aggregate, rank with RRF, deterministically sort, and return Top K."""
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
        breakdown = ranking_score_breakdown(item, ranking_config, state=state)
        item["rrf_score"] = breakdown["rrf_score"]
        item["evidence_boost"] = breakdown["evidence_boost"]
        item["final_score"] = breakdown["final_score"]

    ranked.sort(
        key=lambda item: (
            -item["final_score"],
            item["best_route_rank"] if item["best_route_rank"] is not None else inf,
            item["parent_asin"],
        )
    )
    return ranked[:top_k]
