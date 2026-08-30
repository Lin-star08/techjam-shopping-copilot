from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from knowledge.build_lexicon import ALLOWED_ASK_ATTRIBUTES, build, render_playbook


class LexiconTest(unittest.TestCase):
    def test_delivery_artifact_is_loadable(self) -> None:
        artifact = Path("artifacts/lexicon.json")
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "v2")
        self.assertEqual(payload["source"]["product_count"], 50_000)
        self.assertFalse(payload["source"]["public_ground_truth_used"])
        self.assertIn("size", payload["vocabulary"])
        self.assertEqual(payload["vocabulary"]["size"]["aliases"]["plus size"], "plus-size")
        self.assertEqual(payload["catalog_summary"]["classification_audit"]["missing_category_count"], 0)

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
        self.assertIn("public ground truth", render_playbook(payload))


if __name__ == "__main__":
    unittest.main()
