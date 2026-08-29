"""Build the v1 product lexicon from participant-visible catalog fields only.

This script deliberately does not read ``data/public_set.jsonl``.  Its output is
catalog-derived knowledge, not a lookup table fitted to public ground truth.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import json
import math
from pathlib import Path
import re


ALLOWED_ASK_ATTRIBUTES = {
    "category", "material", "color", "size", "style", "brand", "budget",
    "feature", "use_case", "other",
}

# Small, explainable seeds. Counts and category priorities are learned only from
# the frozen catalog. Longer phrases go first to avoid partial matches.
VOCABULARY = {
    "material": [
        "stainless steel", "sterling silver", "faux leather", "genuine leather",
        "memory foam", "polyester", "cotton", "spandex", "leather", "nylon",
        "wool", "silk", "satin", "denim", "canvas", "rubber", "suede",
        "fleece", "lace", "mesh", "acrylic", "rayon", "linen", "cashmere",
        "gold", "silver", "titanium", "ceramic",
    ],
    "color": [
        "rose gold", "navy blue", "light blue", "dark blue", "hot pink",
        "black", "white", "blue", "red", "green", "yellow", "orange",
        "purple", "pink", "brown", "gray", "grey", "beige", "tan", "navy",
        "gold", "silver", "multicolor", "clear",
    ],
    "style": [
        "high waist", "low rise", "slim fit", "regular fit", "relaxed fit",
        "crew neck", "v neck", "long sleeve", "short sleeve", "sleeveless",
        "casual", "formal", "classic", "vintage", "modern", "sporty",
        "minimalist", "boho", "western", "athletic", "dress", "oversized",
    ],
    "feature": [
        "waterproof", "water resistant", "breathable", "lightweight",
        "quick drying", "quick dry", "moisture wicking", "uv protection",
        "hypoallergenic", "non slip", "slip resistant", "stretch", "insulated",
        "machine washable", "reversible", "adjustable", "padded", "supportive",
        "comfortable", "durable", "compression", "wrinkle resistant",
    ],
    "use_case": [
        "running", "walking", "hiking", "training", "workout", "travel",
        "wedding", "party", "office", "work", "school", "outdoor", "winter",
        "summer", "swimming", "cycling", "dance", "costume", "everyday",
        "gift", "sleep", "maternity",
    ],
}

ALIASES = {
    "color": {"grey": "gray", "navy blue": "navy"},
    "feature": {
        "quick drying": "quick dry",
        "moisture wicking": "moisture-wicking",
        "water resistant": "water-resistant",
        "non slip": "slip-resistant",
        "slip resistant": "slip-resistant",
        "machine washable": "machine-washable",
        "uv protection": "UV protection",
    },
    "style": {"v neck": "v-neck"},
}

QUESTION_LABELS = {
    "material": "Do you have a material preference?",
    "color": "What color would you prefer?",
    "style": "What style or fit do you prefer?",
    "brand": "Do you have a preferred brand?",
    "budget": "What budget would you like to stay within?",
    "feature": "Which feature matters most to you?",
    "use_case": "What will you mainly use it for?",
}

# A brand can have high mathematical entropy without being the best first
# question. These priors keep the catalog signal useful while preferring more
# product-defining attributes for a vague shopper.
QUESTION_WEIGHTS = {
    "material": 1.0,
    "color": 0.9,
    "style": 1.0,
    "brand": 0.45,
    "budget": 0.8,
    "feature": 1.0,
    "use_case": 1.0,
}


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key} {item}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _patterns() -> dict[str, re.Pattern[str]]:
    result = {}
    for attribute, phrases in VOCABULARY.items():
        alternatives = "|".join(re.escape(phrase) for phrase in sorted(phrases, key=len, reverse=True))
        result[attribute] = re.compile(rf"(?<![a-z0-9])(?:{alternatives})(?![a-z0-9])", re.I)
    return result


def _matches(text: str, pattern: re.Pattern[str], attribute: str) -> set[str]:
    aliases = ALIASES.get(attribute, {})
    return {
        aliases.get(match.group(0).lower(), match.group(0).lower())
        for match in pattern.finditer(text)
    }


def _question_score(product_count: int, present_count: int, values: Counter[str]) -> float:
    """Information-value proxy: usable coverage times normalized value entropy."""
    if product_count == 0 or present_count == 0 or len(values) < 2:
        return 0.0
    coverage = present_count / product_count
    total = sum(values.values())
    entropy = -sum((count / total) * math.log(count / total) for count in values.values())
    normalized_entropy = entropy / math.log(len(values))
    return coverage * normalized_entropy


def build(catalog_path: Path, top_categories: int) -> dict:
    patterns = _patterns()
    product_count = 0
    priced_count = 0
    leaf_counts: Counter[str] = Counter()
    stores: Counter[str] = Counter()
    global_values = {name: Counter() for name in VOCABULARY}
    category_presence: dict[str, Counter[str]] = defaultdict(Counter)
    category_values: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: defaultdict(Counter)
    )

    with catalog_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            product = json.loads(line)
            product_count += 1
            categories = [str(item).strip() for item in product.get("categories", []) if str(item).strip()]
            leaf = categories[-1] if categories else "Uncategorized"
            leaf_counts[leaf] += 1

            store = str(product.get("store") or "").strip()
            if store:
                stores[store] += 1
                category_presence[leaf]["brand"] += 1
                category_values[leaf]["brand"][store] += 1

            price = product.get("price")
            if isinstance(price, (int, float)) and price >= 0:
                priced_count += 1
                category_presence[leaf]["budget"] += 1
                # Log-friendly price bands avoid false precision in question priority.
                band = "<25" if price < 25 else "25-50" if price < 50 else "50-100" if price < 100 else "100+"
                category_values[leaf]["budget"][band] += 1

            visible_text = " ".join(
                _text(product.get(field))
                for field in ("title", "features", "description", "details")
            ).lower()
            for attribute, attribute_patterns in patterns.items():
                values = _matches(visible_text, attribute_patterns, attribute)
                if values:
                    category_presence[leaf][attribute] += 1
                    for value in values:
                        global_values[attribute][value] += 1
                        category_values[leaf][attribute][value] += 1

    focus_categories = [name for name, _ in leaf_counts.most_common(top_categories)]
    playbook = {}
    for category in focus_categories:
        count = leaf_counts[category]
        candidates = []
        for attribute in QUESTION_LABELS:
            present = category_presence[category][attribute]
            score = _question_score(count, present, category_values[category][attribute]) * QUESTION_WEIGHTS[attribute]
            candidates.append({
                "ask_attribute": attribute,
                "question": QUESTION_LABELS[attribute],
                "coverage": round(present / count, 4),
                "information_value": round(score, 4),
                "top_values": [value for value, _ in category_values[category][attribute].most_common(8)],
            })
        candidates.sort(key=lambda item: (-item["information_value"], -item["coverage"], item["ask_attribute"]))
        playbook[category] = {
            "product_count": count,
            "high_value_questions": candidates[:3],
        }

    return {
        "schema_version": "1.0",
        "generated_on": date.today().isoformat(),
        "source": {
            "path": catalog_path.as_posix(),
            "product_count": product_count,
            "participant_visible_fields_only": True,
            "public_ground_truth_used": False,
        },
        "contract": {
            "allowed_ask_attributes": sorted(ALLOWED_ASK_ATTRIBUTES),
            "neutral_rule": "Never ask an attribute recorded as neutral.",
            "asked_rule": "Never repeat an attribute already recorded as asked.",
            "override_rule": "A new explicit value replaces the old value; invalidated values must not enter current-state retrieval.",
            "hard_filter_rule": "Use a value as a hard filter only when parsing is explicit and reliable.",
        },
        "catalog_summary": {
            "priced_product_count": priced_count,
            "priced_coverage": round(priced_count / product_count, 4),
            "top_leaf_categories": [
                {"category": name, "product_count": count}
                for name, count in leaf_counts.most_common(top_categories)
            ],
            "top_stores": [{"store": name, "product_count": count} for name, count in stores.most_common(50)],
        },
        "vocabulary": {
            attribute: {
                "values": [value for value, _ in counts.most_common(100)],
                "aliases": ALIASES.get(attribute, {}),
            }
            for attribute, counts in global_values.items()
        },
        "category_playbook": playbook,
    }


def render_playbook(payload: dict) -> str:
    lines = [
        "# Category Question Playbook v1",
        "",
        "This file is generated from `data/catalog.jsonl` by `knowledge/build_lexicon.py`.",
        "It does not use public ground truth. The machine-readable source of truth is",
        "`artifacts/lexicon.json`.",
        "",
        "## Usage contract for member 2",
        "",
        "1. Consider questions in the listed order, but skip attributes already in `asked`, `neutral`, or current slots.",
        "2. Ask at most one attribute, and only if it is expected to narrow the current candidates; otherwise return `ask_attribute = null`.",
        "3. Treat catalog-derived priorities as a weak policy prior, not as hard constraints.",
        "4. A later explicit preference replaces the earlier value. Invalidated values must never re-enter current-state retrieval.",
        "5. Some frozen catalog leaf labels are noisy (for example, `Westlake`). Do not hard-filter on a category inferred only from a noisy leaf label.",
        "",
        "## Catalog summary",
        "",
        f"- Products scanned: {payload['source']['product_count']}",
        f"- Products with usable prices: {payload['catalog_summary']['priced_product_count']} ({payload['catalog_summary']['priced_coverage']:.2%})",
        "- Priority formula: attribute coverage x normalized value entropy x explainable policy prior.",
        "",
        "## Top category priorities",
        "",
    ]
    for category, item in payload["category_playbook"].items():
        questions = ", ".join(
            f"`{question['ask_attribute']}` (coverage {question['coverage']:.1%})"
            for question in item["high_value_questions"]
        )
        lines.extend([
            f"### {category} ({item['product_count']} products)",
            "",
            f"Priority: {questions}.",
            "",
        ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/lexicon.json"))
    parser.add_argument("--playbook-output", type=Path, default=Path("artifacts/category_playbook.md"))
    parser.add_argument("--top-categories", type=int, default=30)
    args = parser.parse_args()
    payload = build(args.catalog, args.top_categories)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.playbook_output.write_text(render_playbook(payload) + "\n", encoding="utf-8")
    print(f"wrote {args.output} and {args.playbook_output} from {payload['source']['product_count']} products")


if __name__ == "__main__":
    main()
