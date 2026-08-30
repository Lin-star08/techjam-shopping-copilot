from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starter.agent import Agent
from starter.constraints import apply_hard_filters, extract_basic_hard_constraints, hard_filter_diagnostics
from starter.retrieval import (
    CatalogRetriever,
    candidate_recall,
    category_queries_from_text,
    ensure_valid_recommendations,
    merge_candidates,
)
from starter.state import SessionState
from tools.diagnose_retrieval import _target_candidate_info


CATALOG_ROWS = [
    {
        "parent_asin": "A",
        "title": "Brown leather walking shoes",
        "features": ["comfortable", "leather upper"],
        "details": {"color": "brown", "material": "leather"},
        "description": ["casual walking shoe"],
        "categories": ["Clothing", "Shoes"],
        "store": "Example",
        "price": 49.0,
    },
    {
        "parent_asin": "B",
        "title": "Black winter boots",
        "features": ["warm leather boot"],
        "details": {"color": "black", "material": "leather"},
        "description": ["winter outdoor boot"],
        "categories": ["Clothing", "Boots"],
        "store": "Example",
        "price": 89.0,
    },
    {
        "parent_asin": "C",
        "title": "Blue cotton shirt",
        "features": ["breathable cotton"],
        "details": {"color": "blue", "material": "cotton"},
        "description": ["casual shirt"],
        "categories": ["Clothing", "Shirts"],
        "store": "Example",
        "price": None,
    },
    {
        "parent_asin": "D",
        "title": "Red travel bag",
        "features": ["durable nylon"],
        "details": {"color": "red", "material": "nylon"},
        "description": ["small travel bag"],
        "categories": ["Bags"],
        "store": "Example",
        "price": 35.0,
    },
    {
        "parent_asin": "E",
        "title": "Gold pendant necklace",
        "features": ["minimal jewelry"],
        "details": {"color": "gold", "material": "metal"},
        "description": ["accessories necklace"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Jewelry", "Necklaces"],
        "store": "Example",
        "price": 25.0,
    },
    {
        "parent_asin": "F",
        "title": "Everyday wireless bra",
        "features": ["soft everyday support"],
        "details": {"color": "white", "material": "cotton"},
        "description": ["everyday bras"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Lingerie", "Everyday Bras"],
        "store": "Example",
        "price": 28.0,
    },
    {
        "parent_asin": "G",
        "title": "Brown leather tote bag",
        "features": ["work tote"],
        "details": {"color": "brown", "material": "leather"},
        "description": ["totes and handbags"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Handbags", "Totes"],
        "store": "Example",
        "price": 55.0,
    },
    {
        "parent_asin": "H",
        "title": "Silver wrist watch",
        "features": ["classic accessory"],
        "details": {"color": "silver", "material": "metal"},
        "description": ["wrist watches"],
        "categories": ["Clothing, Shoes & Jewelry", "Men", "Watches", "Wrist Watches"],
        "store": "Example",
        "price": 70.0,
    },
]


class RetrievalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.catalog_path = Path(self.tmp.name) / "catalog.jsonl"
        self.catalog_path.write_text(
            "".join(json.dumps(row) + "\n" for row in CATALOG_ROWS),
            encoding="utf-8",
        )
        self.retriever = CatalogRetriever(self.catalog_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_current_message_retrieval_returns_candidates(self) -> None:
        candidates = self.retriever.retrieve_current_message("brown leather shoes", limit=5)
        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["route"], "current_message")
        self.assertIn("parent_asin", candidates[0])

    def test_retrieve_category_uses_message_category_without_state(self) -> None:
        candidates = self.retriever.retrieve_category({}, "I need shoes for walking", limit=5)
        self.assertTrue(candidates)
        self.assertTrue(all(candidate["route"] == "category" for candidate in candidates))

    def test_category_alias_recognizes_accessories_and_jewelry(self) -> None:
        candidates = self.retriever.retrieve_category({}, "I'm looking for jewelry necklaces", limit=5)

        self.assertTrue(candidates)
        self.assertIn("jewelry", candidates[0]["matched_terms"])
        self.assertIn("necklaces", candidates[0]["matched_terms"])

    def test_category_alias_recognizes_bras_watches_belts_totes(self) -> None:
        self.assertEqual(category_queries_from_text("everyday bras"), ["everyday bras", "bras"])
        self.assertEqual(category_queries_from_text("wrist watches"), ["wrist watches", "watches"])
        self.assertEqual(category_queries_from_text("leather belts and totes"), ["belts", "totes"])

    def test_popular_category_route_returns_candidates_without_category(self) -> None:
        candidates = self.retriever.retrieve_popular_category(limit=5)

        self.assertTrue(candidates)
        self.assertTrue(all(candidate["route"] == "popular_category" for candidate in candidates))

    def test_popular_categories_are_catalog_driven(self) -> None:
        terms = self.retriever.popular_category_terms

        self.assertIn("necklaces", terms)
        self.assertIn("everyday bras", terms)
        self.assertIn("totes", terms)

    def test_browsing_profile_route_uses_profile_when_message_is_generic(self) -> None:
        candidates = self.retriever.retrieve_browsing_profile(
            {},
            {"preference_tags": ["comfort"], "summary": "likes walking"},
            "I'm still exploring",
            limit=5,
        )

        self.assertTrue(candidates)
        self.assertTrue(all(candidate["route"] == "browsing_profile" for candidate in candidates))
        self.assertIn("comfort", candidates[0]["matched_terms"])

    def test_browsing_uses_coarse_category_from_generic_message(self) -> None:
        self.assertEqual(category_queries_from_text("I'm looking for women wrist watches, but I'm still exploring"), ["wrist watches", "watches"])

    def test_profile_terms_are_combined_with_category_not_used_alone(self) -> None:
        state = SessionState.create("s1", {})
        state.apply(
            [{"attribute": "category", "value": "shoes", "kind": "hard", "confidence": 0.95}],
            turn=1,
        )

        candidates = self.retriever.retrieve_attribute_profile(
            state,
            {"preference_tags": ["comfort"], "summary": ""},
            limit=5,
        )

        self.assertTrue(candidates)
        self.assertIn("shoes", candidates[0]["matched_terms"])
        self.assertIn("comfort", candidates[0]["matched_terms"])

    def test_no_preference_is_not_used_as_search_term(self) -> None:
        candidates = self.retriever.retrieve_browsing_profile(
            {},
            {"preference_tags": [], "summary": "no preference use your judgment"},
            "I don't have a preference; please use your judgment.",
            limit=5,
        )

        self.assertEqual(candidates, [])

    def test_boundary_no_preference_does_not_pollute_retrieval(self) -> None:
        self.assertEqual(category_queries_from_text("I don't have a preference; please use your judgment."), [])

    def test_neutral_attribute_does_not_return_from_profile(self) -> None:
        state = SessionState.create("s1", {"preference_tags": ["comfort", "durability"]})
        state.apply(
            [{"attribute": "feature", "value": "no_preference", "kind": "neutral", "confidence": 1.0}],
            turn=1,
        )

        candidates = self.retriever.retrieve_attribute_profile(
            state,
            {"preference_tags": ["comfort", "durability"], "summary": "likes comfortable durable items"},
            limit=5,
        )

        for candidate in candidates:
            self.assertNotIn("comfort", candidate["matched_terms"])
            self.assertNotIn("durability", candidate["matched_terms"])

    def test_neutral_attribute_from_state_blocks_profile_terms(self) -> None:
        state = {
            "current_slots": {"category": "shoes"},
            "neutral_attributes": ["feature"],
        }

        candidates = self.retriever.retrieve_attribute_profile(
            state,
            {"preference_tags": ["comfort"], "summary": "comfortable lightweight"},
            limit=5,
        )

        for candidate in candidates:
            self.assertNotIn("comfort", candidate["matched_terms"])
            self.assertNotIn("comfortable", candidate["matched_terms"])
            self.assertNotIn("lightweight", candidate["matched_terms"])

    def test_current_state_accepts_empty_state(self) -> None:
        self.assertEqual(self.retriever.retrieve_current_state({}, limit=5), [])

    def test_retrieval_uses_session_state_current_slots(self) -> None:
        state = SessionState.create("s1", {})
        state.apply(
            [
                {"attribute": "category", "value": "shoes", "kind": "hard", "confidence": 0.95},
                {"attribute": "color", "value": "brown", "kind": "hard", "confidence": 0.95},
            ],
            turn=1,
        )

        candidates = self.retriever.retrieve_current_state(state, limit=5)

        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["route"], "current_state")
        self.assertIn("brown", candidates[0]["matched_terms"])
        self.assertIn("shoes", candidates[0]["matched_terms"])

    def test_invalidated_slots_do_not_enter_current_state_query(self) -> None:
        state = SessionState.create("s1", {})
        state.apply(
            [{"attribute": "color", "value": "black", "kind": "hard", "confidence": 0.95}],
            turn=1,
        )
        state.apply(
            [{"attribute": "color", "value": "brown", "kind": "override", "confidence": 0.95}],
            turn=2,
        )

        candidates = self.retriever.retrieve_current_state(state, limit=5)

        self.assertTrue(candidates)
        self.assertNotIn("black", candidates[0]["matched_terms"])
        self.assertIn("brown", candidates[0]["matched_terms"])

    def test_merge_candidates_deduplicates_parent_asin(self) -> None:
        merged = merge_candidates(
            [
                [{"parent_asin": "A", "route": "current_message", "matched_terms": ["brown"]}],
                [{"parent_asin": "A", "route": "category", "matched_terms": ["shoes"]}],
            ],
            limit=10,
        )
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["route"], "current_message")
        self.assertEqual(merged[0]["matched_terms"], ["brown", "shoes"])

    def test_hard_filter_budget_is_safe(self) -> None:
        candidates = [{"parent_asin": "A"}, {"parent_asin": "B"}]
        filtered = apply_hard_filters(
            candidates,
            {"budget_max": 50},
            self.retriever.product_lookup,
            min_results=1,
        )
        self.assertEqual([item["parent_asin"] for item in filtered], ["A"])

    def test_hard_filter_does_not_drop_unknown_price(self) -> None:
        candidates = [{"parent_asin": "C"}]
        filtered = apply_hard_filters(
            candidates,
            {"budget_max": 50},
            self.retriever.product_lookup,
            min_results=1,
        )
        self.assertEqual([item["parent_asin"] for item in filtered], ["C"])

    def test_state_hard_constraints_drive_filtering(self) -> None:
        state = SessionState.create("s1", {})
        state.apply(
            [{"attribute": "budget", "value": 50.0, "kind": "hard", "confidence": 0.99}],
            turn=1,
        )
        candidates = [{"parent_asin": "A"}, {"parent_asin": "B"}]

        filtered = apply_hard_filters(
            candidates,
            state.hard_constraints,
            self.retriever.product_lookup,
            min_results=1,
        )

        self.assertEqual([item["parent_asin"] for item in filtered], ["A"])

    def test_uncertain_preference_not_hard_filtered(self) -> None:
        constraints = extract_basic_hard_constraints("I want comfortable casual premium shoes")
        self.assertNotIn("comfortable", constraints.values())
        self.assertNotIn("casual", constraints.values())
        self.assertEqual(constraints["category"], "shoes")

    def test_fallback_returns_valid_unique_recommendations(self) -> None:
        recs = ensure_valid_recommendations(
            [{"parent_asin": "missing"}, {"parent_asin": "A"}, {"parent_asin": "A"}],
            self.retriever.catalog_ids,
            self.retriever.fallback_candidates("", limit=4),
            top_k=3,
        )
        self.assertEqual(len(recs), 3)
        self.assertEqual(len({item["parent_asin"] for item in recs}), 3)

    def test_candidate_recall_debug_finds_target_before_filter(self) -> None:
        diagnostics = candidate_recall(
            [{"parent_asin": "A"}, {"parent_asin": "B"}],
            "B",
            cutoffs=(1, 2),
        )

        self.assertFalse(diagnostics["recall_at_1"])
        self.assertTrue(diagnostics["recall_at_2"])
        self.assertEqual(diagnostics["target_position"], 2)

    def test_hard_filter_diagnostics_reports_candidate_loss(self) -> None:
        diagnostics = hard_filter_diagnostics(
            [{"parent_asin": "A"}, {"parent_asin": "B"}],
            [{"parent_asin": "A"}],
            target_parent_asin="B",
        )

        self.assertEqual(diagnostics["before_filter_count"], 2)
        self.assertEqual(diagnostics["after_filter_count"], 1)
        self.assertTrue(diagnostics["target_filtered_out"])

    def test_diagnose_reports_candidate_rank_and_best_route(self) -> None:
        diagnostics = _target_candidate_info(
            [
                {"parent_asin": "A", "route": "current_message"},
                {"parent_asin": "B", "route": "category"},
            ],
            "B",
        )

        self.assertEqual(diagnostics["target_candidate_rank"], 2)
        self.assertEqual(diagnostics["target_best_route"], "category")

    def test_agent_response_contract(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {"preference_tags": ["comfort"], "summary": "likes walking shoes"})
        response = agent.respond("s1", "brown leather shoes under $50", 1, 10)
        self.assertEqual(set(response), {"message", "ask_attribute", "recommendations", "usage"})
        self.assertLessEqual(len(response["recommendations"]), 10)
        for recommendation in response["recommendations"]:
            self.assertEqual(set(recommendation), {"parent_asin", "score"})
            self.assertIsInstance(recommendation["score"], float)

    def test_agent_integrates_state_without_leaking_debug_fields(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {"preference_tags": ["comfort"]})
        agent.respond("s1", "I need black shoes.", 1, 10)
        response = agent.respond("s1", "Actually, ignore the earlier color; make them brown.", 2, 10)
        state = agent._sessions["s1"]

        self.assertEqual(state.current_slots["color"], "brown")
        self.assertEqual(state.invalidated_slots["color"], ["black"])
        for recommendation in response["recommendations"]:
            self.assertNotIn("route", recommendation)
            self.assertNotIn("matched_terms", recommendation)
            self.assertNotIn("debug_reason", recommendation)


if __name__ == "__main__":
    unittest.main()
