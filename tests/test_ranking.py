from __future__ import annotations

import unittest

from starter.ranking import aggregate_candidates, rerank_candidates


class RankingTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
