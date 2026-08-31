"""Build the product lexicon from participant-visible catalog fields only.

This script deliberately does not read ``data/public_set.jsonl``.  Its output is
catalog-derived knowledge, not a lookup table fitted to public ground truth.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import importlib.util
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

CATEGORY_FIRST_LEAVES = {"Westlake", "Clothing", "Women", "Men"}

CATEGORY_QUALITY_NOTES = {
    "Westlake": ("noisy_leaf", "The leaf does not describe a stable product type; infer from the full path and title."),
    "Shoes": ("broad_leaf", "The leaf is valid but too broad; identify footwear purpose before details."),
    "Clothing": ("broad_leaf", "The leaf is valid but too broad; identify garment type before details."),
    "Casual": ("ambiguous_leaf", "The same leaf appears under dresses, pants, skirts, and shorts; retain its parent path."),
    "Sets": ("ambiguous_leaf", "The same leaf appears under sleepwear, swimwear, activewear, and underwear; retain its parent path."),
    "Women": ("broad_leaf", "Audience is not a product type; infer the requested item before attributes."),
    "Men": ("broad_leaf", "Audience is not a product type; infer the requested item before attributes."),
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RETRIEVAL_SOURCE = REPOSITORY_ROOT / "starter" / "retrieval.py"
EVIDENCE_AUDIT_FIELDS = ("title", "categories", "features", "details", "description", "store")
EVIDENCE_BROAD_COVERAGE_THRESHOLD = 0.01
EVIDENCE_BROAD_MAX_TOP_LEAF_SHARE = 0.35

# These rules are deliberately conservative. They describe how downstream
# modules may derive a soft product type without rewriting the frozen catalog.
# A noisy leaf is never sufficient evidence for a hard category filter.
UNRELIABLE_CATEGORY_POLICIES = {
    "Westlake": {
        "semantic_role": "noise",
        "action": "ignore_leaf_then_infer_unique_title_type_or_ask",
        "hard_filter_allowed_from_leaf": False,
    },
    "Clothing": {
        "semantic_role": "broad_container",
        "action": "ignore_leaf_then_infer_unique_title_type_or_ask",
        "hard_filter_allowed_from_leaf": False,
    },
    "Women": {
        "semantic_role": "audience",
        "action": "move_leaf_to_audience_then_infer_unique_title_type_or_ask",
        "hard_filter_allowed_from_leaf": False,
    },
    "Men": {
        "semantic_role": "audience",
        "action": "move_leaf_to_audience_then_infer_unique_title_type_or_ask",
        "hard_filter_allowed_from_leaf": False,
    },
    "Casual": {
        "semantic_role": "style",
        "action": "use_parent_as_product_type_and_leaf_as_style",
        "hard_filter_allowed_from_leaf": False,
    },
    "Sets": {
        "semantic_role": "bundle_form",
        "action": "combine_nearest_informative_parent_with_sets",
        "hard_filter_allowed_from_leaf": False,
    },
}

CASUAL_PARENT_TYPES = {
    "Dresses": "Dresses",
    "Pants": "Pants",
    "Skirts": "Skirts",
    "Shorts": "Shorts",
}

SETS_CONTEXT_TYPES = {
    "Sleep & Lounge": "Sleepwear Sets",
    "Bikinis": "Bikini Sets",
    "Tankinis": "Tankini Sets",
    "Active": "Activewear Sets",
    "Thermal Underwear": "Thermal Underwear Sets",
    "Jiu-Jitsu": "Jiu-Jitsu Sets",
    "Cold Weather": "Cold Weather Sets",
    "Cycling": "Cycling Sets",
    "Karate": "Karate Sets",
    "Kung Fu": "Kung Fu Sets",
    "Taekwondo": "Taekwondo Sets",
}

# Product nouns are catalog-visible language. Multiple matches are treated as
# ambiguous rather than choosing whichever happens to occur first.
TITLE_PRODUCT_TYPE_PATTERNS = {
    "T-Shirts": r"\b(?:t[ -]?shirts?|tees?)\b",
    "Socks": r"\bsocks?\b",
    "Dresses": r"\bdress(?:es)?\b",
    "Pants": r"\b(?:pants?|trousers?|joggers?|sweatpants?)\b",
    "Shorts": r"\bshorts?\b",
    "Skirts": r"\bskirts?\b",
    "Tops": r"\b(?:tops?|blouses?|shirts?|tunics?)\b",
    "Hoodies": r"\b(?:hoodies?|sweatshirts?)\b",
    "Shoes": r"\b(?:shoes?|sneakers?|boots?|sandals?|slippers?|loafers?)\b",
    "Underwear": r"\b(?:underwear|bras?|panties|briefs?|undershirts?)\b",
    "Swimwear": r"\b(?:swimsuits?|bikinis?|tankinis?)\b",
    "Jewelry": r"\b(?:earrings?|necklaces?|bracelets?|rings?)\b",
    "Bags": r"\b(?:bags?|purses?|backpacks?|wallets?|totes?)\b",
    "Accessories": r"\b(?:hats?|caps?|scarves?|belts?|gloves?)\b",
}
TITLE_PRODUCT_TYPE_REGEX = {
    product_type: re.compile(pattern, re.I)
    for product_type, pattern in TITLE_PRODUCT_TYPE_PATTERNS.items()
}


def _load_retrieval_module():
    """Load the evaluated retrieval constants without copying or drifting them."""
    spec = importlib.util.spec_from_file_location("techjam_retrieval_contract", RETRIEVAL_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load retrieval contract from {RETRIEVAL_SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _configured_evidence_contract(retrieval) -> tuple[dict[str, set[str]], set[str], dict[str, str]]:
    category_aliases = {
        **dict(retrieval.CATEGORY_ALIASES),
        **dict(retrieval.CATEGORY_PHRASES),
    }
    requirement_feature_terms = {
        "wash", "hand", "pull", "closure", "band",
    }
    role_terms = {
        "category": set(retrieval.CATEGORY_EVIDENCE_TERMS),
        "color": set(retrieval.COLOR_TERMS),
        "material": set(retrieval.MATERIAL_TERMS),
        "use_case": set(retrieval.USE_CASE_TERMS),
        "feature": requirement_feature_terms,
    }
    configured_terms = set().union(*role_terms.values(), set(retrieval.UNCERTAIN_ROUTE_TERMS))
    return role_terms, configured_terms, category_aliases


def _route_attribute(retrieval, route: str, term: str) -> str:
    classified = retrieval._classify_matched_attributes(route, [term])
    return next(iter(classified), "feature")


def _short_catalog_example(value: object, limit: int = 120) -> str:
    text = " ".join(_text(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _quality_flags(
    term: str,
    configured_roles: list[str],
    product_matches: int,
    field_counts: Counter[str],
    leaf_counts: Counter[str],
    total_products: int,
) -> tuple[list[str], list[str]]:
    flags: list[str] = []
    reasons: list[str] = []
    non_store_matches = sum(field_counts[field] for field in EVIDENCE_AUDIT_FIELDS if field != "store")
    coverage = product_matches / total_products if total_products else 0.0
    top_leaf_share = max(leaf_counts.values(), default=0) / product_matches if product_matches else 0.0

    if product_matches == 0:
        flags.append("noise")
        reasons.append("not found in any searchable catalog field")
    elif non_store_matches == 0:
        flags.append("noise")
        reasons.append("matched only the store field, not product evidence")
    if len(configured_roles) > 1 or term in {"casual", "sets", "set"}:
        flags.append("ambiguous")
        reasons.append("has multiple semantic roles or requires category context")
    if (
        product_matches
        and coverage >= EVIDENCE_BROAD_COVERAGE_THRESHOLD
        and top_leaf_share <= EVIDENCE_BROAD_MAX_TOP_LEAF_SHARE
    ):
        flags.append("broad")
        reasons.append("matches at least 1% of products and is spread across leaf categories")
    if not flags:
        flags.append("accurate")
        reasons.append("single configured role with traceable catalog-field evidence")
    return flags, reasons


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


def _title_product_types(title: str) -> list[str]:
    return [
        product_type
        for product_type, pattern in TITLE_PRODUCT_TYPE_REGEX.items()
        if pattern.search(title)
    ]


def _derived_category_resolution(categories: list[str], title: str) -> dict | None:
    if not categories:
        return None
    leaf = categories[-1]
    policy = UNRELIABLE_CATEGORY_POLICIES.get(leaf)
    if policy is None:
        return None

    base = {
        "source_leaf": leaf,
        "semantic_role": policy["semantic_role"],
        "action": policy["action"],
        "hard_filter_allowed": False,
    }
    if leaf == "Casual":
        parent = categories[-2] if len(categories) > 1 else ""
        product_type = CASUAL_PARENT_TYPES.get(parent)
        if product_type:
            return {
                **base,
                "status": "resolved_from_parent",
                "confidence": "high",
                "product_type": product_type,
                "style": "casual",
            }
    elif leaf == "Sets":
        for context in reversed(categories[:-1]):
            product_type = SETS_CONTEXT_TYPES.get(context)
            if product_type:
                return {
                    **base,
                    "status": "resolved_from_parent",
                    "confidence": "high",
                    "product_type": product_type,
                }
    else:
        matches = _title_product_types(title)
        if len(matches) == 1:
            resolved = {
                **base,
                "status": "resolved_from_title",
                "confidence": "medium",
                "product_type": matches[0],
            }
            if leaf in {"Women", "Men"}:
                resolved["audience"] = leaf
            return resolved
        return {
            **base,
            "status": "ambiguous_title" if matches else "unresolved",
            "confidence": "low",
            "candidate_product_types": matches,
            "next_action": "ask_category",
            **({"audience": leaf} if leaf in {"Women", "Men"} else {}),
        }

    return {
        **base,
        "status": "unresolved",
        "confidence": "low",
        "candidate_product_types": [],
        "next_action": "ask_category",
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
    retrieval = _load_retrieval_module()
    evidence_role_terms, configured_evidence_terms, retrieval_category_aliases = _configured_evidence_contract(retrieval)
    evidence_roles_by_term: dict[str, list[str]] = {
        term: sorted(role for role, role_terms in evidence_role_terms.items() if term in role_terms)
        for term in configured_evidence_terms
    }
    variant_to_evidence_terms: dict[str, set[str]] = defaultdict(set)
    for term in configured_evidence_terms:
        for variant in retrieval._term_variants(term):
            variant_to_evidence_terms[variant].add(term)

    alias_keys: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for alias in retrieval_category_aliases:
        key = tuple(retrieval._phrase_terms(alias))
        if key:
            alias_keys[key].add(alias)
    alias_lengths = sorted({len(key) for key in alias_keys})

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
    category_resolution_status: dict[str, Counter[str]] = defaultdict(Counter)
    category_resolution_types: dict[str, Counter[str]] = defaultdict(Counter)
    evidence_field_counts: dict[str, Counter[str]] = defaultdict(Counter)
    evidence_product_counts: Counter[str] = Counter()
    evidence_leaf_counts: dict[str, Counter[str]] = defaultdict(Counter)
    evidence_examples: dict[str, list[dict[str, str]]] = defaultdict(list)
    alias_field_counts: dict[str, Counter[str]] = defaultdict(Counter)
    alias_product_counts: Counter[str] = Counter()
    alias_leaf_counts: dict[str, Counter[str]] = defaultdict(Counter)

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
            resolution = _derived_category_resolution(categories, str(product.get("title") or ""))
            if resolution:
                category_resolution_status[leaf][str(resolution["status"])] += 1
                product_type = resolution.get("product_type")
                if product_type:
                    category_resolution_types[leaf][str(product_type)] += 1

            product_evidence_terms: set[str] = set()
            product_aliases: set[str] = set()
            for field in EVIDENCE_AUDIT_FIELDS:
                field_value = product.get(field)
                field_terms = set(retrieval.terms(_text(field_value)))
                matched_field_terms: set[str] = set()
                for field_term in field_terms:
                    matched_field_terms.update(variant_to_evidence_terms.get(field_term, set()))
                for term in matched_field_terms:
                    evidence_field_counts[term][field] += 1
                    product_evidence_terms.add(term)
                    if len(evidence_examples[term]) < 2:
                        example = {"field": field, "text": _short_catalog_example(field_value)}
                        if example not in evidence_examples[term]:
                            evidence_examples[term].append(example)

                if field not in {"title", "categories"}:
                    continue
                phrase_terms = retrieval._phrase_terms(_text(field_value))
                matched_aliases: set[str] = set()
                for length in alias_lengths:
                    if length > len(phrase_terms):
                        continue
                    for start in range(len(phrase_terms) - length + 1):
                        matched_aliases.update(alias_keys.get(tuple(phrase_terms[start:start + length]), set()))
                for alias in matched_aliases:
                    alias_field_counts[alias][field] += 1
                    product_aliases.add(alias)

            for term in product_evidence_terms:
                evidence_product_counts[term] += 1
                evidence_leaf_counts[term][leaf] += 1
            for alias in product_aliases:
                alias_product_counts[alias] += 1
                alias_leaf_counts[alias][leaf] += 1

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
            issue = {
                "category": category,
                "product_count": count,
                "issue_type": issue_type,
                "distinct_parent_paths": len(category_paths[category]),
                "handling": note,
            }
            if category in UNRELIABLE_CATEGORY_POLICIES:
                statuses = category_resolution_status[category]
                auto_resolved_count = statuses["resolved_from_parent"] + statuses["resolved_from_title"]
                issue["auto_resolved_count"] = auto_resolved_count
                issue["needs_clarification_count"] = count - auto_resolved_count
            quality_issues.append(issue)
    for category, count in leaf_equals_store.most_common():
        quality_issues.append({
            "category": category,
            "product_count": count,
            "issue_type": "brand_like_leaf",
            "distinct_parent_paths": len(category_paths[category]),
            "handling": "The leaf equals the store name; do not use it as a reliable product-type hard filter.",
        })

    evidence_term_stats = []
    evidence_quality_summary: Counter[str] = Counter({
        "accurate": 0,
        "broad": 0,
        "ambiguous": 0,
        "noise": 0,
    })
    for term in sorted(configured_evidence_terms):
        configured_roles = evidence_roles_by_term[term]
        product_matches = evidence_product_counts[term]
        field_counts = evidence_field_counts[term]
        matched_leaf_counts = evidence_leaf_counts[term]
        flags, reasons = _quality_flags(
            term,
            configured_roles,
            product_matches,
            field_counts,
            matched_leaf_counts,
            product_count,
        )
        root_category_saturation = (
            "category" in configured_roles
            and field_counts["categories"] == product_count
            and product_count > 0
        )
        if root_category_saturation:
            reasons.append("category field matches all products because the generic root path contains this term")
        evidence_quality_summary.update(flags)
        if root_category_saturation:
            treatment = "exclude_generic_root_path_from_evidence"
        elif "noise" in flags:
            treatment = "block_until_catalog_evidence_exists"
        elif "ambiguous" in flags:
            treatment = "route_dependent_soft_evidence"
        elif "broad" in flags:
            treatment = "cap_or_downweight"
        else:
            treatment = "keep_but_hard_filter_only_when_explicit"
        item = {
            "term": term,
            "configured_roles": configured_roles or ["feature_fallback"],
            "effective_attribute_by_route": {
                "default_routes": _route_attribute(retrieval, "current_message", term),
                "category_routes": _route_attribute(retrieval, "category", term),
                "brand_route": _route_attribute(retrieval, "field_brand", term),
            },
            "soft_signal": term in retrieval.UNCERTAIN_ROUTE_TERMS,
            "root_category_saturation": root_category_saturation,
            "matched_product_count": product_matches,
            "catalog_coverage": round(product_matches / product_count, 6) if product_count else 0.0,
            "field_product_counts": {
                field: field_counts[field]
                for field in EVIDENCE_AUDIT_FIELDS
            },
            "field_product_hit_count": sum(field_counts.values()),
            "top_leaf_categories": [
                {"category": matched_leaf, "product_count": count}
                for matched_leaf, count in matched_leaf_counts.most_common(5)
            ],
            "quality_flags": flags,
            "quality_reasons": reasons,
            "recommended_treatment": treatment,
        }
        if flags != ["accurate"]:
            item["catalog_examples"] = evidence_examples[term]
        evidence_term_stats.append(item)

    term_stats_by_name = {item["term"]: item for item in evidence_term_stats}
    alias_audit = []
    alias_status_summary: dict[str, list[str]] = defaultdict(list)
    for alias, canonical in sorted(retrieval_category_aliases.items()):
        alias_terms = retrieval._phrase_terms(alias)
        canonical_terms = retrieval._phrase_terms(canonical)
        collision_terms = sorted({
            term
            for term in [*alias_terms, *canonical_terms]
            if len(evidence_roles_by_term.get(term, [])) > 1
        })
        broad_terms = sorted({
            term
            for term in canonical_terms
            if "broad" in term_stats_by_name.get(term, {}).get("quality_flags", [])
        })
        if canonical in {"sets"} or alias in {"set", "sets"}:
            status = "requires_parent_context"
        elif collision_terms:
            status = "route_dependent"
        elif broad_terms:
            status = "broad_soft_alias"
        elif alias_product_counts[alias] == 0:
            status = "catalog_unverified_alias"
        else:
            status = "kept_as_soft_alias"
        alias_status_summary[status].append(alias)
        alias_audit.append({
            "alias": alias,
            "canonical": canonical,
            "status": status,
            "hard_filter_allowed": False,
            "catalog_product_count": alias_product_counts[alias],
            "field_product_counts": {
                field: alias_field_counts[alias][field]
                for field in ("title", "categories")
            },
            "collision_terms": collision_terms,
            "broad_terms": broad_terms,
            "top_leaf_categories": [
                {"category": matched_leaf, "product_count": count}
                for matched_leaf, count in alias_leaf_counts[alias].most_common(5)
            ],
        })

    category_aliases_for_consumers = {
        item["alias"]: item["canonical"]
        for item in alias_audit
        if item["status"] == "kept_as_soft_alias"
    }
    vocabulary_payload = {
        attribute: {
            "values": [value for value, _ in counts.most_common(100)],
            "aliases": ALIASES.get(attribute, {}),
        }
        for attribute, counts in global_values.items()
    }
    vocabulary_payload["category"] = {
        "values": list(dict.fromkeys([
            *[name for name, _ in leaf_counts.most_common(100)],
            *retrieval_category_aliases.values(),
        ])),
        "aliases": retrieval_category_aliases,
        "safe_soft_aliases": category_aliases_for_consumers,
        "hard_filter_allowed_from_alias_alone": False,
    }

    retrieval_source_bytes = RETRIEVAL_SOURCE.read_bytes()
    retrieval_source_text = retrieval_source_bytes.decode("utf-8")

    return {
        "version": "v3",
        "schema_version": "1.3",
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
        "vocabulary": vocabulary_payload,
        "evidence_audit": {
            "source": {
                "retrieval_path": RETRIEVAL_SOURCE.relative_to(REPOSITORY_ROOT).as_posix(),
                "retrieval_sha256": hashlib.sha256(retrieval_source_bytes).hexdigest(),
                "catalog_path": catalog_path.as_posix(),
                "public_ground_truth_used": False,
                "runtime_lexicon_reference_found": "lexicon" in retrieval_source_text.lower(),
            },
            "definitions": {
                "frequency": "field-product matches; one product may contribute once per matching field",
                "coverage": "unique matched products divided by all catalog products",
                "accurate": "one configured role with traceable catalog-field evidence",
                "broad": "coverage >= 1% and top leaf share <= 35%; use as capped or downweighted soft evidence",
                "ambiguous": "multiple configured roles or a context-dependent category term",
                "noise": "no catalog evidence or store-only evidence",
            },
            "classification_priority_in_retrieval": ["color", "material", "brand_route", "category", "use_case", "feature_fallback"],
            "route_groups": {
                "default_routes": ["current_message", "current_state", "title", "relaxed", "browsing_profile", "attribute_profile", "field_requirement"],
                "category_routes": ["category", "field_category", "popular_category", "same_category_popular"],
                "brand_route": ["field_brand"],
            },
            "known_classifier_gaps": {
                "attributes_without_dedicated_term_sets": ["size", "style"],
                "current_fallback": "Unrecognized matched terms are labeled feature.",
                "consumer_action": "Member 3 should use lexicon attribute metadata instead of defaulting size/style terms to feature.",
            },
            "quality_summary": dict(sorted(evidence_quality_summary.items())),
            "term_stats": evidence_term_stats,
            "category_alias_audit": {
                "source_alias_count": len(retrieval_category_aliases),
                "status_summary": {
                    status: aliases
                    for status, aliases in sorted(alias_status_summary.items())
                },
                "entries": alias_audit,
            },
        },
        "category_normalization": {
            "principles": {
                "preserve_original_catalog": True,
                "derived_categories_are_soft_evidence": True,
                "unreliable_leaf_hard_filter_allowed": False,
                "ambiguous_or_unresolved_action": "ask_category",
            },
            "unreliable_leaves": {
                category: {
                    **policy,
                    "product_count": leaf_counts[category],
                    "resolution_status": dict(category_resolution_status[category]),
                    "derived_product_types": [
                        {"product_type": product_type, "product_count": count}
                        for product_type, count in category_resolution_types[category].most_common()
                    ],
                }
                for category, policy in UNRELIABLE_CATEGORY_POLICIES.items()
            },
            "parent_context_rules": {
                "Casual": [
                    {"parent": parent, "product_type": product_type, "style": "casual"}
                    for parent, product_type in CASUAL_PARENT_TYPES.items()
                ],
                "Sets": [
                    {"context": context, "product_type": product_type}
                    for context, product_type in SETS_CONTEXT_TYPES.items()
                ],
            },
            "title_inference": {
                "applies_to": ["Westlake", "Clothing", "Women", "Men"],
                "confidence": "medium_only_when_exactly_one_product_type_matches",
                "multiple_or_zero_matches": "ask_category",
                "patterns": TITLE_PRODUCT_TYPE_PATTERNS,
            },
        },
        "category_playbook": playbook,
    }


def render_playbook(payload: dict) -> str:
    lines = [
        "# Category Question Playbook v3",
        "",
        "This file is generated from `data/catalog.jsonl` by `artifacts/build_lexicon.py`.",
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
        "| Leaf label | Products | Issue | Parent paths | Auto-resolved | Ask category | Required handling |",
        "| --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for issue in payload["catalog_summary"]["classification_audit"]["quality_issues"]:
        auto_resolved = issue.get("auto_resolved_count", "N/A")
        needs_clarification = issue.get("needs_clarification_count", "N/A")
        lines.append(
            f"| {issue['category']} | {issue['product_count']} | {issue['issue_type']} | "
            f"{issue['distinct_parent_paths']} | {auto_resolved} | "
            f"{needs_clarification} | {issue['handling']} |"
        )
    lines.extend([
        "",
        "## Normalization rules for unreliable leaves",
        "",
        "- `Casual`: use the parent (`Dresses`, `Pants`, `Skirts`, or `Shorts`) as `product_type`; keep `casual` as `style`.",
        "- `Sets`: combine the nearest informative parent with `Sets`, such as `Sleepwear Sets`, `Bikini Sets`, or `Activewear Sets`.",
        "- `Women` / `Men`: move the leaf to `audience`; it is never a product type.",
        "- `Westlake` / `Clothing`: ignore the leaf as a product type. A unique title noun may be soft evidence; multiple or zero matches require a category question.",
        "- Never hard-filter from an unreliable leaf or a title-derived category. Preserve the original catalog path for audit.",
        "",
        "## Retrieval evidence audit",
        "",
        f"- Retrieval source: `{payload['evidence_audit']['source']['retrieval_path']}` (`sha256: {payload['evidence_audit']['source']['retrieval_sha256']}`).",
        f"- Runtime currently references this lexicon: `{str(payload['evidence_audit']['source']['runtime_lexicon_reference_found']).lower()}`. Member 3 must explicitly consume the metadata for it to affect retrieval.",
        "- `frequency` counts field-product matches; `coverage` counts unique matched products. They are not relevance labels.",
        "- Broad, ambiguous, and noisy terms are soft/downweighted/block candidates; no audit flag alone authorizes a hard filter.",
        "- Quality flag counts: " + ", ".join(
            f"{quality}={count}"
            for quality, count in payload["evidence_audit"]["quality_summary"].items()
        ),
        "",
        "| Risk term | Configured role(s) | Default attribute | Products | Coverage | Matching fields | Flag(s) | Treatment |",
        "| --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ])
    risky_terms = sorted(
        (
            item for item in payload["evidence_audit"]["term_stats"]
            if item["quality_flags"] != ["accurate"]
        ),
        key=lambda item: (-item["matched_product_count"], item["term"]),
    )[:30]
    for item in risky_terms:
        matching_fields = ", ".join(
            f"{field}:{count}"
            for field, count in item["field_product_counts"].items()
            if count
        ) or "none"
        lines.append(
            f"| `{item['term']}` | {', '.join(item['configured_roles'])} | "
            f"{item['effective_attribute_by_route']['default_routes']} | "
            f"{item['matched_product_count']} | {item['catalog_coverage']:.2%} | "
            f"{matching_fields} | {', '.join(item['quality_flags'])} | {item['recommended_treatment']} |"
        )
    alias_status = payload["evidence_audit"]["category_alias_audit"]["status_summary"]
    lines.extend([
        "",
        "### Category alias actions",
        "",
        f"- Kept as soft aliases: {len(alias_status.get('kept_as_soft_alias', []))}.",
        f"- Require parent context: {', '.join(f'`{value}`' for value in alias_status.get('requires_parent_context', [])) or 'none'}.",
        f"- Route-dependent because of attribute collisions: {', '.join(f'`{value}`' for value in alias_status.get('route_dependent', [])) or 'none'}.",
        f"- Not observed verbatim in catalog title/category fields: {len(alias_status.get('catalog_unverified_alias', []))}; keep only as soft query rewrites until validated.",
        "",
        "## Question order table",
        "",
        "Each cell shows `coverage` and `info`. Coverage is how many products expose the attribute; info is the weighted normalized-entropy score (0-1) estimating how much the answer can split candidates. High coverage does not automatically mean high information value. Size coverage is conservative because numeric sizes are parsed separately by member 2.",
        "",
        "| Category | Products | Ask 1 | Ask 2 | Ask 3 | Ask 4 |",
        "| --- | ---: | --- | --- | --- | --- |",
    ])
    for category, item in payload["category_playbook"].items():
        questions = [
            f"`{question['ask_attribute']}`: {question['question']} (coverage {question['coverage']:.1%}; info {question['information_value']:.3f})"
            for question in item["question_order"]
        ]
        lines.append(f"| {category} | {item['product_count']} | " + " | ".join(questions) + " |")
    lines.extend([
        "",
        "## No-preference flow",
        "",
        "For every row: record the current attribute as `neutral`, move to the next column, and never ask the neutral attribute again. If all four are answered, neutral, already asked, or unable to narrow live candidates, use `ask_attribute = null`.",
        "",
        "## Team handoff",
        "",
        "- Member 2: consume `category_playbook[*].question_order`; skip asked/neutral/current slots and use the normalization `next_action` as the fallback reason.",
        "- Member 3: consume `evidence_audit.term_stats`, `safe_soft_aliases`, and unreliable-leaf policies. Do not label size/style terms as feature by default and do not hard-filter from aliases alone.",
        "- Member 4: treat `accurate` explicit matches as candidates for stronger evidence; cap/downweight `broad`, keep `ambiguous` route-dependent, and block `noise` until catalog evidence exists.",
        "- Member 5: rebuild with `python artifacts/build_lexicon.py`, run `python -m unittest discover -s tests -p test_lexicon.py -v`, and compare coverage/quality counts before accepting a change.",
        "",
        "## Evidence boundary",
        "",
        "All counts, vocabulary, aliases, category families, and classification findings come from participant-visible fields in `data/catalog.jsonl`. Public ground truth, target ASINs, and session-specific answer rules were not used.",
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
