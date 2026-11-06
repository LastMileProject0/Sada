"""Harness checks only; a green harness does NOT mean the holdout passed."""
import socket
from urllib import request

import pytest

from holdout.run_policy_grounding import (
    NetworkForbidden, classify, exit_code, load_cases, no_network,
)


def test_frozen_synthetic_manifest_is_balanced_and_separate_from_approved_kb():
    data = load_cases()
    assert len(data['cases']) == 96
    assert all(pid in ('H1', 'H2') for texts in data['evidence_sets'].values() for pid in texts)
    assert {'en', 'ar', 'en-ar', 'ar-JO', 'ar-EG', 'ar-Gulf'} == {
        c['language'] for c in data['cases']
    }


@pytest.mark.parametrize(('expected', 'actual', 'outcome'), [
    ('Answered', 'Answered', 'correct_acceptance'),
    ('Answered', 'ReviewRequired', 'false_rejection'),
    ('ReviewRequired', 'Answered', 'false_acceptance'),
    ('ReviewRequired', 'ReviewRequired', 'correct_rejection'),
])
def test_classification_does_not_turn_a_safety_failure_into_a_pass(expected, actual, outcome):
    assert classify(expected, actual) == outcome


def test_unknown_status_is_not_silently_counted_as_safe():
    with pytest.raises(ValueError):
        classify('ReviewRequired', 'UnexpectedStatus')


@pytest.mark.parametrize(('totals', 'code'), [
    ({'false_acceptance': 1, 'false_rejection': 0}, 1),
    ({'false_acceptance': 0, 'false_rejection': 1}, 1),
    ({'false_acceptance': 0, 'false_rejection': 0}, 0),
])
def test_audit_returns_nonzero_for_either_kind_of_semantic_mismatch(totals, code):
    assert exit_code({'totals': totals}) == code


def test_network_barrier_blocks_before_dns_or_connection():
    with no_network() as attempts:
        for operation in [
            lambda: socket.getaddrinfo('example.invalid', 443),
            lambda: socket.create_connection(('example.invalid', 443)),
            lambda: request.urlopen('https://example.invalid'),
        ]:
            with pytest.raises(NetworkForbidden):
                operation()
    assert len(attempts) == 3
