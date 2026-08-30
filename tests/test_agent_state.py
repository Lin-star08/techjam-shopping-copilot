from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from starter.agent import Agent


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
            set(second),
            {"message", "ask_attribute", "recommendations", "usage"},
        )
        self.assertIsNone(first["ask_attribute"])

    def test_agent_applies_no_preference_to_last_asked_attribute(self) -> None:
        self.agent.reset("session-a", {})
        state = self.agent._sessions["session-a"]
        state.mark_asked("brand")

        self.agent.respond(
            "session-a",
            "I don't have a preference; please use your judgment.",
            1,
            10,
        )

        self.assertEqual(state.neutral_attributes, ["brand"])
        self.assertFalse(state.is_askable("brand"))


if __name__ == "__main__":
    unittest.main()
