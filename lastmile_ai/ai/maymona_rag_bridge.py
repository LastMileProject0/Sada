"""Read-only bridge from Maymona's verified excerpts to Salma's AI sidecar.

No Agent/simulation modules are imported, called, or modified here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from lastmile_ai.knowledge.retrieval import load_evidence_corpus, retrieve_evidence
from lastmile_ai.ai.policy_explainer import ExplanationResult, explain_policy


def to_policy_retrieval(question: str, result: dict[str, Any], *, corpus_path: str | Path | None = None) -> dict[str, Any]:
    """Adapt retrieved excerpts only when their identities and text match the corpus."""
    if result.get('question') != question:
        raise ValueError('Retrieval question mismatch')
    if result.get('status') not in ('EVIDENCE_FOUND', 'INSUFFICIENT_EVIDENCE'):
        raise ValueError('Unexpected retrieval status')
    raw = result.get('evidence_items')
    if not isinstance(raw, list):
        raise ValueError('evidence_items must be a list')
    if result['status'] == 'INSUFFICIENT_EVIDENCE' and raw:
        raise ValueError('Insufficient status with nonempty evidence')
    if result['status'] == 'EVIDENCE_FOUND' and not raw:
        raise ValueError('Evidence found status without evidence')

    corpus = load_evidence_corpus(corpus_path)
    by_id = {item['evidence_id']: item for item in corpus['items']}
    passages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError('Malformed retrieved evidence')
        pid = item.get('evidence_id')
        original = by_id.get(pid)
        if not original or pid in seen:
            raise ValueError('Unknown or duplicate retrieved evidence ID')
        seen.add(pid)
        for key in ('source_id', 'source_title', 'section', 'official_url', 'text'):
            if item.get(key) != original.get(key):
                raise ValueError(f'Retrieved evidence provenance mismatch: {key}')
        if item.get('pdf_page') != original.get('pdf_page'):
            raise ValueError('Retrieved evidence page mismatch')
        page = original.get('pdf_page')
        locator = (f"PDF page {page}; {original['section']}" if page is not None
                   else f"Official HTML; {original['section']}")
        passages.append({
            'passage_id': pid,
            'source_id': original['source_id'],
            'source_title': original['source_title'],
            'section': original['section'],
            'official_url': original['official_url'],
            'locator': locator,
            'text': original['text'],
            'source_verified': True,  # Matched verbatim to Maymona's audited, curated local corpus.
            'score': item.get('score'),
        })
    return {
        'schema_version': 'policy_retrieval.v1',
        'query': question,
        'method': 'lexical',
        'passages': passages,
        'limitations': [
            *result.get('limitations', []),
            'source_verified means matched to Maymona’s audited local excerpts, not freshly checked against websites.',
        ],
    }


def explain_from_maymona(
    question: str, *, top_k: int = 4,
    provider: Callable[[str, str], str] | None = None,
    model_id: str | None = None,
    corpus_path: str | Path | None = None,
) -> ExplanationResult:
    """Retrieve curated passages, then call the read-only explanation model."""
    source_result = retrieve_evidence(question, top_k=top_k, corpus_path=corpus_path)
    retrieval = to_policy_retrieval(question, source_result, corpus_path=corpus_path)
    return explain_policy(question, retrieval, provider=provider, model_id=model_id)


def main() -> None:
    """Run a live local Ollama smoke test; print an auditable structured response."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('question', help='Policy question in Arabic or English')
    parser.add_argument('--top-k', type=int, default=4)
    args = parser.parse_args()
    result = explain_from_maymona(args.question, top_k=args.top_k)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    if result.status != 'Answered':
        raise SystemExit('Not Answered; review status/limitations. No answer is invented.')


if __name__ == '__main__':
    main()
