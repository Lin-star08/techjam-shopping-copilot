from __future__ import annotations

import unittest

from tools.analyze_question_traces import compare_results, summarize_sessions


class QuestionTraceAnalysisTest(unittest.TestCase):
    def test_summarizes_answer_yield_and_next_turn_hit(self) -> None:
        sessions = [{
            "sample_id": "s1",
            "scenario_type": "browsing",
            "hit": True,
            "turns": [
                {
                    "ask_attribute": "feature",
                    "agent_message": "To narrow these down, which feature is closer: waterproof, or lightweight?",
                },
                {
                    "ask_attribute": None,
                    "user_message": "For that, what matters is: waterproof.",
                    "eligible_for_hit": True,
                    "target_rank": 2,
                },
            ],
        }]

        report = summarize_sessions(sessions)

        self.assertEqual(report["attribute_report"]["feature"]["answer_yield"], 1.0)
        self.assertEqual(report["attribute_report"]["feature"]["next_turn_hit_rate"], 1.0)
        self.assertEqual(report["attribute_report"]["feature"]["contrastive"], 1)

    def test_compares_gained_and_lost_hits(self) -> None:
        baseline = {"sessions": [
            {"sample_id": "gain", "hit": False},
            {"sample_id": "lost", "hit": True},
        ]}
        current = {"sessions": [
            {"sample_id": "gain", "hit": True},
            {"sample_id": "lost", "hit": False},
        ]}

        comparison = compare_results(baseline, current)

        self.assertEqual(comparison["gained_hits"], ["gain"])
        self.assertEqual(comparison["lost_hits"], ["lost"])


if __name__ == "__main__":
    unittest.main()
