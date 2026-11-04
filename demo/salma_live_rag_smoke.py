"""Optional local end-to-end smoke test using verified retrieval from Maymona.

Usage from repository root:
 python demo/salma_live_rag_smoke.py path/to/policy_retrieval_result.json

The JSON must be a REAL result from Maymona, not the synthetic test fixture.
"""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lastmile_ai.ai.policy_explainer import explain_policy


def main():
    if len(sys.argv)!=2:
        raise SystemExit('Usage: python demo/salma_live_rag_smoke.py policy_retrieval_result.json')
    value=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    question=value.get('query')
    if not isinstance(question,str) or not question.strip():
        raise SystemExit('Retrieval JSON must include a nonempty original query.')
    result=explain_policy(question,value)
    print(json.dumps(result.to_dict(),ensure_ascii=False,indent=2))
    if result.status!='Answered':
        raise SystemExit('Smoke test did not yield a verified Answered status; inspect limitations.')

if __name__=='__main__': main()
