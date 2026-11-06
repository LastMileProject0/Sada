from fastapi.testclient import TestClient
from sada_bridge.api import create_app


def test_readiness_checks_existing_storage(tmp_path):
    path = tmp_path / 'test.sqlite'
    with TestClient(create_app(path)) as client:
        assert client.get('/api/health').status_code == 200
        path.unlink()  # Temporary fixture only; never the working application DB.
        failed = client.get('/api/health')
        assert failed.status_code == 503
        assert failed.json() == {'detail': 'Evaluation service unavailable'}
        assert not path.exists()


def test_readiness_checks_dataset_access(tmp_path, monkeypatch):
    with TestClient(create_app(tmp_path / 'test.sqlite')) as client:
        monkeypatch.setattr('sada_bridge.api.os.access', lambda *_: False)
        assert client.get('/api/health').status_code == 503
