from __future__ import annotations

import unittest

from starter.constraints import parse_constraints


class ConstraintParserTest(unittest.TestCase):
    def test_parses_explicit_values_and_budget(self) -> None:
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

        self.assertEqual(constraints[0]["attribute"], "color")
        self.assertEqual(constraints[0]["kind"], "neutral")

    def test_override_marker_marks_new_value(self) -> None:
        constraints = parse_constraints("Actually, ignore the earlier color; make them brown.")
        color = next(item for item in constraints if item["attribute"] == "color")

        self.assertEqual(color["value"], "brown")
        self.assertEqual(color["kind"], "override")

    def test_unknown_message_does_not_invent_a_constraint(self) -> None:
        self.assertEqual(parse_constraints("I'm still exploring."), [])


if __name__ == "__main__":
    unittest.main()
