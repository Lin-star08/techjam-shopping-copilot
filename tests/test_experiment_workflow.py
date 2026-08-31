from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.run_goal_workflow import (
    audit_no_public_label_literals,
    select_samples,
    target_status,
)


class ExperimentWorkflowTest(unittest.TestCase):
    def test_target_status_uses_strict_thresholds(self) -> None:
        status = target_status({"hit_rate_at_10": 0.99, "mrr": 0.96, "mttc": 2.159})
        boundary = target_status({"hit_rate_at_10": 0.98, "mrr": 0.95, "mttc": 2.16})

        self.assertTrue(all(item["passed"] for item in status.values()))
        self.assertFalse(any(item["passed"] for item in boundary.values()))

    def test_select_samples_uses_checked_in_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "samples.jsonl"
            split = root / "split.json"
            rows = [
                {"sample_id": "a", "ground_truth": {"parent_asin": "A"}},
                {"sample_id": "b", "ground_truth": {"parent_asin": "B"}},
            ]
            dataset.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            split.write_text(json.dumps({
                "development_sample_ids": ["a"],
                "holdout_sample_ids": ["b"],
            }), encoding="utf-8")

            selected = select_samples(dataset, split, "development")

        self.assertEqual([row["sample_id"] for row in selected], ["a"])

    def test_leakage_audit_detects_sample_or_target_literals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            dataset = root / "samples.jsonl"
            dataset.write_text(json.dumps({
                "sample_id": "public_x",
                "ground_truth": {"parent_asin": "TARGET"},
            }) + "\n", encoding="utf-8")
            (source / "agent.py").write_text("SPECIAL = 'TARGET'\n", encoding="utf-8")

            findings = audit_no_public_label_literals(source, dataset)

        self.assertEqual(len(findings), 1)


if __name__ == "__main__":
    unittest.main()
