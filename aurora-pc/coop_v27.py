"""v2.7 Aurora UDP diagnostics: room-authenticated echo on Aurora-only UDP 24645.

This is NOT a test of Stardew Valley's UDP 24642 game socket. It proves that
small datagrams can traverse the current route to a separately opened Aurora
socket. No port forwarding, VPN creation, NAT traversal, or game patching.
"""
from __future__ import annotations

import hmac
import re
import socket
import threading

import coop_v20 as base

DIAG_PORT = 24645
CHALLENGE = b"AURORA_UDP_V1 "
RESPONSE = b"AURORA_UDP_OK_V1 "
HEX16 = re.compile(rb"^[0-9a-f]{16}$")
HEX32 = re.compile(rb"^[0-9a-f]{32}$")


def reply_challenge(payload: bytes, address: str, token: str) -> bytes | None:
    if not base.local_address(address) or len(payload) != len(CHALLENGE) + 32 + 1 + 16:
        return None
    if not payload.startswith(CHALLENGE):
        return None
    provided = payload[len(CHALLENGE):]
    key, delimiter, nonce = provided.partition(b" ")
    if delimiter != b" " or not HEX16.fullmatch(nonce) or not HEX32.fullmatch(key):
        return None
    if not hmac.compare_digest(key, token.encode("ascii")):
        return None
    return RESPONSE + nonce


class CoopAdvancedService(base.CoopLANService):
    def __init__(self, *args, diag_port: int = DIAG_PORT, **kwargs):
        super().__init__(*args, **kwargs)
        self.diag_port = diag_port
        self._diagnostic_sock: socket.socket | None = None
        self._diagnostic_thread: threading.Thread | None = None

    def start(self) -> None:
        if self._diagnostic_sock is not None:
            return
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp.bind(("0.0.0.0", self.diag_port))
            udp.settimeout(0.4)
            super().start()
        except Exception:
            udp.close()
            raise
        self._diagnostic_sock = udp
        self._diagnostic_thread = threading.Thread(target=self._serve_echo, daemon=True,
                                                   name="AuroraUDPPreflight")
        self._diagnostic_thread.start()

    def _serve_echo(self):
        udp = self._diagnostic_sock
        while udp is not None and not self._stopping.is_set():
            try:
                packet, endpoint = udp.recvfrom(128)
                response = reply_challenge(packet, endpoint[0], self.room_token)
                if response:
                    udp.sendto(response, endpoint)
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self):
        if self._diagnostic_sock is not None:
            self._diagnostic_sock.close()
            self._diagnostic_sock = None
        super().stop()
        if self._diagnostic_thread is not None:
            self._diagnostic_thread.join(timeout=2)
            self._diagnostic_thread = None
