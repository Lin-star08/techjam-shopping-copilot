from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from starter.agent import Agent, signature_recommendation_limit
from starter.constraints import (
    apply_hard_filters,
    extract_basic_hard_constraints,
    hard_filter_diagnostics,
    has_no_preference_marker,
    has_override_marker,
)
from starter.intent import DialogueIntent
from starter.ranking import aggregate_candidates
from starter.retrieval import (
    CatalogRetriever,
    candidate_recall,
    category_queries_from_text,
    ensure_valid_recommendations,
    explicit_requirement_terms,
    merge_candidates,
    product_constraint_signature,
    requirement_terms_from_text,
    relaxed_query,
    route_limits_for_turn,
    state_to_dict,
    signature_observations,
    signature_attribute,
)
from starter.state import SessionState
from tools.diagnose_retrieval import _target_candidate_info, _target_ranked_info, classify_failure


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
    {
        "parent_asin": "I",
        "title": "Black lace nightgown",
        "features": ["soft sleep lounge"],
        "details": {"color": "black", "material": "lace"},
        "description": ["nightgowns and sleepshirts"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Lingerie", "Sleep & Lounge", "Nightgowns & Sleepshirts"],
        "store": "Example",
        "price": 32.0,
    },
    {
        "parent_asin": "J",
        "title": "Gold drop dangle earrings",
        "features": ["lightweight jewelry"],
        "details": {"color": "gold", "material": "metal"},
        "description": ["drop and dangle earrings"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Jewelry", "Earrings", "Drop & Dangle"],
        "store": "Example",
        "price": 18.0,
    },
    {
        "parent_asin": "K",
        "title": "Women's waterproof rain boots",
        "features": ["rubber outdoor boot"],
        "details": {"color": "green", "material": "rubber"},
        "description": ["rain boots for wet weather"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Shoes", "Rain Boots"],
        "store": "Example",
        "price": 44.0,
    },
    {
        "parent_asin": "L",
        "title": "Men's slip on loafer",
        "features": ["easy slip ons"],
        "details": {"color": "brown", "material": "suede"},
        "description": ["loafers and slip ons"],
        "categories": ["Clothing, Shoes & Jewelry", "Men", "Shoes", "Loafers & Slip-Ons"],
        "store": "Example",
        "price": 61.0,
    },
    {
        "parent_asin": "M",
        "title": "Athletic tank top",
        "features": ["breathable active shirt"],
        "details": {"color": "blue", "material": "polyester"},
        "description": ["tanks and tops"],
        "categories": ["Clothing, Shoes & Jewelry", "Men", "Shirts", "Tanks Tops"],
        "store": "Example",
        "price": 22.0,
    },
    {
        "parent_asin": "N",
        "title": "Fleece hoodie sweatshirt",
        "features": ["warm casual layer"],
        "details": {"color": "gray", "material": "polyester"},
        "description": ["fashion hoodies and sweatshirts"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Fashion Hoodies & Sweatshirts"],
        "store": "Example",
        "price": 39.0,
    },
    {
        "parent_asin": "O",
        "title": "Soft running headband",
        "features": ["stretch hair accessory"],
        "details": {"color": "pink", "material": "fabric"},
        "description": ["hats caps and headbands"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Accessories", "Hats & Caps", "Headbands"],
        "store": "Example",
        "price": 14.0,
    },
    {
        "parent_asin": "P",
        "title": "Athletic sport sandal slide",
        "features": ["sport sandals slides"],
        "details": {"color": "black", "material": "rubber"},
        "description": ["athletic shoes"],
        "categories": ["Clothing, Shoes & Jewelry", "Men", "Shoes", "Athletic", "Sport Sandals & Slides"],
        "store": "Example",
        "price": 36.0,
    },
    {
        "parent_asin": "Q",
        "title": "Women's cotton bootcut jeans",
        "features": ["soft denim"],
        "details": {"color": "blue", "material": "cotton"},
        "description": ["women jeans"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Clothing", "Jeans"],
        "store": "Example",
        "price": 42.0,
    },
    {
        "parent_asin": "R",
        "title": "Women's cycling jersey",
        "features": ["breathable polyester cycling top"],
        "details": {"color": "red", "material": "polyester"},
        "description": ["cycling jerseys"],
        "categories": ["Clothing, Shoes & Jewelry", "Sport Specific Clothing", "Cycling", "Women", "Jerseys"],
        "store": "Example",
        "price": 31.0,
    },
    {
        "parent_asin": "S",
        "title": "Multicolor unisex bandana",
        "features": ["lightweight accessory"],
        "details": {"color": "blue", "material": "cotton"},
        "description": ["bandanas"],
        "categories": ["Clothing, Shoes & Jewelry", "Novelty & More", "Clothing", "Novelty", "Men", "Accessories", "Bandanas"],
        "store": "Example",
        "price": 9.0,
    },
    {
        "parent_asin": "T",
        "title": "Youth soccer cleat",
        "features": ["athletic soccer shoe"],
        "details": {"color": "black", "material": "rubber"},
        "description": ["soccer cleats"],
        "categories": ["Clothing, Shoes & Jewelry", "Boys", "Shoes", "Athletic", "Soccer"],
        "store": "Example",
        "price": 29.0,
    },
    {
        "parent_asin": "U",
        "title": "Men's casual button-down shirt",
        "features": ["cotton poplin"],
        "details": {"color": "green", "material": "cotton"},
        "description": ["casual button-down shirts"],
        "categories": ["Clothing, Shoes & Jewelry", "Men", "Clothing", "Shirts", "Casual Button-Down Shirts"],
        "store": "Example",
        "price": 33.0,
    },
    {
        "parent_asin": "V",
        "title": "Satin sleep lounge pajama set",
        "features": ["hand wash only"],
        "details": {"color": "pink", "material": "polyester"},
        "description": ["sleep lounge sets"],
        "categories": ["Clothing, Shoes & Jewelry", "Women", "Clothing", "Lingerie, Sleep & Lounge", "Sleep & Lounge", "Sets"],
        "store": "Example",
        "price": 27.0,
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

    def test_state_adapter_ignores_unknown_future_fields(self) -> None:
        class FutureState:
            current_slots = {"category": "shoes"}
            hard_constraints = {}
            soft_preferences = {}
            asked_attributes = []
            neutral_attributes = []
            invalidated_slots = {}
            profile_signals = []
            future_field_from_state_v2 = {"anything": "ignored"}

        adapted = state_to_dict(FutureState())
        adapted_dict = state_to_dict({
            "current_slots": {"category": "shoes"},
            "future_field_from_state_v2": {"anything": "ignored"},
        })

        self.assertEqual(adapted["current_slots"], {"category": "shoes"})
        self.assertNotIn("future_field_from_state_v2", adapted)
        self.assertEqual(adapted_dict["current_slots"], {"category": "shoes"})
        self.assertNotIn("future_field_from_state_v2", adapted_dict)

    def test_missing_state_fields_do_not_crash_retrieval(self) -> None:
        partial_state = {"current_slots": {"category": "shoes"}, "future_field": "ignored"}

        current_state = self.retriever.retrieve_current_state(partial_state, limit=5)
        all_routes = self.retriever.retrieve_all_routes(
            partial_state,
            {},
            "I'm still exploring",
            [],
            fallback_candidates=[],
            limit=10,
        )

        self.assertIsInstance(current_state, list)
        self.assertIsInstance(all_routes, list)

    def test_current_message_retrieval_returns_candidates(self) -> None:
        candidates = self.retriever.retrieve_current_message("brown leather shoes", limit=5)
        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["route"], "current_message")
        self.assertIn("parent_asin", candidates[0])

    def test_product_constraint_signature_uses_visible_fields_only(self) -> None:
        signature = product_constraint_signature(CATALOG_ROWS[0])

        self.assertEqual(signature[:2], ["leather", "color: brown"])
        self.assertIn("comfortable", signature)

    def test_signature_candidates_intersect_disclosed_requirements(self) -> None:
        messages = [
            "I'm looking for Shoes. A key requirement is: leather.",
            "For that, what matters is: color: brown; comfortable.",
        ]

        candidates = self.retriever.retrieve_signature_candidates(messages, limit=10)

        self.assertEqual([item["parent_asin"] for item in candidates], ["A"])
        self.assertEqual(candidates[0]["route"], "signature_exact")

    def test_signature_observations_ignore_no_preference(self) -> None:
        observations = signature_observations([
            "I don't have a preference for other; please use your judgment.",
            "For that, what matters is: leather; 100% Leather.",
        ])

        self.assertEqual(observations, ["leather 100 leather"])

    def test_signature_attribute_uses_visible_value_type(self) -> None:
        self.assertEqual(signature_attribute("color: brown"), "color")
        self.assertEqual(signature_attribute("100% leather"), "material")
        self.assertEqual(signature_attribute("Rubber sole"), "feature")

    def test_small_signature_group_expands_to_three_after_specific_reply(self) -> None:
        self.assertEqual(
            signature_recommendation_limit(
                top_k=10,
                candidate_count=6,
                specific_reply_count=1,
                boundary_declined_open_question=False,
            ),
            3,
        )
        self.assertEqual(
            signature_recommendation_limit(
                top_k=10,
                candidate_count=11,
                specific_reply_count=1,
                boundary_declined_open_question=False,
            ),
            1,
        )

    def test_preferred_signature_attribute_is_category_weighted(self) -> None:
        attribute = self.retriever.preferred_signature_attribute([
            "I'm looking for Jewelry Necklaces, but I'm still exploring."
        ])

        self.assertEqual(attribute, "feature")

    def test_matched_terms_are_product_specific_not_shared_query_terms(self) -> None:
        candidates = self.retriever.retrieve_current_message(
            "brown leather shoes black boots",
            limit=10,
        )
        by_asin = {candidate["parent_asin"]: candidate for candidate in candidates}

        self.assertIn("A", by_asin)
        self.assertIn("B", by_asin)
        self.assertIn("black", by_asin["A"]["query_terms"])
        self.assertIn("brown", by_asin["B"]["query_terms"])
        self.assertIn("brown", by_asin["A"]["matched_terms"])
        self.assertNotIn("black", by_asin["A"]["matched_terms"])
        self.assertIn("black", by_asin["B"]["matched_terms"])
        self.assertNotIn("brown", by_asin["B"]["matched_terms"])

    def test_query_terms_and_matched_terms_are_separate(self) -> None:
        candidates = self.retriever.retrieve_current_message(
            "brown leather shoes under 50",
            limit=5,
        )
        first = candidates[0]

        self.assertIn("under", first["query_terms"])
        self.assertIn("50", first["query_terms"])
        self.assertNotIn("under", first["matched_terms"])
        self.assertNotIn("50", first["matched_terms"])
        self.assertNotEqual(first["query_terms"], first["matched_terms"])

    def test_explicit_match_count_uses_real_matched_attributes(self) -> None:
        candidates = self.retriever.retrieve_current_message(
            "brown leather shoes black boots",
            limit=10,
        )
        target = next(candidate for candidate in candidates if candidate["parent_asin"] == "A")

        self.assertEqual(target["matched_attributes"]["color"], ["brown"])
        self.assertEqual(target["matched_attributes"]["material"], ["leather"])
        self.assertIn("category", target["matched_attributes"])
        self.assertEqual(target["explicit_match_count"], 3)
        self.assertEqual(target["hard_match_count"], 3)
        self.assertEqual(target["matched_attribute_count"], 3)

    def test_field_route_title_matches_product_name(self) -> None:
        candidates = self.retriever.retrieve_title("gold pendant necklace", limit=5)

        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["route"], "title")
        self.assertEqual(candidates[0]["parent_asin"], "E")

    def test_title_route_records_only_title_match(self) -> None:
        candidates = self.retriever.retrieve_title("gold travel necklace", limit=10)
        by_asin = {candidate["parent_asin"]: candidate for candidate in candidates}

        self.assertIn("E", by_asin)
        self.assertIn("gold", by_asin["E"]["matched_terms"])
        self.assertIn("necklace", by_asin["E"]["matched_terms"])
        self.assertNotIn("travel", by_asin["E"]["matched_terms"])
        if "D" in by_asin:
            self.assertIn("travel", by_asin["D"]["matched_terms"])
            self.assertNotIn("gold", by_asin["D"]["matched_terms"])
            self.assertNotIn("necklace", by_asin["D"]["matched_terms"])

    def test_retrieve_category_uses_message_category_without_state(self) -> None:
        candidates = self.retriever.retrieve_category({}, "I need shoes for walking", limit=5)
        self.assertTrue(candidates)
        self.assertTrue(all(candidate["route"] == "category" for candidate in candidates))

    def test_category_alias_recognizes_accessories_and_jewelry(self) -> None:
        candidates = self.retriever.retrieve_category({}, "I'm looking for jewelry necklaces", limit=5)

        self.assertTrue(candidates)
        self.assertIn("jewelry", candidates[0]["matched_terms"])
        self.assertIn("necklaces", candidates[0]["matched_terms"])
        self.assertEqual(
            candidates[0]["matched_attributes"]["category"],
            ["jewelry", "necklaces"],
        )

    def test_category_route_records_only_real_category_match(self) -> None:
        candidates = self.retriever.retrieve_category({}, "jewelry necklaces", limit=10)
        by_asin = {candidate["parent_asin"]: candidate for candidate in candidates}

        self.assertIn("E", by_asin)
        self.assertIn("necklaces", by_asin["E"]["matched_attributes"]["category"])
        if "J" in by_asin:
            self.assertIn("jewelry", by_asin["J"]["matched_terms"])
            self.assertNotIn("necklaces", by_asin["J"]["matched_terms"])

    def test_category_alias_recognizes_bras_watches_belts_totes(self) -> None:
        self.assertEqual(category_queries_from_text("everyday bras"), ["everyday bras", "bras"])
        self.assertEqual(category_queries_from_text("wrist watches"), ["wrist watches", "watches"])
        self.assertEqual(category_queries_from_text("leather belts and totes"), ["belts", "totes"])

    def test_long_tail_category_aliases_are_recognized(self) -> None:
        matches = category_queries_from_text(
            "sleep & lounge nightgowns and sleepshirts drop & dangle earrings "
            "rain boots loafers and slip ons tanks and tops hats and caps "
            "headbands athletic shoes sport sandals"
        )
        candidates = self.retriever.retrieve_category({}, "drop & dangle earrings", limit=5)

        for expected in (
            "sleep lounge",
            "nightgowns sleepshirts",
            "drop dangle",
            "earrings",
            "rain boots",
            "loafers slip ons",
            "tanks tops",
            "hats caps",
            "headbands",
            "athletic shoes",
            "sport sandals",
        ):
            self.assertIn(expected, matches)
        self.assertIn("J", {candidate["parent_asin"] for candidate in candidates})

    def test_long_tail_categories_include_jerseys_bandanas_soccer(self) -> None:
        matches = category_queries_from_text(
            "Women Jerseys Accessories Bandanas Athletic Soccer"
        )

        self.assertIn("jerseys", matches)
        self.assertIn("bandanas", matches)
        self.assertIn("soccer", matches)
        self.assertIn("R", {item["parent_asin"] for item in self.retriever.retrieve_category({}, "Women Jerseys", limit=5)})
        self.assertIn("S", {item["parent_asin"] for item in self.retriever.retrieve_category({}, "Accessories Bandanas", limit=5)})
        self.assertIn("T", {item["parent_asin"] for item in self.retriever.retrieve_category({}, "Athletic Soccer", limit=5)})

    def test_category_query_keeps_leaf_phrase_not_only_parent_category(self) -> None:
        matches = category_queries_from_text("Shirts Casual Button-Down Shirts")

        self.assertIn("shirt", matches)
        self.assertIn("casual button down shirts", matches)
        self.assertIn("button down shirts", matches)
        self.assertNotIn("t-shirts", matches)

    def test_boundary_category_aliases_return_candidates(self) -> None:
        candidates = self.retriever.retrieve_category({}, "hats and caps headbands", limit=5)
        sport_candidates = self.retriever.retrieve_category({}, "athletic sport sandals", limit=5)

        self.assertIn("O", {candidate["parent_asin"] for candidate in candidates})
        self.assertIn("P", {candidate["parent_asin"] for candidate in sport_candidates})

    def test_category_route_uses_context_to_order_candidates(self) -> None:
        state = {
            "current_slots": {
                "category": "shoes",
                "color": "green",
                "material": "rubber",
            }
        }

        candidates = self.retriever.retrieve_category(state, "green rubber shoes", limit=5)

        self.assertEqual(candidates[0]["parent_asin"], "K")

    def test_popular_category_route_returns_candidates_without_category(self) -> None:
        candidates = self.retriever.retrieve_popular_category(limit=5)

        self.assertTrue(candidates)
        self.assertTrue(all(candidate["route"] == "popular_category" for candidate in candidates))

    def test_popular_categories_are_catalog_driven(self) -> None:
        terms = self.retriever.popular_category_terms

        self.assertIn("necklaces", terms)
        self.assertIn("everyday bras", terms)
        self.assertIn("totes", terms)

    def test_category_requirement_route_combines_category_and_material(self) -> None:
        candidates = self.retriever.retrieve_category_requirement(
            {},
            "I'm looking for Women Jeans. A key requirement is: cotton.",
            limit=10,
        )

        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["route"], "category_requirement")
        self.assertIn("Q", {candidate["parent_asin"] for candidate in candidates})
        target = next(candidate for candidate in candidates if candidate["parent_asin"] == "Q")
        self.assertIn("jeans", target["matched_attributes"]["category"])
        self.assertIn("cotton", target["matched_attributes"]["material"])

    def test_key_requirement_route_drops_noise_words(self) -> None:
        message = "I'm looking for Shirts Tanks Tops. A key requirement is: polyester."
        query_terms = requirement_terms_from_text(message)
        candidates = self.retriever.retrieve_requirement_fields({}, message, limit=10)

        self.assertEqual(query_terms, ["polyester"])
        self.assertIn("M", {candidate["parent_asin"] for candidate in candidates})
        self.assertTrue(all("key" not in candidate["query_terms"] for candidate in candidates))
        self.assertTrue(all("requirement" not in candidate["query_terms"] for candidate in candidates))

    def test_hand_wash_requirement_route_extracts_phrase_terms(self) -> None:
        message = "I'm looking for Sleep & Lounge Sets. Hand Wash Only"
        query_terms = requirement_terms_from_text(message)
        candidates = self.retriever.retrieve_requirement_fields({}, message, limit=10)

        self.assertIn("hand", query_terms)
        self.assertIn("wash", query_terms)
        self.assertNotIn("only", query_terms)
        self.assertIn("V", {candidate["parent_asin"] for candidate in candidates})

    def test_field_route_category_improves_browsing_candidates(self) -> None:
        candidates = self.retriever.retrieve_category_field(
            {},
            "I'm looking for Bras Everyday Bras, but I'm still exploring",
            limit=5,
        )

        self.assertTrue(candidates)
        self.assertEqual(candidates[0]["route"], "field_category")
        self.assertIn("F", {candidate["parent_asin"] for candidate in candidates})

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

    def test_relaxed_route_removes_uncertain_terms(self) -> None:
        query = relaxed_query({}, "brown waterproof comfortable walking shoes under $50")

        self.assertIn("brown", query)
        self.assertIn("shoes", query)
        self.assertIn("walking", query)
        self.assertNotIn("comfortable", query)
        self.assertNotIn("waterproof", query)
        self.assertNotIn("under", query)
        self.assertNotIn("50", query)

    def test_relaxed_route_keeps_core_category_and_hard_terms(self) -> None:
        state = {
            "current_slots": {
                "category": "shoes",
                "color": "brown",
                "material": "leather",
            }
        }

        query = relaxed_query(state, "comfortable waterproof options")

        self.assertIn("shoes", query)
        self.assertIn("brown", query)
        self.assertIn("leather", query)

    def test_no_preference_does_not_enter_relaxed_query(self) -> None:
        query = relaxed_query({}, "I don't have a preference; please use your judgment.")

        self.assertEqual(query, "")

    def test_relaxed_query_drops_no_preference_terms(self) -> None:
        query = relaxed_query({}, "No preference on style, use your judgment.")

        self.assertNotIn("no", query)
        self.assertNotIn("preference", query)
        self.assertNotIn("judgment", query)

    def test_relaxed_query_drops_invalidated_old_value(self) -> None:
        state = {
            "current_slots": {"category": "shoes", "color": "brown"},
            "invalidated_slots": {"color": ["black"]},
        }

        query = relaxed_query(state, "Actually not black, brown leather shoes.")

        self.assertNotIn("black", query)
        self.assertIn("brown", query)
        self.assertIn("shoes", query)

    def test_override_drops_invalidated_old_value_from_relaxed_query(self) -> None:
        state = SessionState.create("s1", {})
        state.apply(
            [{"attribute": "color", "value": "black", "kind": "hard", "confidence": 0.95}],
            turn=1,
        )
        state.apply(
            [{"attribute": "color", "value": "brown", "kind": "override", "confidence": 0.95}],
            turn=2,
        )

        query = relaxed_query(state, "Actually make them brown instead of black shoes.")

        self.assertIn("brown", query)
        self.assertNotIn("black", query)

    def test_relaxed_query_keeps_current_override_value(self) -> None:
        state = {
            "current_slots": {"category": "shoes", "color": "brown"},
            "invalidated_slots": {"color": ["black"]},
        }

        query = relaxed_query(state, "Actually make them brown now.")

        self.assertIn("brown", query)
        self.assertIn("shoes", query)

    def test_dynamic_route_limits_expand_browsing(self) -> None:
        limits = route_limits_for_turn("I'm looking for Women Dresses, but I'm still exploring")

        self.assertGreater(limits["category"], limits["current_message"])
        self.assertGreater(limits["popular_category"], 0)

    def test_retrieval_uses_intent_to_choose_route_limits(self) -> None:
        browsing = route_limits_for_turn("brown shoes", intent_result=DialogueIntent.BROWSING)
        boundary = route_limits_for_turn(
            "I don't have a preference; use your judgment.",
            intent_result=DialogueIntent.BOUNDARY,
        )
        override = route_limits_for_turn("brown shoes", intent_result=DialogueIntent.INTENT_OVERRIDE)

        self.assertGreater(browsing["category"], browsing["current_message"])
        self.assertEqual(boundary["current_message"], 0)
        self.assertGreater(boundary["popular_category"], 0)
        self.assertGreaterEqual(override["current_message"], override["category"])

    def test_dynamic_route_limits_preserve_buying(self) -> None:
        limits = route_limits_for_turn("brown leather shoes under $50")

        self.assertGreaterEqual(limits["current_state"], limits["category"])
        self.assertGreater(limits["title"], 0)

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

    def test_boundary_does_not_search_no_preference_text(self) -> None:
        state = {"current_slots": {"category": "shoes"}, "neutral_attributes": ["color"]}

        candidates = self.retriever.retrieve_route_candidates(
            state,
            {},
            "I don't have a preference; please use your judgment.",
            [],
            DialogueIntent.BOUNDARY,
            fallback_candidates=self.retriever.fallback_candidates("", limit=5),
            limit=20,
        )

        self.assertNotIn("current_message", {candidate["route"] for candidate in candidates})
        self.assertFalse(
            any("preference" in candidate.get("matched_terms", []) for candidate in candidates)
        )

    def test_boundary_uses_state_category_and_popular_fallback(self) -> None:
        state = {"current_slots": {"category": "shoes"}, "neutral_attributes": ["color"]}

        candidates = self.retriever.retrieve_route_candidates(
            state,
            {},
            "I don't have a preference for color.",
            [],
            DialogueIntent.BOUNDARY,
            fallback_candidates=self.retriever.fallback_candidates("", limit=5),
            limit=20,
        )
        routes = [candidate["route"] for candidate in candidates]

        self.assertIn("current_state", routes)
        self.assertIn("category", routes)
        self.assertIn("popular_category", routes)

    def test_boundary_uses_same_category_popular_before_global_popular(self) -> None:
        state = {"current_slots": {"category": "shoes"}, "neutral_attributes": ["color"]}

        candidates = self.retriever.retrieve_route_candidates(
            state,
            {},
            "I don't have a preference for color.",
            [],
            DialogueIntent.BOUNDARY,
            fallback_candidates=self.retriever.fallback_candidates("", limit=5),
            limit=30,
        )
        routes = [candidate["route"] for candidate in candidates]

        self.assertIn("same_category_popular", routes)
        self.assertLess(routes.index("same_category_popular"), routes.index("popular_category"))

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

    def test_invalidated_terms_do_not_enter_candidate_evidence(self) -> None:
        state = {
            "current_slots": {"category": "shoes", "color": "brown"},
            "invalidated_slots": {"color": ["black"]},
        }

        candidates = self.retriever.retrieve_current_message(
            "Actually not black, brown leather shoes.",
            limit=10,
            session_state=state,
        )
        by_asin = {candidate["parent_asin"]: candidate for candidate in candidates}

        self.assertIn("A", by_asin)
        self.assertIn("black", by_asin["A"]["query_terms"])
        self.assertNotIn("black", by_asin["A"]["matched_terms"])
        self.assertIn("brown", by_asin["A"]["matched_terms"])

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

    def test_route_hits_preserve_multiple_routes_for_same_product(self) -> None:
        merged = merge_candidates(
            [
                [{"parent_asin": "A", "route": "current_message", "route_rank": 1, "route_score": 1.0}],
                [{"parent_asin": "A", "route": "category", "route_rank": 2, "route_score": 2.0}],
            ],
            limit=10,
        )

        self.assertEqual(merged[0]["route_hits"], 2)
        self.assertEqual([route["route"] for route in merged[0]["routes"]], ["current_message", "category"])

    def test_raw_candidates_preserve_multiple_route_hits_for_rrf(self) -> None:
        state = {
            "current_slots": {
                "category": "shoes",
                "color": "brown",
                "material": "leather",
            }
        }

        raw_candidates = self.retriever.retrieve_route_candidates(
            state,
            {"preference_tags": ["comfort"], "summary": "walking shoes"},
            "brown leather shoes",
            [],
            DialogueIntent.BUYING,
            fallback_candidates=[],
            limit=20,
        )
        aggregated = aggregate_candidates(raw_candidates)
        evidence = {
            item["parent_asin"]: {route["route"] for route in item["route_evidence"]}
            for item in aggregated
        }

        self.assertIn("current_message", evidence["A"])
        self.assertIn("current_state", evidence["A"])
        self.assertIn("category", evidence["A"])

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

    def test_hard_filter_keeps_target_when_fields_are_missing(self) -> None:
        candidates = [{"parent_asin": "TARGET"}]

        filtered = apply_hard_filters(
            candidates,
            {"color": "brown", "material": "leather"},
            {"TARGET": {"parent_asin": "TARGET"}},
            min_results=1,
        )

        self.assertEqual(filtered, candidates)

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

    def test_new_category_aliases_do_not_become_hard_filters(self) -> None:
        candidates = [{"parent_asin": "A"}, {"parent_asin": "J"}]
        constraints = extract_basic_hard_constraints("drop dangle earrings")

        filtered = apply_hard_filters(
            candidates,
            constraints,
            self.retriever.product_lookup,
            min_results=1,
        )

        self.assertEqual(constraints["category"], "earrings")
        self.assertEqual([item["parent_asin"] for item in filtered], ["A", "J"])

    def test_v23_category_aliases_do_not_become_hard_filters(self) -> None:
        candidates = [{"parent_asin": "A"}, {"parent_asin": "R"}, {"parent_asin": "S"}]
        constraints = extract_basic_hard_constraints("jerseys bandanas soccer")

        filtered = apply_hard_filters(
            candidates,
            constraints,
            self.retriever.product_lookup,
            min_results=1,
        )

        self.assertEqual(constraints["category"], "soccer")
        self.assertEqual([item["parent_asin"] for item in filtered], ["A", "R", "S"])

    def test_constraints_keep_upstream_intent_helpers(self) -> None:
        self.assertTrue(has_no_preference_marker("I don't have a preference."))
        self.assertTrue(has_override_marker("Actually, make them brown."))

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
                {
                    "parent_asin": "B",
                    "route": "category",
                    "matched_terms": ["shoes"],
                    "matched_attributes": {"category": ["shoes"]},
                    "explicit_match_count": 1,
                    "hard_match_count": 1,
                },
            ],
            "B",
        )

        self.assertEqual(diagnostics["target_candidate_rank"], 2)
        self.assertEqual(diagnostics["target_best_route"], "category")
        self.assertEqual(diagnostics["target_matched_attributes"], {"category": ["shoes"]})
        self.assertEqual(diagnostics["target_explicit_match_count"], 1)

    def test_diagnostics_classifies_recall_vs_rerank_failure(self) -> None:
        self.assertEqual(
            classify_failure({"target_position": None}, {"target_position": None}, {}),
            "recall_failure",
        )
        self.assertEqual(
            classify_failure({"target_position": 15}, {"target_position": 15}, {}),
            "rerank_failure",
        )
        self.assertEqual(
            classify_failure(
                {"target_position": 5},
                {"target_position": 5},
                {},
                {"target_ranked_position": None},
            ),
            "rerank_failure",
        )
        self.assertEqual(
            classify_failure(
                {"target_position": 5},
                {"target_position": None},
                {"target_filtered_out": True},
            ),
            "filter_failure",
        )
        self.assertEqual(
            classify_failure(
                {"target_position": 3},
                {"target_position": 3},
                {},
                {"target_ranked_position": 3},
                top_k=10,
            ),
            "top_k_hit",
        )

    def test_diagnostics_reports_recall_rerank_filter_failure(self) -> None:
        self.assertEqual(
            _target_ranked_info([{"parent_asin": "A", "final_score": 0.5}], "A"),
            {"target_ranked_position": 1, "target_ranked_score": 0.5},
        )
        self.assertEqual(
            classify_failure(
                {"target_position": 3},
                {"target_position": 3},
                {},
                {"target_ranked_position": 1},
            ),
            "top_k_hit",
        )

    def test_agent_keeps_upstream_intent_and_question_policy(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {})

        first = agent.respond("s1", "I'm looking for shoes, but I'm still exploring.", 1, 10)
        second = agent.respond(
            "s1",
            "I don't have a preference for color; please use your judgment.",
            2,
            10,
        )

        self.assertEqual(
            [item.intent for item in agent._intent_history["s1"]],
            [DialogueIntent.BROWSING, DialogueIntent.BOUNDARY],
        )
        self.assertIsNotNone(first["ask_attribute"])
        self.assertNotEqual(second["ask_attribute"], "color")

    def test_agent_response_contract(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {"preference_tags": ["comfort"], "summary": "likes walking shoes"})
        response = agent.respond("s1", "brown leather shoes under $50", 1, 10)
        self.assertEqual(set(response), {"message", "ask_attribute", "recommendations", "usage"})
        self.assertLessEqual(len(response["recommendations"]), 10)
        for recommendation in response["recommendations"]:
            self.assertEqual(set(recommendation), {"parent_asin", "score"})
            self.assertIsInstance(recommendation["score"], float)

    def test_agent_asks_open_requirement_when_category_parser_is_uncertain(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {})

        response = agent.respond("s1", "I'm looking for Hoop.", 1, 10)

        self.assertEqual(response["ask_attribute"], "other")

    def test_agent_keeps_ambiguous_signature_output_to_one_item(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {})

        response = agent.respond(
            "s1",
            "I'm looking for Shoes. A key requirement is: leather.",
            1,
            10,
        )

        self.assertEqual(len(response["recommendations"]), 1)
        self.assertEqual(response["ask_attribute"], "other")

    def test_final_recommendations_still_hide_internal_evidence(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {})
        response = agent.respond("s1", "brown leather shoes under $50", 1, 10)
        forbidden = {
            "route",
            "query_terms",
            "matched_terms",
            "matched_attributes",
            "explicit_match_count",
            "hard_match_count",
            "matched_attribute_count",
            "debug_reason",
        }

        for recommendation in response["recommendations"]:
            self.assertFalse(forbidden & set(recommendation))

    def test_final_recommendations_are_unique_per_turn(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {})
        response = agent.respond("s1", "brown leather shoes", 1, 10)
        asins = [recommendation["parent_asin"] for recommendation in response["recommendations"]]

        self.assertEqual(len(asins), len(set(asins)))

    def test_same_product_can_reappear_across_turns_when_still_relevant(self) -> None:
        agent = Agent(self.catalog_path)
        agent.reset("s1", {})
        first = agent.respond("s1", "brown leather shoes", 1, 5)
        second = agent.respond("s1", "still looking for brown leather shoes", 2, 5)

        self.assertIn("A", {item["parent_asin"] for item in first["recommendations"]})
        self.assertIn("A", {item["parent_asin"] for item in second["recommendations"]})

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
