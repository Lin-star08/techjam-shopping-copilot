from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from starter.agent import Agent
from starter.intent import DialogueIntent


class AgentStateIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        catalog = Path(self.directory.name) / "catalog.jsonl"
        rows = [
            {
                "parent_asin": "A",
                "title": "Black leather shoes",
                "categories": ["Clothing", "Shoes"],
                "features": [],
                "details": {},
                "store": "Example",
                "description": [],
            },
            {
                "parent_asin": "B",
                "title": "Brown leather shoes",
                "categories": ["Clothing", "Shoes"],
                "features": [],
                "details": {},
                "store": "Example",
                "description": [],
            },
        ]
        catalog.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        self.agent = Agent(catalog)

    def tearDown(self) -> None:
        self.agent.retriever.connection.close()
        self.directory.cleanup()

    def test_agent_updates_state_without_changing_response_contract(self) -> None:
        self.agent.reset("session-a", {"preference_tags": ["comfort"]})
        first = self.agent.respond("session-a", "I need black shoes.", 1, 10)
        second = self.agent.respond(
            "session-a",
            "Actually, ignore the earlier color; make them brown.",
            2,
            10,
        )

        state = self.agent._sessions["session-a"]
        self.assertEqual(state.current_slots["color"], "brown")
        self.assertEqual(state.invalidated_slots["color"], ["black"])
        self.assertEqual(
            [item.intent for item in self.agent._intent_history["session-a"]],
            [DialogueIntent.BUYING, DialogueIntent.INTENT_OVERRIDE],
        )
        self.assertEqual(
            set(second),
            {"message", "ask_attribute", "recommendations", "usage"},
        )
        self.assertIsNotNone(first["ask_attribute"])
        self.assertIsNotNone(second["ask_attribute"])
        self.assertNotEqual(first["ask_attribute"], second["ask_attribute"])
        self.assertEqual(
            state.asked_attributes,
            [first["ask_attribute"], second["ask_attribute"]],
        )

    def test_agent_applies_no_preference_to_last_asked_attribute(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.mark_asked("brand")

        response = self.agent.respond(
            "session-a",
            "I don't have a preference; please use your judgment.",
            1,
            10,
        )

        self.assertEqual(state.neutral_attributes, ["brand"])
        self.assertFalse(state.is_askable("brand"))
        self.assertEqual(response["ask_attribute"], "category")
        self.assertEqual(
            self.agent._intent_history["session-a"][-1].intent,
            DialogueIntent.BOUNDARY,
        )

    def test_agent_does_not_repeat_a_neutral_attribute(self) -> None:
        self.agent.reset("session-a", {})
        first = self.agent.respond(
            "session-a",
            "I'm looking for shoes, but I'm still exploring.",
            1,
            10,
        )
        second = self.agent.respond(
            "session-a",
            "I don't have a preference for color; please use your judgment.",
            2,
            10,
        )

        state = self.agent._sessions["session-a"]
        self.assertIsNotNone(first["ask_attribute"])
        self.assertNotEqual(second["ask_attribute"], "color")
        self.assertIn("color", state.neutral_attributes)
        self.assertEqual(
            [item.intent for item in self.agent._intent_history["session-a"]],
            [DialogueIntent.BROWSING, DialogueIntent.BOUNDARY],
        )

    def test_agent_uses_override_recovery_after_question_budget_is_full(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        for attribute in ("color", "brand", "material"):
            state.mark_asked(attribute)

        response = self.agent.respond(
            "session-a",
            "Actually, ignore the earlier color; make them brown.",
            4,
            10,
        )

        self.assertEqual(
            self.agent._intent_history["session-a"][-1].intent,
            DialogueIntent.INTENT_OVERRIDE,
        )
        self.assertEqual(response["ask_attribute"], "category")
        self.assertIn("updated your request", response["message"])

    def test_agent_buying_turn_respects_shorter_question_budget(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.mark_asked("color")
        state.mark_asked("brand")

        response = self.agent.respond(
            "session-a",
            "I need leather shoes.",
            3,
            10,
        )

        self.assertEqual(
            self.agent._intent_history["session-a"][-1].intent,
            DialogueIntent.BUYING,
        )
        self.assertIsNone(response["ask_attribute"])

    def test_agent_stores_contextual_long_tail_answer_as_soft_preferences(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.apply([{
            "attribute": "category",
            "value": "Shoes",
            "kind": "hard",
            "confidence": 0.95,
            "source": "test_setup",
            "raw_text": "Shoes",
        }], turn=1)
        state.mark_asked("feature")

        self.agent.respond(
            "session-a",
            "For that, what matters is: Pull-On closure; Hand Wash Only.",
            2,
            10,
        )

        self.assertEqual(
            state.soft_preferences["feature"],
            ["Pull-On closure", "Hand Wash Only"],
        )
        self.assertEqual(self.agent._no_new_info_streak["session-a"], 0)

    def test_agent_tracks_two_consecutive_empty_answers(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.apply([{
            "attribute": "category",
            "value": "Shoes",
            "kind": "hard",
            "confidence": 0.95,
            "source": "test_setup",
            "raw_text": "Shoes",
        }], turn=1)
        state.apply([{
            "attribute": "color",
            "value": "black",
            "kind": "soft",
            "confidence": 0.8,
            "source": "test_setup",
            "raw_text": "black",
        }], turn=1)
        state.mark_asked("use_case")

        first = self.agent.respond(
            "session-a",
            "Those options are not quite right yet. Ask me about one specific attribute.",
            2,
            10,
        )
        second = self.agent.respond(
            "session-a",
            "I still need another suggestion before I can decide.",
            3,
            10,
        )

        self.assertIn("ask_attribute", first)
        self.assertIn("ask_attribute", second)
        self.assertEqual(self.agent._no_new_info_streak["session-a"], 2)

    def test_agent_keeps_exploring_after_two_empty_answers_without_a_preference(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.apply([{
            "attribute": "category",
            "value": "Shoes",
            "kind": "hard",
            "confidence": 0.95,
            "source": "test_setup",
            "raw_text": "Shoes",
        }], turn=1)
        state.mark_asked("use_case")

        self.agent.respond(
            "session-a",
            "Those options are not quite right yet. Ask me about one specific attribute.",
            2,
            10,
        )
        second = self.agent.respond(
            "session-a",
            "I still need another suggestion before I can decide.",
            3,
            10,
        )

        self.assertIsNotNone(second["ask_attribute"])
        self.assertEqual(self.agent._no_new_info_streak["session-a"], 2)

    def test_agent_new_contextual_answer_resets_no_information_streak(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.apply([{
            "attribute": "category",
            "value": "Shoes",
            "kind": "hard",
            "confidence": 0.95,
            "source": "test_setup",
            "raw_text": "Shoes",
        }], turn=1)
        state.mark_asked("use_case")

        first = self.agent.respond(
            "session-a",
            "Those options are not quite right yet. Ask me about one specific attribute.",
            2,
            10,
        )
        self.assertEqual(self.agent._no_new_info_streak["session-a"], 1)
        self.assertIsNotNone(first["ask_attribute"])

        self.agent.respond(
            "session-a",
            "For that, what matters is: Pull-On closure; Hand Wash Only.",
            3,
            10,
        )

        self.assertEqual(self.agent._no_new_info_streak["session-a"], 0)

if __name__ == "__main__":
    unittest.main()
