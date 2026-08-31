from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
}
CATEGORY_ALIASES = {
    "accessory": "accessories",
    "accessories": "accessories",
    "shoe": "shoes",
    "shoes": "shoes",
    "sneaker": "shoes",
    "sneakers": "shoes",
    "boot": "boots",
    "boots": "boots",
    "dress": "dress",
    "dresses": "dress",
    "shirt": "shirt",
    "shirts": "shirt",
    "jacket": "jacket",
    "jackets": "jacket",
    "bag": "bag",
    "bags": "bag",
    "sock": "socks",
    "socks": "socks",
    "pant": "pants",
    "pants": "pants",
    "jean": "jeans",
    "jeans": "jeans",
    "skirt": "skirt",
    "skirts": "skirt",
    "coat": "coat",
    "coats": "coat",
    "jewelry": "jewelry",
    "jewellery": "jewelry",
    "necklace": "necklaces",
    "necklaces": "necklaces",
    "belt": "belts",
    "belts": "belts",
    "watch": "watches",
    "watches": "watches",
    "bra": "bras",
    "bras": "bras",
    "tote": "totes",
    "totes": "totes",
    "tunic": "tunics",
    "tunics": "tunics",
    "mule": "mules",
    "mules": "mules",
    "clog": "clogs",
    "clogs": "clogs",
    "basketball": "basketball",
    "tee": "tees",
    "tees": "tees",
    "blouse": "blouses",
    "blouses": "blouses",
    "flat": "flats",
    "flats": "flats",
    "sandal": "sandals",
    "sandals": "sandals",
    "short": "shorts",
    "shorts": "shorts",
    "legging": "leggings",
    "leggings": "leggings",
    "brief": "briefs",
    "briefs": "briefs",
    "underwear": "underwear",
    "wallet": "wallets",
    "wallets": "wallets",
    "handbag": "handbags",
    "handbags": "handbags",
    "lingerie": "lingerie",
    "nightgown": "nightgowns",
    "nightgowns": "nightgowns",
    "sleepshirt": "sleepshirts",
    "sleepshirts": "sleepshirts",
    "earring": "earrings",
    "earrings": "earrings",
    "dangle": "drop dangle",
    "romper": "rompers",
    "rompers": "rompers",
    "jumpsuit": "jumpsuits",
    "jumpsuits": "jumpsuits",
    "overall": "overalls",
    "overalls": "overalls",
    "hoodie": "hoodies",
    "hoodies": "hoodies",
    "sweatshirt": "sweatshirts",
    "sweatshirts": "sweatshirts",
    "rain": "rain boots",
    "loafer": "loafers",
    "loafers": "loafers",
    "slide": "slides",
    "slides": "slides",
    "tank": "tanks tops",
    "tanks": "tanks tops",
    "active": "active",
    "athletic": "athletic",
    "hat": "hats",
    "hats": "hats",
    "cap": "caps",
    "caps": "caps",
    "headband": "headbands",
    "headbands": "headbands",
    "jersey": "jerseys",
    "jerseys": "jerseys",
    "bandana": "bandanas",
    "bandanas": "bandanas",
    "soccer": "soccer",
    "parka": "parkas",
    "parkas": "parkas",
    "vest": "vests",
    "vests": "vests",
    "pajama": "pajama pants",
    "pajamas": "pajama pants",
    "set": "sets",
    "sets": "sets",
}
CATEGORY_PHRASES = {
    "t shirt": "t-shirts",
    "t shirts": "t-shirts",
    "tee shirt": "t-shirts",
    "tee shirts": "t-shirts",
    "fashion sneaker": "fashion sneakers",
    "fashion sneakers": "fashion sneakers",
    "wrist watch": "wrist watches",
    "wrist watches": "wrist watches",
    "mules clogs": "mules clogs",
    "mules and clogs": "mules clogs",
    "mid calf": "mid-calf",
    "everyday bra": "everyday bras",
    "everyday bras": "everyday bras",
    "sleep lounge": "sleep lounge",
    "sleep and lounge": "sleep lounge",
    "sleep bottoms": "sleep bottoms",
    "nightgowns sleepshirts": "nightgowns sleepshirts",
    "nightgowns and sleepshirts": "nightgowns sleepshirts",
    "drop dangle": "drop dangle",
    "drop and dangle": "drop dangle",
    "jumpsuits rompers overalls": "jumpsuits rompers overalls",
    "jumpsuits rompers and overalls": "jumpsuits rompers overalls",
    "rompers overalls": "rompers overalls",
    "rompers and overalls": "rompers overalls",
    "fashion hoodies": "fashion hoodies",
    "fashion hoodies sweatshirts": "fashion hoodies sweatshirts",
    "fashion hoodies and sweatshirts": "fashion hoodies sweatshirts",
    "rain boots": "rain boots",
    "loafers slip ons": "loafers slip ons",
    "loafers and slip ons": "loafers slip ons",
    "slip ons": "slip ons",
    "sport sandals": "sport sandals",
    "sport sandals slides": "sport sandals slides",
    "sport sandals and slides": "sport sandals slides",
    "athletic shoes": "athletic shoes",
    "hats caps": "hats caps",
    "hats and caps": "hats caps",
    "tanks tops": "tanks tops",
    "tanks and tops": "tanks tops",
    "tops tees blouses": "tops tees blouses",
    "tops tees and blouses": "tops tees blouses",
    "tees blouses": "tees blouses",
    "tees and blouses": "tees blouses",
    "blouses button down shirts": "blouses button down shirts",
    "blouses and button down shirts": "blouses button down shirts",
    "button down shirts": "button down shirts",
    "button-down shirts": "button down shirts",
    "casual button down shirts": "casual button down shirts",
    "casual button-down shirts": "casual button down shirts",
    "club night out": "club night out",
    "club and night out": "club night out",
    "coats jackets vests": "coats jackets vests",
    "coats jackets and vests": "coats jackets vests",
    "down jackets parkas": "down jackets parkas",
    "down jackets and parkas": "down jackets parkas",
    "pajama pants": "pajama pants",
    "pajama bottoms": "pajama pants",
    "sleep lounge sets": "sleep lounge sets",
    "sleep sets": "sleep sets",
    "cycling jerseys": "cycling jerseys",
    "soccer cleats": "soccer cleats",
}
SEARCH_FIELDS = ("title", "categories", "features", "details", "store", "description")
EVIDENCE_FIELD_SCOPES = {
    "all": SEARCH_FIELDS,
    "title": ("title",),
    "category": ("categories", "title"),
    "category_field": ("categories",),
    "attribute": ("features", "details", "description"),
    "store": ("store",),
}
FIELD_TABLES = {
    "title": "products_title",
    "category": "products_category",
    "attribute": "products_attribute",
    "store": "products_store",
}
STATE_KEYS = (
    "current_slots",
    "hard_constraints",
    "soft_preferences",
    "asked_attributes",
    "neutral_attributes",
    "invalidated_slots",
    "profile_signals",
)
GENERIC_TERMS = {
    "exploring", "browse", "browsing", "options", "option", "recommend",
    "recommendation", "suggest", "specific", "attribute", "preference",
    "preferences", "judgment", "decide", "don", "dont", "have", "any",
    "fine", "additional", "no", "use", "your", "still", "just", "quite",
    "right", "yet", "ask", "about", "key", "requirement", "required",
    "require",
}
POPULAR_CATEGORY_SEEDS = (
    "shoes", "t-shirts", "dresses", "fashion sneakers", "flats",
    "jewelry", "necklaces", "accessories", "belts", "watches",
    "bras", "totes", "tunics", "mules clogs", "pants",
    "lingerie", "sleep lounge", "earrings", "rompers", "jumpsuits",
    "hoodies", "sweatshirts", "rain boots", "loafers", "slides",
    "hats caps", "headbands", "sport sandals", "athletic shoes",
    "jerseys", "bandanas", "soccer", "button down shirts",
    "sleep sets", "club night out", "parkas", "vests", "pajama pants",
)
GENERIC_CATEGORY_PARTS = {
    "clothing", "shoes jewelry", "clothing shoes jewelry", "women", "men",
    "girls", "boys", "baby", "novelty", "shops", "uniforms work safety",
}
NEUTRAL_ATTRIBUTE_TERMS = {
    "feature": {"comfort", "comfortable", "durability", "durable", "lightweight", "breathable"},
    "material": {"material", "cotton", "polyester", "leather", "nylon", "wool", "fabric"},
    "style": {"style", "fit", "casual", "formal", "athletic", "classic"},
    "color": {"color", "black", "white", "blue", "brown", "red", "green", "gray", "grey"},
    "brand": {"brand", "maker", "store"},
    "budget": {"budget", "price"},
}
COLOR_TERMS = {
    "black", "white", "blue", "red", "pink", "green", "brown", "gray",
    "grey", "purple", "yellow", "orange", "navy", "beige", "tan", "silver", "gold",
}
MATERIAL_TERMS = {
    "cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk",
    "rayon", "fabric", "rubber", "mesh", "suede", "denim", "canvas", "lace",
    "alloy", "stainless", "steel", "metal",
}
UNCERTAIN_ROUTE_TERMS = {
    "comfortable", "comfort", "casual", "cute", "premium", "nice", "stylish",
    "good", "best", "quality", "durable", "durability", "waterproof",
    "lightweight", "breathable", "soft", "classic", "modern",
}
BUDGET_QUERY_TERMS = {
    "under", "below", "less", "than", "maximum", "max", "budget",
    "around", "price", "dollar", "dollars",
}
ATTRIBUTE_LABEL_TERMS = {
    "category", "color", "colour", "material", "brand", "style", "feature",
    "features", "use", "case", "preference", "preferences",
}
USE_CASE_TERMS = {
    "walking", "running", "travel", "work", "office", "formal", "wedding",
    "outdoor", "winter", "summer", "athletic", "sport", "sports",
    "basketball", "training", "hiking", "everyday", "casual", "sleep",
    "lounge", "rain", "soccer", "cycling", "club",
}
TERM_VARIANTS = {
    "comfort": {"comfort", "comfortable"},
    "comfortable": {"comfort", "comfortable"},
    "durability": {"durability", "durable"},
    "durable": {"durability", "durable"},
    "breathable": {"breathable", "breathability"},
    "breathability": {"breathable", "breathability"},
    "lightweight": {"lightweight", "light"},
}
REQUIREMENT_MARKERS = (
    re.compile(r"\bkey\s+requirement\s+is\s*:?\s*([^.;]+)", re.IGNORECASE),
    re.compile(r"\bmust\s+have\s+([^.;]+)", re.IGNORECASE),
    re.compile(r"\bneed(?:s|ed)?\s+to\s+have\s+([^.;]+)", re.IGNORECASE),
    re.compile(r"\b(?:hand\s+wash\s+only|pull\s+on\s+closure|stainless\s+steel\s+band)\b", re.IGNORECASE),
)
REQUIREMENT_PHRASES = {
    "hand wash only",
    "pull on closure",
    "stainless steel band",
}
HARD_EVIDENCE_ATTRIBUTES = {"category", "color", "material", "brand"}
EXPLICIT_EVIDENCE_ATTRIBUTES = HARD_EVIDENCE_ATTRIBUTES | {"use_case", "feature"}


def text_for_index(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{key} {item}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def terms(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if len(token) > 1 and token.lower() not in STOPWORDS
    ]


def product_text(product: dict) -> str:
    return " ".join(text_for_index(product.get(field)) for field in SEARCH_FIELDS).strip()


def product_text_for_scope(product: dict, field_scope: str) -> str:
    fields = EVIDENCE_FIELD_SCOPES.get(field_scope, SEARCH_FIELDS)
    return " ".join(text_for_index(product.get(field)) for field in fields).strip()


def _flatten_state_values(value: object) -> list[str]:
    if isinstance(value, dict):
        flattened: list[str] = []
        for key, item in value.items():
            if item in (None, "", [], {}):
                continue
            if isinstance(item, list):
                flattened.extend(str(entry) for entry in item if entry not in (None, ""))
            else:
                flattened.append(f"{key} {item}")
        return flattened
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    return [str(value)] if value not in (None, "") else []


def state_to_dict(session_state: object) -> dict:
    if session_state is None:
        return {}
    if isinstance(session_state, dict):
        return {key: session_state[key] for key in STATE_KEYS if key in session_state}
    to_dict = getattr(session_state, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
        if isinstance(value, dict):
            return {key: value[key] for key in STATE_KEYS if key in value}
        return {}
    result: dict[str, object] = {}
    for key in STATE_KEYS:
        if hasattr(session_state, key):
            result[key] = getattr(session_state, key)
    return result


def _invalidated_values(session_state: dict) -> set[str]:
    values: set[str] = set()
    invalidated = session_state.get("invalidated_slots")
    if not isinstance(invalidated, dict):
        return values
    for item in invalidated.values():
        for value in _flatten_state_values(item):
            values.update(terms(value))
    return values


def _active_state_parts(session_state: dict, keys: Iterable[str]) -> list[str]:
    invalidated = _invalidated_values(session_state)
    neutral = set(str(value) for value in session_state.get("neutral_attributes") or [])
    parts: list[str] = []
    for key in keys:
        source = session_state.get(key)
        if isinstance(source, dict):
            for attribute, value in source.items():
                if str(attribute) in neutral:
                    continue
                active_terms = [term for term in terms(" ".join(_flatten_state_values(value))) if term not in invalidated]
                if active_terms:
                    parts.append(" ".join(active_terms))
        else:
            for value in _flatten_state_values(source):
                active_terms = [term for term in terms(value) if term not in invalidated]
                if active_terms:
                    parts.append(" ".join(active_terms))
    return parts


def _neutral_profile_terms(session_state: dict) -> set[str]:
    blocked: set[str] = set()
    for attribute in session_state.get("neutral_attributes") or []:
        blocked.update(NEUTRAL_ATTRIBUTE_TERMS.get(str(attribute), set()))
    return blocked


def is_generic_message(user_message: str) -> bool:
    content_terms = [term for term in terms(user_message) if term not in GENERIC_TERMS]
    return len(content_terms) <= 2


def _phrase_terms(phrase: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(phrase)
        if token.lower() == "t" or (len(token) > 1 and token.lower() not in STOPWORDS)
    ]


def _contains_phrase(text: str, phrase: str) -> re.Match[str] | None:
    pieces = [re.escape(piece) for piece in _phrase_terms(phrase)]
    if not pieces:
        return None
    separator = r"[^a-z0-9]+(?:(?:and|or|for|of|the|with)[^a-z0-9]+)*"
    expression = separator.join(pieces)
    return re.search(rf"(?<![a-z0-9]){expression}(?![a-z0-9])", text.lower())


def category_queries_from_text(text: str) -> list[str]:
    matches: list[tuple[int, int, str]] = []
    for alias, canonical in {**CATEGORY_ALIASES, **CATEGORY_PHRASES}.items():
        match = _contains_phrase(text, alias)
        if match:
            matches.append((match.start(), -len(match.group(0)), canonical))
    ordered: list[str] = []
    seen: set[str] = set()
    for _, _, canonical in sorted(matches):
        if canonical not in seen:
            ordered.append(canonical)
            seen.add(canonical)
    return ordered


def _normalize_category_part(value: object) -> str:
    normalized = " ".join(terms(str(value)))
    if normalized in GENERIC_CATEGORY_PARTS:
        return ""
    return normalized


CATEGORY_EVIDENCE_TERMS = set(CATEGORY_ALIASES) | set(terms(
    " ".join([*CATEGORY_ALIASES.values(), *CATEGORY_PHRASES.values()])
))


def _state_category(session_state: dict) -> str:
    slots = session_state.get("current_slots")
    if isinstance(slots, dict):
        return str(slots.get("category") or "")
    return ""


def _term_variants(term: str) -> set[str]:
    normalized = term.lower()
    variants = {normalized}
    variants.update(TERM_VARIANTS.get(normalized, set()))
    if normalized.endswith("ies") and len(normalized) > 3:
        variants.add(normalized[:-3] + "y")
    elif normalized.endswith("y") and len(normalized) > 2:
        variants.add(normalized[:-1] + "ies")
    if normalized.endswith("s") and len(normalized) > 3:
        variants.add(normalized[:-1])
    elif len(normalized) > 2:
        variants.add(normalized + "s")
    return variants


def _term_matches_field(term: str, field_terms: set[str]) -> bool:
    return bool(_term_variants(term) & field_terms)


def _evidence_blocked_terms(session_state: object) -> set[str]:
    state = state_to_dict(session_state)
    return (
        _invalidated_values(state)
        | _neutral_profile_terms(state)
        | GENERIC_TERMS
        | BUDGET_QUERY_TERMS
        | ATTRIBUTE_LABEL_TERMS
    )


def _clean_query_terms_for_evidence(query_terms: Iterable[str], session_state: object = None) -> list[str]:
    blocked = _evidence_blocked_terms(session_state)
    clean_terms: list[str] = []
    seen: set[str] = set()
    for term in query_terms:
        normalized = str(term).lower().strip()
        if (
            not normalized
            or normalized in seen
            or normalized in blocked
            or normalized.isdigit()
        ):
            continue
        clean_terms.append(normalized)
        seen.add(normalized)
    return clean_terms


def _classify_matched_attributes(route: str, matched_terms: Iterable[str]) -> dict[str, list[str]]:
    attributes: dict[str, list[str]] = {}
    for term in matched_terms:
        attribute = ""
        if term in COLOR_TERMS:
            attribute = "color"
        elif term in MATERIAL_TERMS:
            attribute = "material"
        elif route == "field_brand":
            attribute = "brand"
        elif term in CATEGORY_EVIDENCE_TERMS or route in {"category", "field_category", "popular_category"}:
            attribute = "category"
        elif term in USE_CASE_TERMS:
            attribute = "use_case"
        else:
            attribute = "feature"
        attributes.setdefault(attribute, [])
        if term not in attributes[attribute]:
            attributes[attribute].append(term)
    return attributes


def evidence_counts(matched_attributes: dict[str, list[str]] | None) -> dict[str, int]:
    attributes = matched_attributes or {}
    explicit_terms = {
        term
        for attribute in EXPLICIT_EVIDENCE_ATTRIBUTES
        for term in attributes.get(attribute, [])
    }
    hard_terms = {
        term
        for attribute in HARD_EVIDENCE_ATTRIBUTES
        for term in attributes.get(attribute, [])
    }
    return {
        "explicit_match_count": len(explicit_terms),
        "hard_match_count": len(hard_terms),
        "matched_attribute_count": sum(1 for values in attributes.values() if values),
    }


def candidate_match_evidence(
    product: dict | None,
    query_terms: Iterable[str],
    route: str,
    field_scope: str = "all",
    session_state: object = None,
) -> dict:
    """Return product-specific match evidence for one retrieval candidate."""
    clean_query_terms = _clean_query_terms_for_evidence(query_terms, session_state)
    if not product:
        return {
            "query_terms": list(dict.fromkeys(str(term).lower() for term in query_terms if str(term))),
            "matched_terms": [],
            "matched_attributes": {},
            "soft_matched_terms": [],
        }

    field_terms = set(terms(product_text_for_scope(product, field_scope)))
    matched_terms = [
        term
        for term in clean_query_terms
        if _term_matches_field(term, field_terms)
    ]
    matched_terms = list(dict.fromkeys(matched_terms))
    return {
        "query_terms": list(dict.fromkeys(str(term).lower() for term in query_terms if str(term))),
        "matched_terms": matched_terms,
        "matched_attributes": _classify_matched_attributes(route, matched_terms),
        "soft_matched_terms": [
            term for term in matched_terms if term in UNCERTAIN_ROUTE_TERMS
        ],
    }


def requirement_terms_from_text(user_message: str) -> list[str]:
    raw_text = str(user_message or "")
    segments: list[str] = []
    for pattern in REQUIREMENT_MARKERS:
        for match in pattern.finditer(raw_text):
            groups = [group for group in match.groups() if group]
            segments.append(groups[0] if groups else match.group(0))
    lowered = raw_text.lower()
    for phrase in REQUIREMENT_PHRASES:
        if _contains_phrase(lowered, phrase):
            segments.append(phrase)

    explicit_terms = [
        term
        for term in terms(raw_text)
        if term in COLOR_TERMS
        or term in MATERIAL_TERMS
        or term in USE_CASE_TERMS
        or term in {"wash", "hand", "pull", "closure", "band"}
    ]
    blocked = GENERIC_TERMS | BUDGET_QUERY_TERMS | ATTRIBUTE_LABEL_TERMS | {"only"}
    ordered: list[str] = []
    for term in [*terms(" ".join(segments)), *explicit_terms]:
        if (
            term in blocked
            or term in CATEGORY_ALIASES
            or term.isdigit()
            or term in ordered
        ):
            continue
        ordered.append(term)
    return ordered


def requirement_terms_from_state(session_state: object) -> list[str]:
    state = state_to_dict(session_state)
    invalidated = _invalidated_values(state)
    blocked = _neutral_profile_terms(state) | invalidated | GENERIC_TERMS | BUDGET_QUERY_TERMS
    result: list[str] = []
    for source_key in ("current_slots", "hard_constraints", "soft_preferences"):
        source = state.get(source_key)
        if not isinstance(source, dict):
            continue
        for attribute, value in source.items():
            if str(attribute) not in {"color", "material", "brand", "use_case", "feature", "style"}:
                continue
            for term in terms(" ".join(_flatten_state_values(value))):
                if term in blocked or term.isdigit() or term in result:
                    continue
                result.append(term)
    return result


def explicit_requirement_terms(session_state: object, user_message: str) -> list[str]:
    return list(dict.fromkeys([
        *requirement_terms_from_text(user_message),
        *requirement_terms_from_state(session_state),
    ]))


def _constraint_terms_from_state(session_state: dict) -> list[str]:
    parts: list[str] = []
    for source_key in ("current_slots", "hard_constraints"):
        source = session_state.get(source_key)
        if not isinstance(source, dict):
            continue
        for attribute, value in source.items():
            if str(attribute) == "budget" or str(attribute) == "budget_max":
                continue
            if value in (None, "", [], {}):
                continue
            if str(attribute) in {"category", "color", "material", "brand", "use_case"}:
                parts.extend(_flatten_state_values(value))
    return parts


def relaxed_query(session_state: object, user_message: str) -> str:
    state = state_to_dict(session_state)
    invalidated = _invalidated_values(state)
    blocked = _neutral_profile_terms(state)
    raw_parts = [user_message, *_constraint_terms_from_state(state)]
    category_terms = category_queries_from_text(" ".join(raw_parts))
    excluded = GENERIC_TERMS | UNCERTAIN_ROUTE_TERMS | invalidated | blocked | BUDGET_QUERY_TERMS
    important_terms: list[str] = []
    for term in terms(" ".join(raw_parts)):
        if term in excluded or term.isdigit():
            continue
        if term in COLOR_TERMS or term in MATERIAL_TERMS or term in CATEGORY_ALIASES:
            important_terms.append(term)
            continue
        important_terms.append(term)
    ordered = list(dict.fromkeys([*category_terms, *important_terms]))
    return " ".join(ordered[:10])


def _has_override_constraint(parsed_constraints: Iterable[dict] | None) -> bool:
    if parsed_constraints is None:
        return False
    return any(
        isinstance(item, dict) and item.get("kind") == "override"
        for item in parsed_constraints
    )


def _intent_name(intent_result: object = None) -> str:
    if intent_result is None:
        return ""
    intent = getattr(intent_result, "intent", intent_result)
    value = getattr(intent, "value", intent)
    return str(value)


def route_limits_for_turn(
    user_message: str,
    session_state: object = None,
    parsed_constraints: Iterable[dict] | None = None,
    intent_result: object = None,
) -> dict[str, int]:
    state = state_to_dict(session_state)
    neutral = bool(state.get("neutral_attributes"))
    intent = _intent_name(intent_result)
    generic = intent == "browsing" or is_generic_message(user_message) or neutral
    if intent == "boundary":
        return {
            "current_state": 70,
            "category": 70,
            "same_category_popular": 45,
            "field_category": 60,
            "category_requirement": 25,
            "field_requirement": 15,
            "relaxed": 45,
            "popular_category": 45,
            "attribute_profile": 20,
            "field_attribute": 15,
            "current_message": 0,
            "title": 0,
            "browsing_profile": 0,
            "field_brand": 0,
        }
    if intent == "intent_override" or _has_override_constraint(parsed_constraints):
        return {
            "current_message": 60,
            "current_state": 60,
            "title": 45,
            "category": 35,
            "category_requirement": 35,
            "field_category": 35,
            "field_requirement": 30,
            "field_attribute": 25,
            "attribute_profile": 15,
            "relaxed": 35,
            "same_category_popular": 0,
            "browsing_profile": 0,
            "popular_category": 0,
            "field_brand": 20,
        }
    if generic:
        return {
            "category": 70,
            "current_message": 25,
            "current_state": 45,
            "title": 25,
            "same_category_popular": 35,
            "field_category": 50,
            "category_requirement": 35,
            "field_requirement": 20,
            "field_attribute": 45,
            "attribute_profile": 35,
            "relaxed": 45,
            "browsing_profile": 25,
            "popular_category": 35,
            "field_brand": 10,
        }
    return {
        "current_message": 50,
        "current_state": 65,
        "title": 45,
        "category": 40,
        "category_requirement": 45,
        "field_category": 35,
        "field_requirement": 35,
        "field_attribute": 35,
        "attribute_profile": 25,
        "relaxed": 30,
        "same_category_popular": 0,
        "browsing_profile": 0,
        "popular_category": 0,
        "field_brand": 20,
    }


def _candidate(
    parent_asin: str,
    route: str,
    rank: int,
    score: float,
    query_terms: list[str] | None = None,
    matched_terms: list[str] | None = None,
    matched_attributes: dict[str, list[str]] | None = None,
    soft_matched_terms: list[str] | None = None,
) -> dict:
    clean_query_terms = list(dict.fromkeys(query_terms or []))
    clean_matched_terms = list(dict.fromkeys(matched_terms or []))
    clean_attributes = {
        str(attribute): list(dict.fromkeys(str(term) for term in values if str(term)))
        for attribute, values in (matched_attributes or {}).items()
        if isinstance(values, (list, tuple, set))
    }
    counts = evidence_counts(clean_attributes)
    return {
        "parent_asin": parent_asin,
        "route": route,
        "route_rank": rank,
        "route_score": float(score),
        "query_terms": clean_query_terms,
        "matched_terms": clean_matched_terms,
        "matched_attributes": clean_attributes,
        "soft_matched_terms": list(dict.fromkeys(soft_matched_terms or [])),
        **counts,
        "routes": [{"route": route, "route_rank": rank, "route_score": float(score)}],
        "route_hits": 1,
        "debug_reason": f"matched via {route}",
    }


class CatalogRetriever:
    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.catalog_path = Path(catalog_path)
        self.connection = sqlite3.connect(":memory:")
        self.product_lookup: dict[str, dict] = {}
        self.catalog_ids: set[str] = set()
        self.fallback_asins: list[str] = []
        self.category_asins: dict[str, list[str]] = {}
        self.popular_category_terms: list[str] = []
        self._search_cache: dict[tuple[str, str, int], list[dict]] = {}
        self._product_terms: dict[str, set[str]] = {}
        self._title_terms: dict[str, set[str]] = {}
        self._build_index()

    def _build_index(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        cursor.execute(
            "CREATE VIRTUAL TABLE products_title USING fts5("
            "parent_asin UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')"
        )
        cursor.execute(
            "CREATE VIRTUAL TABLE products_category USING fts5("
            "parent_asin UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')"
        )
        cursor.execute(
            "CREATE VIRTUAL TABLE products_attribute USING fts5("
            "parent_asin UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')"
        )
        cursor.execute(
            "CREATE VIRTUAL TABLE products_store USING fts5("
            "parent_asin UNINDEXED, text, tokenize='unicode61 remove_diacritics 2')"
        )
        batch: list[tuple[str, str, str, str, str, str, str]] = []
        title_batch: list[tuple[str, str]] = []
        category_batch: list[tuple[str, str]] = []
        attribute_batch: list[tuple[str, str]] = []
        store_batch: list[tuple[str, str]] = []
        category_counter: Counter[str] = Counter()
        with self.catalog_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                product = json.loads(line)
                parent_asin = str(product["parent_asin"])
                self.product_lookup[parent_asin] = product
                self.catalog_ids.add(parent_asin)
                self.fallback_asins.append(parent_asin)
                title_text = text_for_index(product.get("title"))
                category_text = text_for_index(product.get("categories"))
                attribute_text = " ".join(
                    text_for_index(product.get(field))
                    for field in ("features", "details", "description")
                )
                store_text = text_for_index(product.get("store"))
                self._title_terms[parent_asin] = set(terms(title_text))
                self._product_terms[parent_asin] = set(terms(
                    " ".join((title_text, category_text, attribute_text, store_text))
                ))
                for category in product.get("categories") or []:
                    category_text = str(category)
                    normalized_category = _normalize_category_part(category_text)
                    for part in category_text.split(","):
                        normalized = _normalize_category_part(part)
                        if normalized:
                            category_counter[normalized] += 1
                            self.category_asins.setdefault(normalized, []).append(parent_asin)
                    if not normalized_category or normalized_category in GENERIC_CATEGORY_PARTS:
                        continue
                    for query in category_queries_from_text(category_text):
                        category_counter[query] += 2
                        self.category_asins.setdefault(query, []).append(parent_asin)
                batch.append(
                    (
                        parent_asin,
                        title_text,
                        category_text,
                        text_for_index(product.get("features")),
                        text_for_index(product.get("details")),
                        store_text,
                        text_for_index(product.get("description")),
                    )
                )
                title_batch.append((parent_asin, title_text))
                category_batch.append((parent_asin, category_text))
                attribute_batch.append((parent_asin, attribute_text))
                store_batch.append((parent_asin, store_text))
                if len(batch) >= 1000:
                    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                    cursor.executemany("INSERT INTO products_title VALUES (?, ?)", title_batch)
                    cursor.executemany("INSERT INTO products_category VALUES (?, ?)", category_batch)
                    cursor.executemany("INSERT INTO products_attribute VALUES (?, ?)", attribute_batch)
                    cursor.executemany("INSERT INTO products_store VALUES (?, ?)", store_batch)
                    batch.clear()
                    title_batch.clear()
                    category_batch.clear()
                    attribute_batch.clear()
                    store_batch.clear()
        if batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
            cursor.executemany("INSERT INTO products_title VALUES (?, ?)", title_batch)
            cursor.executemany("INSERT INTO products_category VALUES (?, ?)", category_batch)
            cursor.executemany("INSERT INTO products_attribute VALUES (?, ?)", attribute_batch)
            cursor.executemany("INSERT INTO products_store VALUES (?, ?)", store_batch)
        self.connection.commit()
        self.popular_category_terms = self._catalog_popular_terms(category_counter)

    def _category_context_score(self, parent_asin: str, context_terms: set[str], category_terms: set[str]) -> float:
        title_terms = self._title_terms.get(parent_asin, set())
        full_terms = self._product_terms.get(parent_asin, set())
        category_overlap = len(category_terms & full_terms)
        context_overlap = len(context_terms & full_terms)
        title_overlap = len(context_terms & title_terms)
        return float(category_overlap * 3 + context_overlap * 3 + title_overlap)

    def _candidate_for_product(
        self,
        parent_asin: str,
        route: str,
        rank: int,
        score: float,
        query_terms: list[str],
        field_scope: str = "all",
        session_state: object = None,
    ) -> dict:
        evidence = candidate_match_evidence(
            self.product_lookup.get(parent_asin),
            query_terms,
            route,
            field_scope,
            session_state,
        )
        return _candidate(
            parent_asin,
            route,
            rank,
            score,
            evidence["query_terms"],
            evidence["matched_terms"],
            evidence["matched_attributes"],
            evidence["soft_matched_terms"],
        )

    def _category_index_candidates(
        self,
        queries: Iterable[str],
        route: str,
        limit: int,
        context: str = "",
        session_state: object = None,
        extra_query_terms: Iterable[str] = (),
    ) -> list[dict]:
        query_list = [query for query in dict.fromkeys(queries) if query]
        seen: set[str] = set()
        category_query_terms = list(dict.fromkeys(term for query in query_list for term in terms(query)))
        extra_terms = list(dict.fromkeys(str(term).lower() for term in extra_query_terms if str(term)))
        query_terms = list(dict.fromkeys([*category_query_terms, *extra_terms]))
        category_terms = set(category_query_terms)
        context_terms = {
            term
            for term in terms(context)
            if term not in GENERIC_TERMS
            and term not in UNCERTAIN_ROUTE_TERMS
            and term not in BUDGET_QUERY_TERMS
            and not term.isdigit()
        }
        ranked: list[tuple[float, int, str]] = []
        order = 0
        scan_limit_per_query = max(limit * 8, limit)
        for query in query_list:
            scanned = 0
            for parent_asin in self.category_asins.get(query, []):
                if parent_asin in seen:
                    continue
                seen.add(parent_asin)
                score = self._category_context_score(parent_asin, context_terms, category_terms)
                ranked.append((score, order, parent_asin))
                order += 1
                scanned += 1
                if scanned >= scan_limit_per_query:
                    break
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [
            self._candidate_for_product(
                parent_asin,
                route,
                rank,
                score,
                query_terms,
                "category",
                session_state,
            )
            for rank, (score, _, parent_asin) in enumerate(ranked[:limit], start=1)
        ]

    def _catalog_popular_terms(self, category_counter: Counter[str]) -> list[str]:
        terms_by_count = [
            term
            for term, _ in category_counter.most_common()
            if term and term not in GENERIC_CATEGORY_PARTS
        ]
        ordered: list[str] = []
        seen: set[str] = set()
        for term in [*POPULAR_CATEGORY_SEEDS, *terms_by_count]:
            if term in seen:
                continue
            ordered.append(term)
            seen.add(term)
            if len(ordered) >= 60:
                break
        return ordered

    def _search(
        self,
        query: str,
        route: str,
        limit: int = 50,
        *,
        field_scope: str = "all",
        session_state: object = None,
    ) -> list[dict]:
        unique_terms = list(dict.fromkeys(terms(query)))[:40]
        expression = " OR ".join(f'"{term}"' for term in unique_terms)
        if not expression:
            return []
        evidence_block_key = " ".join(sorted(_evidence_blocked_terms(session_state)))
        cache_key = (" ".join(unique_terms), route, field_scope, evidence_block_key, limit)
        if cache_key in self._search_cache:
            return [dict(candidate) for candidate in self._search_cache[cache_key]]
        rows = self.connection.execute(
            "SELECT parent_asin, bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0) AS score "
            "FROM products WHERE products MATCH ? ORDER BY score LIMIT ?",
            (expression, limit),
        ).fetchall()
        candidates = [
            self._candidate_for_product(
                str(parent_asin),
                route,
                rank,
                float(score),
                unique_terms,
                field_scope,
                session_state,
            )
            for rank, (parent_asin, score) in enumerate(rows, start=1)
        ]
        self._search_cache[cache_key] = [dict(candidate) for candidate in candidates]
        return candidates

    def _search_field(
        self,
        field: str,
        query: str,
        route: str,
        limit: int = 50,
        *,
        session_state: object = None,
    ) -> list[dict]:
        table = FIELD_TABLES[field]
        unique_terms = list(dict.fromkeys(terms(query)))[:30]
        expression = " OR ".join(f'"{term}"' for term in unique_terms)
        if not expression:
            return []
        field_scope = "category_field" if field == "category" else field
        evidence_block_key = " ".join(sorted(_evidence_blocked_terms(session_state)))
        cache_key = (f"{field}:{' '.join(unique_terms)}", route, field_scope, evidence_block_key, limit)
        if cache_key in self._search_cache:
            return [dict(candidate) for candidate in self._search_cache[cache_key]]
        rows = self.connection.execute(
            f"SELECT parent_asin, bm25({table}, 0.0, 1.0) AS score "
            f"FROM {table} WHERE {table} MATCH ? ORDER BY score LIMIT ?",
            (expression, limit),
        ).fetchall()
        candidates = [
            self._candidate_for_product(
                str(parent_asin),
                route,
                rank,
                float(score),
                unique_terms,
                field_scope,
                session_state,
            )
            for rank, (parent_asin, score) in enumerate(rows, start=1)
        ]
        self._search_cache[cache_key] = [dict(candidate) for candidate in candidates]
        return candidates

    def retrieve_current_message(
        self,
        user_message: str,
        limit: int = 50,
        session_state: object = None,
    ) -> list[dict]:
        return self._search(user_message, "current_message", limit, session_state=session_state)

    def retrieve_title(
        self,
        user_message: str,
        limit: int = 50,
        session_state: object = None,
    ) -> list[dict]:
        return self._search_field("title", user_message, "title", limit, session_state=session_state)

    def retrieve_category_field(
        self,
        session_state: object,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        state = state_to_dict(session_state)
        category = _state_category(state)
        category_matches = category_queries_from_text(category or user_message)
        query = " ".join(category_matches[:4]) if category_matches else category or user_message
        return self._search_field("category", query, "field_category", limit, session_state=state)

    def retrieve_attribute_fields(
        self,
        session_state: object,
        user_profile: dict | None,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        state = state_to_dict(session_state)
        parts = [user_message]
        if state:
            parts.extend(_active_state_parts(state, ("soft_preferences", "profile_signals")))
        if isinstance(user_profile, dict):
            parts.extend(_flatten_state_values(user_profile.get("preference_tags")))
        blocked_terms = _neutral_profile_terms(state) if state else set()
        query_terms = [
            term for term in terms(" ".join(parts))
            if term not in GENERIC_TERMS and term not in blocked_terms
        ]
        return self._search_field(
            "attribute",
            " ".join(query_terms[:10]),
            "field_attribute",
            limit,
            session_state=state,
        )

    def retrieve_brand(self, session_state: object, user_message: str, limit: int = 50) -> list[dict]:
        state = state_to_dict(session_state)
        parts: list[str] = []
        for source_key in ("current_slots", "hard_constraints"):
            source = state.get(source_key)
            if isinstance(source, dict) and source.get("brand"):
                parts.extend(_flatten_state_values(source.get("brand")))
        if "brand" in terms(user_message):
            parts.append(user_message)
        if not parts:
            return []
        return self._search_field("store", " ".join(parts), "field_brand", limit, session_state=state)

    def retrieve_current_state(self, session_state: object, limit: int = 50) -> list[dict]:
        state = state_to_dict(session_state)
        if not state:
            return []
        parts = _active_state_parts(state, ("current_slots", "hard_constraints", "soft_preferences"))
        return self._search(" ".join(parts), "current_state", limit, session_state=state)

    def retrieve_category(
        self,
        session_state: object,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        category = ""
        state = state_to_dict(session_state)
        slots = state.get("current_slots")
        if isinstance(slots, dict):
            category = str(slots.get("category") or "")
        if not category:
            category_matches = category_queries_from_text(user_message)
            if category_matches:
                category = " ".join(category_matches[:3])
        category_matches = category_queries_from_text(category)
        if not category_matches and category:
            category_matches = [_normalize_category_part(category)]
        context = " ".join([user_message, category, *_constraint_terms_from_state(state)])
        index_candidates = self._category_index_candidates(
            category_matches,
            "category",
            limit,
            context,
            session_state=state,
        )
        fts_candidates = self._search(
            category,
            "category",
            limit,
            field_scope="category",
            session_state=state,
        )
        return merge_candidates([index_candidates, fts_candidates], limit)

    def _category_matches_for_turn(self, session_state: object, user_message: str) -> list[str]:
        state = state_to_dict(session_state)
        slots = state.get("current_slots")
        state_category = str(slots.get("category") or "") if isinstance(slots, dict) else ""
        matches = [
            *category_queries_from_text(state_category),
            *category_queries_from_text(user_message),
        ]
        if state_category and not matches:
            matches.append(_normalize_category_part(state_category))
        return [match for match in dict.fromkeys(matches) if match]

    def retrieve_category_requirement(
        self,
        session_state: object,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        state = state_to_dict(session_state)
        category_matches = self._category_matches_for_turn(state, user_message)
        requirement_terms = explicit_requirement_terms(state, user_message)
        if not category_matches or not requirement_terms:
            return []
        context = " ".join([
            user_message,
            *category_matches,
            *requirement_terms,
            *_constraint_terms_from_state(state),
        ])
        index_candidates = self._category_index_candidates(
            category_matches,
            "category_requirement",
            limit,
            context,
            session_state=state,
            extra_query_terms=requirement_terms,
        )
        fts_candidates = self._search(
            " ".join([*category_matches[:4], *requirement_terms[:8]]),
            "category_requirement",
            limit,
            session_state=state,
        )
        return merge_candidates([index_candidates, fts_candidates], limit)

    def retrieve_requirement_fields(
        self,
        session_state: object,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        state = state_to_dict(session_state)
        requirement_terms = explicit_requirement_terms(state, user_message)
        if not requirement_terms:
            return []
        return self._search_field(
            "attribute",
            " ".join(requirement_terms[:12]),
            "field_requirement",
            limit,
            session_state=state,
        )

    def retrieve_same_category_popular(
        self,
        session_state: object,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        state = state_to_dict(session_state)
        category_matches = self._category_matches_for_turn(state, user_message)
        if not category_matches:
            return []
        context = " ".join([user_message, *_constraint_terms_from_state(state)])
        return self._category_index_candidates(
            category_matches,
            "same_category_popular",
            limit,
            context,
            session_state=state,
        )

    def retrieve_attribute_profile(
        self,
        session_state: object,
        user_profile: dict | None,
        limit: int = 50,
    ) -> list[dict]:
        parts: list[str] = []
        state = state_to_dict(session_state)
        if state:
            parts.extend(_active_state_parts(state, ("soft_preferences", "profile_signals")))
        if isinstance(user_profile, dict):
            parts.extend(_flatten_state_values(user_profile.get("preference_tags")))
            summary = user_profile.get("summary")
            if summary:
                parts.append(str(summary))
        blocked_terms = _neutral_profile_terms(state) if state else set()
        state_category = ""
        slots = state.get("current_slots") if state else None
        if isinstance(slots, dict):
            state_category = str(slots.get("category") or "")
        profile_terms = [
            term for term in terms(" ".join(parts))
            if term not in GENERIC_TERMS and term not in blocked_terms
        ]
        queries: list[str] = []
        if state_category and profile_terms:
            queries.append(" ".join([state_category, *profile_terms[:6]]))
        if profile_terms:
            queries.append(" ".join(profile_terms[:8]))
        if not queries:
            return []
        candidate_lists = [
            self._search(query, "attribute_profile", limit, field_scope="attribute", session_state=state)
            for query in queries
        ]
        return merge_candidates(candidate_lists, limit)

    def retrieve_browsing_profile(
        self,
        session_state: object,
        user_profile: dict | None,
        user_message: str,
        limit: int = 50,
    ) -> list[dict]:
        if not is_generic_message(user_message):
            return []
        state = state_to_dict(session_state)
        profile_terms: list[str] = []
        if state:
            profile_terms.extend(_active_state_parts(state, ("profile_signals", "soft_preferences")))
        if isinstance(user_profile, dict):
            profile_terms.extend(_flatten_state_values(user_profile.get("preference_tags")))
            summary = user_profile.get("summary")
            if summary:
                profile_terms.append(str(summary))
        blocked_terms = _neutral_profile_terms(state) if state else set()
        clean_terms = list(dict.fromkeys(
            term for term in terms(" ".join(profile_terms))
            if term not in GENERIC_TERMS and term not in blocked_terms
        ))
        if not clean_terms:
            return []
        category_terms = self.popular_category_terms[:3] if self.popular_category_terms else list(POPULAR_CATEGORY_SEEDS[:3])
        query = " ".join([*clean_terms[:6], *category_terms])
        return self._search(query, "browsing_profile", limit, session_state=state)

    def retrieve_popular_category(self, limit: int = 50) -> list[dict]:
        category_terms = self.popular_category_terms[:20] if self.popular_category_terms else list(POPULAR_CATEGORY_SEEDS)
        return self._search(" ".join(category_terms), "popular_category", limit, field_scope="category")

    def retrieve_relaxed(self, session_state: object, user_message: str, limit: int = 50) -> list[dict]:
        query = relaxed_query(session_state, user_message)
        if not query:
            return []
        return self._search(query, "relaxed", limit, session_state=session_state)

    def _route_lists_for_turn(
        self,
        session_state: object,
        user_profile: dict | None,
        user_message: str,
        parsed_constraints: Iterable[dict] | None = None,
        intent_result: object = None,
        *,
        fallback_candidates: Iterable[dict] = (),
    ) -> list[list[dict]]:
        limits = route_limits_for_turn(user_message, session_state, parsed_constraints, intent_result)
        state = state_to_dict(session_state)
        intent = _intent_name(intent_result)
        generic = intent == "browsing" or is_generic_message(user_message) or bool(state.get("neutral_attributes"))
        override = intent == "intent_override" or _has_override_constraint(parsed_constraints)

        def maybe(candidates: list[dict], route_limit: int) -> list[dict]:
            return candidates if route_limit > 0 else []

        if intent == "boundary":
            return [
                maybe(self.retrieve_current_state(session_state, limits["current_state"]), limits["current_state"]),
                maybe(self.retrieve_category(session_state, user_message, limits["category"]), limits["category"]),
                maybe(self.retrieve_same_category_popular(session_state, user_message, limits["same_category_popular"]), limits["same_category_popular"]),
                maybe(self.retrieve_category_field(session_state, user_message, limits["field_category"]), limits["field_category"]),
                maybe(self.retrieve_relaxed(session_state, user_message, limits["relaxed"]), limits["relaxed"]),
                maybe(self.retrieve_attribute_fields(session_state, user_profile, user_message, limits["field_attribute"]), limits["field_attribute"]),
                maybe(self.retrieve_attribute_profile(session_state, user_profile, limits["attribute_profile"]), limits["attribute_profile"]),
                maybe(self.retrieve_category_requirement(session_state, user_message, limits["category_requirement"]), limits["category_requirement"]),
                maybe(self.retrieve_requirement_fields(session_state, user_message, limits["field_requirement"]), limits["field_requirement"]),
                maybe(self.retrieve_popular_category(limits["popular_category"]), limits["popular_category"]),
                list(fallback_candidates),
            ]

        if generic:
            return [
                maybe(self.retrieve_category(session_state, user_message, limits["category"]), limits["category"]),
                maybe(self.retrieve_category_field(session_state, user_message, limits["field_category"]), limits["field_category"]),
                maybe(self.retrieve_same_category_popular(session_state, user_message, limits["same_category_popular"]), limits["same_category_popular"]),
                maybe(self.retrieve_current_state(session_state, limits["current_state"]), limits["current_state"]),
                maybe(self.retrieve_current_message(user_message, limits["current_message"], session_state), limits["current_message"]),
                maybe(self.retrieve_title(user_message, limits["title"], session_state), limits["title"]),
                maybe(self.retrieve_attribute_fields(session_state, user_profile, user_message, limits["field_attribute"]), limits["field_attribute"]),
                maybe(self.retrieve_attribute_profile(session_state, user_profile, limits["attribute_profile"]), limits["attribute_profile"]),
                maybe(self.retrieve_relaxed(session_state, user_message, limits["relaxed"]), limits["relaxed"]),
                maybe(self.retrieve_browsing_profile(session_state, user_profile, user_message, limits["browsing_profile"]), limits["browsing_profile"]),
                maybe(self.retrieve_category_requirement(session_state, user_message, limits["category_requirement"]), limits["category_requirement"]),
                maybe(self.retrieve_requirement_fields(session_state, user_message, limits["field_requirement"]), limits["field_requirement"]),
                maybe(self.retrieve_popular_category(limits["popular_category"]), limits["popular_category"]),
                list(fallback_candidates),
            ]

        if override:
            return [
                maybe(self.retrieve_current_message(user_message, limits["current_message"], session_state), limits["current_message"]),
                maybe(self.retrieve_current_state(session_state, limits["current_state"]), limits["current_state"]),
                maybe(self.retrieve_title(user_message, limits["title"], session_state), limits["title"]),
                maybe(self.retrieve_category(session_state, user_message, limits["category"]), limits["category"]),
                maybe(self.retrieve_category_field(session_state, user_message, limits["field_category"]), limits["field_category"]),
                maybe(self.retrieve_relaxed(session_state, user_message, limits["relaxed"]), limits["relaxed"]),
                maybe(self.retrieve_attribute_fields(session_state, user_profile, user_message, limits["field_attribute"]), limits["field_attribute"]),
                maybe(self.retrieve_brand(session_state, user_message, limits["field_brand"]), limits["field_brand"]),
                maybe(self.retrieve_attribute_profile(session_state, user_profile, limits["attribute_profile"]), limits["attribute_profile"]),
                maybe(self.retrieve_category_requirement(session_state, user_message, limits["category_requirement"]), limits["category_requirement"]),
                maybe(self.retrieve_requirement_fields(session_state, user_message, limits["field_requirement"]), limits["field_requirement"]),
                list(fallback_candidates),
            ]

        return [
            maybe(self.retrieve_current_message(user_message, limits["current_message"], session_state), limits["current_message"]),
            maybe(self.retrieve_current_state(session_state, limits["current_state"]), limits["current_state"]),
            maybe(self.retrieve_title(user_message, limits["title"], session_state), limits["title"]),
            maybe(self.retrieve_category(session_state, user_message, limits["category"]), limits["category"]),
            maybe(self.retrieve_category_field(session_state, user_message, limits["field_category"]), limits["field_category"]),
            maybe(self.retrieve_attribute_fields(session_state, user_profile, user_message, limits["field_attribute"]), limits["field_attribute"]),
            maybe(self.retrieve_attribute_profile(session_state, user_profile, limits["attribute_profile"]), limits["attribute_profile"]),
            maybe(self.retrieve_relaxed(session_state, user_message, limits["relaxed"]), limits["relaxed"]),
            maybe(self.retrieve_brand(session_state, user_message, limits["field_brand"]), limits["field_brand"]),
            maybe(self.retrieve_category_requirement(session_state, user_message, limits["category_requirement"]), limits["category_requirement"]),
            maybe(self.retrieve_requirement_fields(session_state, user_message, limits["field_requirement"]), limits["field_requirement"]),
            list(fallback_candidates),
        ]

    def retrieve_route_candidates(
        self,
        session_state: object,
        user_profile: dict | None,
        user_message: str,
        parsed_constraints: Iterable[dict] | None = None,
        intent_result: object = None,
        *,
        fallback_candidates: Iterable[dict] = (),
        limit: int = 100,
    ) -> list[dict]:
        route_lists = self._route_lists_for_turn(
            session_state,
            user_profile,
            user_message,
            parsed_constraints,
            intent_result,
            fallback_candidates=fallback_candidates,
        )
        merged = merge_candidates(route_lists, limit)
        allowed_asins = {str(candidate.get("parent_asin") or "") for candidate in merged}
        return [
            candidate
            for route_candidates in route_lists
            for candidate in route_candidates
            if str(candidate.get("parent_asin") or "") in allowed_asins
        ]

    def retrieve_all_routes(
        self,
        session_state: object,
        user_profile: dict | None,
        user_message: str,
        parsed_constraints: Iterable[dict] | None = None,
        intent_result: object = None,
        *,
        fallback_candidates: Iterable[dict] = (),
        limit: int = 100,
    ) -> list[dict]:
        route_lists = self._route_lists_for_turn(
            session_state,
            user_profile,
            user_message,
            parsed_constraints,
            intent_result,
            fallback_candidates=fallback_candidates,
        )
        return merge_candidates(route_lists, limit)

    def fallback_candidates(self, query: str, limit: int = 50) -> list[dict]:
        searched = self._search(query, "fallback_bm25", limit)
        if searched:
            return searched
        return [
            _candidate(parent_asin, "fallback_catalog", rank, 0.0, [])
            for rank, parent_asin in enumerate(self.fallback_asins[:limit], start=1)
        ]


def merge_candidates(candidate_lists: Iterable[Iterable[dict]], limit: int = 100) -> list[dict]:
    merged: dict[str, dict] = {}
    order: list[str] = []

    def merge_list_field(target: dict, source: dict, field: str) -> None:
        seen = set(target.get(field) or [])
        for term in source.get(field) or []:
            if term not in seen:
                target.setdefault(field, []).append(term)
                seen.add(term)

    def merge_attribute_field(target: dict, source: dict) -> None:
        source_attributes = source.get("matched_attributes") or {}
        if not isinstance(source_attributes, dict):
            return
        target_attributes = target.setdefault("matched_attributes", {})
        for attribute, values in source_attributes.items():
            if not isinstance(values, (list, tuple, set)):
                continue
            seen = set(target_attributes.get(attribute) or [])
            for term in values:
                if term not in seen:
                    target_attributes.setdefault(attribute, []).append(term)
                    seen.add(term)

    for candidates in candidate_lists:
        for candidate in candidates:
            parent_asin = str(candidate.get("parent_asin") or "").strip()
            if not parent_asin:
                continue
            if parent_asin not in merged:
                merged[parent_asin] = dict(candidate)
                merged[parent_asin]["query_terms"] = list(candidate.get("query_terms") or [])
                merged[parent_asin]["matched_terms"] = list(candidate.get("matched_terms") or [])
                merged[parent_asin]["soft_matched_terms"] = list(candidate.get("soft_matched_terms") or [])
                merged[parent_asin]["matched_attributes"] = {
                    attribute: list(values)
                    for attribute, values in (candidate.get("matched_attributes") or {}).items()
                    if isinstance(values, (list, tuple, set))
                }
                if "routes" not in merged[parent_asin]:
                    merged[parent_asin]["routes"] = [{
                        "route": candidate.get("route"),
                        "route_rank": candidate.get("route_rank"),
                        "route_score": candidate.get("route_score"),
                    }]
                merged[parent_asin]["route_hits"] = len({
                    route.get("route")
                    for route in merged[parent_asin].get("routes", [])
                    if route.get("route")
                })
                order.append(parent_asin)
            else:
                merge_list_field(merged[parent_asin], candidate, "query_terms")
                merge_list_field(merged[parent_asin], candidate, "matched_terms")
                merge_list_field(merged[parent_asin], candidate, "soft_matched_terms")
                merge_attribute_field(merged[parent_asin], candidate)
                merged[parent_asin].update(evidence_counts(merged[parent_asin].get("matched_attributes")))
                seen_routes = {
                    route.get("route")
                    for route in merged[parent_asin].get("routes", [])
                    if route.get("route")
                }
                candidate_routes = candidate.get("routes") or [{
                    "route": candidate.get("route"),
                    "route_rank": candidate.get("route_rank"),
                    "route_score": candidate.get("route_score"),
                }]
                for route in candidate_routes:
                    route_name = route.get("route")
                    if route_name and route_name not in seen_routes:
                        merged[parent_asin].setdefault("routes", []).append(dict(route))
                        seen_routes.add(route_name)
                merged[parent_asin]["route_hits"] = len(seen_routes)
                route_names = [
                    str(route.get("route"))
                    for route in merged[parent_asin].get("routes", [])
                    if route.get("route")
                ]
                merged[parent_asin]["debug_reason"] = "matched via " + " + ".join(
                    route_names
                )
            if len(order) >= limit:
                return [merged[parent_asin] for parent_asin in order]
    return [merged[parent_asin] for parent_asin in order[:limit]]


def ensure_valid_recommendations(
    candidates: Iterable[dict],
    catalog_ids: set[str],
    fallback_candidates: Iterable[dict] = (),
    top_k: int = 10,
) -> list[dict]:
    recommendations: list[dict] = []
    seen: set[str] = set()
    for candidate in [*candidates, *fallback_candidates]:
        parent_asin = str(candidate.get("parent_asin") or "").strip()
        if not parent_asin or parent_asin in seen or parent_asin not in catalog_ids:
            continue
        score = candidate.get("route_score", candidate.get("score", 0.0))
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            numeric_score = 0.0
        recommendations.append({"parent_asin": parent_asin, "score": numeric_score})
        seen.add(parent_asin)
        if len(recommendations) >= top_k:
            break
    return recommendations


def candidate_recall(candidates: Iterable[dict], target_parent_asin: str, cutoffs: Iterable[int] = (50, 100)) -> dict:
    candidate_list = list(candidates)
    target = str(target_parent_asin)
    position = None
    for index, candidate in enumerate(candidate_list, start=1):
        if str(candidate.get("parent_asin") or "") == target:
            position = index
            break
    result: dict[str, object] = {
        "target_parent_asin": target,
        "candidate_count": len(candidate_list),
        "target_position": position,
    }
    for cutoff in cutoffs:
        result[f"recall_at_{cutoff}"] = position is not None and position <= cutoff
    return result
