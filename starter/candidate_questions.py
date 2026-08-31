"""Candidate-pool statistics for contrastive clarification questions."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Iterable, Mapping


MIN_CANDIDATES = 8
MIN_VALUE_SHARE = 0.05
MIN_PAIR_COVERAGE = 0.25
MIN_SPLIT_SCORE = 0.12
ATTRIBUTE_UTILITY_PRIORS = {
    "feature": 1.0,
    "material": 1.0,
    "color": 0.75,
    "size": 0.60,
    "style": 0.35,
    "use_case": 0.25,
    "budget": 0.10,
    "brand": 0.10,
}

ATTRIBUTE_VALUES: dict[str, tuple[str, ...]] = {
    "material": (
        "cotton", "polyester", "leather", "nylon", "wool", "spandex",
        "silk", "rayon", "rubber", "mesh", "suede", "denim", "canvas",
        "lace", "stainless steel",
    ),
    "color": (
        "black", "white", "blue", "red", "pink", "green", "brown",
        "gray", "grey", "purple", "yellow", "orange", "navy", "beige",
        "tan", "silver", "gold",
    ),
    "style": (
        "casual", "formal", "athletic", "classic", "modern", "vintage",
        "slim fit", "regular fit", "relaxed fit", "loose fit", "crew neck",
        "v-neck", "high waist", "low rise",
    ),
    "use_case": (
        "running", "hiking", "walking", "work", "everyday", "outdoor",
        "gym", "training", "travel", "party", "wedding", "sleep",
        "cycling", "soccer", "basketball", "swimming",
    ),
    "feature": (
        "waterproof", "water resistant", "lightweight", "breathable",
        "machine washable", "machine wash", "hand wash", "quick dry",
        "moisture wicking", "uv protection", "stretch", "pockets",
        "zipper closure", "pull-on closure", "button closure", "cushioned",
        "non-slip", "adjustable", "reversible",
    ),
}


@dataclass(frozen=True)
class CandidateQuestion:
    attribute: str
    left_value: str
    right_value: str
    information_gain: float
    coverage: float

    @property
    def message(self) -> str:
        labels = {
            "brand": "brand",
            "budget": "price range",
            "color": "color direction",
            "feature": "feature",
            "material": "material",
            "size": "size",
            "style": "style",
            "use_case": "main use",
        }
        label = labels.get(self.attribute, self.attribute.replace("_", " "))
        return (
            f"To narrow these down, which {label} is closer to what you want: "
            f"{self.left_value}, or {self.right_value}?"
        )


def _product_text(product: Mapping[str, object]) -> str:
    parts: list[str] = []
    for field in ("title", "features", "details", "description", "categories"):
        value = product.get(field)
        if isinstance(value, Mapping):
            parts.extend(f"{key} {item}" for key, item in value.items())
        elif isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value)
        elif value not in (None, ""):
            parts.append(str(value))
    return " ".join(parts).casefold()


def _first_vocab_value(text: str, values: tuple[str, ...]) -> str | None:
    matches: list[tuple[int, int, str]] = []
    for value in values:
        match = re.search(rf"\b{re.escape(value)}\b", text, re.I)
        if match:
            matches.append((match.start(), -len(value), value))
    if not matches:
        return None
    return min(matches)[2]


def _size_value(text: str) -> str | None:
    match = re.search(
        r"\b(?:size|width)\s*[:#-]?\s*(xxs|xs|s|m|l|xl|xxl|\d{1,2}(?:\.5)?)\b",
        text,
        re.I,
    )
    return match.group(1).upper() if match else None


def _clean_brand(value: object) -> str | None:
    brand = re.sub(r"\s+", " ", str(value or "")).strip(" ,.;:-")
    if not brand or len(brand) > 40 or len(brand.split()) > 5:
        return None
    return brand


def _attribute_value(product: Mapping[str, object], attribute: str) -> str | None:
    if attribute == "brand":
        return _clean_brand(product.get("store"))
    text = _product_text(product)
    if attribute == "size":
        return _size_value(text)
    values = ATTRIBUTE_VALUES.get(attribute)
    return _first_vocab_value(text, values) if values else None


def _normalized_entropy(parts: Iterable[int]) -> float:
    counts = [count for count in parts if count > 0]
    total = sum(counts)
    if total <= 0 or len(counts) <= 1:
        return 0.0
    entropy = -sum((count / total) * math.log2(count / total) for count in counts)
    return entropy / math.log2(len(counts))


def _categorical_question(
    products: list[Mapping[str, object]],
    attribute: str,
    value_cache: dict[tuple[str, str], str | None] | None = None,
) -> CandidateQuestion | None:
    values: list[str] = []
    for product in products:
        parent_asin = str(product.get("parent_asin") or "").strip()
        cache_key = (parent_asin, attribute)
        if value_cache is not None and parent_asin and cache_key in value_cache:
            value = value_cache[cache_key]
        else:
            value = _attribute_value(product, attribute)
            if value_cache is not None and parent_asin:
                value_cache[cache_key] = value
        if value is not None:
            values.append(value)
    counts = Counter(values)
    minimum = max(2, math.ceil(len(products) * MIN_VALUE_SHARE))
    common = [(value, count) for value, count in counts.most_common() if count >= minimum]
    if len(common) < 2:
        return None
    (left, left_count), (right, right_count) = common[:2]
    pair_count = left_count + right_count
    coverage = pair_count / len(products)
    if coverage < MIN_PAIR_COVERAGE:
        return None
    other_count = max(0, len(products) - pair_count)
    balance = 2 * min(left_count, right_count) / pair_count
    score = _normalized_entropy((left_count, right_count, other_count)) * coverage * (
        0.5 + 0.5 * balance
    )
    if score < MIN_SPLIT_SCORE:
        return None
    return CandidateQuestion(attribute, left, right, score, coverage)


def _budget_question(products: list[Mapping[str, object]]) -> CandidateQuestion | None:
    prices = sorted(
        float(product["price"])
        for product in products
        if isinstance(product.get("price"), (int, float))
        and not isinstance(product.get("price"), bool)
        and float(product["price"]) > 0
    )
    if len(prices) < max(6, math.ceil(len(products) * 0.15)):
        return None
    midpoint = prices[len(prices) // 2]
    lower = sum(price < midpoint for price in prices)
    upper = len(prices) - lower
    if lower == 0 or upper == 0:
        return None
    coverage = len(prices) / len(products)
    score = _normalized_entropy((lower, upper, len(products) - len(prices))) * coverage
    if score < MIN_SPLIT_SCORE:
        return None
    threshold = f"under ${midpoint:.0f}"
    return CandidateQuestion("budget", threshold, f"${midpoint:.0f} or more", score, coverage)


def best_candidate_question(
    candidate_products: Iterable[Mapping[str, object]],
    attributes: Iterable[str],
    *,
    value_cache: dict[tuple[str, str], str | None] | None = None,
    use_utility_priors: bool = True,
) -> CandidateQuestion | None:
    """Return the highest-separation question supported by the current pool."""

    products = [product for product in candidate_products if isinstance(product, Mapping)][:100]
    if len(products) < MIN_CANDIDATES:
        return None
    questions: list[CandidateQuestion] = []
    for attribute in attributes:
        question = (
            _budget_question(products)
            if attribute == "budget"
            else _categorical_question(products, attribute, value_cache)
        )
        if question is not None:
            questions.append(question)
    if not questions:
        return None
    priority = {name: index for index, name in enumerate(
        ("feature", "use_case", "material", "style", "color", "size", "budget", "brand")
    )}
    return max(
        questions,
        key=lambda item: (
            item.information_gain * (
                ATTRIBUTE_UTILITY_PRIORS.get(item.attribute, 0.25)
                if use_utility_priors
                else 1.0
            ),
            item.coverage,
            -priority.get(item.attribute, 99),
        ),
    )
