"""Opt-in genuine HTTPS website inference test. Never prints credentials/content.

Run ONLY after OPENROUTER_API_KEY is saved in Replit Secrets:
  python -B scripts/security/smoke_openrouter_policy.py
This may consume existing inference credit; it never purchases any.
"""
import http.cookiejar
import json
import os
import sys
from urllib import request


def main():
    if not os.environ.get('OPENROUTER_API_KEY'):
        print('BLOCKED: OPENROUTER_API_KEY is not available; no inference attempted.')
        return 2
    domain = os.environ.get('REPLIT_DEV_DOMAIN')
    if not domain:
        print('BLOCKED: development preview domain unavailable.')
        return 2
    base = f'https://{domain}'
    opener = request.build_opener(request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for language, question in [
        ('en', 'What does CAP say about the instruction field?'),
        ('ar', 'ما معنى حقل instruction في معيار CAP؟'),
    ]:
        req = request.Request(base + '/api/policy/explain', method='POST',
                              data=json.dumps({'question': question}).encode(),
                              headers={'Content-Type': 'application/json', 'Origin': base})
        try:
            with opener.open(req, timeout=185) as response:
                body = json.loads(response.read(131073))
                status = response.status
            explanation = body['explanation']
            cited = [c['passage_id'] for c in explanation['citations']]
            print(json.dumps({'language': language, 'http': status,
                              'status': explanation['status'], 'citations': cited,
                              'llm_invoked': explanation['llm_invoked'],
                              'model_id': explanation['model_id']}))
            assert explanation['status'] == 'Answered'
            assert explanation['llm_invoked'] and explanation['execution_mode'] == 'live_llm'
            assert explanation['model_id'] == 'qwen/qwen-2.5-7b-instruct'
            assert explanation['answer'].strip() and cited
            assert all(c in {e['evidence_id'] for e in body['retrieval']['evidence_items']}
                       for c in cited)
            if language == 'ar':
                assert any('\u0600' <= char <= '\u06ff' for char in explanation['answer'])
        except Exception:
            # No exception text, upstream body, cookie or key is printed.
            print('FAILED: genuine website inference was not accepted; inspect safe status above.')
            return 1
    print('PASS: genuine bilingual website inference with validated citations.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
