from __future__ import annotations

from pathlib import Path

from starter.constraints import apply_hard_filters, extract_basic_hard_constraints, parse_constraints
from starter.ranking import rerank_candidates
from starter.retrieval import CatalogRetriever, ensure_valid_recommendations, is_generic_message
from starter.state import SessionState


class Agent:
    """Day 1 retrieval-oriented agent with safe fallbacks and no LLM dependency."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.retriever = CatalogRetriever(catalog_path)
        self._sessions: dict[str, SessionState] = {}
        self._profiles: dict[str, dict] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._sessions[session_id] = SessionState.create(session_id, user_profile)
        self._profiles[session_id] = user_profile

    def respond(
        self,
        session_id: str,
        user_message: str,
        turn: int,
        top_k: int,
    ) -> dict:
        session_state = self._sessions.get(session_id)
        if session_state is None:
            raise RuntimeError("reset must be called before respond")

        constraints = parse_constraints(
            user_message,
            last_asked_attribute=session_state.last_asked_attribute,
        )
        session_state.apply(constraints, turn)
        user_profile = self._profiles.get(session_id, {})
        hard_constraints = session_state.hard_constraints or extract_basic_hard_constraints(user_message)
        fallback = self.retriever.fallback_candidates(user_message, limit=max(50, top_k))
        generic_message = is_generic_message(user_message)
        if generic_message:
            route_lists = [
                self.retriever.retrieve_category(session_state, user_message, limit=50),
                self.retriever.retrieve_current_message(user_message, limit=50),
                self.retriever.retrieve_current_state(session_state, limit=50),
                self.retriever.retrieve_attribute_profile(session_state, user_profile, limit=50),
            ]
            route_lists.extend([
                self.retriever.retrieve_browsing_profile(session_state, user_profile, user_message, limit=25),
                self.retriever.retrieve_popular_category(limit=25),
            ])
        else:
            route_lists = [
                self.retriever.retrieve_current_message(user_message, limit=50),
                self.retriever.retrieve_current_state(session_state, limit=50),
                self.retriever.retrieve_category(session_state, user_message, limit=50),
                self.retriever.retrieve_attribute_profile(session_state, user_profile, limit=50),
            ]
        route_lists.append(fallback)
        candidates = [candidate for route_candidates in route_lists for candidate in route_candidates]
        unique_candidates: list[dict] = []
        seen_asins: set[str] = set()
        for candidate in candidates:
            parent_asin = str(candidate.get("parent_asin") or "").strip()
            if not parent_asin or parent_asin in seen_asins:
                continue
            seen_asins.add(parent_asin)
            unique_candidates.append(candidate)
        filtered_unique = apply_hard_filters(
            unique_candidates,
            hard_constraints,
            self.retriever.product_lookup,
            min_results=top_k,
        )
        allowed_asins = {
            str(candidate.get("parent_asin") or "").strip()
            for candidate in filtered_unique
        }
        filtered = [
            candidate
            for candidate in candidates
            if str(candidate.get("parent_asin") or "").strip() in allowed_asins
        ]
        ranked = rerank_candidates(filtered, session_state, top_k=top_k)
        recommendations = ensure_valid_recommendations(
            [
                {"parent_asin": candidate["parent_asin"], "score": candidate["final_score"]}
                for candidate in ranked
            ],
            self.retriever.catalog_ids,
            fallback,
            top_k=top_k,
        )
        return {
            "message": "Here are the closest matches I found.",
            "ask_attribute": None,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
