"""Aurora PC v2.2: verified, non-destructive mod-profile backup only.

No restore and never reads game saves. ZIP is written to a new user-selected
path, verified by SHA-256 on read-back and atomically replaced.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

MAX_FILES=10000
MAX_BYTES=1024*1024*1024
MAX_SINGLE=512*1024*1024
MANIFEST="aurora-profile-manifest.json"


def backup_profile(mods: Path, output: Path) -> int:
    mods=mods.resolve()
    output=output.resolve()
    if not mods.is_dir():
        raise ValueError("Mods folder does not exist")
    if output.is_relative_to(mods) or output==mods:
        raise ValueError("Backup output must be outside the Mods folder")
    if output.exists():
        raise FileExistsError("Backup path already exists; existing files are never overwritten")
    if output.suffix.lower()!=".zip":
        raise ValueError("Choose a new .zip file")
    files=[]
    amount=0
    for item in mods.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlink inside mod profile; backup refused")
        if not item.is_file():
            continue
        if len(files)>=MAX_FILES or item.stat().st_size>MAX_SINGLE:
            raise ValueError("Profile exceeds safe file limit")
        amount+=item.stat().st_size
        if amount>MAX_BYTES:
            raise ValueError("Mods profile exceeds 1 GiB limit")
        rel=item.relative_to(mods).as_posix()
        if rel==MANIFEST or not rel or "\x00" in rel:
            raise ValueError("Unsafe mod path")
        files.append((item,rel))
    if not files:
        raise ValueError("Mod profile is empty")
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=".aurora-mod-backup-",suffix=".zip",dir=output.parent)
    os.close(fd)
    try:
        metadata=[]
        with zipfile.ZipFile(temp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for item,rel in files:
                h=hashlib.sha256()
                before=item.stat()
                with item.open("rb") as src, z.open(rel,"w") as dest:
                    while True:
                        chunk=src.read(1024*1024)
                        if not chunk:break
                        h.update(chunk);dest.write(chunk)
                after=item.stat()
                if before.st_size!=after.st_size or before.st_mtime_ns!=after.st_mtime_ns:
                    raise ValueError("A mod changed during backup; close the game first")
                metadata.append({"path":rel,"bytes":before.st_size,"sha256":h.hexdigest()})
            z.writestr(MANIFEST,json.dumps({
                "schema":"aurora-pc-mod-backup/v1","files":metadata},
                ensure_ascii=False))
        # Re-read archive, validate entries and every digest before success.
        with zipfile.ZipFile(temp) as z:
            entry=set(z.namelist())
            if entry!=set(rel for _,rel in files)|{MANIFEST}:
                raise ValueError("Backup contents changed")
            archive_manifest=json.loads(z.read(MANIFEST))
            if archive_manifest.get("schema")!="aurora-pc-mod-backup/v1":
                raise ValueError("Backup manifest changed")
            for row in archive_manifest["files"]:
                h=hashlib.sha256()
                size=0
                with z.open(row["path"]) as data:
                    while True:
                        chunk=data.read(1024*1024)
                        if not chunk:break
                        h.update(chunk);size+=len(chunk)
                if size!=row["bytes"] or h.hexdigest()!=row["sha256"]:
                    raise ValueError("Backup failed integrity check")
        if output.exists():
            raise FileExistsError("Output exists: abort rather than overwrite")
        os.rename(temp,output)
        return len(files)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
