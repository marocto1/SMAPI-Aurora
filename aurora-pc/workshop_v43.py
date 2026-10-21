"""Aurora Workshop 5.0: safe profile-only metadata export/compare.

Does not package mod DLLs, redistribute Nexus files or install dependencies.
Report is explicitly untrusted metadata supplied by another user.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import aurora_core as core
import workshop_v25 as workshop

SCHEMA="aurora-workshop-profile/v1"
MAX_BYTES=65536
ID=re.compile(r"^[A-Za-z0-9_.-]{1,140}$")
VER=re.compile(r"^[^\x00-\x1f]{1,80}$")


def profile_report(game: Path, profile: str, root: Path|None=None) -> dict:
    mods=core.get_mods(game,profile,root)
    if len(mods)>180:
        raise ValueError("Too many mods for portable metadata report")
    seen=set()
    entries=[]
    for mod in mods:
        key=mod["id"].strip()
        version=mod["version"].strip()
        if not ID.fullmatch(key) or not VER.fullmatch(version) or key.casefold() in seen:
            raise ValueError("Invalid or duplicate SMAPI mod manifest")
        seen.add(key.casefold())
        entries.append({"id":key,"version":version})
    issues=workshop.check_dependencies(game,profile,root)
    return {"schema":SCHEMA,
            "origin":"Aurora SMAPI PC metadata (NOT proof of runtime compatibility)",
            "mods":sorted(entries,key=lambda x:x["id"].casefold()),
            "issues":[{"mod":str(x["mod"])[:100],
                       "dependency":str(x["requires"])[:140],
                       "reason":str(x["reason"])[:40]} for x in issues[:180]],
            "note":"No mod archives, executable paths, user data, passwords or saves"}


def validate_report(data: object) -> dict:
    if not isinstance(data,dict) or data.get("schema")!=SCHEMA:
        raise ValueError("Unsupported profile report")
    mods=data.get("mods")
    if not isinstance(mods,list) or len(mods)>180:
        raise ValueError("Too many mods")
    seen=set()
    for row in mods:
        if not isinstance(row,dict):
            raise ValueError("Malformed mod entry")
        mid=row.get("id")
        version=row.get("version")
        if not isinstance(mid,str) or not ID.fullmatch(mid):
            raise ValueError("Invalid mod identifier")
        if not isinstance(version,str) or not VER.fullmatch(version):
            raise ValueError("Invalid version")
        if mid.casefold() in seen:
            raise ValueError("Duplicate mod ID")
        seen.add(mid.casefold())
    return data


def export_report(data: dict, destination: Path) -> None:
    validate_report(data)
    payload=json.dumps(data,ensure_ascii=False,indent=2).encode("utf-8")
    if len(payload)>MAX_BYTES:
        raise ValueError("Report exceeds 64 KiB")
    # Exclusive new file. Never overwrites an existing report.
    with destination.open("xb") as handle:
        handle.write(payload)


def read_report(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size>MAX_BYTES:
        raise ValueError("Invalid or oversized report")
    with path.open("r",encoding="utf-8") as handle:
        result=json.load(handle)
    return validate_report(result)


def compare_reports(local: dict, peer: dict) -> dict:
    left=validate_report(local)
    right=validate_report(peer)
    a={x["id"].casefold():x["version"] for x in left["mods"]}
    b={x["id"].casefold():x["version"] for x in right["mods"]}
    return {
        "local_only":sorted(set(a)-set(b)),
        "peer_only":sorted(set(b)-set(a)),
        "version_mismatch":{x:{"local":a[x],"peer":b[x]}
                            for x in sorted(set(a)&set(b)) if a[x]!=b[x]},
        "gameplay_verified":False,
    }


def format_comparison(diff: dict)->str:
    chunks=[
        f"Только у тебя: {len(diff['local_only'])}",
        f"Только у друга: {len(diff['peer_only'])}",
        f"Разные версии: {len(diff['version_mismatch'])}",
        "Метаданные не подтверждают работу DLL в Android или сетевую игру."
    ]
    for mid in diff["local_only"][:20]: chunks.append("+ "+mid+" только локально")
    for mid in diff["peer_only"][:20]: chunks.append("- "+mid+" только у друга")
    for mid,row in list(diff["version_mismatch"].items())[:25]:
        chunks.append("! "+mid+" "+row["local"]+" / "+row["peer"])
    return "\n".join(chunks)
