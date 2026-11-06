"""Single production API supervisor. Never launches Vite or exposes Python."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]


def prepare_python_runtime():
    packages = (ROOT / '.pythonlibs' / 'lib'
                / f'python{sys.version_info.major}.{sys.version_info.minor}'
                / 'site-packages')
    if not packages.is_dir():
        raise RuntimeError('Packaged Python runtime dependencies are missing')
    sys.path.insert(0, str(packages))
    # Child Python must use this payload, not development-only PYTHONPATH entries.
    return {'PYTHONPATH': str(packages)}


def safe_startup_error(error):
    if isinstance(error, ModuleNotFoundError):
        name = error.name or ''
        if name and all(part.isascii() and part.isidentifier() for part in name.split('.')):
            return f'ModuleNotFoundError: {name}'
        return 'ModuleNotFoundError'
    return str(error) if isinstance(error, RuntimeError) else type(error).__name__


def require_configuration():
    if len(os.environ.get('SESSION_SECRET', '').encode()) < 32:
        raise RuntimeError('A stable production SESSION_SECRET is required')
    from urllib.parse import urlsplit
    origin = os.environ.get('SADA_PUBLIC_ORIGIN', '')
    parsed = urlsplit(origin)
    if (parsed.scheme != 'https' or not parsed.netloc or parsed.username
            or origin != f'https://{parsed.netloc}'):
        raise RuntimeError('An exact SADA_PUBLIC_ORIGIN HTTPS origin is required')
    sys.path.insert(0, str(ROOT / 'backend'))
    from sada_bridge.storage_backend import create_store
    store = create_store(production=True)
    store.check_readable()  # Read-only validation; no startup DDL or data import.
    for artifact in ['artifacts/api-server/dist/index.mjs',
                     'artifacts/sada/dist/public/index.html']:
        if not (ROOT / artifact).is_file():
            raise RuntimeError('Built production assets are missing')
    ports = []
    for key, default in [('PORT', '8080'), ('SADA_PYTHON_PORT', '8000')]:
        value = os.environ.get(key, default)
        if not value.isascii() or not value.isdigit() or not 1 <= int(value) <= 65535:
            raise RuntimeError('Invalid production service port')
        ports.append(int(value))
    if ports[0] == ports[1]:
        raise RuntimeError('Node and Python must use different ports')
    return ports


def wait_ready(url, processes, timeout=30):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if any(p.poll() is not None for p in processes):
            raise RuntimeError('A production child exited before readiness')
        remaining = until - time.monotonic()
        if remaining <= 0:
            break
        try:
            # Encloses Node's bounded 8-second Python probe; never extend the
            # overall startup deadline while allowing hosted DB round trips.
            with urlopen(url, timeout=min(10, remaining)) as response:
                if response.status == 200 and json.load(response).get('status') == 'ok':
                    return
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError('Production readiness timed out')


def main():
    children = []
    def stop(_signal=None, _frame=None):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        runtime_environment = prepare_python_runtime()
        node_port, python_port = require_configuration()
        env = {**os.environ, **runtime_environment,
               'NODE_ENV': 'production', 'PORT': str(node_port)}
        children.append(subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'sada_bridge.api:app',
            '--host', '127.0.0.1', '--port', str(python_port),
            '--workers', '1', '--no-server-header',
        ], cwd=ROOT / 'backend', env=env))
        wait_ready(f'http://127.0.0.1:{python_port}/api/health', children)
        children.append(subprocess.Popen([
            'node', '--enable-source-maps', 'artifacts/api-server/dist/index.mjs',
        ], cwd=ROOT, env=env))
        wait_ready(f'http://127.0.0.1:{node_port}/api/healthz', children)
        print('SADA production API ready: Node gateway and private Python', flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.2)
        raise RuntimeError('A production child exited; stopping the paired service')
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        # Only controlled configuration/lifecycle messages, no credentials.
        message = safe_startup_error(error)
        print(f'Production startup failed: {message}', file=sys.stderr)
        return 1
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in reversed(children):
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    sys.exit(main())
