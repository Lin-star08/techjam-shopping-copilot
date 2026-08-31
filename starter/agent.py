from __future__ import annotations

from pathlib import Path

from starter.constraints import apply_hard_filters, extract_basic_hard_constraints, parse_constraints
from starter.ranking import ranking_config_from_environment, rerank_candidates
from starter.retrieval import CatalogRetriever, ensure_valid_recommendations, merge_candidates
from starter.state import SessionState
from starter.dialogue_policy import QuestionPolicy
from starter.intent import IntentResult, recognize_intent


class Agent:
    """Day 1 retrieval-oriented agent with safe fallbacks and no LLM dependency."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.retriever = CatalogRetriever(catalog_path)
        self.ranking_config = ranking_config_from_environment()
        self._sessions: dict[str, SessionState] = {}
        self._profiles: dict[str, dict] = {}
        self.question_policy = QuestionPolicy()
        self._intent_history: dict[str, list[IntentResult]] = {}
        self._no_new_info_streak: dict[str, int] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._sessions[session_id] = SessionState.create(session_id, user_profile)
        self._profiles[session_id] = user_profile
        self._intent_history[session_id] = []
        self._no_new_info_streak[session_id] = 0

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

        before_active = {
            "current_slots": dict(session_state.current_slots),
            "hard_constraints": dict(session_state.hard_constraints),
            "soft_preferences": {
                key: list(values)
                for key, values in session_state.soft_preferences.items()
            },
        }
        constraints = parse_constraints(
            user_message,
            last_asked_attribute=session_state.last_asked_attribute,
        )
        intent_result = recognize_intent(user_message, constraints)
        self._intent_history[session_id].append(intent_result)
        intent_name = getattr(intent_result.intent, "value", str(intent_result.intent))
        session_state.apply(constraints, turn)
        after_active = {
            "current_slots": session_state.current_slots,
            "hard_constraints": session_state.hard_constraints,
            "soft_preferences": session_state.soft_preferences,
        }
        positive_kinds = {"hard", "soft", "override"}
        has_positive_constraint = any(
            str(constraint.get("kind", "")) in positive_kinds
            for constraint in constraints
        )
        if has_positive_constraint and before_active != after_active:
            self._no_new_info_streak[session_id] = 0
        else:
            self._no_new_info_streak[session_id] = (
                self._no_new_info_streak.get(session_id, 0) + 1
            )
        user_profile = self._profiles.get(session_id, {})
        hard_constraints = session_state.hard_constraints or extract_basic_hard_constraints(user_message)
        fallback_query = "" if intent_name == "boundary" else user_message
        fallback = self.retriever.fallback_candidates(fallback_query, limit=max(50, top_k))
        candidates = self.retriever.retrieve_route_candidates(
            session_state,
            user_profile,
            user_message,
            constraints,
            intent_result,
            fallback_candidates=fallback,
            limit=100,
        )
        unique_candidates = merge_candidates([candidates], limit=100)
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
        ranked = rerank_candidates(
            filtered,
            session_state,
            top_k=top_k,
            config=self.ranking_config,
        )
        recommendations = ensure_valid_recommendations(
            [
                {"parent_asin": candidate["parent_asin"], "score": candidate["final_score"]}
                for candidate in ranked
            ],
            self.retriever.catalog_ids,
            fallback,
            top_k=top_k,
        )
        changed_attributes = {
            str(constraint.get("attribute", ""))
            for constraint in constraints
            if str(constraint.get("kind", "")) in {"neutral", "override"}
        }
        decision = self.question_policy.decide(
            session_state,
            intent=intent_result.intent,
            changed_attributes=changed_attributes,
            no_new_info_streak=self._no_new_info_streak[session_id],
            candidate_products=(
                self.retriever.product_lookup[parent_asin]
                for candidate in filtered_unique
                if (parent_asin := str(candidate.get("parent_asin") or ""))
                in self.retriever.product_lookup
            ),
        )
        if decision.ask_attribute is not None:
            session_state.mark_asked(decision.ask_attribute)

        return {
            "message": decision.message,
            "ask_attribute": decision.ask_attribute,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
