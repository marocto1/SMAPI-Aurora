#!/usr/bin/env python3
"""Validate and stage privately supplied Android game compilation references.

Only the three explicit DLL filenames are accepted, from the archive root or
DependenciesDll/. Never commits or uploads game binaries.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import zipfile

REQUIRED = frozenset({
    "StardewValley.dll",
    "StardewValley.GameData.dll",
    "MonoGame.Framework.dll",
})
MAX_PER_FILE = 200 * 1024 * 1024
MAX_TOTAL = 400 * 1024 * 1024


def stage_references(archive_file: Path, target_dir: Path) -> list[str]:
    if not archive_file.is_file():
        raise FileNotFoundError(f"Private references archive not found: {archive_file}")

    with zipfile.ZipFile(archive_file) as archive:
        found: dict[str, zipfile.ZipInfo] = {}
        total = 0
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            name = entry.filename
            parts = name.split("/")
            # Refuse traversal, absolute paths, platform separators and extra
            # payload; the files are never executed during staging.
            if "\\" in name or (
                len(parts) != 1
                and not (len(parts) == 2 and parts[0] == "DependenciesDll")
            ):
                raise ValueError(f"Unexpected archive entry: {name}")
            filename = parts[-1]
            if filename not in REQUIRED or filename in found:
                raise ValueError(f"Unexpected or duplicated DLL: {name}")
            if entry.file_size <= 0 or entry.file_size > MAX_PER_FILE:
                raise ValueError(f"Invalid DLL file size: {name}")
            total += entry.file_size
            if total > MAX_TOTAL:
                raise ValueError("Uncompressed reference DLLs exceed safety limit")
            found[filename] = entry

        missing = REQUIRED.difference(found)
        if missing:
            raise ValueError("Missing required compilation references: " + ", ".join(sorted(missing)))

        target_dir.mkdir(parents=True, exist_ok=True)
        for filename in sorted(REQUIRED):
            destination = target_dir / filename
            # Copy via a temporary file and replace only after successful
            # extraction, so incomplete downloads don't masquerade as DLLs.
            tmp = target_dir / (filename + ".part")
            try:
                with archive.open(found[filename]) as src, tmp.open("wb") as out:
                    shutil.copyfileobj(src, out, length=1024 * 1024)
                if tmp.stat().st_size != found[filename].file_size:
                    raise ValueError(f"Truncated reference file: {filename}")
                tmp.replace(destination)
            finally:
                tmp.unlink(missing_ok=True)
    return sorted(REQUIRED)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage private game DLL compilation references")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    filenames = stage_references(args.archive, args.target)
    print("PASS: privately staged " + ", ".join(filenames))


if __name__ == "__main__":
    main()
