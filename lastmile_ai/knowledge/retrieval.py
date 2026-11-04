"""Citation-first, deterministic excerpt retrieval for LastMile AI.

Scope: retrieve short verified passages from the five approved official sources.
This is NOT an LLM, a RAG generator, a legal-compliance validator, or a claim
that the entire source documents are indexed. No network or external packages.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

_CORPUS_FILE = Path(__file__).with_name("evidence_chunks.json")

_STOPWORDS = {
    "a", "an", "and", "are", "as", "be", "can", "could", "do", "does",
    "for", "from", "have", "how", "i", "in", "is", "it", "of", "on", "or",
    "our", "the", "their", "there", "these", "this", "to", "under", "us",
    "was", "were", "what", "when", "which", "who", "why", "with", "would",
    "yes", "no", "we", "if", "into", "its", "should", "automatically",
    "2021", "2019", "1", "2", "3", "4", "5", "0",
    "هل", "ما", "هو", "هي", "في", "من", "عن", "على", "الى", "او", "ان",
    "اذا", "كان", "تكون", "يمكن", "عند", "مع", "هذا", "هذه", "بدون", "حسب",
    "كيف", "لماذا", "التي", "الذي", "لنا", "لدينا", "يتم", "لذلك", "صحيح",
}


def _normalize_token(token: str) -> str:
    token = unicodedata.normalize("NFKC", token).lower()
    token = "".join(ch for ch in token if unicodedata.category(ch) != "Mn")
    token = token.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    # Normalize definite article for Arabic stem matching, without stemming English.
    if len(token) > 4 and token.startswith("ال") and re.search(r"[\u0600-\u06ff]", token):
        token = token[2:]
    return token


def _tokens(text: str) -> set[str]:
    raw = re.findall(r"[A-Za-z0-9_]+|[\u0621-\u064A]+", text, flags=re.UNICODE)
    return {term for item in raw if (term := _normalize_token(item)) and len(term) > 1 and term not in _STOPWORDS}


def load_evidence_corpus(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate a local excerpt collection, rejecting unsafe/malformed IDs."""
    data = json.loads(Path(path or _CORPUS_FILE).read_text(encoding="utf-8"))
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Corpus must contain nonempty items")
    ids: set[str] = set()
    source_ids: set[str] = set()
    for item in items:
        required = ("evidence_id", "source_id", "source_title", "official_url", "section", "text")
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in required):
            raise ValueError("Missing or empty evidence fields")
        if item["evidence_id"] in ids:
            raise ValueError("Duplicate evidence ID")
        if not re.fullmatch(r"SRC-0[1-5]-E\d{2}", item["evidence_id"]):
            raise ValueError("Invalid evidence ID")
        if item["source_id"] != item["evidence_id"].split("-E")[0]:
            raise ValueError("Source ID does not match evidence ID")
        if not item["official_url"].startswith("https://"):
            raise ValueError("Expected official HTTPS source URL")
        ids.add(item["evidence_id"])
        source_ids.add(item["source_id"])
    if source_ids != {f"SRC-0{i}" for i in range(1, 6)}:
        raise ValueError("Corpus must reference all five approved sources")
    return data


def retrieve_evidence(question: str, top_k: int = 4, *, corpus_path: str | Path | None = None) -> dict[str, Any]:
    """Return source-text evidence, or an explicit insufficient-evidence status.

    Ranking compares user query words (Arabic/English) against real passage text,
    section, title and bilingual search tags. Tags help discovery only; the returned
    evidence is always the verified source passage, never a fabricated answer.
    """
    if not isinstance(question, str):
        raise TypeError("question must be a string")
    if type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer in 1..20")
    q = _tokens(question)
    corpus = load_evidence_corpus(corpus_path)
    results: list[tuple[float, dict[str, Any]]] = []
    if q:
        docs = []
        for item in corpus["items"]:
            literal = _tokens(item["text"] + " " + item["section"] + " " + item["source_title"])
            tags = _tokens(item.get("search_terms", ""))
            docs.append((item, literal, tags))
        df = Counter(t for _item, lit, tags in docs for t in (lit | tags))
        n = len(docs)
        for item, literal, tags in docs:
            overlap = q & (literal | tags)
            if len(overlap) < 2:
                continue
            # Rare matched words matter more; exact source-text/section matches
            # count more strongly than editorial bilingual search tags.
            score = sum((math.log(1 + (n + 0.5) / (df[t] + 0.5))) * (2 if t in literal else 1) for t in overlap)
            if score < 2.0:
                continue
            results.append((score, item))
    results.sort(key=lambda pair: (-pair[0], pair[1]["evidence_id"]))
    # Keep passages from a source only if at least one passage from that
    # source is close to the best match. This reduces weak matches caused
    # only by generic terms such as "UAE" and "emergency alert".
    if results:
        best_score = results[0][0]
        best_by_source: dict[str, float] = {}
        for score, item in results:
            source_id = item["source_id"]
            best_by_source[source_id] = max(best_by_source.get(source_id, 0.0), score)
        relevant_sources = {
            source_id
            for source_id, score in best_by_source.items()
            if score >= 0.85 * best_score
        }
        results = [
            (score, item)
            for score, item in results
            if item["source_id"] in relevant_sources
        ]
    evidence = [
        {
            "evidence_id": item["evidence_id"],
            "source_id": item["source_id"],
            "source_title": item["source_title"],
            "section": item["section"],
            "pdf_page": item["pdf_page"],
            "official_url": item["official_url"],
            "text": item["text"],
            "score": round(score, 4),
        }
        for score, item in results[:top_k]
    ]
    return {
        "question": question,
        "status": "EVIDENCE_FOUND" if evidence else "INSUFFICIENT_EVIDENCE",
        "evidence_items": evidence,
        "limitations": [
            "Curated source-text excerpts only: not exhaustive full-document search.",
            "Search relevance does not establish legal applicability, CAP compliance, or actual warning usability.",
            "No generation or modification of simulation, delivery, recovery, or KPI outputs.",
        ],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrieve source-text evidence by question")
    parser.add_argument("question", type=str, help="Arabic or English question")
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(retrieve_evidence(args.question, args.top_k), ensure_ascii=False, indent=2))
