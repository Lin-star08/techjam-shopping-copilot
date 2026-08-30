"""Parse a user message into the team's frozen Constraint format.

The parser is deliberately deterministic and conservative.  It uses only the
catalog-derived vocabulary in ``artifacts/lexicon.json`` and does not inspect
public ground truth.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import TypedDict


ALLOWED_ATTRIBUTES = {
    "category", "material", "color", "size", "style", "brand",
    "budget", "feature", "use_case", "other",
}
SOFT_ATTRIBUTES = {"style", "feature", "use_case"}
DEFAULT_LEXICON_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "lexicon.json"

ATTRIBUTE_LABELS = {
    "category": ("category", "product type", "item type"),
    "material": ("material", "fabric"),
    "color": ("color", "colour"),
    "size": ("size", "sizing"),
    "style": ("style", "fit"),
    "brand": ("brand", "maker"),
    "budget": ("budget", "price"),
    "feature": ("feature",),
    "use_case": ("use case", "use-case", "purpose"),
}

NEUTRAL_MARKERS = (
    re.compile(r"\b(?:no|not any)\s+(?:additional\s+)?preference\b", re.I),
    re.compile(r"\b(?:i\s+)?(?:do not|don't)\s+have\s+(?:an?\s+|any\s+)?(?:additional\s+)?preference\b", re.I),
    re.compile(r"\bany\s+(?:brand|color|colour|material|size|style|feature|budget)\s+is\s+fine\b", re.I),
    re.compile(r"\b(?:it|that)\s+(?:does not|doesn't)\s+matter\b", re.I),
    re.compile(r"\b(?:use your judgment|you decide|no preference)\b", re.I),
)
OVERRIDE_MARKER = re.compile(
    r"\b(?:actually|instead|ignore (?:my |the )?(?:earlier|previous)|changed my mind|rather)\b",
    re.I,
)
BUDGET_RE = re.compile(
    r"(?:under|below|less than|up to|at most|max(?:imum)?(?: of)?|budget(?: is| of| around)?)\s*\$?\s*(\d+(?:\.\d{1,2})?)",
    re.I,
)
SIZE_RE = re.compile(r"\bsize\s*[:#-]?\s*([a-z0-9.]+)\b", re.I)


class Constraint(TypedDict):
    attribute: str
    value: str | float
    kind: str
    confidence: float
    source: str
    raw_text: str


@lru_cache(maxsize=4)
def load_lexicon(path: str = str(DEFAULT_LEXICON_PATH)) -> dict:
    """Load the catalog-derived lexicon from the contract-defined location."""

    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("vocabulary"), dict):
        raise ValueError("lexicon must contain a vocabulary object")
    return payload


def _contains_phrase(text: str, phrase: str) -> re.Match[str] | None:
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"[\s-]+")
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text)


def _named_attributes(text: str) -> list[str]:
    result: list[str] = []
    for attribute, labels in ATTRIBUTE_LABELS.items():
        if any(_contains_phrase(text, label) for label in labels):
            result.append(attribute)
    return result


def _neutral_attributes(text: str, last_asked_attribute: str | None) -> list[str]:
    if not any(pattern.search(text) for pattern in NEUTRAL_MARKERS):
        return []
    named = _named_attributes(text)
    if named:
        return named
    if last_asked_attribute in ALLOWED_ATTRIBUTES:
        return [str(last_asked_attribute)]
    return []


def _constraint(
    attribute: str,
    value: str | float,
    kind: str,
    confidence: float,
    raw_text: str,
) -> Constraint:
    return {
        "attribute": attribute,
        "value": value,
        "kind": kind,
        "confidence": confidence,
        "source": "current_message",
        "raw_text": raw_text,
    }


def _first_vocabulary_value(text: str, item: dict) -> str | None:
    candidates: list[tuple[int, int, str]] = []
    aliases = item.get("aliases") if isinstance(item.get("aliases"), dict) else {}
    for value in item.get("values", []):
        if not isinstance(value, str) or not value:
            continue
        match = _contains_phrase(text, value)
        if match:
            candidates.append((match.start(), -len(match.group(0)), value))
    for alias, canonical in aliases.items():
        if not isinstance(alias, str) or not isinstance(canonical, str):
            continue
        match = _contains_phrase(text, alias)
        if match:
            candidates.append((match.start(), -len(match.group(0)), canonical))
    if not candidates:
        return None
    return min(candidates)[2]


def _category_value(text: str, lexicon: dict) -> str | None:
    playbook = lexicon.get("category_playbook")
    if not isinstance(playbook, dict):
        return None
    matches: list[tuple[int, int, str]] = []
    for category in playbook:
        if not isinstance(category, str):
            continue
        match = _contains_phrase(text, category)
        if match:
            matches.append((match.start(), -len(match.group(0)), category))
    return min(matches)[2] if matches else None


def _brand_value(text: str, lexicon: dict) -> str | None:
    summary = lexicon.get("catalog_summary")
    stores = summary.get("top_stores", []) if isinstance(summary, dict) else []
    matches: list[tuple[int, int, str]] = []
    for item in stores:
        store = item.get("store") if isinstance(item, dict) else None
        if not isinstance(store, str) or not store:
            continue
        match = _contains_phrase(text, store)
        if match:
            matches.append((match.start(), -len(match.group(0)), store))
    return min(matches)[2] if matches else None


def parse_constraints(
    user_message: str,
    *,
    last_asked_attribute: str | None = None,
    lexicon_path: str | Path = DEFAULT_LEXICON_PATH,
) -> list[Constraint]:
    """Return conservative, normalized constraints found in one user message."""

    raw_text = str(user_message)
    text = raw_text.lower().strip()
    if not text:
        return []
    lexicon = load_lexicon(str(Path(lexicon_path).resolve()))
    neutral = _neutral_attributes(text, last_asked_attribute)
    constraints = [
        _constraint(attribute, "no_preference", "neutral", 1.0, raw_text)
        for attribute in neutral
    ]
    override = bool(OVERRIDE_MARKER.search(text))
    seen = set(neutral)

    budget = BUDGET_RE.search(text)
    if budget and "budget" not in seen:
        kind = "override" if override else "hard"
        constraints.append(_constraint("budget", float(budget.group(1)), kind, 0.99, raw_text))
        seen.add("budget")

    size = SIZE_RE.search(text)
    if size and "size" not in seen:
        kind = "override" if override else "hard"
        constraints.append(_constraint("size", size.group(1).lower(), kind, 0.97, raw_text))
        seen.add("size")

    vocabulary = lexicon["vocabulary"]
    for attribute in ("material", "color", "style", "feature", "use_case"):
        if attribute in seen or not isinstance(vocabulary.get(attribute), dict):
            continue
        value = _first_vocabulary_value(text, vocabulary[attribute])
        if value is None:
            continue
        kind = "override" if override else "soft" if attribute in SOFT_ATTRIBUTES else "hard"
        confidence = 0.93 if kind != "soft" else 0.85
        constraints.append(_constraint(attribute, value, kind, confidence, raw_text))
        seen.add(attribute)

    category = _category_value(text, lexicon)
    if category is not None and "category" not in seen:
        kind = "override" if override else "hard"
        constraints.append(_constraint("category", category, kind, 0.92, raw_text))
        seen.add("category")

    brand = _brand_value(text, lexicon)
    if brand is not None and "brand" not in seen:
        kind = "override" if override else "hard"
        constraints.append(_constraint("brand", brand, kind, 0.9, raw_text))

    return constraints
