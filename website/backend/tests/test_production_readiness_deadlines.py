"""Isolated supervisor deadlines: no database, child process or network I/O."""
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def supervisor():
    path = Path(__file__).resolve().parents[2] / 'scripts/production/run.py'
    spec = importlib.util.spec_from_file_location('readiness_deadline_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_encloses_node_deadline_and_accepts_hosted_health(supervisor, monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(supervisor, 'time', SimpleNamespace(
        monotonic=lambda: clock[0], sleep=lambda _seconds: None))
    response = io.BytesIO(b'{"status":"ok"}')
    response.status = 200

    def probe(_url, *, timeout):
        assert timeout == 10
        clock[0] += 3.2
        return response

    monkeypatch.setattr(supervisor, 'urlopen', probe)
    supervisor.wait_ready('http://127.0.0.1:8000/api/health', [], timeout=30)


def test_probe_is_clamped_to_remaining_overall_deadline(supervisor, monkeypatch):
    clock = [0.0]
    budgets = []
    monkeypatch.setattr(supervisor, 'time', SimpleNamespace(
        monotonic=lambda: clock[0],
        sleep=lambda seconds: clock.__setitem__(0, clock[0] + seconds)))

    def unavailable(_url, *, timeout):
        budgets.append(timeout)
        clock[0] += timeout
        raise TimeoutError()

    monkeypatch.setattr(supervisor, 'urlopen', unavailable)
    with pytest.raises(RuntimeError, match='Production readiness timed out'):
        supervisor.wait_ready('http://127.0.0.1:8000/api/health', [], timeout=12)
    assert budgets[0] == 10
    assert 0 < budgets[1] < 2
    assert clock[0] < 12.2


def test_exited_child_fails_before_any_probe(supervisor, monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('Must not probe after a child exits')

    monkeypatch.setattr(supervisor, 'urlopen', forbidden)
    with pytest.raises(RuntimeError, match='child exited'):
        supervisor.wait_ready('http://127.0.0.1:8000/api/health',
                              [SimpleNamespace(poll=lambda: 1)])
