"""Minimal, explainable clarification policy for the shopping dialogue."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Mapping

from starter.constraints import ALLOWED_ATTRIBUTES, DEFAULT_LEXICON_PATH, load_lexicon
from starter.state import SessionState


MAX_ASKED_ATTRIBUTES = 3
ENOUGH_NON_CATEGORY_SIGNALS = 2
MIN_COVERAGE = 0.1
MIN_INFORMATION_VALUE = 0.01

FALLBACK_QUESTIONS = {
    "category": "What type of product are you looking for?",
    "use_case": "What will you mainly use it for?",
    "material": "Do you have a material preference?",
    "style": "What style or fit do you prefer?",
    "color": "What color would you prefer?",
    "size": "What size do you need?",
    "budget": "What budget would you like to stay within?",
    "feature": "Which feature matters most to you?",
    "brand": "Do you have a preferred brand?",
    "other": "What other requirement matters most, such as material, fit, or a must-have feature?",
}
FALLBACK_PRIORITY = (
    "use_case", "material", "style", "color", "size", "budget", "feature", "brand",
)


@dataclass(frozen=True)
class QuestionDecision:
    ask_attribute: str | None
    message: str


class QuestionPolicy:
    """Choose at most one useful, non-repeated clarification question."""

    def __init__(
        self,
        lexicon_path: str | Path = DEFAULT_LEXICON_PATH,
        *,
        max_asked_attributes: int = MAX_ASKED_ATTRIBUTES,
    ) -> None:
        self.lexicon = load_lexicon(str(Path(lexicon_path).resolve()))
        self.max_asked_attributes = max_asked_attributes

    def decide(self, state: SessionState) -> QuestionDecision:
        if state.turn >= 10 or len(state.asked_attributes) >= self.max_asked_attributes:
            return QuestionDecision(None, "Here are the closest matches I found.")

        known = self._known_attributes(state)
        category = state.current_slots.get("category")
        if category is None and self._available(state, "category", known):
            return QuestionDecision("category", FALLBACK_QUESTIONS["category"])

        # A broad first clarification lets the customer volunteer the strongest
        # remaining requirement instead of forcing it into a guessed attribute.
        # This is especially valuable for long-tail catalog fields that the
        # fixed vocabulary cannot classify safely.
        if state.turn == 1 and self._available(state, "other", known):
            return QuestionDecision("other", FALLBACK_QUESTIONS["other"])

        non_category_known = len(known - {"category"})
        if non_category_known >= ENOUGH_NON_CATEGORY_SIGNALS:
            return QuestionDecision(None, "Here are the closest matches I found.")

        for item in self._category_questions(str(category)):
            attribute = item.get("ask_attribute")
            if not isinstance(attribute, str) or not self._available(state, attribute, known):
                continue
            coverage = item.get("coverage", 0.0)
            information_value = item.get("information_value", 0.0)
            if not isinstance(coverage, (int, float)) or coverage < MIN_COVERAGE:
                continue
            if not isinstance(information_value, (int, float)) or information_value < MIN_INFORMATION_VALUE:
                continue
            message = item.get("question")
            if not isinstance(message, str) or not message.strip():
                message = FALLBACK_QUESTIONS[attribute]
            return QuestionDecision(attribute, message)

        for attribute in FALLBACK_PRIORITY:
            if self._available(state, attribute, known):
                return QuestionDecision(attribute, FALLBACK_QUESTIONS[attribute])
        return QuestionDecision(None, "Here are the closest matches I found.")

    @staticmethod
    def _known_attributes(state: SessionState) -> set[str]:
        known = set(state.current_slots) | set(state.soft_preferences)
        for key in state.hard_constraints:
            known.add("budget" if key == "budget_max" else key)
        return known

    @staticmethod
    def _available(state: SessionState, attribute: str, known: set[str]) -> bool:
        return (
            attribute in ALLOWED_ATTRIBUTES
            and attribute not in known
            and state.is_askable(attribute)
        )

    def _category_questions(self, category: str) -> list[Mapping[str, object]]:
        playbook = self.lexicon.get("category_playbook")
        if not isinstance(playbook, dict) or not category:
            return []
        normalized = self._tokens(category)
        best: tuple[float, Mapping[str, object]] | None = None
        for name, item in playbook.items():
            if not isinstance(name, str) or not isinstance(item, Mapping):
                continue
            candidate = self._tokens(name)
            if not candidate:
                continue
            if name.casefold() == category.casefold():
                score = 2.0
            else:
                score = len(normalized & candidate) / len(normalized | candidate) if normalized | candidate else 0.0
            if score > 0 and (best is None or score > best[0]):
                best = (score, item)
        if best is None:
            return []
        questions = best[1].get("high_value_questions")
        if not isinstance(questions, list):
            return []
        return [item for item in questions if isinstance(item, Mapping)]

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", value.casefold()))
