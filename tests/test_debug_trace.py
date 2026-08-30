from __future__ import annotations

import unittest

from evaluator.debug_trace import trace_session


class AlwaysTargetAgent:
    def reset(self, session_id: str, user_profile: dict) -> None:
        self.session_id = session_id

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        return {
            "message": "candidate",
            "ask_attribute": None,
            "recommendations": [{"parent_asin": "A"}],
        }


class DebugTraceTest(unittest.TestCase):
    def test_intent_override_cannot_hit_before_override_turn(self) -> None:
        sample = {
            "sample_id": "public_test",
            "scenario_type": "intent_override",
            "user_profile": {"summary": "test"},
            "ground_truth": {"parent_asin": "A"},
            "intent_card": {
                "target_category": "Blue shoe",
                "hard_constraints": ["blue"],
                "soft_preferences": ["comfortable"],
            },
            "behavior": {
                "scenario_type": "intent_override",
                "override": {
                    "turn": 3,
                    "old_value": "comfortable",
                    "new_value": "blue",
                    "message": "Actually, I need blue.",
                },
            },
        }
        products = {"A": {"parent_asin": "A"}}
        result = trace_session(
            AlwaysTargetAgent(),
            sample,
            {"A"},
            {"A": ["Clothing", "Shoes"]},
            products,
        )
        self.assertTrue(result["hit"])
        self.assertEqual(result["first_hit_turn"], 3)
        self.assertFalse(result["turns"][0]["eligible_for_hit"])
        self.assertFalse(result["turns"][1]["eligible_for_hit"])
        self.assertTrue(result["turns"][2]["eligible_for_hit"])


if __name__ == "__main__":
    unittest.main()
