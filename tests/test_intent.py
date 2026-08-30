from __future__ import annotations

import unittest

from starter.constraints import parse_constraints
from starter.intent import DialogueIntent, recognize_intent


class IntentRecognitionTest(unittest.TestCase):
    def classify(self, message: str, last_asked_attribute: str | None = None):
        constraints = parse_constraints(
            message,
            last_asked_attribute=last_asked_attribute,
        )
        return recognize_intent(message, constraints)

    def test_recognizes_buying_from_explicit_requirements(self) -> None:
        result = self.classify("I need black leather shoes under $50.")

        self.assertEqual(result.intent, DialogueIntent.BUYING)
        self.assertIn("explicit_constraints", result.evidence)

    def test_recognizes_browsing_before_specific_preferences_exist(self) -> None:
        result = self.classify("I'm looking for shoes, but I'm still exploring.")

        self.assertEqual(result.intent, DialogueIntent.BROWSING)

    def test_recognizes_intent_override(self) -> None:
        result = self.classify("Actually, ignore my earlier choice; make them brown.")

        self.assertEqual(result.intent, DialogueIntent.INTENT_OVERRIDE)

    def test_recognizes_boundary_from_named_no_preference(self) -> None:
        result = self.classify("Any brand is fine.")

        self.assertEqual(result.intent, DialogueIntent.BOUNDARY)

    def test_recognizes_boundary_using_last_asked_attribute(self) -> None:
        result = self.classify(
            "I don't have a preference; please use your judgment.",
            last_asked_attribute="color",
        )

        self.assertEqual(result.intent, DialogueIntent.BOUNDARY)

    def test_boundary_takes_precedence_over_override_wording(self) -> None:
        result = self.classify("Actually, I don't have a preference for color.")

        self.assertEqual(result.intent, DialogueIntent.BOUNDARY)

    def test_vague_message_defaults_to_browsing(self) -> None:
        result = self.classify("Can you help me choose?")

        self.assertEqual(result.intent, DialogueIntent.BROWSING)
        self.assertEqual(result.confidence, 0.6)


if __name__ == "__main__":
    unittest.main()
