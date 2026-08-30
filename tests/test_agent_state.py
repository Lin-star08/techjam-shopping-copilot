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
        self.agent.connection.close()
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
        self.assertEqual(first["ask_attribute"], "brand")
        self.assertEqual(second["ask_attribute"], "material")
        self.assertEqual(state.asked_attributes, ["brand", "material"])

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
        self.assertEqual(first["ask_attribute"], "color")
        self.assertNotEqual(second["ask_attribute"], "color")
        self.assertIn("color", state.neutral_attributes)
        self.assertEqual(
            [item.intent for item in self.agent._intent_history["session-a"]],
            [DialogueIntent.BROWSING, DialogueIntent.BOUNDARY],
        )


if __name__ == "__main__":
    unittest.main()
