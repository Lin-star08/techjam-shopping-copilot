from __future__ import annotations

import unittest

from starter.dialogue_policy import QuestionPolicy
from starter.state import SessionState


def add_value(state: SessionState, attribute: str, value: str, kind: str = "hard") -> None:
    state.apply([{
        "attribute": attribute,
        "value": value,
        "kind": kind,
        "confidence": 0.95,
        "source": "current_message",
        "raw_text": value,
    }], max(1, state.turn + 1))


class QuestionPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = QuestionPolicy()

    def test_asks_category_when_category_is_unknown(self) -> None:
        state = SessionState.create("session-a", {})
        state.turn = 1

        decision = self.policy.decide(state)

        self.assertEqual(decision.ask_attribute, "category")

    def test_uses_category_playbook_priority(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")

        decision = self.policy.decide(state)

        self.assertEqual(decision.ask_attribute, "use_case")
        self.assertEqual(decision.message, "What will you mainly use it for?")

    def test_skips_known_asked_and_neutral_attributes(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        add_value(state, "color", "black")
        state.mark_asked("brand")
        state.neutral_attributes.append("material")

        decision = self.policy.decide(state)

        self.assertNotIn(decision.ask_attribute, {"color", "brand", "material"})

    def test_stops_when_two_non_category_signals_are_known(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        add_value(state, "color", "black")
        add_value(state, "material", "leather")

        decision = self.policy.decide(state)

        self.assertIsNone(decision.ask_attribute)

    def test_stops_after_question_limit(self) -> None:
        state = SessionState.create("session-a", {})
        state.turn = 4
        for attribute in ("category", "color", "brand"):
            state.mark_asked(attribute)

        self.assertIsNone(self.policy.decide(state).ask_attribute)

    def test_does_not_ask_on_last_turn(self) -> None:
        state = SessionState.create("session-a", {})
        state.turn = 10

        self.assertIsNone(self.policy.decide(state).ask_attribute)


if __name__ == "__main__":
    unittest.main()
