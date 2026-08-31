from __future__ import annotations

from pathlib import Path

from starter.constraints import apply_hard_filters, extract_basic_hard_constraints, parse_constraints
from starter.retrieval import CatalogRetriever, ensure_valid_recommendations
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
        candidates = self.retriever.retrieve_all_routes(
            session_state,
            user_profile,
            user_message,
            constraints,
            fallback_candidates=fallback,
            limit=100,
        )
        filtered = apply_hard_filters(
            candidates,
            hard_constraints,
            self.retriever.product_lookup,
            min_results=top_k,
        )
        recommendations = ensure_valid_recommendations(
            filtered,
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
