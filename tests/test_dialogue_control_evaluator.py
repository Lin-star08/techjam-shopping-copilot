from __future__ import annotations

from collections import Counter
import unittest

from tools.evaluate_dialogue_control import (
    evaluate_answer_utilization,
    evaluate_candidate_question_selection,
    evaluate_cases,
    load_answer_cases,
    load_candidate_question_cases,
    load_cases,
)


class DialogueControlEvaluatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_cases()
        cls.answer_cases = load_answer_cases()
        cls.candidate_question_cases = load_candidate_question_cases()

    def test_fixture_is_balanced_and_has_eighty_cases(self) -> None:
        counts = Counter(str(case["scenario"]) for case in self.cases)

        self.assertEqual(len(self.cases), 80)
        self.assertEqual(
            counts,
            Counter({
                "buying": 20,
                "browsing": 20,
                "boundary": 20,
                "intent_override": 20,
            }),
        )

    def test_adaptive_policy_passes_the_dialogue_control_contract(self) -> None:
        report = evaluate_cases(self.cases, policy_mode="adaptive")

        self.assertEqual(report["dialogue_control_pass_rate"], 1.0)
        self.assertEqual(report["failure_reasons"], {})

    def test_metric_detects_improvement_over_legacy_policy(self) -> None:
        legacy = evaluate_cases(self.cases, policy_mode="legacy")
        adaptive = evaluate_cases(self.cases, policy_mode="adaptive")

        self.assertGreater(
            adaptive["dialogue_control_pass_rate"],
            legacy["dialogue_control_pass_rate"],
        )

    def test_contextual_answer_fixture_has_twenty_cases(self) -> None:
        self.assertEqual(len(self.answer_cases), 20)

    def test_answer_utilization_measures_contextual_capture(self) -> None:
        legacy = evaluate_answer_utilization(
            self.answer_cases,
            contextual_fallback=False,
        )
        adaptive = evaluate_answer_utilization(
            self.answer_cases,
            contextual_fallback=True,
        )

        self.assertEqual(adaptive["answer_utilization_rate"], 1.0)
        self.assertGreater(
            adaptive["answer_utilization_rate"],
            legacy["answer_utilization_rate"],
        )

    def test_candidate_question_fixture_has_twelve_cases(self) -> None:
        self.assertEqual(len(self.candidate_question_cases), 12)

    def test_dynamic_candidate_questions_improve_utility(self) -> None:
        static = evaluate_candidate_question_selection(
            self.candidate_question_cases,
            dynamic=False,
        )
        dynamic = evaluate_candidate_question_selection(
            self.candidate_question_cases,
            dynamic=True,
        )

        self.assertEqual(dynamic["candidate_question_utility_rate"], 1.0)
        self.assertGreater(
            dynamic["candidate_question_utility_rate"],
            static["candidate_question_utility_rate"],
        )


if __name__ == "__main__":
    unittest.main()
