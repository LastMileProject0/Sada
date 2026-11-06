"""Independent offline audit. Exit 1 means semantic mismatches, not a harness pass.

No approved KB/retriever, original regression fixtures or private guard constants
are imported. All candidate answers and evidence are synthetic, frozen inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager, ExitStack
import copy
import csv
import hashlib
import http.client
import json
from pathlib import Path
import socket
import sys
from unittest.mock import patch
from urllib import request

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from lastmile_ai.ai.policy_explainer import explain_policy
from sada_bridge.policy_grounding import guard_policy_explanation

CASES = Path(__file__).with_name('policy_grounding_cases.json')


class NetworkForbidden(BaseException):
    """Cannot be swallowed by a provider's ordinary transport-error handler."""


@contextmanager
def no_network():
    attempts = []

    def deny(label, original):
        def blocked(*args, **kwargs):
            # ASGI/asyncio uses AF_UNIX socketpairs for local thread wakeups.
            # Permit that IPC only; IP sockets/DNS/HTTP remain forbidden.
            if (args and isinstance(args[0], socket.socket)
                    and args[0].family == socket.AF_UNIX):
                return original(*args, **kwargs)
            attempts.append(label)
            raise NetworkForbidden('Offline holdout attempted network operation: ' + label)
        return blocked

    with ExitStack() as stack:
        targets = [
            (socket, 'create_connection'), (socket, 'getaddrinfo'),
            (socket.socket, 'connect'), (socket.socket, 'connect_ex'),
            (socket.socket, 'send'), (socket.socket, 'sendall'), (socket.socket, 'sendto'),
            (request, 'urlopen'), (request.OpenerDirector, 'open'),
            (http.client.HTTPConnection, 'connect'), (http.client.HTTPSConnection, 'connect'),
        ]
        if hasattr(socket.socket, 'sendmsg'):
            targets.append((socket.socket, 'sendmsg'))
        for obj, name in targets:
            stack.enter_context(patch.object(obj, name, deny(name, getattr(obj, name))))
        yield attempts


def load_cases(path=CASES):
    data = json.loads(path.read_text(encoding='utf-8'))
    fresh = data['schema_version'] == 'sada.claim-aware-holdout.v1'
    assert fresh or data['schema_version'] == 'sada.offline-grounding-holdout.v1'
    cases = data['cases']
    count, size, half = (32, 4, 2) if fresh else (96, 12, 6)
    assert len(cases) == count and len({c['id'] for c in cases}) == count
    assert len({c['group'] for c in cases}) == 8
    assert all(n == size for n in Counter(c['group'] for c in cases).values())
    for case in cases:
        assert case['expected'] in ('Answered', 'ReviewRequired')
        assert case['basis'].strip() and case['answer'].strip()
        assert case['source'] in data['evidence_sets']
        if not fresh:
            assert all(pid.startswith('H') for pid in data['evidence_sets'][case['source']])
    for group in {c['group'] for c in cases}:
        assert Counter(c['expected'] for c in cases if c['group'] == group) == {
            'Answered': half, 'ReviewRequired': half,
        }
    return data


def classify(expected, actual):
    if actual not in ('Answered', 'ReviewRequired', 'InsufficientInformation', 'ModelUnavailable'):
        raise ValueError('Unknown production result status')
    if expected == 'Answered':
        return 'correct_acceptance' if actual == 'Answered' else 'false_rejection'
    return 'false_acceptance' if actual == 'Answered' else 'correct_rejection'


def exit_code(report):
    totals = report['totals']
    return int(bool(totals.get('false_acceptance', 0) or totals.get('false_rejection', 0)))


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_holdout(path=CASES):
    data = load_cases(path)
    frozen = copy.deepcopy(data)
    protected = [
        BACKEND / 'sada_bridge/policy_grounding.py',
        BACKEND / 'sada_bridge/policy_claims.py',
        BACKEND / 'lastmile_ai/ai/policy_explainer.py',
        BACKEND / 'ai_explanation/ai_explanation.py',
    ]
    hashes = {str(p.relative_to(ROOT)): _hash(p) for p in protected}
    fixture_hash = _hash(path)
    for name, digest in data.get('frozen_boundary_sha256', {}).items():
        assert _hash(ROOT / name) == digest, 'Boundary changed after fresh holdout freeze'
    records = []
    with no_network() as attempts:
        for case in data['cases']:
            texts = data['evidence_sets'][case['source']]
            retrieval = {
                'schema_version': 'policy_retrieval.v1',
                'passages': [({
                    'passage_id': pid, 'source_id': 'HOLDOUT-' + pid,
                    'source_title': 'Synthetic holdout fixture; not approved KB',
                    'section': 'Synthetic audit only', 'text': text,
                    'official_url': 'https://example.invalid/offline/' + pid,
                    'locator': 'Offline synthetic fixture', 'source_verified': True,
                } | data.get('source_metadata', {}).get(pid, {}))
                    for pid, text in texts.items()],
            }
            if 'alter' in case:
                retrieval['passages'][0][case['alter']['field']] = case['alter']['value']
            untouched = copy.deepcopy(retrieval)
            calls = []

            def fixture_provider(prompt, model):
                # Retry, if the original citation checker asks for it, returns
                # the SAME frozen fixture. Never repair an answer for the audit.
                calls.append(model)
                return case['answer']

            core = explain_policy(
                'Explain the synthetic bulletin rule using only its cited evidence.',
                retrieval, provider=fixture_provider, model_id='OFFLINE-HOLDOUT-FIXTURE',
            )
            final = guard_policy_explanation(core, retrieval)
            assert core.status in ('Answered', 'ReviewRequired')
            assert final.status in ('Answered', 'ReviewRequired')
            assert retrieval == untouched
            assert len(calls) in (1, 2)
            records.append({
                **case, 'evidence': texts, 'core_status': core.status,
                'actual_status': final.status,
                'classification': classify(case['expected'], final.status),
                'rejection_stage': (
                    'none' if final.status == 'Answered'
                    else 'original_pipeline' if core.status != 'Answered' else 'website_guard'
                ),
                'offline_fixture_calls': len(calls),
                'limitations': list(final.limitations),
            })
    assert not attempts and data == frozen and _hash(path) == fixture_hash
    assert all(_hash(ROOT / name) == digest for name, digest in hashes.items())
    totals = Counter(r['classification'] for r in records)
    grouped = defaultdict(Counter)
    languages = defaultdict(Counter)
    for record in records:
        grouped[record['group']][record['classification']] += 1
        languages[record['language']][record['classification']] += 1
    return {
        'schema_version': 'sada.offline-grounding-results.v1',
        'notice': 'Synthetic offline fixture audit, not real inference or approved policy facts.',
        'independence_limits': (
            'Fresh author-labelled cases, separate from original tests/allowlists/KB. '
            'Not externally blinded or a representative production sample. '
            'Faithful paraphrase rejections count as false rejections even where '
            'the conservative guard intentionally withholds them.'
        ),
        'fixture_sha256': fixture_hash, 'unchanged_source_sha256': hashes,
        'fixture_schema': data['schema_version'],
        'boundary_freeze': data.get('frozen_boundary_sha256', {}),
        'network_attempts': len(attempts), 'case_count': len(records),
        'totals': {k: totals[k] for k in (
            'correct_acceptance', 'correct_rejection', 'false_acceptance', 'false_rejection',
        )},
        'by_group': {k: dict(v) for k, v in grouped.items()},
        'by_language': {k: dict(v) for k, v in languages.items()},
        'cases': records,
    }


def write_reports(report, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8',
    )
    columns = [
        'id', 'group', 'language', 'expected', 'core_status', 'actual_status',
        'classification', 'rejection_stage', 'answer', 'basis', 'evidence',
        'offline_fixture_calls', 'limitations', 'alter',
    ]
    with (output / 'results.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in report['cases']:
            writer.writerow({
                key: json.dumps(row.get(key, ''), ensure_ascii=False)
                if isinstance(row.get(key), (dict, list)) else row.get(key, '') for key in columns
            })
    lines = [
        '# Independent offline grounding holdout — full results',
        '', report['notice'], '', report['independence_limits'], '',
        f"Fixture SHA-256: `{report['fixture_sha256']}`",
        f"Network attempts: **{report['network_attempts']}**",
        '', '## Totals', '', '| Outcome | Count |', '| --- | ---: |',
    ]
    lines.extend(f'| {name} | {n} |' for name, n in report['totals'].items())
    lines += ['', '## All case verdicts', '',
              '| Case | Group | Language | Expected | Core | Website | Outcome |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for r in report['cases']:
        lines.append('| ' + ' | '.join(str(r[k]) for k in (
            'id', 'group', 'language', 'expected', 'core_status', 'actual_status', 'classification',
        )) + ' |')
    lines += ['', '## Complete fixtures and explanations', '']
    for r in report['cases']:
        lines += [
            f"### {r['id']} — {r['classification']}", '',
            f"Expected: {r['expected']}; actual: {r['actual_status']}; core: {r['core_status']}.",
            '', 'Evidence (synthetic):', '',
            '```json', json.dumps(r['evidence'], ensure_ascii=False, indent=2), '```',
            '', 'Candidate (synthetic):', '', '```text', r['answer'], '```',
            '', 'Oracle rationale: ' + r['basis'], '',
            'Synthetic input alterations: ' + json.dumps(r.get('alter', {}), ensure_ascii=False), '',
            'Production limitations: ' + ' / '.join(r['limitations']), '',
        ]
    (output / 'results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'generated-artifacts/grounding-holdout')
    parser.add_argument('--cases', type=Path, default=CASES)
    args = parser.parse_args()
    report = run_holdout(args.cases)
    write_reports(report, args.output)
    print(json.dumps({k: report[k] for k in (
        'case_count', 'totals', 'by_group', 'by_language', 'network_attempts', 'fixture_sha256',
    )}, ensure_ascii=False, indent=2))
    print('Full reports:', args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output)
    print('FAIL: semantic mismatches remain.' if exit_code(report) else 'PASS: all labels matched.')
    return exit_code(report)


if __name__ == '__main__':
    raise SystemExit(main())
