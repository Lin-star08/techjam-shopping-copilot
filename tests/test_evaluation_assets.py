from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from scripts.create_public_split import HOLDOUT_COUNTS, build_split


class EvaluationAssetsTest(unittest.TestCase):
    def test_checked_in_split_matches_source_and_expected_counts(self) -> None:
        expected = build_split("data/public_set.jsonl")
        checked_in = json.loads(Path("docs/internal_split.json").read_text(encoding="utf-8"))
        self.assertEqual(checked_in, expected)
        self.assertEqual(checked_in["counts"]["development"], 150)
        self.assertEqual(checked_in["counts"]["holdout"], 50)
        self.assertEqual(checked_in["counts"]["holdout_by_scenario"], dict(sorted(HOLDOUT_COUNTS.items())))

        rows = [json.loads(line) for line in Path("data/public_set.jsonl").read_text(encoding="utf-8").splitlines()]
        scenario_by_id = {row["sample_id"]: row["scenario_type"] for row in rows}
        development = checked_in["development_sample_ids"]
        holdout = checked_in["holdout_sample_ids"]
        self.assertFalse(set(development) & set(holdout))
        self.assertEqual(set(development) | set(holdout), set(scenario_by_id))
        self.assertEqual(Counter(scenario_by_id[value] for value in holdout), Counter(HOLDOUT_COUNTS))


if __name__ == "__main__":
    unittest.main()
