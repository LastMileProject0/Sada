"""NEW read-only website adapter; original retrieval and AI logic are unchanged."""
from __future__ import annotations
import fcntl
from dataclasses import replace
from pathlib import Path
import re
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from lastmile_ai.ai.maymona_rag_bridge import to_policy_retrieval
from lastmile_ai.ai.policy_explainer import explain_policy
from lastmile_ai.knowledge.retrieval import retrieve_evidence
from sada_bridge.openrouter_provider import MODEL, openrouter_provider
from sada_bridge.policy_grounding import guard_policy_explanation


class PolicyQuestion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=1200)

    @field_validator('question')
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Question cannot be blank')
        return value.strip()


def create_policy_router(lock_directory: Path) -> APIRouter:
    router = APIRouter()

    @router.post('/api/policy/explain')
    def explain(payload: PolicyQuestion, owner: str | None = Header(None, alias='X-SADA-Owner')):
        if owner is None or not re.fullmatch(r'[0-9a-f]{64}', owner):
            raise HTTPException(status_code=404, detail='Resource not found')
        # Non-waiting cross-thread/process admission, independent of simulation.
        # No question, prompt, response, or session identifier is stored.
        lock_directory.mkdir(parents=True, exist_ok=True)
        with (lock_directory / 'policy.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise HTTPException(status_code=503, detail='Policy assistant busy',
                                    headers={'Retry-After': '3'}) from None
            try:
                evidence = retrieve_evidence(payload.question, top_k=4)
                retrieval = to_policy_retrieval(payload.question, evidence)
                result = explain_policy(payload.question, retrieval,
                                        provider=openrouter_provider, model_id=MODEL)
                result = guard_policy_explanation(result, retrieval)
                if result.status == 'ModelUnavailable':
                    # Original core wording refers to Ollama. Adapt only the public
                    # transport limitation, not retrieval/prompt/answer validation.
                    result = replace(result, limitations=(
                        'OpenRouter unavailable: check server credentials, account credits, '
                        'privacy-compatible model availability or retry later.',))
                return {'retrieval': evidence, 'explanation': result.to_dict()}
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    return router
