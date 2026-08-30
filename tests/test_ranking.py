from __future__ import annotations

import json
import tempfile
import unittest
from math import isclose
from os import environ
from pathlib import Path
from unittest.mock import patch

from starter.agent import Agent
from starter.ranking import (
    RANKING_CONFIGS,
    aggregate_candidates,
    ranking_config_from_environment,
    ranking_score_breakdown,
    reciprocal_rank_fusion_score,
    rerank_candidates,
)


class RankingTest(unittest.TestCase):
    def tearDown(self) -> None:
        environ.pop("RANKING_CONFIG_NAME", None)

    def test_duplicate_asin_is_returned_once_with_both_routes(self) -> None:
        candidates = [
            {"parent_asin": "A", "route": "message", "route_rank": 2},
            {"parent_asin": "A", "route": "state", "route_rank": 5},
        ]
        result = rerank_candidates(candidates)
        self.assertEqual([item["parent_asin"] for item in result], ["A"])
        self.assertEqual(
            [evidence["route"] for evidence in result[0]["route_evidence"]],
            ["message", "state"],
        )

    def test_aggregation_preserves_route_fields(self) -> None:
        candidate = {
            "parent_asin": "A",
            "route": "message",
            "route_rank": 3,
            "route_score": 12.5,
            "debug_reason": "matched query",
        }
        evidence = aggregate_candidates([candidate])[0]["route_evidence"][0]
        self.assertEqual(evidence["route_rank"], 3)
        self.assertEqual(evidence["route_score"], 12.5)
        self.assertEqual(evidence["debug_reason"], "matched query")

    def test_lower_route_rank_has_higher_rrf_score(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "LOW", "route": "message", "route_rank": 8},
            {"parent_asin": "HIGH", "route": "message", "route_rank": 1},
        ])
        self.assertEqual([item["parent_asin"] for item in result], ["HIGH", "LOW"])

    def test_raw_score_scale_does_not_affect_ranking(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "A", "route": "bm25", "route_rank": 2, "route_score": 1e20},
            {"parent_asin": "B", "route": "category", "route_rank": 1, "route_score": 0.001},
        ])
        self.assertEqual([item["parent_asin"] for item in result], ["B", "A"])

    def test_top_k_is_applied(self) -> None:
        candidates = [
            {"parent_asin": str(index), "route": "message", "route_rank": index + 1}
            for index in range(5)
        ]
        self.assertEqual(len(rerank_candidates(candidates, top_k=3)), 3)

    def test_repeated_runs_are_identical(self) -> None:
        candidates = [
            {"parent_asin": "B", "route": "message", "route_rank": 1},
            {"parent_asin": "A", "route": "message", "route_rank": 1},
        ]
        self.assertEqual(rerank_candidates(candidates), rerank_candidates(candidates))
        self.assertEqual(
            [item["parent_asin"] for item in rerank_candidates(candidates)],
            ["A", "B"],
        )

    def test_empty_candidates(self) -> None:
        self.assertEqual(rerank_candidates([]), [])
        self.assertEqual(rerank_candidates(None), [])

    def test_missing_route_rank_is_safe(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "MISSING", "route": "message"},
            {"parent_asin": "VALID", "route": "message", "route_rank": 4},
        ])
        self.assertEqual([item["parent_asin"] for item in result], ["VALID", "MISSING"])
        self.assertEqual(result[1]["final_score"], 0.0)

    def test_missing_route_score_is_safe(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "A", "route": "message", "route_rank": 1},
        ])
        self.assertEqual(result[0]["route_evidence"][0]["route_score"], None)

    def test_matched_terms_are_merged_and_deduplicated(self) -> None:
        aggregated = aggregate_candidates([
            {"parent_asin": "A", "route": "message", "matched_terms": ["blue", "shoe"]},
            {"parent_asin": "A", "route": "state", "matched_terms": ["shoe", "running"]},
        ])
        self.assertEqual(aggregated[0]["matched_terms"], ["blue", "shoe", "running"])

    def test_all_output_asins_are_unique(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "A", "route": "one", "route_rank": 1},
            {"parent_asin": "A", "route": "two", "route_rank": 2},
            {"parent_asin": "B", "route": "one", "route_rank": 3},
        ])
        asins = [item["parent_asin"] for item in result]
        self.assertEqual(len(asins), len(set(asins)))

    def test_route_weights_and_rrf_k_are_configurable(self) -> None:
        result = rerank_candidates(
            [
                {"parent_asin": "A", "route": "weak", "route_rank": 1},
                {"parent_asin": "B", "route": "strong", "route_rank": 4},
            ],
            config={"rrf_k": 10, "route_weights": {"strong": 2.0}},
        )
        self.assertEqual([item["parent_asin"] for item in result], ["B", "A"])

    def test_duplicate_records_from_one_route_count_only_once(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "A", "route": "message", "route_rank": 2},
            {"parent_asin": "A", "route": "message", "route_rank": 3},
            {"parent_asin": "B", "route": "message", "route_rank": 1},
        ])
        self.assertEqual([item["parent_asin"] for item in result], ["B", "A"])

    def test_actual_retrieval_routes_are_fused(self) -> None:
        candidates = [
            {
                "parent_asin": "A",
                "route": "current_message",
                "route_rank": 2,
                "route_score": -12.0,
                "matched_terms": ["brown", "shoes"],
                "debug_reason": "matched via current_message",
            },
            {
                "parent_asin": "A",
                "route": "current_state",
                "route_rank": 3,
                "route_score": -0.01,
                "matched_terms": ["shoes", "walking"],
                "debug_reason": "matched via current_state",
            },
            {
                "parent_asin": "B",
                "route": "category",
                "route_rank": 1,
                "route_score": 0.0,
                "matched_terms": ["shoes"],
                "debug_reason": "matched via category",
            },
        ]

        result = rerank_candidates(candidates)

        self.assertEqual([item["parent_asin"] for item in result], ["A", "B"])
        self.assertEqual(
            {evidence["route"] for evidence in result[0]["route_evidence"]},
            {"current_message", "current_state"},
        )

    def test_invalid_route_ranks_do_not_crash_or_score(self) -> None:
        result = rerank_candidates([
            {"parent_asin": "ZERO", "route": "current_message", "route_rank": 0},
            {"parent_asin": "TEXT", "route": "current_state", "route_rank": "1"},
            {"parent_asin": "BOOL", "route": "category", "route_rank": True},
        ])

        self.assertEqual([item["parent_asin"] for item in result], ["BOOL", "TEXT", "ZERO"])
        self.assertTrue(all(item["final_score"] == 0.0 for item in result))

    def test_agent_passes_multi_route_candidates_through_ranking(self) -> None:
        products = [
            {
                "parent_asin": "A",
                "title": "Brown leather walking shoes",
                "features": ["comfortable"],
                "details": {"color": "brown", "material": "leather"},
                "description": ["walking shoes"],
                "categories": ["Clothing", "Shoes"],
                "store": "Example",
                "price": 49.0,
            },
            {
                "parent_asin": "B",
                "title": "Black winter boots",
                "features": ["warm"],
                "details": {"color": "black"},
                "description": ["outdoor boots"],
                "categories": ["Clothing", "Boots"],
                "store": "Example",
                "price": 89.0,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            catalog_path = Path(directory) / "catalog.jsonl"
            catalog_path.write_text(
                "".join(json.dumps(product) + "\n" for product in products),
                encoding="utf-8",
            )
            agent = Agent(catalog_path)
            agent.reset("s1", {"preference_tags": ["comfort"], "summary": "walking shoes"})
            captured_candidates: list[dict] = []

            real_rerank = rerank_candidates

            def capture(candidates, state=None, top_k=10, config=None):
                captured_candidates.extend(candidates)
                return real_rerank(candidates, state, top_k, config)

            with patch("starter.agent.rerank_candidates", side_effect=capture):
                response = agent.respond("s1", "brown leather shoes", 1, 10)

        routes_for_a = {
            candidate["route"]
            for candidate in captured_candidates
            if candidate["parent_asin"] == "A"
        }
        self.assertIn("current_message", routes_for_a)
        self.assertIn("current_state", routes_for_a)
        self.assertEqual(
            len(response["recommendations"]),
            len({item["parent_asin"] for item in response["recommendations"]}),
        )
        self.assertTrue(all(set(item) == {"parent_asin", "score"} for item in response["recommendations"]))

    def test_unset_and_equal_configs_preserve_v11_equal_weights(self) -> None:
        environ.pop("RANKING_CONFIG_NAME", None)
        unset = ranking_config_from_environment()
        environ["RANKING_CONFIG_NAME"] = "equal"
        equal = ranking_config_from_environment()

        self.assertEqual(unset, equal)
        self.assertEqual(set(equal["route_weights"].values()), {1.0})
        self.assertEqual(equal["rrf_k"], 60.0)

    def test_unknown_named_config_fails_clearly(self) -> None:
        environ["RANKING_CONFIG_NAME"] = "not-a-config"

        with self.assertRaisesRegex(ValueError, "unknown RANKING_CONFIG_NAME"):
            ranking_config_from_environment()

    def test_current_message_weight_changes_expected_order(self) -> None:
        candidates = [
            {"parent_asin": "EXPLICIT", "route": "current_message", "route_rank": 1},
            {"parent_asin": "MULTI", "route": "popular_category", "route_rank": 30},
            {"parent_asin": "MULTI", "route": "fallback_catalog", "route_rank": 30},
        ]

        equal = rerank_candidates(candidates, config=RANKING_CONFIGS["equal"])
        stronger = rerank_candidates(candidates, config=RANKING_CONFIGS["stronger"])

        self.assertEqual(equal[0]["parent_asin"], "MULTI")
        self.assertEqual(stronger[0]["parent_asin"], "EXPLICIT")

    def test_unknown_route_uses_default_weight(self) -> None:
        aggregated = aggregate_candidates([
            {"parent_asin": "A", "route": "future_route", "route_rank": 2},
        ])[0]
        config = {"rrf_k": 60.0, "route_weights": {}, "default_route_weight": 0.5}

        self.assertEqual(reciprocal_rank_fusion_score(aggregated, config), 0.5 / 62.0)

    def test_score_breakdown_sums_to_production_score_without_changing_order(self) -> None:
        candidates = [
            {"parent_asin": "A", "route": "current_message", "route_rank": 2},
            {"parent_asin": "A", "route": "current_message", "route_rank": 5},
            {"parent_asin": "A", "route": "category", "route_rank": 3},
            {"parent_asin": "B", "route": "current_state", "route_rank": 1},
        ]
        ranked_before = rerank_candidates(candidates, config=RANKING_CONFIGS["mild"])
        breakdowns = [
            ranking_score_breakdown(item, RANKING_CONFIGS["mild"])
            for item in ranked_before
        ]
        ranked_after = rerank_candidates(candidates, config=RANKING_CONFIGS["mild"])

        self.assertEqual(ranked_before, ranked_after)
        for item, breakdown in zip(ranked_before, breakdowns):
            self.assertTrue(isclose(item["final_score"], breakdown["final_score"]))
            self.assertTrue(isclose(
                breakdown["final_score"],
                sum(part["contribution"] for part in breakdown["contributions"]),
            ))
        a_breakdown = next(item for item in breakdowns if item["parent_asin"] == "A")
        self.assertEqual(
            [part["route"] for part in a_breakdown["contributions"]],
            ["category", "current_message"],
        )


if __name__ == "__main__":
    unittest.main()
