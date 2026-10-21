"""Aurora Workshop 3.0: official mod pages and local dependency preflight.

No Nexus scraping, token, CDN mirroring, unsigned auto-updates or mods rewriting.
The only direct ZIP in Android Aurora remains the first-party pinned smoke mod.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any
import aurora_core as core

OFFICIAL_SOURCES = (
    ("Content Patcher", "Framework", "https://www.nexusmods.com/stardewvalley/mods/1915",
     "Pathoschild.ContentPatcher"),
    ("Generic Mod Config Menu", "User Interface",
     "https://www.nexusmods.com/stardewvalley/mods/5098",
     "spacechase0.GenericModConfigMenu"),
    ("Stardew Valley Expanded", "World Expansion",
     "https://www.nexusmods.com/stardewvalley/mods/3753", ""),
    ("Automate", "Automation", "https://www.nexusmods.com/stardewvalley/mods/1063",
     "Pathoschild.Automate"),
    ("Lookup Anything", "Tools", "https://www.nexusmods.com/stardewvalley/mods/541",
     "Pathoschild.LookupAnything"),
    ("NPC Map Locations", "Interface", "https://www.nexusmods.com/stardewvalley/mods/239",
     "Bouhm.NPCMapLocations"),
)


def read_manifest(folder: Path) -> dict[str, Any] | None:
    item = folder / "manifest.json"
    try:
        if item.is_symlink() or not item.is_file() or item.stat().st_size > 128000:
            return None
        with item.open(encoding="utf-8-sig") as stream:
            record = json.load(stream)
        if not isinstance(record, dict) or not isinstance(record.get("UniqueID"), str):
            return None
        return record
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def compare_numeric_version(actual: str, minimum: str) -> bool | None:
    """Compare numeric release strings only; unknown prerelease -> manual check."""
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,4}", str(actual)):
        return None
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,4}", str(minimum)):
        return None
    a=[int(n) for n in actual.split(".")]
    b=[int(n) for n in minimum.split(".")]
    n=max(len(a),len(b));a.extend([0]*(n-len(a)));b.extend([0]*(n-len(b)))
    return a>=b


def check_dependencies(game: Path, profile: str = "Default",
                       root: Path | None = None) -> list[dict[str, Any]]:
    directory = core.mods_directory(game,profile,root)
    if not directory.is_dir():
        return []
    profiles=[]
    for folder in directory.iterdir():
        if folder.is_dir() and not folder.is_symlink():
            manifest=read_manifest(folder)
            if manifest:
                profiles.append(manifest)
    installed={
        m["UniqueID"].casefold():str(m.get("Version","?"))
        for m in profiles if isinstance(m.get("UniqueID"),str)
    }
    notices=[]
    for m in profiles:
        deps=list(m.get("Dependencies",[])) if isinstance(m.get("Dependencies"),list) else []
        content=m.get("ContentPackFor")
        if isinstance(content,dict) and isinstance(content.get("UniqueID"),str):
            deps.append({"UniqueID":content["UniqueID"],"IsRequired":True})
        for dep in deps[:100]:
            if not isinstance(dep,dict) or not isinstance(dep.get("UniqueID"),str):
                continue
            if dep.get("IsRequired",True) is False:
                continue
            required=dep["UniqueID"]
            actual=installed.get(required.casefold())
            minimum=dep.get("MinimumVersion")
            reason=None
            if actual is None: reason="missing"
            elif isinstance(minimum,str):
                ok=compare_numeric_version(actual,minimum)
                if ok is False:reason="too-old"
                if ok is None:reason="check-manually"
            if reason:
                notices.append({
                    "mod":str(m.get("Name",m["UniqueID"]))[:100],
                    "requires":required[:140],
                    "minimum":str(minimum or "")[:80],
                    "installed":actual or "",
                    "reason":reason,
                })
    return notices[:300]
