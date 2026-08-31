from __future__ import annotations

import unittest

from starter.dialogue_policy import QuestionPolicy
from starter.intent import DialogueIntent
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

    def test_buying_stops_after_two_questions_but_browsing_can_continue(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        state.mark_asked("color")
        state.mark_asked("brand")

        buying = self.policy.decide(state, intent=DialogueIntent.BUYING)
        browsing = self.policy.decide(state, intent=DialogueIntent.BROWSING)

        self.assertIsNone(buying.ask_attribute)
        self.assertEqual(browsing.ask_attribute, "use_case")

    def test_browsing_collects_a_third_non_category_signal(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        add_value(state, "color", "black")
        add_value(state, "material", "leather")

        decision = self.policy.decide(state, intent=DialogueIntent.BROWSING)

        self.assertEqual(decision.ask_attribute, "use_case")

    def test_boundary_replaces_one_declined_question_then_stops(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        state.mark_asked("color")
        state.neutral_attributes.append("color")

        replacement = self.policy.decide(
            state,
            intent=DialogueIntent.BOUNDARY,
            changed_attributes={"color"},
        )
        state.mark_asked(str(replacement.ask_attribute))
        stopped = self.policy.decide(state, intent=DialogueIntent.BOUNDARY)

        self.assertEqual(replacement.ask_attribute, "use_case")
        self.assertIn("skip that preference", replacement.message)
        self.assertIsNone(stopped.ask_attribute)

    def test_override_allows_one_recovery_question_after_normal_limit(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        add_value(state, "color", "brown", kind="override")
        for attribute in ("color", "brand", "material"):
            state.mark_asked(attribute)

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.INTENT_OVERRIDE,
            changed_attributes={"color"},
        )

        self.assertEqual(decision.ask_attribute, "use_case")
        self.assertIn("updated your request", decision.message)

    def test_override_does_not_immediately_reask_changed_attribute(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.INTENT_OVERRIDE,
            changed_attributes={"use_case"},
        )

        self.assertEqual(decision.ask_attribute, "feature")

    def test_stops_after_two_empty_turns_once_enough_signals_are_known(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        add_value(state, "color", "black")
        add_value(state, "material", "leather")
        add_value(state, "size", "9")

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.BROWSING,
            no_new_info_streak=2,
        )

        self.assertIsNone(decision.ask_attribute)

    def test_two_empty_answers_do_not_end_pure_exploration(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.BROWSING,
            no_new_info_streak=2,
        )

        self.assertEqual(decision.ask_attribute, "use_case")

    def test_candidate_pool_can_replace_static_question_priority(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        products = [
            {"title": "Waterproof shoe", "features": ["waterproof"], "store": ""}
            for _ in range(5)
        ] + [
            {"title": "Lightweight shoe", "features": ["lightweight"], "store": ""}
            for _ in range(5)
        ]

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.BROWSING,
            candidate_products=products,
        )

        self.assertEqual(decision.ask_attribute, "feature")
        self.assertIn("waterproof", decision.message)
        self.assertIn("lightweight", decision.message)

    def test_candidate_pool_never_reasks_a_neutral_attribute(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")
        state.neutral_attributes.append("feature")
        products = [
            {"title": "Waterproof shoe", "features": ["waterproof"], "store": ""}
            for _ in range(5)
        ] + [
            {"title": "Lightweight shoe", "features": ["lightweight"], "store": ""}
            for _ in range(5)
        ]

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.BROWSING,
            candidate_products=products,
        )

        self.assertNotEqual(decision.ask_attribute, "feature")

    def test_one_turn_without_new_information_can_still_ask(self) -> None:
        state = SessionState.create("session-a", {})
        add_value(state, "category", "Shoes")

        decision = self.policy.decide(
            state,
            intent=DialogueIntent.BROWSING,
            no_new_info_streak=1,
        )

        self.assertEqual(decision.ask_attribute, "use_case")


if __name__ == "__main__":
    unittest.main()
