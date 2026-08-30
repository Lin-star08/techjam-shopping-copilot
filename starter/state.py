"""Conversation state for the team's frozen SessionState contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from starter.constraints import ALLOWED_ATTRIBUTES


ALLOWED_KINDS = {"hard", "soft", "neutral", "override", "unknown"}
SOFT_ATTRIBUTES = {"style", "feature", "use_case"}
HARD_CONFIDENCE_THRESHOLD = 0.8


def _unique_strings(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in result:
            result.append(normalized)
    return result


@dataclass
class SessionState:
    session_id: str
    turn: int = 0
    current_slots: dict[str, object] = field(default_factory=dict)
    hard_constraints: dict[str, object] = field(default_factory=dict)
    soft_preferences: dict[str, list[object]] = field(default_factory=dict)
    asked_attributes: list[str] = field(default_factory=list)
    neutral_attributes: list[str] = field(default_factory=list)
    invalidated_slots: dict[str, list[object]] = field(default_factory=dict)
    profile_signals: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, session_id: str, user_profile: Mapping[str, object]) -> "SessionState":
        normalized_session_id = str(session_id).strip()
        if not normalized_session_id:
            raise ValueError("session_id must not be empty")
        tags = user_profile.get("preference_tags", []) if isinstance(user_profile, Mapping) else []
        return cls(
            session_id=normalized_session_id,
            profile_signals=_unique_strings(tags),
        )

    @property
    def last_asked_attribute(self) -> str | None:
        return self.asked_attributes[-1] if self.asked_attributes else None

    def mark_asked(self, attribute: str) -> None:
        if attribute not in ALLOWED_ATTRIBUTES:
            raise ValueError(f"unsupported ask_attribute: {attribute}")
        if attribute not in self.asked_attributes:
            self.asked_attributes.append(attribute)

    def is_askable(self, attribute: str) -> bool:
        return (
            attribute in ALLOWED_ATTRIBUTES
            and attribute not in self.asked_attributes
            and attribute not in self.neutral_attributes
        )

    def apply(self, constraints: Iterable[Mapping[str, object]], turn: int) -> None:
        if not isinstance(turn, int) or turn < 1:
            raise ValueError("turn must be a positive integer")
        self.turn = turn
        for constraint in constraints:
            self._apply_one(constraint)

    def _apply_one(self, constraint: Mapping[str, object]) -> None:
        attribute = str(constraint.get("attribute", ""))
        kind = str(constraint.get("kind", "unknown"))
        value = constraint.get("value")
        confidence_value = constraint.get("confidence", 0.0)
        confidence = float(confidence_value) if isinstance(confidence_value, (int, float)) else 0.0
        if attribute not in ALLOWED_ATTRIBUTES or kind not in ALLOWED_KINDS:
            return
        if kind == "unknown" or value is None or value == "":
            return
        if kind == "neutral":
            self._invalidate_and_clear(attribute)
            if attribute not in self.neutral_attributes:
                self.neutral_attributes.append(attribute)
            return

        if attribute in self.neutral_attributes:
            self.neutral_attributes.remove(attribute)

        if kind == "soft" or (kind == "hard" and confidence < HARD_CONFIDENCE_THRESHOLD):
            self._add_soft(attribute, value)
            return

        self._replace_active(attribute, value, prefer_soft=kind == "override" and attribute in SOFT_ATTRIBUTES)

    def _replace_active(self, attribute: str, value: object, *, prefer_soft: bool) -> None:
        old_values = self._active_values(attribute)
        if any(old_value != value for old_value in old_values):
            for old_value in old_values:
                if old_value != value:
                    self._record_invalidated(attribute, old_value)
        self._clear_active(attribute)
        if prefer_soft:
            self.soft_preferences[attribute] = [value]
        elif attribute == "budget":
            self.hard_constraints["budget_max"] = value
        else:
            self.current_slots[attribute] = value

    def _add_soft(self, attribute: str, value: object) -> None:
        values = self.soft_preferences.setdefault(attribute, [])
        if value not in values:
            values.append(value)

    def _active_values(self, attribute: str) -> list[object]:
        values: list[object] = []
        if attribute in self.current_slots:
            values.append(self.current_slots[attribute])
        hard_key = "budget_max" if attribute == "budget" else attribute
        if hard_key in self.hard_constraints:
            values.append(self.hard_constraints[hard_key])
        values.extend(self.soft_preferences.get(attribute, []))
        return values

    def _record_invalidated(self, attribute: str, value: object) -> None:
        values = self.invalidated_slots.setdefault(attribute, [])
        if value not in values:
            values.append(value)

    def _clear_active(self, attribute: str) -> None:
        self.current_slots.pop(attribute, None)
        self.hard_constraints.pop(attribute, None)
        if attribute == "budget":
            self.hard_constraints.pop("budget_max", None)
        self.soft_preferences.pop(attribute, None)

    def _invalidate_and_clear(self, attribute: str) -> None:
        for value in self._active_values(attribute):
            self._record_invalidated(attribute, value)
        self._clear_active(attribute)

    def to_dict(self) -> dict[str, object]:
        return deepcopy({
            "session_id": self.session_id,
            "turn": self.turn,
            "current_slots": self.current_slots,
            "hard_constraints": self.hard_constraints,
            "soft_preferences": self.soft_preferences,
            "asked_attributes": self.asked_attributes,
            "neutral_attributes": self.neutral_attributes,
            "invalidated_slots": self.invalidated_slots,
            "profile_signals": self.profile_signals,
        })
