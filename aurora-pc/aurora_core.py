"""Aurora SMAPI PC: offline-first Windows game/mod profile manager and LAN status service.

Uses user's existing Stardew Valley and SMAPI files, never includes commercial
game assets and never downloads the game. MIT? No: part of GPL-3.0 project.
"""
from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import socketserver
import subprocess
import tempfile
import threading
from typing import Any
import zipfile

VERSION = "1.6.0-preview.1"
STATUS_PORT = 24643  # Aurora-only discovery; Stardew's UDP game port is 24642.
SCHEMA = "aurora-coop-status/v1"
PROFILE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,39}$")
MAX_ARCHIVE = 128 * 1024 * 1024
MAX_UNPACKED = 512 * 1024 * 1024
MAX_ENTRY = 128 * 1024 * 1024
MAX_FILES = 4000


def data_root() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    return Path(base if base else Path.home() / ".local" / "share") / "AuroraSMAPIPC"


def settings_file(root: Path | None = None) -> Path:
    return (root or data_root()) / "settings.json"


def save_settings(values: dict[str, Any], root: Path | None = None) -> None:
    dest = settings_file(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    safe = {
        "game_directory": str(values.get("game_directory", "")),
        "profile": str(values.get("profile", "Default")),
    }
    safe["game_version"] = str(values.get("game_version", ""))[:48]
    safe["smapi_version"] = str(values.get("smapi_version", ""))[:48]
    if safe["profile"] != "Default" and not PROFILE_NAME.fullmatch(safe["profile"]):
        raise ValueError("Invalid profile")
    fd, tmp = tempfile.mkstemp(prefix=".aurora-", dir=dest.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as writer:
            json.dump(safe, writer, ensure_ascii=False, indent=2)
            writer.flush()
            os.fsync(writer.fileno())
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_settings(root: Path | None = None) -> dict[str, str]:
    dest = settings_file(root)
    if not dest.is_file():
        return {"game_directory": "", "profile": "Default", "game_version": "", "smapi_version": ""}
    try:
        if dest.stat().st_size > 16384:
            raise ValueError("Settings too large")
        with dest.open(encoding="utf-8") as file:
            raw = json.load(file)
        if not isinstance(raw, dict):
            raise ValueError("Bad settings")
        game = raw.get("game_directory", "")
        profile = raw.get("profile", "Default")
        if not isinstance(game, str) or not isinstance(profile, str):
            raise ValueError("Invalid settings")
        if profile != "Default" and not PROFILE_NAME.fullmatch(profile):
            raise ValueError("Invalid profile")
        g = raw.get("game_version", "")
        sm = raw.get("smapi_version", "")
        if not isinstance(g, str) or not isinstance(sm, str):
            raise ValueError("Invalid declared versions")
        return {"game_directory": game, "profile": profile,
                "game_version": g[:48], "smapi_version": sm[:48]}
    except (OSError, ValueError, json.JSONDecodeError):
        return {"game_directory": "", "profile": "Default"}


def detect_game() -> Path | None:
    candidates = []
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if base:
            candidates += [
                Path(base) / "Steam" / "steamapps" / "common" / "Stardew Valley",
                Path(base) / "GOG Galaxy" / "Games" / "Stardew Valley",
            ]
    candidates += [
        Path("C:/GOG Games/Stardew Valley"),
        Path("D:/SteamLibrary/steamapps/common/Stardew Valley"),
    ]
    for item in candidates:
        if (item / "Stardew Valley.exe").is_file() or (item / "StardewModdingAPI.exe").is_file():
            return item
    return None


def launch_game(game: Path, use_smapi: bool, profile: str = "Default",
                root: Path | None = None, *, spawn=subprocess.Popen):
    directory = game.expanduser().resolve()
    file = directory / ("StardewModdingAPI.exe" if use_smapi else "Stardew Valley.exe")
    if not file.is_file():
        raise FileNotFoundError(f"Executable not found: {file.name}. Install game/SMAPI first.")
    args = [str(file)]
    if use_smapi and profile != "Default":
        folder = profile_folder(profile, root)
        folder.mkdir(parents=True, exist_ok=True)
        args += ["--mods-path", str(folder)]
    return spawn(args, cwd=str(directory))


def profile_folder(name: str, root: Path | None = None) -> Path:
    if name == "Default":
        raise ValueError("Default profile uses game's Mods folder")
    if not PROFILE_NAME.fullmatch(name):
        raise ValueError("Invalid profile name")
    return (root or data_root()) / "profiles" / name / "Mods"


def available_profiles(root: Path | None = None) -> list[str]:
    folder = (root or data_root()) / "profiles"
    if not folder.exists():
        return ["Default"]
    names = sorted(
        p.name for p in folder.iterdir()
        if p.is_dir() and not p.is_symlink() and PROFILE_NAME.fullmatch(p.name)
    )
    return ["Default"] + names


def mods_directory(game: Path, profile: str = "Default", root: Path | None = None) -> Path:
    return game / "Mods" if profile == "Default" else profile_folder(profile, root)


def get_mods(game: Path, profile: str = "Default",
             root: Path | None = None) -> list[dict[str, str]]:
    base = mods_directory(game, profile, root)
    results: list[dict[str, str]] = []
    if not base.is_dir():
        return results
    for manifest in base.glob("*/manifest.json"):
        try:
            if manifest.is_symlink() or manifest.stat().st_size > 1_000_000:
                continue
            with manifest.open(encoding="utf-8-sig") as f:
                entry = json.load(f)
            if not isinstance(entry, dict):
                continue
            results.append({
                "id": str(entry.get("UniqueID", ""))[:140],
                "name": str(entry.get("Name", manifest.parent.name))[:140],
                "version": str(entry.get("Version", "?"))[:80],
                "folder": str(manifest.parent),
            })
        except (OSError, ValueError, UnicodeError):
            continue
    return sorted(results, key=lambda r: r["name"].casefold())


def import_zip(archive: Path, game: Path, profile: str = "Default",
               root: Path | None = None) -> Path:
    """Validate a single SMAPI-mod archive, install atomically, NEVER overwrite.

    Does not execute mod code. Replaces neither saves nor another mod. The user
    explicitly selects ZIP and destination in Aurora's GUI.
    """
    archive = archive.resolve()
    if not archive.is_file() or archive.stat().st_size > MAX_ARCHIVE:
        raise ValueError("ZIP absent or exceeds size limit (128 MB)")
    destination = mods_directory(game, profile, root)
    destination.mkdir(parents=True, exist_ok=True)
    files: list[tuple[zipfile.ZipInfo, str]] = []
    seen: set[str] = set()
    total = 0
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            parts = PurePosixPath(name).parts
            if (not name or name.startswith("/") or ":" in name or
                any(p in (".", "..") for p in parts) or
                "\x00" in name or len(name) > 1024):
                raise ValueError("Unsafe ZIP filename")
            lowered = name.rstrip("/").casefold()
            if lowered in seen:
                raise ValueError("Duplicate ZIP filename")
            seen.add(lowered)
            file_type = (info.external_attr >> 16) & 0o170000
            if file_type == 0o120000:
                raise ValueError("ZIP symlinks are not permitted")
            if info.is_dir():
                continue
            if info.file_size > MAX_ENTRY:
                raise ValueError("Oversized ZIP entry")
            total += info.file_size
            if total > MAX_UNPACKED or len(files) >= MAX_FILES:
                raise ValueError("ZIP exceeds safe extraction limit")
            files.append((info, name))
        manifests = [name for _, name in files if name.lower().endswith("/manifest.json") or
                     name.lower() == "manifest.json"]
        if len(manifests) != 1:
            raise ValueError("ZIP must contain exactly one SMAPI manifest.json")
        manifest = manifests[0]
        prefix = manifest[:-len("manifest.json")]
        if any(not name.startswith(prefix) for _, name in files):
            raise ValueError("ZIP must contain only one mod, not a bundle")
        with z.open(manifest) as reader:
            raw = reader.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError("Manifest too large")
            metadata = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(metadata, dict) or not all(
            isinstance(metadata.get(k), str) and metadata[k].strip()
            for k in ("Name", "UniqueID", "Version")
        ):
            raise ValueError("Not a valid SMAPI mod manifest")
        # Folder names derive from publisher's UniqueID, not an untrusted ZIP path.
        identifier = re.sub(r"[^A-Za-z0-9._-]+", "_", metadata["UniqueID"])[:80]
        if not identifier or identifier in (".", ".."):
            raise ValueError("Invalid mod identifier")
        target = destination / identifier
        if target.exists():
            raise FileExistsError(f"Already installed: {identifier}. No automatic overwrite.")
        stage = Path(tempfile.mkdtemp(prefix=".aurora-install-", dir=destination))
        try:
            extracted = 0
            for info, name in files:
                relative = name[len(prefix):]
                if not relative:
                    continue
                path = stage.joinpath(*PurePosixPath(relative).parts)
                if not path.resolve().is_relative_to(stage.resolve()):
                    raise ValueError("ZIP path escapes staging directory")
                path.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as reader, path.open("xb") as writer:
                    while True:
                        chunk = reader.read(65536)
                        if not chunk:
                            break
                        extracted += len(chunk)
                        if extracted > MAX_UNPACKED:
                            raise ValueError("Expanded ZIP exceeds limit")
                        writer.write(chunk)
            stage.rename(target)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return target


def network_ipv4() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 80))  # route selection only, sends no UDP data
            ip = sock.getsockname()[0]
            return ip
    except OSError:
        return "Не удалось определить — проверь Wi-Fi или ipconfig"


def status_data(game: Path, profile: str) -> dict[str, str]:
    return {
        "schema": SCHEMA,
        "launcher": "Aurora SMAPI PC",
        "launcher_version": VERSION,
        "platform": "windows",
        "game_installed": str((game / "Stardew Valley.exe").exists()).lower(),
        "smapi_installed": str((game / "StardewModdingAPI.exe").exists()).lower(),
        "profile": profile,
        "note": "Aurora status only: NOT proof of a Stardew multiplayer session",
    }


class _LANServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _StatusHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            ip = ipaddress.ip_address(self.client_address[0])
            if not (ip.is_private or ip.is_loopback):
                return
            body = json.dumps(self.server.status_callback(), ensure_ascii=False)
            if len(body) > 4096:
                return
            self.wfile.write((body + "\n").encode("utf-8"))
        except (OSError, ValueError):
            return


class LANStatusService:
    def __init__(self, game: Path, profile: str = "Default",
                 port: int = STATUS_PORT):
        self.game = game
        self.profile = profile
        self.port = port
        self.server: _LANServer | None = None
        self.worker: threading.Thread | None = None

    def start(self) -> None:
        if self.server is not None:
            return
        self.server = _LANServer(("0.0.0.0", self.port), _StatusHandler)
        self.server.status_callback = lambda: status_data(self.game, self.profile)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.worker = None
