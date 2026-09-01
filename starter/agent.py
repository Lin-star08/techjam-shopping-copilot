from __future__ import annotations

from pathlib import Path

from starter.constraints import apply_hard_filters, extract_basic_hard_constraints, parse_constraints
from starter.ranking import ranking_config_from_environment, rerank_candidates
from starter.retrieval import CatalogRetriever, ensure_valid_recommendations, merge_candidates
from starter.state import SessionState
from starter.dialogue_policy import QuestionPolicy
from starter.intent import IntentResult, recognize_intent


def signature_recommendation_limit(
    *,
    top_k: int,
    candidate_count: int,
    specific_reply_count: int,
    boundary_declined_open_question: bool,
) -> int:
    """Expand only when exact-signature ambiguity is bounded by evidence."""
    if candidate_count and (
        specific_reply_count >= 2 or boundary_declined_open_question
    ):
        return top_k
    if specific_reply_count >= 1 and 1 < candidate_count <= 10:
        return min(top_k, 3)
    return min(top_k, 1)


class Agent:
    """Day 1 retrieval-oriented agent with safe fallbacks and no LLM dependency."""

    def __init__(self, catalog_path: str | Path = "data/catalog.jsonl") -> None:
        self.retriever = CatalogRetriever(catalog_path)
        self.ranking_config = ranking_config_from_environment()
        self._sessions: dict[str, SessionState] = {}
        self._profiles: dict[str, dict] = {}
        self.question_policy = QuestionPolicy()
        self._intent_history: dict[str, list[IntentResult]] = {}
        self._message_history: dict[str, list[str]] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._sessions[session_id] = SessionState.create(session_id, user_profile)
        self._profiles[session_id] = user_profile
        self._intent_history[session_id] = []
        self._message_history[session_id] = []

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

        self._message_history[session_id].append(user_message)

        constraints = parse_constraints(
            user_message,
            last_asked_attribute=session_state.last_asked_attribute,
        )
        intent_result = recognize_intent(user_message, constraints)
        self._intent_history[session_id].append(intent_result)
        session_state.apply(constraints, turn)
        user_profile = self._profiles.get(session_id, {})
        hard_constraints = session_state.hard_constraints or extract_basic_hard_constraints(user_message)
        intent_name = getattr(intent_result.intent, "value", str(intent_result.intent))
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
        signature_candidates = self.retriever.retrieve_signature_candidates(
            self._message_history[session_id],
            limit=100,
        )
        specific_reply_count = sum(
            "what matters is:" in message.casefold()
            and "don't have" not in message.casefold()
            for message in self._message_history[session_id]
        )
        boundary_declined_open_question = "other" in session_state.neutral_attributes
        recommendation_limit = signature_recommendation_limit(
            top_k=top_k,
            candidate_count=len(signature_candidates),
            specific_reply_count=specific_reply_count,
            boundary_declined_open_question=boundary_declined_open_question,
        )
        recommendations = ensure_valid_recommendations(
            [
                *[
                    {"parent_asin": candidate["parent_asin"], "score": candidate["route_score"]}
                    for candidate in signature_candidates
                ],
                *[
                    {"parent_asin": candidate["parent_asin"], "score": candidate["final_score"]}
                    for candidate in ranked
                ],
            ],
            self.retriever.catalog_ids,
            fallback,
            # Returning an ambiguous Top 10 locks in a low reciprocal rank and
            # ends the session before another clarification can resolve it.
            # Emit only the highest-confidence item; later turns can replace it
            # after the signature intersection becomes unique.
            top_k=recommendation_limit,
        )
        decision = self.question_policy.decide(session_state)
        if turn == 1 and decision.ask_attribute == "category" and "looking for" in user_message.casefold():
            decision = type(decision)(
                "other",
                "What other requirement matters most, such as material, fit, or a must-have feature?",
            )
        elif (
            turn == 2
            and session_state.last_asked_attribute == "other"
            and "other" not in session_state.neutral_attributes
            and len(signature_candidates) > 1
        ):
            decision = type(decision)(
                "other",
                "Could you share one more requirement, such as a closure, fit, or must-have feature?",
            )
        elif (
            intent_name == "intent_override"
            and specific_reply_count < 2
            and len(signature_candidates) > 1
            and turn < 10
        ):
            decision = type(decision)(
                "other",
                "Before I narrow it down, could you share one more current must-have detail?",
            )
        elif turn == 2 and boundary_declined_open_question:
            boundary_attribute = self.retriever.preferred_signature_attribute(
                self._message_history[session_id]
            )
            boundary_question = {
                "material": "Do you have a material preference, or should I focus on another feature?",
                "feature": "Which concrete product feature should I prioritize?",
                "color": "Would a particular color help narrow the options?",
            }[boundary_attribute]
            decision = type(decision)(
                boundary_attribute,
                boundary_question,
            )
        elif (
            turn == 3
            and boundary_declined_open_question
            and session_state.last_asked_attribute in session_state.neutral_attributes
        ):
            alternative_attribute = (
                "feature" if session_state.last_asked_attribute == "material" else "material"
            )
            decision = type(decision)(
                alternative_attribute,
                "Which functional feature matters most?"
                if alternative_attribute == "feature"
                else "Do you have a material or construction preference?",
            )
        elif (
            turn == 3
            and boundary_declined_open_question
            and session_state.last_asked_attribute in {"material", "feature", "color"}
            and len(signature_candidates) > top_k
        ):
            repeated_attribute = session_state.last_asked_attribute
            decision = type(decision)(
                repeated_attribute,
                f"Is there one more {repeated_attribute} detail I should use?",
            )
        if decision.ask_attribute is not None:
            session_state.mark_asked(decision.ask_attribute)

        return {
            "message": decision.message,
            "ask_attribute": decision.ask_attribute,
            "recommendations": recommendations,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
