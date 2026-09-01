"""Observable, turn-level dialogue intent recognition.

The recognizer never reads evaluator labels or public ground truth.  It only
uses the current message and already parsed constraints, so a boundary session
becomes observable as ``boundary`` when the user actually declines a preference.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Mapping, Sequence

from starter.constraints import has_no_preference_marker, has_override_marker


class DialogueIntent(str, Enum):
    BUYING = "buying"
    BROWSING = "browsing"
    INTENT_OVERRIDE = "intent_override"
    BOUNDARY = "boundary"


@dataclass(frozen=True)
class IntentResult:
    intent: DialogueIntent
    confidence: float
    evidence: tuple[str, ...]


BROWSING_MARKER = re.compile(
    r"\b(?:still exploring|just browsing|just looking|not sure|open to|"
    r"show me (?:some )?(?:ideas|options)|compare options|considering)\b",
    re.I,
)
BUYING_MARKER = re.compile(
    r"\b(?:i need|i want|looking for|must have|key requirement|"
    r"prefer|budget|under \$?\d|size \w+)\b",
    re.I,
)


def recognize_intent(
    user_message: str,
    constraints: Sequence[Mapping[str, object]] = (),
) -> IntentResult:
    """Classify the current turn into one of the four operational scenarios."""

    text = str(user_message).strip()
    kinds = {str(item.get("kind", "unknown")) for item in constraints}

    # A declined preference is operationally a boundary even when introduced
    # with "actually" because the next action is to skip that attribute.
    if "neutral" in kinds or has_no_preference_marker(text):
        return IntentResult(DialogueIntent.BOUNDARY, 1.0, ("no_preference",))
    if "override" in kinds or has_override_marker(text):
        return IntentResult(DialogueIntent.INTENT_OVERRIDE, 0.98, ("override_marker",))
    if BROWSING_MARKER.search(text):
        return IntentResult(DialogueIntent.BROWSING, 0.95, ("browsing_language",))

    meaningful = [item for item in constraints if str(item.get("kind")) != "unknown"]
    if meaningful:
        attributes = tuple(dict.fromkeys(str(item.get("attribute")) for item in meaningful))
        return IntentResult(DialogueIntent.BUYING, 0.9, ("explicit_constraints", *attributes))
    if BUYING_MARKER.search(text):
        return IntentResult(DialogueIntent.BUYING, 0.75, ("buying_language",))
    return IntentResult(DialogueIntent.BROWSING, 0.6, ("default_vague",))
