"""Aurora PC v1.8: opt-in LAN discovery and read-only compatibility preflight.

TCP 24643 returns profile metadata; UDP 24644 answers explicit broadcast
probes. Stardew game traffic (UDP 24642) is never touched. No authentication:
enable ONLY on a trusted private LAN; returned mod IDs/versions are visible to
other devices on that LAN while the service is running.
"""
from __future__ import annotations

import ipaddress
import json
from pathlib import Path
import re
import socket
import socketserver
import threading
from typing import Any

import aurora_core as core

VERSION = "1.8.0-preview.1"
SCHEMA = "aurora-coop-status/v2"
UDP_PORT = 24644
TCP_PORT = 24643
DISCOVER_PREFIX = b"AURORA_DISCOVER_V2 "
REPLY_PREFIX = b"AURORA_HERE_V2 "
NONCE = re.compile(rb"^[a-f0-9]{16}$")
VERSION_TEXT = re.compile(r"^[A-Za-z0-9.+_-]{1,48}$")
MAX_MODS = 180


def local_address(ip: str) -> bool:
    try:
        x = ipaddress.ip_address(ip)
        return isinstance(x, ipaddress.IPv4Address) and (
            x.is_loopback or x in ipaddress.ip_network("10.0.0.0/8") or
            x in ipaddress.ip_network("172.16.0.0/12") or
            x in ipaddress.ip_network("192.168.0.0/16")
        )
    except ValueError:
        return False


def declared_version(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if not VERSION_TEXT.fullmatch(value):
        raise ValueError("Use a version such as 1.6.15 or 4.5.2 (48 chars max)")
    return value


def compatibility_status(game: Path, profile: str,
                         game_version: str = "", smapi_version: str = "",
                         *, data_dir: Path | None = None) -> dict[str, Any]:
    # The fields are user-declared, not measured against running game/SMAPI.
    g = declared_version(game_version)
    sm = declared_version(smapi_version)
    mods = core.get_mods(game, profile, data_dir)
    if len(mods) > MAX_MODS:
        raise ValueError("Too many mods to safely publish a compatibility snapshot")
    result = {
        "schema": SCHEMA,
        "launcher": "Aurora SMAPI PC",
        "launcher_version": VERSION,
        "platform": "windows",
        "game_installed": bool((game / "Stardew Valley.exe").is_file()),
        "smapi_installed": bool((game / "StardewModdingAPI.exe").is_file()),
        "game_version": g,
        "smapi_version": sm,
        "version_source": "user-declared (not verified against running game)",
        "mod_source": "selected PC mod profile manifests (not runtime loaded)",
        "mods": [
            {"id": mod["id"], "version": mod["version"]}
            for mod in mods
            if mod["id"].strip()
        ],
        "mod_count": len(mods),
        "profile": profile[:40],
        "note": "Launcher LAN metadata only; NO VPN, game join or UDP farm test"
    }
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > 32000:
        raise ValueError("Compatibility payload too large")
    return result


class _TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _TCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        if not local_address(self.client_address[0]):
            return
        try:
            payload = json.dumps(self.server.provider(), ensure_ascii=False)
            self.request.settimeout(1.5)
            self.wfile.write(payload.encode("utf-8") + b"\n")
        except (ValueError, OSError):
            return


def reply_probe(payload: bytes, source_ip: str) -> bytes | None:
    if not local_address(source_ip) or len(payload) != len(DISCOVER_PREFIX) + 16:
        return None
    if not payload.startswith(DISCOVER_PREFIX):
        return None
    nonce = payload[len(DISCOVER_PREFIX):]
    if not NONCE.fullmatch(nonce):
        return None
    return REPLY_PREFIX + nonce + b" 24643"


class CoopLANService:
    def __init__(self, game: Path, profile: str = "Default",
                 game_version: str = "", smapi_version: str = "",
                 *, tcp_port: int = TCP_PORT, udp_port: int = UDP_PORT,
                 data_dir: Path | None = None):
        self.game = game
        self.profile = profile
        self.game_version = declared_version(game_version)
        self.smapi_version = declared_version(smapi_version)
        self.data_dir = data_dir
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self._tcp: _TCPServer | None = None
        self._udp: socket.socket | None = None
        self._stopping = threading.Event()
        self._threads: list[threading.Thread] = []

    def _snapshot(self) -> dict[str, Any]:
        return compatibility_status(self.game, self.profile, self.game_version,
                                    self.smapi_version, data_dir=self.data_dir)

    def start(self) -> None:
        if self._tcp is not None:
            return
        # Bind both first; if one fails, do not leave a half-started service.
        tcp = _TCPServer(("0.0.0.0", self.tcp_port), _TCPHandler)
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp.bind(("0.0.0.0", self.udp_port))
            udp.settimeout(0.4)
        except Exception:
            udp.close()
            tcp.server_close()
            raise
        tcp.provider = self._snapshot
        self._tcp, self._udp = tcp, udp
        self._stopping.clear()
        self._threads = [
            threading.Thread(target=tcp.serve_forever, name="AuroraTCPStatus",
                             daemon=True),
            threading.Thread(target=self._discovery_loop, name="AuroraUDPDiscovery",
                             daemon=True)
        ]
        for thread in self._threads:
            thread.start()

    def _discovery_loop(self) -> None:
        udp = self._udp
        if udp is None:
            return
        while not self._stopping.is_set():
            try:
                data, endpoint = udp.recvfrom(128)
                answer = reply_probe(data, endpoint[0])
                if answer:
                    udp.sendto(answer, endpoint)
            except socket.timeout:
                continue
            except OSError:
                break

    def stop(self) -> None:
        self._stopping.set()
        if self._udp is not None:
            self._udp.close()
            self._udp = None
        if self._tcp is not None:
            self._tcp.shutdown()
            self._tcp.server_close()
            self._tcp = None
        for thread in self._threads:
            thread.join(timeout=2)
        self._threads.clear()
