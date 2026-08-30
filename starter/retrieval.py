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
}
SEARCH_FIELDS = ("title", "categories", "features", "details", "store", "description")
GENERIC_TERMS = {
    "exploring", "browse", "browsing", "options", "option", "recommend",
    "recommendation", "suggest", "specific", "attribute", "preference",
    "preferences", "judgment", "decide", "don", "dont", "have", "any",
    "fine", "additional", "no", "use", "your",
}
POPULAR_CATEGORY_SEEDS = (
    "shoes", "t-shirts", "dresses", "fashion sneakers", "flats",
    "jewelry", "necklaces", "accessories", "belts", "watches",
    "bras", "totes", "tunics", "mules clogs", "pants",
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
        return session_state
    to_dict = getattr(session_state, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
        return value if isinstance(value, dict) else {}
    result: dict[str, object] = {}
    for key in (
        "current_slots",
        "hard_constraints",
        "soft_preferences",
        "asked_attributes",
        "neutral_attributes",
        "invalidated_slots",
        "profile_signals",
    ):
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


def _contains_phrase(text: str, phrase: str) -> re.Match[str] | None:
    escaped = re.escape(phrase.lower()).replace(r"\ ", r"[\s-]+")
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower())


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


def _candidate(parent_asin: str, route: str, rank: int, score: float, matched_terms: list[str]) -> dict:
    return {
        "parent_asin": parent_asin,
        "route": route,
        "route_rank": rank,
        "route_score": float(score),
        "matched_terms": matched_terms,
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
        self._build_index()

    def _build_index(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            "CREATE VIRTUAL TABLE products USING fts5("
            "parent_asin UNINDEXED, title, categories, features, details, store, description, "
            "tokenize='unicode61 remove_diacritics 2')"
        )
        batch: list[tuple[str, str, str, str, str, str, str]] = []
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
                for category in product.get("categories") or []:
                    for part in str(category).split(","):
                        normalized = _normalize_category_part(part)
                        if normalized:
                            category_counter[normalized] += 1
                            self.category_asins.setdefault(normalized, []).append(parent_asin)
                    for query in category_queries_from_text(str(category)):
                        category_counter[query] += 2
                        self.category_asins.setdefault(query, []).append(parent_asin)
                batch.append(
                    (
                        parent_asin,
                        text_for_index(product.get("title")),
                        text_for_index(product.get("categories")),
                        text_for_index(product.get("features")),
                        text_for_index(product.get("details")),
                        text_for_index(product.get("store")),
                        text_for_index(product.get("description")),
                    )
                )
                if len(batch) >= 1000:
                    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
                    batch.clear()
        if batch:
            cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
        self.connection.commit()
        self.popular_category_terms = self._catalog_popular_terms(category_counter)

    def _category_index_candidates(self, queries: Iterable[str], route: str, limit: int) -> list[dict]:
        candidates: list[dict] = []
        seen: set[str] = set()
        matched_terms = list(dict.fromkeys(term for query in queries for term in terms(query)))
        for query in queries:
            for parent_asin in self.category_asins.get(query, []):
                if parent_asin in seen:
                    continue
                seen.add(parent_asin)
                candidates.append(
                    _candidate(
                        parent_asin,
                        route,
                        len(candidates) + 1,
                        0.0,
                        matched_terms,
                    )
                )
                if len(candidates) >= limit:
                    return candidates
        return candidates

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
            if len(ordered) >= 30:
                break
        return ordered

    def _search(self, query: str, route: str, limit: int = 50) -> list[dict]:
        unique_terms = list(dict.fromkeys(terms(query)))[:40]
        expression = " OR ".join(f'"{term}"' for term in unique_terms)
        if not expression:
            return []
        cache_key = (" ".join(unique_terms), route, limit)
        if cache_key in self._search_cache:
            return [dict(candidate) for candidate in self._search_cache[cache_key]]
        rows = self.connection.execute(
            "SELECT parent_asin, bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0) AS score "
            "FROM products WHERE products MATCH ? ORDER BY score LIMIT ?",
            (expression, limit),
        ).fetchall()
        candidates = [
            _candidate(str(parent_asin), route, rank, float(score), unique_terms)
            for rank, (parent_asin, score) in enumerate(rows, start=1)
        ]
        self._search_cache[cache_key] = [dict(candidate) for candidate in candidates]
        return candidates

    def retrieve_current_message(self, user_message: str, limit: int = 50) -> list[dict]:
        return self._search(user_message, "current_message", limit)

    def retrieve_current_state(self, session_state: object, limit: int = 50) -> list[dict]:
        state = state_to_dict(session_state)
        if not state:
            return []
        parts = _active_state_parts(state, ("current_slots", "hard_constraints", "soft_preferences"))
        return self._search(" ".join(parts), "current_state", limit)

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
        index_candidates = self._category_index_candidates(category_matches, "category", limit)
        fts_candidates = self._search(category, "category", limit)
        return merge_candidates([index_candidates, fts_candidates], limit)

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
        candidate_lists = [self._search(query, "attribute_profile", limit) for query in queries]
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
        return self._search(query, "browsing_profile", limit)

    def retrieve_popular_category(self, limit: int = 50) -> list[dict]:
        category_terms = self.popular_category_terms[:20] if self.popular_category_terms else list(POPULAR_CATEGORY_SEEDS)
        return self._search(" ".join(category_terms), "popular_category", limit)

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
    for candidates in candidate_lists:
        for candidate in candidates:
            parent_asin = str(candidate.get("parent_asin") or "").strip()
            if not parent_asin:
                continue
            if parent_asin not in merged:
                merged[parent_asin] = dict(candidate)
                merged[parent_asin]["matched_terms"] = list(candidate.get("matched_terms") or [])
                order.append(parent_asin)
            else:
                seen = set(merged[parent_asin].get("matched_terms") or [])
                for term in candidate.get("matched_terms") or []:
                    if term not in seen:
                        merged[parent_asin].setdefault("matched_terms", []).append(term)
                        seen.add(term)
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
