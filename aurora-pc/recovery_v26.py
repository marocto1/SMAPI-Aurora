"""Aurora Recovery v2.6 — verify old ZIP and restore ONLY into a NEW isolated profile.

No app-private Android writes, no Stardew Saves restoration, no overwriting old
PC Mods or profiles. The old source archive is treated as untrusted. Rebuilds
the exact versioned v2.2 archive into an atomically published new PC mod profile.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import os
import re
import shutil
import tempfile
import zipfile

import aurora_core as core
import safety_v22

MAX_FILES = 10000
MAX_BYTES = 1024 * 1024 * 1024
MAX_ENTRY = 512 * 1024 * 1024
MAX_MANIFEST = 4 * 1024 * 1024
HEX64 = re.compile(r"^[a-f0-9]{64}$")
WINDOWS_RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)


def _safe_rel(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 1000:
        raise ValueError("Invalid backup entry")
    if "\\" in value or ":" in value or value.startswith("/") or "\x00" in value:
        raise ValueError("Unsafe archive pathname")
    parts = value.split("/")
    for part in parts:
        if (part in (".", "..", "") or part.endswith(" ") or
            part.endswith(".") or WINDOWS_RESERVED.fullmatch(part)):
            raise ValueError("Unsafe Windows path component")
    if len(parts) > 40:
        raise ValueError("Path exceeds safe depth")
    return value


def preview_archive(archive: Path) -> list[dict[str, object]]:
    """Read metadata only; do NOT extract. Exhaustive layout and bomb gates."""
    if not archive.is_file() or archive.stat().st_size > MAX_BYTES:
        raise ValueError("No ZIP or archive too large")
    with zipfile.ZipFile(archive) as z:
        records = z.infolist()
        if len(records) > MAX_FILES + 1:
            raise ValueError("Too many ZIP entries")
        seen = set()
        info_by_name = {}
        payload_bytes = 0
        for item in records:
            if item.is_dir() or ((item.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("Directory/symlink ZIP entries are not accepted")
            path = _safe_rel(item.filename)
            casekey = path.casefold()
            if casekey in seen:
                raise ValueError("Duplicate or case-colliding ZIP entries")
            seen.add(casekey)
            if item.file_size > MAX_ENTRY and path != safety_v22.MANIFEST:
                raise ValueError("Individual entry too large")
            payload_bytes += item.file_size
            if payload_bytes > MAX_BYTES + MAX_MANIFEST:
                raise ValueError("ZIP expands past size cap")
            info_by_name[path] = item
        meta_info = info_by_name.get(safety_v22.MANIFEST)
        if not meta_info or meta_info.file_size > MAX_MANIFEST:
            raise ValueError("Missing/oversized Aurora manifest")
        manifest = json.loads(z.read(meta_info))
        if not isinstance(manifest, dict) or manifest.get("schema") != "aurora-pc-mod-backup/v1":
            raise ValueError("Not an Aurora PC mod-profile backup")
        rows = manifest.get("files")
        if not isinstance(rows, list) or not rows or len(rows) > MAX_FILES:
            raise ValueError("Backup lists no files or too many files")
        declared, result, total = set(), [], 0
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Invalid manifest row")
            path = _safe_rel(row.get("path"))
            casekey = path.casefold()
            if path == safety_v22.MANIFEST or casekey in declared:
                raise ValueError("Invalid/duplicate manifest entry")
            declared.add(casekey)
            length = row.get("bytes")
            digest = row.get("sha256")
            if type(length) is not int or length < 0 or length > MAX_ENTRY or (
                not isinstance(digest, str) or not HEX64.fullmatch(digest)
            ):
                raise ValueError("Invalid declared size/digest")
            info = info_by_name.get(path)
            if info is None or info.file_size != length:
                raise ValueError("Declared file does not match ZIP")
            total += length
            if total > MAX_BYTES:
                raise ValueError("Backup exceeds 1 GiB unpacked")
            result.append({"path": path, "bytes": length, "sha256": digest})
        if set(info_by_name) != {row["path"] for row in result} | {safety_v22.MANIFEST}:
            raise ValueError("Unlisted entry in ZIP")
        return result


def restore_new_profile(archive: Path, profile_name: str,
                        root: Path | None = None) -> Path:
    """Commit only when every byte matches its expected digest; never overwrite."""
    if profile_name == "Default":
        raise ValueError("Restoration to live Default profile is forbidden")
    dest = core.profile_folder(profile_name, root)
    if dest.parent.exists():
        raise FileExistsError("Choose a NEW profile name; existing files are never overwritten")
    rows = preview_archive(archive)
    profiles = dest.parent.parent
    profiles.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".aurora-recovery-", dir=profiles))
    staged_mods = stage / "Mods"
    staged_mods.mkdir()
    try:
        with zipfile.ZipFile(archive) as z:
            for row in rows:
                relative = PurePosixPath(row["path"])
                target = staged_mods.joinpath(*relative.parts)
                if not target.resolve().is_relative_to(staged_mods.resolve()):
                    raise ValueError("Target escapes isolated staging directory")
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                count = 0
                with z.open(row["path"], "r") as source, target.open("xb") as output:
                    while True:
                        block = source.read(1024 * 1024)
                        if not block:
                            break
                        count += len(block)
                        if count > row["bytes"]:
                            raise ValueError("ZIP expands beyond manifest")
                        digest.update(block)
                        output.write(block)
                if count != row["bytes"] or digest.hexdigest() != row["sha256"]:
                    raise ValueError("Backup content failed SHA-256 verification")
        if dest.parent.exists():
            raise FileExistsError("Profile was created while restoring; refuse overwrite")
        os.rename(stage, dest.parent)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return dest
