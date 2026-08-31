from __future__ import annotations

import unittest

from starter.constraints import parse_constraints


class ConstraintParserTest(unittest.TestCase):
    def test_parses_explicit_catalog_values_and_budget(self) -> None:
        constraints = parse_constraints("I need black leather shoes under $50.")
        by_attribute = {item["attribute"]: item for item in constraints}

        self.assertEqual(by_attribute["color"]["value"], "black")
        self.assertEqual(by_attribute["material"]["value"], "leather")
        self.assertEqual(by_attribute["category"]["value"].lower(), "shoes")
        self.assertEqual(by_attribute["budget"]["value"], 50.0)
        self.assertTrue(all(item["source"] == "current_message" for item in constraints))

    def test_no_preference_uses_named_attribute(self) -> None:
        constraints = parse_constraints("Any brand is fine.")

        self.assertEqual(len(constraints), 1)
        self.assertEqual(constraints[0]["attribute"], "brand")
        self.assertEqual(constraints[0]["kind"], "neutral")

    def test_no_preference_falls_back_to_last_asked_attribute(self) -> None:
        constraints = parse_constraints(
            "I don't have a preference; please use your judgment.",
            last_asked_attribute="color",
        )

        self.assertEqual(len(constraints), 1)
        self.assertEqual(constraints[0]["attribute"], "color")
        self.assertEqual(constraints[0]["kind"], "neutral")

    def test_additional_no_preference_does_not_become_a_soft_answer(self) -> None:
        constraints = parse_constraints(
            "I don't have an additional preference for use case.",
            last_asked_attribute="use_case",
        )

        self.assertEqual(len(constraints), 1)
        self.assertEqual(constraints[0]["kind"], "neutral")

    def test_override_marker_marks_new_value(self) -> None:
        constraints = parse_constraints("Actually, ignore the earlier color; make them brown.")
        color = next(item for item in constraints if item["attribute"] == "color")

        self.assertEqual(color["value"], "brown")
        self.assertEqual(color["kind"], "override")
        self.assertEqual(color["raw_text"], "Actually, ignore the earlier color; make them brown.")

    def test_unknown_message_does_not_invent_a_constraint(self) -> None:
        self.assertEqual(parse_constraints("I'm still exploring."), [])

    def test_contextual_feature_answer_captures_two_long_tail_values(self) -> None:
        constraints = parse_constraints(
            "For that, what matters is: Pull-On closure; Hand Wash Only.",
            last_asked_attribute="feature",
        )
        features = [
            item for item in constraints
            if item["attribute"] == "feature"
        ]

        self.assertEqual(
            [item["value"] for item in features],
            ["Pull-On closure", "Hand Wash Only"],
        )
        self.assertTrue(all(item["kind"] == "soft" for item in features))
        self.assertTrue(all(item["confidence"] == 0.65 for item in features))

    def test_contextual_fallback_accepts_a_short_bare_answer(self) -> None:
        constraints = parse_constraints(
            "Magnetic clasp with an engraved dial",
            last_asked_attribute="feature",
        )

        self.assertEqual(constraints[0]["attribute"], "feature")
        self.assertEqual(
            constraints[0]["value"],
            "Magnetic clasp with an engraved dial",
        )
        self.assertEqual(constraints[0]["kind"], "soft")

    def test_contextual_fallback_rejects_generic_negative_feedback(self) -> None:
        constraints = parse_constraints(
            "Those options are not quite right yet. Ask me about one specific attribute.",
            last_asked_attribute="feature",
        )

        self.assertEqual(constraints, [])

    def test_contextual_fallback_can_be_disabled_for_baseline_comparison(self) -> None:
        constraints = parse_constraints(
            "For that, what matters is: Pull-On closure; Hand Wash Only.",
            last_asked_attribute="feature",
            enable_contextual_fallback=False,
        )

        self.assertEqual(constraints, [])


if __name__ == "__main__":
    unittest.main()
