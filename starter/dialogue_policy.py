"""Minimal, explainable clarification policy for the shopping dialogue."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Mapping

from starter.candidate_questions import best_candidate_question
from starter.constraints import ALLOWED_ATTRIBUTES, DEFAULT_LEXICON_PATH, load_lexicon
from starter.intent import DialogueIntent
from starter.state import SessionState


MAX_ASKED_ATTRIBUTES = 3
ENOUGH_NON_CATEGORY_SIGNALS = 2
BROWSING_ENOUGH_NON_CATEGORY_SIGNALS = 3
BUYING_MAX_ASKED_ATTRIBUTES = 2
BOUNDARY_MAX_ASKED_ATTRIBUTES = 2
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
        self._candidate_value_cache: dict[tuple[str, str], str | None] = {}

    def decide(
        self,
        state: SessionState,
        *,
        intent: DialogueIntent | str | None = None,
        changed_attributes: Iterable[str] = (),
        no_new_info_streak: int = 0,
        candidate_products: Iterable[Mapping[str, object]] = (),
    ) -> QuestionDecision:
        """Choose a question using shared rules plus turn-level intent context.

        Buying and browsing adjust question intensity.  Boundary and override
        are handled as events: a boundary may replace one declined question,
        while an override may ask one recovery question even if the normal
        question budget was already exhausted.
        """

        intent_name = self._intent_name(intent)
        excluded = {
            str(attribute)
            for attribute in changed_attributes
            if str(attribute) in ALLOWED_ATTRIBUTES
        }
        max_asked, enough_signals = self._limits(intent_name)
        if state.turn >= 10:
            return self._stop_decision(intent_name)
        if intent_name != DialogueIntent.INTENT_OVERRIDE.value:
            if len(state.asked_attributes) >= max_asked:
                return self._stop_decision(intent_name)

        known = self._known_attributes(state)
        category = state.current_slots.get("category")
        non_category_known = len(known - {"category"})
        # Two empty answers are only a reliable stop signal once the dialogue
        # already has enough concrete preferences to retrieve with.  Otherwise
        # change the attribute instead of ending an under-specified search.
        if no_new_info_streak >= 2 and non_category_known >= enough_signals:
            return self._stop_decision(intent_name)
        if category is None and self._available(state, "category", known, excluded):
            return self._ask_decision(
                "category",
                FALLBACK_QUESTIONS["category"],
                intent_name,
            )

        if non_category_known >= enough_signals:
            return self._stop_decision(intent_name)

        available_attributes = [
            attribute
            for attribute in FALLBACK_PRIORITY
            if self._available(state, attribute, known, excluded)
        ]
        candidate_question = best_candidate_question(
            candidate_products,
            available_attributes,
            value_cache=self._candidate_value_cache,
            use_utility_priors=intent_name != DialogueIntent.INTENT_OVERRIDE.value,
        )
        if candidate_question is not None:
            return self._ask_decision(
                candidate_question.attribute,
                candidate_question.message,
                intent_name,
            )

        for item in self._category_questions(str(category)):
            attribute = item.get("ask_attribute")
            if not isinstance(attribute, str) or not self._available(
                state,
                attribute,
                known,
                excluded,
            ):
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
            return self._ask_decision(attribute, message, intent_name)

        for attribute in FALLBACK_PRIORITY:
            if self._available(state, attribute, known, excluded):
                return self._ask_decision(
                    attribute,
                    FALLBACK_QUESTIONS[attribute],
                    intent_name,
                )
        return self._stop_decision(intent_name)

    def _limits(self, intent_name: str | None) -> tuple[int, int]:
        if intent_name == DialogueIntent.BUYING.value:
            return (
                min(self.max_asked_attributes, BUYING_MAX_ASKED_ATTRIBUTES),
                ENOUGH_NON_CATEGORY_SIGNALS,
            )
        if intent_name == DialogueIntent.BROWSING.value:
            return self.max_asked_attributes, BROWSING_ENOUGH_NON_CATEGORY_SIGNALS
        if intent_name == DialogueIntent.BOUNDARY.value:
            return (
                min(self.max_asked_attributes, BOUNDARY_MAX_ASKED_ATTRIBUTES),
                1,
            )
        if intent_name == DialogueIntent.INTENT_OVERRIDE.value:
            return self.max_asked_attributes, ENOUGH_NON_CATEGORY_SIGNALS
        return self.max_asked_attributes, ENOUGH_NON_CATEGORY_SIGNALS

    @staticmethod
    def _intent_name(intent: DialogueIntent | str | None) -> str | None:
        if isinstance(intent, DialogueIntent):
            return intent.value
        if isinstance(intent, str):
            return intent
        return None

    @staticmethod
    def _ask_decision(
        attribute: str,
        message: str,
        intent_name: str | None,
    ) -> QuestionDecision:
        if intent_name == DialogueIntent.BOUNDARY.value:
            message = f"No problem—I'll skip that preference. {message}"
        elif intent_name == DialogueIntent.INTENT_OVERRIDE.value:
            message = f"Got it—I've updated your request. {message}"
        return QuestionDecision(attribute, message)

    @staticmethod
    def _stop_decision(intent_name: str | None) -> QuestionDecision:
        if intent_name == DialogueIntent.BOUNDARY.value:
            return QuestionDecision(
                None,
                "No problem—I'll skip that preference and use the closest matches.",
            )
        if intent_name == DialogueIntent.INTENT_OVERRIDE.value:
            return QuestionDecision(
                None,
                "Got it—I've updated your request. Here are the closest matches I found.",
            )
        return QuestionDecision(None, "Here are the closest matches I found.")

    @staticmethod
    def _known_attributes(state: SessionState) -> set[str]:
        known = set(state.current_slots) | set(state.soft_preferences)
        for key in state.hard_constraints:
            known.add("budget" if key == "budget_max" else key)
        return known

    @staticmethod
    def _available(
        state: SessionState,
        attribute: str,
        known: set[str],
        excluded: set[str],
    ) -> bool:
        return (
            attribute in ALLOWED_ATTRIBUTES
            and attribute not in known
            and attribute not in excluded
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
