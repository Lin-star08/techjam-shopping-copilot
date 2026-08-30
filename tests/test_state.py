from __future__ import annotations

import unittest

from starter.state import SessionState


def constraint(
    attribute: str,
    value: str | float,
    kind: str = "hard",
    confidence: float = 0.95,
) -> dict:
    return {
        "attribute": attribute,
        "value": value,
        "kind": kind,
        "confidence": confidence,
        "source": "current_message",
        "raw_text": str(value),
    }


class SessionStateTest(unittest.TestCase):
    def test_initial_state_matches_frozen_contract(self) -> None:
        state = SessionState.create(
            "session-a",
            {"preference_tags": ["comfort", "fit", "comfort"]},
        )

        self.assertEqual(set(state.to_dict()), {
            "session_id",
            "turn",
            "current_slots",
            "hard_constraints",
            "soft_preferences",
            "asked_attributes",
            "neutral_attributes",
            "invalidated_slots",
            "profile_signals",
        })
        self.assertEqual(state.profile_signals, ["comfort", "fit"])

    def test_new_value_invalidates_old_value_for_same_attribute(self) -> None:
        state = SessionState.create("session-a", {})
        state.apply([constraint("color", "black")], turn=1)
        state.apply([constraint("color", "brown", kind="override")], turn=2)

        self.assertEqual(state.current_slots["color"], "brown")
        self.assertEqual(state.invalidated_slots["color"], ["black"])
        self.assertNotIn("color", state.soft_preferences)
        self.assertNotIn("color", state.hard_constraints)

    def test_no_preference_removes_active_value_and_blocks_reasking(self) -> None:
        state = SessionState.create("session-a", {})
        state.apply([constraint("brand", "Example")], turn=1)
        state.mark_asked("brand")
        state.apply([constraint("brand", "no_preference", kind="neutral")], turn=2)

        self.assertNotIn("brand", state.current_slots)
        self.assertEqual(state.neutral_attributes, ["brand"])
        self.assertEqual(state.invalidated_slots["brand"], ["Example"])
        self.assertFalse(state.is_askable("brand"))

    def test_asked_attributes_are_unique(self) -> None:
        state = SessionState.create("session-a", {})
        state.mark_asked("color")
        state.mark_asked("color")

        self.assertEqual(state.asked_attributes, ["color"])

    def test_low_confidence_hard_value_is_only_a_soft_preference(self) -> None:
        state = SessionState.create("session-a", {})
        state.apply([constraint("material", "leather", confidence=0.4)], turn=1)

        self.assertNotIn("material", state.current_slots)
        self.assertEqual(state.soft_preferences["material"], ["leather"])

    def test_unknown_constraint_does_not_change_active_state(self) -> None:
        state = SessionState.create("session-a", {})
        state.apply([constraint("other", "maybe", kind="unknown")], turn=1)

        self.assertEqual(state.current_slots, {})
        self.assertEqual(state.hard_constraints, {})
        self.assertEqual(state.soft_preferences, {})

    def test_budget_is_stored_as_a_safe_hard_constraint(self) -> None:
        state = SessionState.create("session-a", {})
        state.apply([constraint("budget", 50.0)], turn=1)

        self.assertEqual(state.hard_constraints, {"budget_max": 50.0})

    def test_to_dict_returns_a_copy(self) -> None:
        state = SessionState.create("session-a", {})
        snapshot = state.to_dict()
        snapshot["current_slots"]["color"] = "black"

        self.assertEqual(state.current_slots, {})


if __name__ == "__main__":
    unittest.main()
