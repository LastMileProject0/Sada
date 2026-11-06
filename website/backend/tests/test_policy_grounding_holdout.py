"""Harness checks, NOT a claim that the guard passes the semantic holdout.

The strict CLI separately returns nonzero for false acceptances/rejections.
Gold labels must never be edited to make these harness tests green.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
import socket
import subprocess
from urllib import request

import pytest

from analysis.grounding_holdout.offline import OfflineViolation, forbid_network
from analysis.grounding_holdout.run import CATEGORIES, evaluate, load_cases, main


@pytest.fixture(scope="module")
def report():
    return evaluate(load_cases())


def test_corpus_has_independent_labels_and_all_requested_axes():
    cases = load_cases()
    assert len(cases) == 56
    assert {c["category"] for c in cases} == CATEGORIES
    for category in CATEGORIES:
        assert Counter(c["supported"] for c in cases if c["category"] == category) == {
            True: 4, False: 4,
        }
    assert all(c["rationale"] and c["language"] for c in cases)
    assert all("SRC-" not in c["answer"] for c in cases)


def test_outcomes_are_computed_from_gold_not_guard_predictions(report):
    expected = Counter()
    for row in report["cases"]:
        accepted = row["actual_status"] == "Answered"
        outcome = (
            "true_acceptance" if row["supported"] and accepted else
            "false_rejection" if row["supported"] else
            "false_acceptance" if accepted else "true_rejection"
        )
        assert row["outcome"] == outcome
        expected[outcome] += 1
    assert report["total"] == 56
    assert report["supported"] == report["unsupported"] == 28
    assert report["summary"] == {key: expected[key] for key in report["summary"]}
    assert report["false_acceptance_rate"] == expected["false_acceptance"] / 28
    assert report["false_rejection_rate"] == expected["false_rejection"] / 28
    assert report["provider_calls"] == 0 and report["network_forbidden"]
    assert len(report["fixture_sha256"]) == len(report["guard_sha256"]) == 64
    for key in report["summary"]:
        assert sum(c[key] for c in report["by_category"].values()) == report["summary"][key]


@pytest.mark.parametrize("attempt", [
    lambda: socket.socket(),
    lambda: socket.socketpair(),
    lambda: socket.getaddrinfo("grounding-holdout.invalid", 443),
    lambda: socket.gethostbyname("grounding-holdout.invalid"),
    lambda: request.urlopen("https://grounding-holdout.invalid"),
    lambda: subprocess.run(["curl", "https://grounding-holdout.invalid"], check=True),
    lambda: os.system("curl https://grounding-holdout.invalid"),
])
def test_network_and_command_escapes_fail_before_io(attempt):
    with forbid_network(), pytest.raises(OfflineViolation, match="Offline holdout forbids"):
        attempt()


def test_threaded_network_attempt_is_also_blocked():
    with ThreadPoolExecutor(max_workers=1) as executor:
        with forbid_network(), pytest.raises(OfflineViolation):
            executor.submit(socket.socket).result()


@pytest.mark.parametrize("method,args", [
    ("send", (b"holdout",)), ("sendall", (b"holdout",)),
    ("connect", (("127.0.0.1", 9),)),
])
def test_socket_created_before_offline_scope_cannot_do_io(method, args):
    # Allocates an unconnected socket, never connects or sends any data.
    with socket.socket() as existing:
        with forbid_network(), pytest.raises(OfflineViolation):
            getattr(existing, method)(*args)


def test_nested_offline_scope_remains_active_until_outer_exit():
    with forbid_network():
        with forbid_network():
            with pytest.raises(OfflineViolation):
                socket.socket()
        with pytest.raises(OfflineViolation):
            socket.socket()
    # Do not open a socket just to test restoration; a harmless audit event
    # exercises our own hook without creating a network operation.
    import sys
    sys.audit("socket.holdout_probe")


def test_invalid_fixture_labels_fail_loudly(tmp_path):
    payload = {"schema_version": "synthetic_grounding_holdout.v1", "cases": load_cases()}
    payload["cases"][0]["supported"] = "false"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="gold label"):
        load_cases(path)


def test_strict_exit_and_full_report_keep_discrepancies_visible(tmp_path, capsys, report):
    path = tmp_path / "results.json"
    discrepancies = report["summary"]["false_acceptance"] + report["summary"]["false_rejection"]
    assert main(["--output", str(path)]) == (1 if discrepancies else 0)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == report
    output = capsys.readouterr().out
    for row in report["cases"]:
        if row["outcome"].startswith("false_"):
            assert f'{row["id"]}: {row["outcome"]}' in output
    assert main(["--report-only"]) == 0
    assert '"false_acceptance"' in capsys.readouterr().out


def test_runner_errors_are_not_disguised_as_review_or_success(monkeypatch, capsys):
    def broken():
        raise RuntimeError("deliberate harness failure")
    monkeypatch.setattr("analysis.grounding_holdout.run.load_cases", broken)
    assert main(["--report-only"]) == 2
    assert "deliberate harness failure" in capsys.readouterr().out
