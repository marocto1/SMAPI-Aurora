#!/usr/bin/env python3
"""Validate a private, lawfully extracted Android game reference bundle.

The archive is *compile-time only*. This tool never downloads games, alters
installed-game signature checks, or writes game assemblies to GitHub sources.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import zipfile

REQUIRED = frozenset({
    "StardewValley.dll",
    "StardewValley.GameData.dll",
    "BmFont.dll",
    "Lidgren.Network.dll",
    "xTile.dll",
})
MAX_ZIP_BYTES = 175 * 1024 * 1024
MAX_FILE_BYTES = 90 * 1024 * 1024
MAX_TOTAL_BYTES = 280 * 1024 * 1024
MAX_RATIO = 350

class InvalidReferences(ValueError):
    pass


def safe_entries(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    infos = archive.infolist()
    if len(infos) != len(REQUIRED):
        raise InvalidReferences(
            f"Expected exactly {len(REQUIRED)} DLLs, found {len(infos)} ZIP entries"
        )
    found: dict[str, zipfile.ZipInfo] = {}
    total = 0
    for entry in infos:
        name = entry.filename
        if "\\" in name or name.startswith("/") or name.count(":") or "\x00" in name:
            raise InvalidReferences("Unsafe path in reference archive")
        parts = name.split("/")
        if len(parts) == 1:
            base = parts[0]
        elif len(parts) == 2 and parts[0] == "DependenciesDll":
            base = parts[1]
        else:
            raise InvalidReferences(
                "DLLs must be in the archive root or DependenciesDll/"
            )
        if entry.is_dir() or base not in REQUIRED:
            raise InvalidReferences("Unexpected directory or file: " + name)
        mode = (entry.external_attr >> 16)
        if stat.S_IFMT(mode) == stat.S_IFLNK:
            raise InvalidReferences("Symbolic links are not accepted")
        if base in found:
            raise InvalidReferences("Duplicate DLL name: " + base)
        if (entry.file_size < 512 or entry.file_size > MAX_FILE_BYTES
                or entry.compress_size == 0
                or entry.file_size > max(1, entry.compress_size) * MAX_RATIO):
            raise InvalidReferences("Invalid size or compression ratio: " + base)
        total += entry.file_size
        if total > MAX_TOTAL_BYTES:
            raise InvalidReferences("Uncompressed archive limit exceeded")
        found[base] = entry
    if frozenset(found) != REQUIRED:
        raise InvalidReferences(
            "Missing required DLLs: " + ", ".join(sorted(REQUIRED - found.keys()))
        )
    return found


def validate_pe_header(stream) -> None:
    header = stream.read(4096)
    if len(header) < 0x100 or header[:2] != b"MZ":
        raise InvalidReferences("A reference DLL is not a Windows PE/.NET assembly")
    pe_offset = int.from_bytes(header[0x3c:0x40], "little")
    if pe_offset < 64 or pe_offset + 24 > len(header):
        raise InvalidReferences("Invalid PE header offset")
    if header[pe_offset:pe_offset + 4] != b"PE\x00\x00":
        raise InvalidReferences("Missing PE signature")
    optional_size = int.from_bytes(header[pe_offset + 20:pe_offset + 22], "little")
    optional_start = pe_offset + 24
    magic = int.from_bytes(header[optional_start:optional_start + 2], "little")
    if magic not in (0x10b, 0x20b):
        raise InvalidReferences("Invalid PE optional header")
    directory_offset = 96 if magic == 0x10b else 112
    cli_entry = optional_start + directory_offset + 14 * 8
    if (optional_size < directory_offset + 15 * 8 or cli_entry + 8 > len(header)):
        raise InvalidReferences("PE has no .NET CLI metadata directory")
    cli_rva = int.from_bytes(header[cli_entry:cli_entry + 4], "little")
    cli_size = int.from_bytes(header[cli_entry + 4:cli_entry + 8], "little")
    if cli_rva == 0 or cli_size < 72:
        raise InvalidReferences("PE is not a managed .NET assembly")


def extract_private_references(archive_path: Path, destination: Path, *,
                               dry_run: bool = False) -> dict[str, int]:
    if not archive_path.is_file() or archive_path.stat().st_size > MAX_ZIP_BYTES:
        raise InvalidReferences("Private reference archive missing or too large")
    if destination.exists():
        raise InvalidReferences("Destination already exists; refusing to overwrite it")
    stats = {}
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            entries = safe_entries(archive)
            for name, info in entries.items():
                with archive.open(info) as source:
                    validate_pe_header(source)
                stats[name] = info.file_size
            if dry_run:
                return stats
            # Write to an ignored temp destination and atomically expose only if
            # all five inputs have passed the exact structural preflight.
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp_dir = Path(tempfile.mkdtemp(
                prefix=".aurora-ref-check-", dir=destination.parent))
            try:
                for name, info in entries.items():
                    with archive.open(info) as source, (temp_dir / name).open("xb") as output:
                        copied = shutil.copyfileobj(source, output, length=128 * 1024)
                    if (temp_dir / name).stat().st_size != info.file_size:
                        raise InvalidReferences("Copied DLL size mismatch: " + name)
                    (temp_dir / name).chmod(0o600)
                temp_dir.rename(destination)
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
    except (zipfile.BadZipFile, RuntimeError) as error:
        raise InvalidReferences("Malformed private reference ZIP") from error
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", type=Path)
    ap.add_argument("--target", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        sizes = extract_private_references(
            args.archive.resolve(), args.target.resolve(), dry_run=args.check)
    except (InvalidReferences, OSError) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        return 1
    print("PASS: complete 5-DLL private compile reference set; game files will not be packaged")
    for filename in sorted(sizes):
        print(f"  {filename}: {sizes[filename]} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
