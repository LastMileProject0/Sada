"""Fail-closed website acceptance, not a general semantic entailment engine.

Every character must belong to a reviewed descriptive claim or complete source
quotation with its OWN correct citation. No keywords grant implicit acceptance.
Never rewrites/generates text, invokes a provider, or changes original RAG.
"""
from __future__ import annotations

from dataclasses import replace
import re
from typing import Any, Mapping

from lastmile_ai.ai.policy_explainer import ExplanationResult
from sada_bridge.policy_claims import PASSAGES

_TAG = re.compile(r'\[([A-Za-z0-9_-]+)\]')
_IDENTITY = ('source_id', 'source_title', 'section', 'official_url', 'locator', 'text')
_QUOTES = (('"', '"'), ("'", "'"), ('“', '”'), ('«', '»'))
MAX_ANSWER_CHARS = 8192
MAX_BLOCKS = 8


def _spaces(text: str) -> str:
    # Whitespace only. Do NOT erase negation, punctuation, case, diacritics,
    # zero-width characters, or replace normative terms with synonyms.
    return ' '.join(text.split())


def _review(result: ExplanationResult) -> ExplanationResult:
    return replace(
        result, status='ReviewRequired', answer='', citations=(),
        limitations=(*result.limitations,
                     'Grounding review required: complete claim/citation verification failed '
                     'or the answer is outside the reviewed demonstration scope.'),
    )


def _citation_end(text: str, start: int, pid: str) -> int | None:
    # Permit the usual sentence punctuation before OR after the source tag.
    if start < len(text) and text[start] == '.':
        start += 1
    while start < len(text) and text[start] == ' ':
        start += 1
    match = _TAG.match(text, start)
    if not match or match[1] != pid:
        return None
    end = match.end()
    if end < len(text) and text[end] == '.':
        end += 1
    # No attached qualifiers, extra citations or hidden formatting.
    if end < len(text) and text[end] != ' ':
        return None
    return end


def guard_policy_explanation(
    result: ExplanationResult, retrieval: Mapping[str, Any],
) -> ExplanationResult:
    if result.status != 'Answered':
        return result
    if (not isinstance(result.answer, str) or not result.answer.strip()
            or len(result.answer) > MAX_ANSWER_CHARS
            or retrieval.get('schema_version') != 'policy_retrieval.v1'):
        return _review(result)
    rows = retrieval.get('passages')
    if not isinstance(rows, (list, tuple)):
        return _review(result)
    available: dict[str, Mapping[str, Any]] = {}
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get('passage_id'), str):
            return _review(result)
        pid = row['passage_id']
        if pid in seen:
            return _review(result)
        seen.add(pid)
        approved = PASSAGES.get(pid)
        if (approved and row.get('source_verified') is True
                and all(isinstance(row.get(k), str) and
                        _spaces(row[k]) == _spaces(approved[k]) for k in _IDENTITY)):
            available[pid] = row

    cited = set()
    for citation in result.citations:
        if not isinstance(citation, Mapping):
            return _review(result)
        pid = citation.get('passage_id')
        if not isinstance(pid, str) or pid not in available or pid in cited:
            return _review(result)
        if not all(citation.get(k) == available[pid].get(k)
                   for k in ('source_id', 'section', 'official_url')):
            return _review(result)
        cited.add(pid)
    if not cited:
        return _review(result)

    text = _spaces(result.answer)
    offset, blocks = 0, 0
    used = set()
    while offset < len(text):
        if blocks >= MAX_BLOCKS:
            return _review(result)
        found = None
        for pid in sorted(cited):
            entry = PASSAGES[pid]
            literals = [
                form for claim in entry['claims'].values() for form in claim.values()
            ]
            # Complete original-language excerpts only, not extracted clauses
            # or generated translations. The two reviewed excerpts do not
            # certify a particular alert's compliance.
            literals.extend(left + entry['text'] + right for left, right in _QUOTES)
            for literal in literals:
                literal = _spaces(literal)
                if text.startswith(literal, offset):
                    end = _citation_end(text, offset + len(literal), pid)
                    if end is not None:
                        found = (end, pid)
                        break
            if found:
                break
        if not found:
            return _review(result)
        offset, pid = found
        used.add(pid)
        blocks += 1
        while offset < len(text) and text[offset] == ' ':
            offset += 1
    if used != cited:
        return _review(result)
    # Return the actual original result object. Acceptance data is never output.
    return result
