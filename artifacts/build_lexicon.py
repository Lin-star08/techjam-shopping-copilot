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
        "synthetic leather", "vegan leather", "pu leather", "faux suede",
        "memory foam", "polyester", "cotton", "spandex", "leather", "nylon",
        "wool", "silk", "satin", "denim", "canvas", "rubber", "suede",
        "fleece", "lace", "mesh", "acrylic", "rayon", "linen", "cashmere",
        "polyurethane", "eva", "microfiber", "velvet", "chiffon", "modal",
        "viscose", "gold", "silver", "titanium", "ceramic",
    ],
    "color": [
        "rose gold", "navy blue", "light blue", "dark blue", "hot pink",
        "black", "white", "blue", "red", "green", "yellow", "orange",
        "purple", "pink", "brown", "gray", "grey", "beige", "tan", "navy",
        "gold", "silver", "multicolor", "clear",
    ],
    "style": [
        "high waist", "low rise", "slim fit", "regular fit", "relaxed fit",
        "high-waisted", "slim-fit", "loose fit", "crew neck", "crewneck",
        "round neck", "v neck", "v-neck", "long sleeve", "short sleeve", "sleeveless",
        "casual", "formal", "classic", "vintage", "modern", "sporty",
        "minimalist", "boho", "western", "athletic", "dress", "oversized",
        "bootcut", "cold shoulder", "cropped", "tunic", "hoodie", "camisole",
    ],
    "feature": [
        "waterproof", "water resistant", "breathable", "lightweight",
        "water repellent", "quick drying", "quick dry", "moisture wicking",
        "sweat wicking", "uv protection", "hypoallergenic", "non slip",
        "anti slip", "slip resistant", "stretch", "insulated", "windproof",
        "machine washable", "reversible", "adjustable", "padded", "supportive",
        "comfortable", "durable", "compression", "wrinkle resistant", "washable",
        "odor resistant", "shock absorbing", "arch support", "cushioned",
        "touchscreen", "pockets",
    ],
    "size": [
        "plus size", "plus-size", "wide width", "extra wide", "petite",
        "big and tall", "extended size", "one size",
    ],
    "use_case": [
        "running", "walking", "hiking", "training", "workout", "travel",
        "wedding", "party", "office", "work", "school", "outdoor", "winter",
        "summer", "swimming", "cycling", "dance", "costume", "everyday",
        "gift", "sleep", "maternity", "jogging", "gym", "fitness", "trekking",
        "camping", "beach", "daily", "commute", "business", "yoga", "tennis",
        "basketball", "soccer", "golf", "skiing",
    ],
}

ALIASES = {
    "color": {"grey": "gray", "navy blue": "navy"},
    "material": {
        "pu leather": "synthetic leather",
        "vegan leather": "faux leather",
    },
    "feature": {
        "quick drying": "quick dry",
        "moisture wicking": "moisture-wicking",
        "sweat wicking": "moisture-wicking",
        "water resistant": "water-resistant",
        "water repellent": "water-resistant",
        "non slip": "slip-resistant",
        "anti slip": "slip-resistant",
        "slip resistant": "slip-resistant",
        "machine washable": "machine-washable",
        "uv protection": "UV protection",
        "shock absorbing": "shock-absorbing",
        "arch support": "arch-support",
    },
    "style": {
        "v neck": "v-neck",
        "crewneck": "crew-neck",
        "crew neck": "crew-neck",
        "high-waisted": "high-waist",
        "high waist": "high-waist",
        "slim-fit": "slim-fit",
        "slim fit": "slim-fit",
        "cold shoulder": "cold-shoulder",
    },
    "size": {
        "plus size": "plus-size",
        "wide width": "wide",
        "extra wide": "extra-wide",
        "big and tall": "big-and-tall",
        "one size": "one-size",
    },
    "use_case": {
        "jogging": "running",
        "gym": "workout",
        "fitness": "workout",
        "trekking": "hiking",
        "daily": "everyday",
        "business": "office",
    },
}

QUESTION_LABELS = {
    "category": "What kind of item are you looking for?",
    "size": "What size or fit do you need?",
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
    "category": 1.0,
    "size": 1.0,
    "material": 1.0,
    "color": 0.9,
    "style": 1.0,
    "brand": 0.45,
    "budget": 0.8,
    "feature": 1.0,
    "use_case": 1.0,
}


# The first questions follow normal shopping conversations. Catalog coverage is
# still exposed so member 2 can skip an attribute that cannot narrow the live
# candidate set. The statistical score is a fallback, not the conversation order.
QUESTION_ORDERS = {
    "footwear": ("use_case", "size", "feature", "style", "material", "budget", "color", "brand"),
    "apparel": ("use_case", "size", "style", "material", "feature", "budget", "color", "brand"),
    "innerwear": ("size", "material", "feature", "use_case", "style", "budget", "color", "brand"),
    "jewelry": ("use_case", "style", "material", "feature", "color", "budget", "brand", "size"),
    "watch": ("use_case", "feature", "style", "material", "budget", "color", "brand", "size"),
    "eyewear": ("use_case", "feature", "style", "color", "material", "budget", "brand", "size"),
    "bag": ("use_case", "size", "feature", "style", "material", "budget", "color", "brand"),
    "costume": ("use_case", "size", "style", "budget", "material", "feature", "color", "brand"),
}

QUESTION_EXPLANATIONS = {
    "category": "Resolve an unreliable or overly broad product type before asking details.",
    "use_case": "Establish the shopping goal first.",
    "size": "Confirm fit or capacity before cosmetic preferences.",
    "feature": "Capture the must-have function.",
    "style": "Narrow the look or fit.",
    "material": "Resolve comfort, care, or allergy needs.",
    "budget": "Apply price only when catalog prices are usable.",
    "color": "Use as a later preference unless explicitly requested.",
    "brand": "Ask late because brand is rarely the best first discriminator.",
}

CATEGORY_FIRST_LEAVES = {"Westlake", "Clothing", "Casual", "Sets", "Women", "Men"}

CATEGORY_QUALITY_NOTES = {
    "Westlake": ("noisy_leaf", "The leaf does not describe a stable product type; infer from the full path and title."),
    "Shoes": ("broad_leaf", "The leaf is valid but too broad; identify footwear purpose before details."),
    "Clothing": ("broad_leaf", "The leaf is valid but too broad; identify garment type before details."),
    "Casual": ("ambiguous_leaf", "The same leaf appears under dresses, pants, skirts, and shorts; retain its parent path."),
    "Sets": ("ambiguous_leaf", "The same leaf appears under sleepwear, swimwear, activewear, and underwear; retain its parent path."),
    "Women": ("broad_leaf", "Audience is not a product type; infer the requested item before attributes."),
    "Men": ("broad_leaf", "Audience is not a product type; infer the requested item before attributes."),
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


def _category_family(category: str) -> str:
    lowered = category.lower()
    keyword_groups = (
        ("watch", ("watch",)),
        ("eyewear", ("sunglass", "eyeglass")),
        ("bag", ("bag", "wallet", "tote", "purse")),
        ("costume", ("costume", "cosplay")),
        ("innerwear", ("sock", "bra", "underwear", "lingerie", "sleep", "robe")),
        ("jewelry", ("necklace", "earring", "dangle", "stud", "ring", "pendant", "hoop", "bracelet")),
        ("footwear", ("shoe", "sneaker", "flat", "loafer", "slip-on", "pump", "sandal", "wedge", "slipper", "running", "walking", "boot", "oxford", "clog", "flip-flop", "slide")),
    )
    for family, keywords in keyword_groups:
        if any(keyword in lowered for keyword in keywords):
            return family
    return "apparel"


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
    category_paths: dict[str, Counter[tuple[str, ...]]] = defaultdict(Counter)
    missing_category_count = 0
    leaf_equals_store: Counter[str] = Counter()

    with catalog_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            product = json.loads(line)
            product_count += 1
            categories = [str(item).strip() for item in product.get("categories", []) if str(item).strip()]
            leaf = categories[-1] if categories else "Uncategorized"
            leaf_counts[leaf] += 1
            category_paths[leaf][tuple(categories[:-1])] += 1
            if not categories:
                missing_category_count += 1

            store = str(product.get("store") or "").strip()
            if store:
                stores[store] += 1
                category_presence[leaf]["brand"] += 1
                category_values[leaf]["brand"][store] += 1
                if leaf.casefold() == store.casefold():
                    leaf_equals_store[leaf] += 1

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
        candidates_by_attribute = {item["ask_attribute"]: item for item in candidates}
        family = _category_family(category)
        question_order = []
        ordered_attributes = QUESTION_ORDERS[family]
        if category in CATEGORY_FIRST_LEAVES:
            ordered_attributes = ("category",) + ordered_attributes
        for attribute in ordered_attributes[:4]:
            item = dict(candidates_by_attribute[attribute])
            item["reason"] = QUESTION_EXPLANATIONS[attribute]
            question_order.append(item)
        playbook[category] = {
            "product_count": count,
            "category_family": family,
            "question_order": question_order,
            # Backward-compatible key for current consumers and tests.
            "high_value_questions": question_order[:3],
            "no_preference_fallback": "Skip this attribute and ask the next unasked attribute; after the listed order is exhausted, do not ask again.",
        }

    quality_issues = []
    for category, (issue_type, note) in CATEGORY_QUALITY_NOTES.items():
        count = leaf_counts[category]
        if count:
            quality_issues.append({
                "category": category,
                "product_count": count,
                "issue_type": issue_type,
                "distinct_parent_paths": len(category_paths[category]),
                "handling": note,
            })
    for category, count in leaf_equals_store.most_common():
        quality_issues.append({
            "category": category,
            "product_count": count,
            "issue_type": "brand_like_leaf",
            "distinct_parent_paths": len(category_paths[category]),
            "handling": "The leaf equals the store name; do not use it as a reliable product-type hard filter.",
        })

    return {
        "version": "v2",
        "schema_version": "1.1",
        "updated_at": date.today().isoformat(),
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
            "classification_audit": {
                "missing_category_count": missing_category_count,
                "quality_issues": quality_issues,
            },
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
    source_path = str(payload.get("source", {}).get("path") or "the configured catalog")
    lines = [
        "# Category Question Playbook v2",
        "",
        f"This file is generated from `{source_path}` by `artifacts/build_lexicon.py`.",
        "It does not use public ground truth. The machine-readable source of truth is",
        "`artifacts/lexicon.json`.",
        "",
        "## Usage contract for member 2",
        "",
        "1. Follow the question order for the category family, but skip attributes already in `asked`, `neutral`, or current slots.",
        "2. Ask at most one natural question per turn, only when the live candidates contain at least two meaningful values for that attribute.",
        "3. If the user says no preference, record that attribute as neutral and move to the next unasked attribute. Never repeat it.",
        "4. Stop asking and return `ask_attribute = null` after the listed order is exhausted or when no question can narrow candidates.",
        "5. A later explicit preference replaces the earlier value. Invalidated values must never re-enter current-state retrieval.",
        "6. Use the full category path. Do not hard-filter on a noisy, broad, ambiguous, or brand-like leaf label alone.",
        "",
        "## Catalog summary",
        "",
        f"- Products scanned: {payload['source']['product_count']}",
        f"- Products with usable prices: {payload['catalog_summary']['priced_product_count']} ({payload['catalog_summary']['priced_coverage']:.2%})",
        "- Coverage is catalog-derived and is a safety signal, not the conversation order.",
        "",
        "## Classification audit",
        "",
        f"- Products with no category path: {payload['catalog_summary']['classification_audit']['missing_category_count']}",
        "- The following leaf labels need fallback handling:",
        "",
        "| Leaf label | Products | Issue | Parent paths | Required handling |",
        "| --- | ---: | --- | ---: | --- |",
    ]
    for issue in payload["catalog_summary"]["classification_audit"]["quality_issues"]:
        lines.append(
            f"| {issue['category']} | {issue['product_count']} | {issue['issue_type']} | "
            f"{issue['distinct_parent_paths']} | {issue['handling']} |"
        )
    lines.extend([
        "",
        "## Question order table",
        "",
        "The percentages show how often the vocabulary found usable catalog evidence. Size coverage is conservative because numeric sizes are parsed separately by member 2.",
        "",
        "| Category | Products | Ask 1 | Ask 2 | Ask 3 | Ask 4 |",
        "| --- | ---: | --- | --- | --- | --- |",
    ])
    for category, item in payload["category_playbook"].items():
        questions = [
            f"`{question['ask_attribute']}`: {question['question']} ({question['coverage']:.1%})"
            for question in item["question_order"]
        ]
        lines.append(f"| {category} | {item['product_count']} | " + " | ".join(questions) + " |")
    lines.extend([
        "",
        "## No-preference flow",
        "",
        "For every row: record the current attribute as `neutral`, move to the next column, and never ask the neutral attribute again. If all four are answered, neutral, already asked, or unable to narrow live candidates, use `ask_attribute = null`.",
        "",
        "## Evidence boundary",
        "",
        f"All counts, vocabulary, aliases, category families, and classification findings come from participant-visible fields in `{source_path}`. Public ground truth, target ASINs, and session-specific answer rules were not used.",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/lexicon.json"))
    parser.add_argument("--playbook-output", type=Path, default=Path("artifacts/category_playbook.md"))
    parser.add_argument("--top-categories", type=int, default=60)
    args = parser.parse_args()
    payload = build(args.catalog, args.top_categories)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.playbook_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.playbook_output.write_text(render_playbook(payload) + "\n", encoding="utf-8")
    print(f"wrote {args.output} and {args.playbook_output} from {payload['source']['product_count']} products")


if __name__ == "__main__":
    main()
