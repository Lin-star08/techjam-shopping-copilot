from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import TypedDict

from starter.retrieval import CATEGORY_ALIASES, product_text, terms


ALLOWED_ATTRIBUTES = {
    "category", "material", "color", "size", "style", "brand",
    "budget", "feature", "use_case", "other",
}
SOFT_ATTRIBUTES = {"style", "feature", "use_case"}
DEFAULT_LEXICON_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "lexicon.json"

COLOR_WORDS = {
    "black", "white", "blue", "red", "pink", "green", "brown", "gray",
    "grey", "purple", "yellow", "orange", "navy", "beige", "tan", "silver", "gold",
}
MATERIAL_WORDS = {
    "cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk",
    "rayon", "fabric", "rubber", "mesh", "suede", "denim", "canvas", "lace",
}
UNCERTAIN_PREFERENCES = {
    "comfortable", "comfort", "durable", "casual", "cute", "premium",
    "nice", "stylish", "good", "best", "quality",
}
SAFE_FILTER_CATEGORIES = {
    "shoes", "boots", "dress", "shirt", "jacket", "bag", "socks",
    "pants", "jeans", "skirt", "coat",
}
BUDGET_RE = re.compile(
    r"(?:under|below|less\s+than|no\s+more\s+than|<=|maximum|max|budget(?:\s+of)?|around)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
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
SIZE_RE = re.compile(r"\bsize\s*[:#-]?\s*([a-z0-9.]+)\b", re.I)


class Constraint(TypedDict):
    attribute: str
    value: str | float
    kind: str
    confidence: float
    source: str
    raw_text: str


def _default_lexicon() -> dict:
    return {
        "vocabulary": {
            "material": {"values": sorted(MATERIAL_WORDS), "aliases": {}},
            "color": {"values": sorted(COLOR_WORDS), "aliases": {"grey": "gray", "navy blue": "navy"}},
            "style": {"values": ["casual", "dress", "classic", "athletic", "formal"], "aliases": {}},
            "feature": {"values": ["comfortable", "lightweight", "breathable", "durable"], "aliases": {}},
            "use_case": {"values": ["running", "walking", "work", "outdoor", "winter", "travel"], "aliases": {}},
        },
        "category_playbook": {
            "Shoes": {},
            "Boots": {},
            "Dresses": {},
            "Shirts": {},
            "Jackets": {},
            "Bags": {},
            "Socks": {},
            "Pants": {},
            "Jeans": {},
            "Skirts": {},
            "Coats": {},
        },
        "catalog_summary": {"top_stores": []},
    }


@lru_cache(maxsize=4)
def load_lexicon(path: str = str(DEFAULT_LEXICON_PATH)) -> dict:
    try:
        with Path(path).open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return _default_lexicon()
    if isinstance(payload, dict) and isinstance(payload.get("vocabulary"), dict):
        return payload
    return _default_lexicon()


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
    if isinstance(playbook, dict):
        matches: list[tuple[int, int, str]] = []
        for category in playbook:
            if not isinstance(category, str):
                continue
            match = _contains_phrase(text, category)
            if match:
                matches.append((match.start(), -len(match.group(0)), category))
        if matches:
            return min(matches)[2]
    for term in terms(text):
        if term in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[term]
    return None


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
        constraints.append(_constraint("budget", float(budget.group(1)), "override" if override else "hard", 0.99, raw_text))
        seen.add("budget")

    size = SIZE_RE.search(text)
    if size and "size" not in seen:
        constraints.append(_constraint("size", size.group(1).lower(), "override" if override else "hard", 0.97, raw_text))
        seen.add("size")

    vocabulary = lexicon["vocabulary"]
    for attribute in ("material", "color", "style", "feature", "use_case"):
        if attribute in seen or not isinstance(vocabulary.get(attribute), dict):
            continue
        value = _first_vocabulary_value(text, vocabulary[attribute])
        if value is None:
            continue
        kind = "override" if override else "soft" if attribute in SOFT_ATTRIBUTES else "hard"
        constraints.append(_constraint(attribute, value, kind, 0.93 if kind != "soft" else 0.85, raw_text))
        seen.add(attribute)

    category = _category_value(text, lexicon)
    if category is not None and "category" not in seen:
        constraints.append(_constraint("category", category, "override" if override else "hard", 0.92, raw_text))
        seen.add("category")

    brand = _brand_value(text, lexicon)
    if brand is not None and "brand" not in seen:
        constraints.append(_constraint("brand", brand, "override" if override else "hard", 0.9, raw_text))

    return constraints


def extract_basic_hard_constraints(user_message: str) -> dict:
    found_terms = terms(user_message)
    constraints: dict[str, object] = {}
    budget = BUDGET_RE.search(user_message)
    if budget:
        constraints["budget_max"] = float(budget.group(1))

    colors = [term for term in found_terms if term in COLOR_WORDS]
    if colors:
        constraints["color"] = colors[-1]

    materials = [term for term in found_terms if term in MATERIAL_WORDS]
    if materials:
        constraints["material"] = materials[-1]

    categories = [CATEGORY_ALIASES[term] for term in found_terms if term in CATEGORY_ALIASES]
    if categories:
        constraints["category"] = categories[-1]

    return constraints


def _values(value: object) -> list[object]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    return [value]


def _contains_word(corpus: str, value: object) -> bool:
    normalized = {term.lower() for term in terms(corpus)}
    wanted = [term for item in _values(value) for term in terms(str(item))]
    return any(term in normalized for term in wanted)


def _price(product: dict) -> float | None:
    value = product.get("price")
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _matches(product: dict, hard_constraints: dict) -> bool:
    corpus = product_text(product)
    if not corpus:
        return True

    budget_max = hard_constraints.get("budget_max")
    if budget_max is not None:
        price = _price(product)
        if price is not None and price > float(budget_max):
            return False

    for key in ("category", "color", "material"):
        value = hard_constraints.get(key)
        if not value:
            continue
        if isinstance(value, str) and value.lower() in UNCERTAIN_PREFERENCES:
            continue
        if key == "category" and str(value).lower() not in SAFE_FILTER_CATEGORIES:
            continue
        if not _contains_word(corpus, value):
            return False
    return True


def apply_hard_filters(
    candidates: Iterable[dict],
    hard_constraints: dict | None,
    product_lookup: dict[str, dict],
    min_results: int = 10,
) -> list[dict]:
    candidate_list = [dict(candidate) for candidate in candidates]
    if not hard_constraints:
        return candidate_list

    filtered: list[dict] = []
    for candidate in candidate_list:
        parent_asin = str(candidate.get("parent_asin") or "")
        product = product_lookup.get(parent_asin)
        if product is None or _matches(product, hard_constraints):
            filtered.append(candidate)

    if len(filtered) >= min_results:
        return filtered

    seen = {candidate.get("parent_asin") for candidate in filtered}
    for candidate in candidate_list:
        parent_asin = candidate.get("parent_asin")
        if parent_asin in seen:
            continue
        fallback = dict(candidate)
        fallback["debug_reason"] = "fallback after strict filter"
        filtered.append(fallback)
        seen.add(parent_asin)
        if len(filtered) >= min_results:
            break
    return filtered


def hard_filter_diagnostics(
    before_candidates: Iterable[dict],
    after_candidates: Iterable[dict],
    target_parent_asin: str | None = None,
) -> dict:
    before = list(before_candidates)
    after = list(after_candidates)
    before_ids = [str(candidate.get("parent_asin") or "") for candidate in before]
    after_ids = [str(candidate.get("parent_asin") or "") for candidate in after]
    before_set = set(before_ids)
    after_set = set(after_ids)
    diagnostics: dict[str, object] = {
        "before_filter_count": len(before),
        "after_filter_count": len(after),
        "filtered_out_count": len(before_set - after_set),
    }
    if target_parent_asin is not None:
        target = str(target_parent_asin)
        diagnostics["target_present_before_filter"] = target in before_set
        diagnostics["target_present_after_filter"] = target in after_set
        diagnostics["target_filtered_out"] = target in before_set and target not in after_set
    return diagnostics
