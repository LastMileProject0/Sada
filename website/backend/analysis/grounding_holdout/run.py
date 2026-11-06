"""Evaluate the unchanged website guard against independently labeled fixtures.

Run from backend: python -B -m analysis.grounding_holdout.run
Exit 1 means semantic discrepancies, 2 means invalid fixtures/runtime failure.
--report-only explicitly permits discrepancies; it never hides them.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from .offline import forbid_network

CASES_PATH = Path(__file__).with_name("cases.json")
CATEGORIES = {
    "english_paraphrase", "arabic_paraphrase", "mixed_language", "arabic_dialect",
    "nested_negation", "cross_sentence_citation", "condition_scope",
}
OUTCOMES = ("true_acceptance", "true_rejection", "false_acceptance", "false_rejection")


def load_cases(path=CASES_PATH):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "synthetic_grounding_holdout.v1":
        raise ValueError("Unexpected holdout schema")
    cases = payload["cases"]
    ids = set()
    for case in cases:
        if case["id"] in ids or not re.fullmatch(r"[A-Z]{2}\d{2}", case["id"]):
            raise ValueError("Duplicate or invalid holdout ID")
        ids.add(case["id"])
        if type(case["supported"]) is not bool or case["category"] not in CATEGORIES:
            raise ValueError("Invalid gold label/category")
        if not case["evidence"] or len(case["evidence"]) > 2:
            raise ValueError("Each case needs one or two synthetic passages")
        for text in [*case["evidence"], case["answer"], case["rationale"], case["language"]]:
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Fixture text must be nonempty")
        tags = re.findall(r"\[([^]]+)\]", case["answer"])
        allowed = {"HOLDOUT-A", "HOLDOUT-B"} if len(case["evidence"]) == 2 else {"HOLDOUT-A"}
        if not tags or not set(tags) <= allowed:
            raise ValueError("Fixture citation must reference its own synthetic passage")
    if not cases:
        raise ValueError("Holdout is empty")
    return cases


def evaluate(cases):
    rows = []
    with forbid_network():
        # Import under the offline guard too. No retriever, KB, API or provider.
        from lastmile_ai.ai.policy_explainer import ExplanationResult
        from sada_bridge.policy_grounding import guard_policy_explanation

        for case in cases:
            passages = [
                {
                    "passage_id": f"HOLDOUT-{'AB'[index]}",
                    "source_id": "SYNTHETIC-HOLDOUT-NOT-KB",
                    "source_title": "Invented offline dispatch fixture — NOT approved KB",
                    "section": "Synthetic holdout only",
                    "text": text,
                    "official_url": "https://grounding-holdout.invalid/not-a-policy",
                    "source_verified": True,
                }
                for index, text in enumerate(case["evidence"])
            ]
            retrieval = {"schema_version": "policy_retrieval.v1", "passages": passages}
            cited_ids = set(re.findall(r"\[([^]]+)\]", case["answer"]))
            citations = tuple(
                {key: p[key] for key in ("passage_id", "source_id", "section", "official_url")}
                for p in passages if p["passage_id"] in cited_ids
            )
            base = ExplanationResult(
                schema_version="ai_explanation.v1",
                question="Offline invented dispatch wording comparison",
                status="Answered", answer=case["answer"], citations=citations,
                model_id=None, llm_invoked=False, execution_mode="offline_holdout",
                limitations=("Synthetic fixture; no generation or real policy evidence.",),
            )
            frozen = deepcopy((base, retrieval))
            result = guard_policy_explanation(base, retrieval)
            if (base, retrieval) != frozen:
                raise AssertionError("Guard mutated fixture input")
            if result.status not in {"Answered", "ReviewRequired"}:
                raise AssertionError(f"Unexpected status: {result.status}")
            if result.llm_invoked or result.model_id is not None:
                raise AssertionError("Offline invocation metadata changed")
            if result.status == "ReviewRequired" and (result.answer or result.citations):
                raise AssertionError("Withheld answer leaked answer/citations")
            accepted = result.status == "Answered"
            if accepted and (result.answer != base.answer or result.citations != base.citations):
                raise AssertionError("Guard rewrote an accepted fixture")
            outcome = (
                "true_acceptance" if case["supported"] and accepted else
                "false_rejection" if case["supported"] else
                "false_acceptance" if accepted else "true_rejection"
            )
            rows.append({
                **case, "expected_status": "Answered" if case["supported"] else "ReviewRequired",
                "actual_status": result.status, "outcome": outcome,
                "guard_reason": result.limitations[-1] if not accepted else None,
            })
    counts = Counter(row["outcome"] for row in rows)
    summary = {key: counts[key] for key in OUTCOMES}
    supported = sum(row["supported"] for row in rows)
    unsupported = len(rows) - supported
    by_category = {}
    for category in sorted({row["category"] for row in rows}):
        category_counts = Counter(row["outcome"] for row in rows if row["category"] == category)
        by_category[category] = {key: category_counts[key] for key in OUTCOMES}
    fixture_hash = hashlib.sha256(
        json.dumps(cases, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "synthetic_grounding_holdout_report.v1",
        "fixture_sha256": fixture_hash,
        "guard_sha256": hashlib.sha256(
            Path(__file__).resolve().parents[2].joinpath("sada_bridge/policy_grounding.py").read_bytes()
        ).hexdigest(),
        "evaluated_layer": "website post-generation guard only; preconstructed Answered inputs",
        "network_forbidden": True, "provider_calls": 0,
        "total": len(rows), "supported": supported, "unsupported": unsupported,
        "summary": summary,
        "false_acceptance_rate": counts["false_acceptance"] / unsupported if unsupported else None,
        "false_rejection_rate": counts["false_rejection"] / supported if supported else None,
        "by_category": by_category, "cases": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write full auditable JSON report")
    parser.add_argument("--report-only", action="store_true",
                        help="Exit zero despite discrepancies, keeping all findings visible")
    args = parser.parse_args(argv)
    try:
        with forbid_network():
            report = evaluate(load_cases())
        print(json.dumps({key: value for key, value in report.items() if key != "cases"},
                         ensure_ascii=False, indent=2))
        for row in report["cases"]:
            if row["outcome"].startswith("false_"):
                print(f'{row["id"]}: {row["outcome"]}; {row["rationale"]}')
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
        discrepancies = report["summary"]["false_acceptance"] + report["summary"]["false_rejection"]
        return 1 if discrepancies and not args.report_only else 0
    except Exception as exc:
        print(f"Holdout failed to execute: {type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
