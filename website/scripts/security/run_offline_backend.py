"""Run backend regressions on disposable stores; deny external Python networking.

Native libpq is NOT covered by a Python socket guard. PostgreSQL integration
fixtures must continue to select their own disposable Unix-socket cluster.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
GUARD = """
import ipaddress
import socket
import sys
_connect, _connect_ex, _resolve = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo
def allowed(sock, address):
    if sock.family == socket.AF_UNIX:
        return True
    if not isinstance(address, tuple):
        return False
    try:
        return ipaddress.ip_address(address[0]).is_loopback
    except ValueError:
        return address[0] == 'localhost'
def connect(sock, address):
    if not allowed(sock, address):
        raise OSError('External network disabled for offline regressions')
    return _connect(sock, address)
def connect_ex(sock, address):
    if not allowed(sock, address):
        raise OSError('External network disabled for offline regressions')
    return _connect_ex(sock, address)
def resolve(host, port, family=0, type=0, proto=0, flags=0):
    # Preserve the native audit event before this outer wrapper can reject DNS.
    # An active stricter holdout guard must reject first with OfflineViolation.
    # Without that guard, external resolution remains denied below.
    sys.audit('socket.getaddrinfo', host, port, family, type, proto)
    if host not in (None, 'localhost'):
        try:
            if not ipaddress.ip_address(host).is_loopback:
                raise OSError('External DNS disabled for offline regressions')
        except ValueError:
            raise OSError('External DNS disabled for offline regressions')
    return _resolve(host, port, family, type, proto, flags)
socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo = connect, connect_ex, resolve
"""


def main():
    with tempfile.TemporaryDirectory(prefix="sada-offline-regression-") as temp:
        Path(temp, "sitecustomize.py").write_text(GUARD)
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([temp, str(ROOT / "backend")]),
               "SADA_STORAGE_BACKEND": "sqlite", "SADA_EVAL_DB": str(Path(temp, "isolated.sqlite")),
               "NODE_ENV": "development", "PYTHONDONTWRITEBYTECODE": "1"}
        # Child tests must not inherit a hosted target or usable model credential.
        for key in ["OPENROUTER_API_KEY", "NEON_SETUP_ADMIN_DSN", "SADA_APP_DB_PASSWORD",
                    "SADA_POSTGRES_DSN", "SADA_DEV_POSTGRES_DSN",
                    "DATABASE_URL", "PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE"]:
            env.pop(key, None)
        return subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "tests", *sys.argv[1:]],
                              cwd=ROOT / "backend", env=env).returncode


if __name__ == "__main__":
    sys.exit(main())
