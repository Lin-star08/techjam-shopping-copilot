from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from artifacts.build_lexicon import (
    ALLOWED_ASK_ATTRIBUTES,
    _derived_category_resolution,
    build,
    render_playbook,
)


class LexiconTest(unittest.TestCase):
    def test_delivery_artifact_is_loadable(self) -> None:
        artifact = Path("artifacts/lexicon.json")
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "v2")
        self.assertEqual(payload["source"]["path"], "data/public_set1.jsonl")
        self.assertEqual(payload["source"]["product_count"], 3_021)
        self.assertFalse(payload["source"]["public_ground_truth_used"])
        self.assertIn("size", payload["vocabulary"])
        self.assertEqual(payload["vocabulary"]["size"]["aliases"]["plus size"], "plus-size")
        self.assertEqual(payload["catalog_summary"]["classification_audit"]["missing_category_count"], 0)
        normalization = payload["category_normalization"]["unreliable_leaves"]
        self.assertEqual(normalization["Casual"]["resolution_status"]["resolved_from_parent"], 1_099)
        self.assertEqual(normalization["Sets"]["resolution_status"]["resolved_from_parent"], 610)
        self.assertFalse(normalization["Westlake"]["hard_filter_allowed_from_leaf"])

        audit = payload["evidence_audit"]
        retrieval_path = Path(audit["source"]["retrieval_path"])
        self.assertEqual(
            audit["source"]["retrieval_sha256"],
            hashlib.sha256(retrieval_path.read_bytes()).hexdigest(),
        )
        self.assertFalse(audit["source"]["public_ground_truth_used"])
        self.assertFalse(audit["source"]["runtime_lexicon_reference_found"])
        self.assertEqual(len(audit["term_stats"]), 202)
        self.assertEqual(
            audit["known_classifier_gaps"]["attributes_without_dedicated_term_sets"],
            ["size", "style"],
        )
        term_stats = {item["term"]: item for item in audit["term_stats"]}
        self.assertEqual(term_stats["jewelry"]["field_product_counts"]["categories"], 50_000)
        self.assertIn("broad", term_stats["jewelry"]["quality_flags"])
        self.assertIn("ambiguous", term_stats["casual"]["quality_flags"])
        self.assertEqual(term_stats["casual"]["effective_attribute_by_route"]["default_routes"], "category")
        alias_entries = {
            item["alias"]: item
            for item in audit["category_alias_audit"]["entries"]
        }
        self.assertEqual(alias_entries["set"]["status"], "requires_parent_context")
        self.assertNotIn("set", payload["vocabulary"]["category"]["safe_soft_aliases"])

    def test_build_uses_catalog_and_returns_loadable_contract(self) -> None:
        rows = [
            {"parent_asin": "A", "title": "Black leather waterproof walking boots", "features": [], "description": [], "price": 49, "categories": ["Root", "Boots"], "details": {}, "store": "Acme"},
            {"parent_asin": "B", "title": "Blue suede hiking boots", "features": [], "description": [], "price": 89, "categories": ["Root", "Boots"], "details": {}, "store": "Beta"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            catalog = Path(directory) / "catalog.jsonl"
            catalog.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            payload = build(catalog, top_categories=5)

        self.assertEqual(payload["source"]["product_count"], 2)
        self.assertFalse(payload["source"]["public_ground_truth_used"])
        questions = payload["category_playbook"]["Boots"]["high_value_questions"]
        self.assertEqual(len(questions), 3)
        self.assertTrue(all(item["ask_attribute"] in ALLOWED_ASK_ATTRIBUTES for item in questions))
        self.assertEqual(questions[0]["ask_attribute"], "use_case")
        self.assertEqual(questions[1]["ask_attribute"], "size")
        self.assertIn("black", payload["vocabulary"]["color"]["values"])
        playbook = render_playbook(payload)
        self.assertIn("public ground truth", playbook)
        self.assertIn("`artifacts/lexicon.json`", playbook)
        self.assertNotIn("`knowledge/lexicon.json`", playbook)
        self.assertIn("coverage", playbook)
        self.assertIn("info", playbook)
        self.assertIn("Team handoff", playbook)

    def test_unreliable_category_resolution_is_conservative(self) -> None:
        casual = _derived_category_resolution(
            ["Clothing, Shoes & Jewelry", "Women", "Clothing", "Dresses", "Casual"],
            "Women's summer dress",
        )
        self.assertEqual(casual["product_type"], "Dresses")
        self.assertEqual(casual["style"], "casual")
        self.assertFalse(casual["hard_filter_allowed"])

        sleepwear = _derived_category_resolution(
            ["Clothing, Shoes & Jewelry", "Women", "Sleep & Lounge", "Sets"],
            "Women's pajama set",
        )
        self.assertEqual(sleepwear["product_type"], "Sleepwear Sets")

        audience = _derived_category_resolution(
            ["Clothing, Shoes & Jewelry", "Women"],
            "Lightweight crossbody bag",
        )
        self.assertEqual(audience["audience"], "Women")
        self.assertEqual(audience["product_type"], "Bags")
        self.assertEqual(audience["confidence"], "medium")

        ambiguous = _derived_category_resolution(
            ["Clothing, Shoes & Jewelry", "Westlake"],
            "Women's shirt dress",
        )
        self.assertEqual(ambiguous["status"], "ambiguous_title")
        self.assertEqual(ambiguous["next_action"], "ask_category")
        self.assertNotIn("product_type", ambiguous)


if __name__ == "__main__":
    unittest.main()
