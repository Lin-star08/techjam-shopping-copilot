from __future__ import annotations

import unittest

from starter.candidate_questions import best_candidate_question


def products_with_feature(left: str, right: str, count: int = 5) -> list[dict]:
    return [
        {
            "parent_asin": f"L{index}",
            "title": f"Product with {left}",
            "features": [left],
            "store": "",
            "price": None,
        }
        for index in range(count)
    ] + [
        {
            "parent_asin": f"R{index}",
            "title": f"Product with {right}",
            "features": [right],
            "store": "",
            "price": None,
        }
        for index in range(count)
    ]


class CandidateQuestionTest(unittest.TestCase):
    def test_selects_balanced_feature_split(self) -> None:
        question = best_candidate_question(
            products_with_feature("waterproof", "lightweight"),
            ["feature", "brand"],
        )

        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.attribute, "feature")
        self.assertEqual({question.left_value, question.right_value}, {"waterproof", "lightweight"})
        self.assertEqual(question.coverage, 1.0)
        self.assertGreaterEqual(question.information_gain, 0.9)
        self.assertIn("waterproof", question.message)
        self.assertIn("lightweight", question.message)

    def test_rejects_pool_without_two_supported_values(self) -> None:
        products = products_with_feature("waterproof", "unknown wording")

        question = best_candidate_question(products, ["feature"])

        self.assertIsNone(question)

    def test_builds_median_budget_split_when_price_coverage_is_sufficient(self) -> None:
        products = [
            {
                "parent_asin": f"P{index}",
                "title": "Product",
                "price": float(10 + index * 5),
                "store": "",
            }
            for index in range(10)
        ]

        question = best_candidate_question(products, ["budget"])

        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.attribute, "budget")
        self.assertIn("under $", question.left_value)
        self.assertIn("or more", question.right_value)

    def test_answer_utility_prior_beats_raw_budget_entropy(self) -> None:
        products = []
        for index in range(10):
            feature = "waterproof" if index < 3 else "lightweight" if index < 6 else ""
            products.append({
                "parent_asin": f"P{index}",
                "title": feature or "Product",
                "features": [feature] if feature else [],
                "price": float(20 if index < 5 else 80),
                "store": "",
            })

        question = best_candidate_question(products, ["feature", "budget"])

        self.assertIsNotNone(question)
        assert question is not None
        self.assertEqual(question.attribute, "feature")

        raw_information_gain_question = best_candidate_question(
            products,
            ["feature", "budget"],
            use_utility_priors=False,
        )
        self.assertIsNotNone(raw_information_gain_question)
        assert raw_information_gain_question is not None
        self.assertEqual(raw_information_gain_question.attribute, "budget")


if __name__ == "__main__":
    unittest.main()
