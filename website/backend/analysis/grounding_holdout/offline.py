"""Deny networking and command escapes while the holdout executes.

This is an in-process safety tripwire for trusted fixtures, not an OS sandbox
for hostile code. No provider is constructed or invoked by the runner.
"""
from contextlib import ExitStack, contextmanager
import socket
import ssl
import sys
from unittest.mock import patch


class OfflineViolation(RuntimeError):
    pass


_active = 0


def _audit(event, args):
    if _active and (
        event.startswith("socket.")
        or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}
    ):
        raise OfflineViolation(f"Offline holdout forbids {event}")


sys.addaudithook(_audit)


@contextmanager
def forbid_network():
    # Global rather than thread-local: worker threads must also be blocked.
    global _active
    _active += 1
    try:
        # Audit events catch new sockets, DNS and child processes. Also block
        # existing connections: send/sendall and TLS read/write need not emit
        # a socket audit event of their own.
        def blocked(*args, **kwargs):
            raise OfflineViolation("Offline holdout forbids socket/TLS I/O")

        with ExitStack() as stack:
            for cls, names in (
                (socket.socket, (
                    "connect", "connect_ex", "send", "sendall", "sendto", "sendmsg",
                    "sendfile", "recv", "recv_into", "recvfrom", "recvfrom_into",
                    "recvmsg", "recvmsg_into", "accept", "bind", "listen",
                )),
                (ssl.SSLSocket, (
                    "connect", "connect_ex", "send", "sendall", "recv", "recv_into",
                    "read", "write", "do_handshake", "unwrap",
                )),
            ):
                for name in names:
                    if hasattr(cls, name):
                        stack.enter_context(patch.object(cls, name, blocked))
            yield
    finally:
        _active -= 1
