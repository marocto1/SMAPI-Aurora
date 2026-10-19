#!/usr/bin/env python3
"""Replace *one* compiled Android interop library in Aurora's complete SMAPI APK.

The original APK is checksum-pinned in CI. The only executable change is
lib/arm64-v8a/lib_JunimoGate.Android.dll.so, whose embedded PE must equal
the freshly compiled patched Android boundary assembly. No game DLLs included.
"""
from pathlib import Path
import argparse
import hashlib
import sys
import zipfile

TARGET="lib/arm64-v8a/lib_JunimoGate.Android.dll.so"
COMMERCIAL={"stardewvalley.dll","stardewvalley.gamedata.dll",
            "lidgren.network.dll","xtile.dll","bmfont.dll"}
EXPECTED_ORIGINAL_MIN=100_000_000

def make(src:Path, patched_dso:Path, dest:Path):
    if dest.exists():raise ValueError("Refusing to overwrite existing APK")
    if src.stat().st_size<EXPECTED_ORIGINAL_MIN:raise ValueError("Original APK unexpectedly tiny")
    from rewrap_managed_elf import u16,u32,u64
    replacement=patched_dso.read_bytes()
    if replacement[:4]!=b"\x7fELF" or u16(replacement,18)!=183:
        raise ValueError("Replacement is not ARM64 ELF")
    with zipfile.ZipFile(src) as read, zipfile.ZipFile(dest,"w") as out:
        entries=read.infolist()
        if len({x.filename for x in entries})!=len(entries):
            raise ValueError("Duplicate APK zip entries")
        if sum(x.filename==TARGET for x in entries)!=1:
            raise ValueError("Original APK missing a unique managed ARM64 Android bridge")
        if read.testzip() is not None:
            raise ValueError("Original APK failed CRC verification")
        for info in entries:
            name=info.filename
            if name.startswith("META-INF/") and name.upper().endswith((".RSA",".SF","MANIFEST.MF")):
                continue  # invalid old V1 signature, re-signed by apksigner
            payload=replacement if name==TARGET else read.read(info)
            out.writestr(info,payload)
    verify(src,dest)

def verify(src:Path, dest:Path):
    with zipfile.ZipFile(src) as a,zipfile.ZipFile(dest) as b:
        a_files={x.filename:x for x in a.infolist() if not x.filename.startswith("META-INF/")}
        b_files={x.filename:x for x in b.infolist() if not x.filename.startswith("META-INF/")}
        if a_files.keys()!=b_files.keys():raise ValueError("Payload names mismatch")
        if b.testzip() is not None:raise ValueError("Generated APK CRC failure")
        modified=[]
        for name in a_files:
            if a_files[name].CRC!=b_files[name].CRC or a.read(name)!=b.read(name):
                modified.append(name)
            if name.lower().rsplit("/",1)[-1] in COMMERCIAL:
                raise ValueError("Proprietary game code in APK")
        if modified != [TARGET]:
            raise ValueError("Unexpected APK code/resource changes: "+repr(modified[:30]))
        if not any("StardewModdingAPI.dll" in x for x in b_files):
            raise ValueError("SMAPI missing from APK")
        for required in (
            "lib/arm64-v8a/lib_JunimoGate.GameHost.dll.so",
            "classes3.dex",
            "assets/smapi-managed/StardewModdingAPI.dll",
        ):
            if required not in b_files:raise ValueError("Missing host/launcher: "+required)
    print("PASS: exactly one rebuilt Android boundary ELF changed")
    print("PASS: intact GameHost, original SMAPI, launcher, resources, native runtime and licenses")
    print("NOT device tested, not a guarantee that all Android installations can prepare or run")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original",type=Path)
    p.add_argument("recompiled_elf",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--verify-only",action="store_true")
    args=p.parse_args()
    try:
        if args.verify_only: verify(args.original,args.output)
        else: make(args.original,args.recompiled_elf,args.output)
    except (OSError,ValueError,zipfile.BadZipFile) as e:
        print("BLOCKED:",e,file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":main()
