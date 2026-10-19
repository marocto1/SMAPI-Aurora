#!/usr/bin/env python3
"""Audit compiled Aurora APK against the pinned upstream binary.

The SMAPI game host and managed/native runtime must be byte identical to the
official JunimoGate v0.3.1 distribution. Only Android resources may differ.
"""
from pathlib import Path
import argparse
import hashlib
import zipfile

CRITICAL_FILE_ENDINGS=(".dex",".so",".dll",".blob",".json")
COMMERCIAL=("stardewvalley.dll","stardewvalley.gamedata.dll","bmfont.dll","lidgren.network.dll","xtile.dll")
MIN_LARGE=50*1024*1024

def check(upstream:Path,derived:Path):
    with zipfile.ZipFile(upstream) as a, zipfile.ZipFile(derived) as b:
        if a.testzip() is not None or b.testzip() is not None:
            raise ValueError("APK CRC verification failed")
        orig=set(a.namelist())
        patched=set(b.namelist())
        # AAPT2 re-encodes/names compiled resources while rebuilding the table.
        # Only framework assets and executable payload must remain unchanged.
        nonresources={x for x in orig if not x.startswith(("META-INF/","res/"))}
        dropped=nonresources-patched
        if dropped:
            raise ValueError("Resource rebuild dropped non-resource payload: "+repr(sorted(dropped)[:18]))
        checked=0
        changed=[]
        for name in sorted(orig):
            lower=name.lower()
            if lower.startswith("meta-inf/"): continue  # re-signing changes signatures
            if (lower.endswith(CRITICAL_FILE_ENDINGS)
                    or lower.startswith(("assemblies/","lib/","assets/smapi","assets/licenses/"))):
                if lower.startswith("res/") and lower.endswith(".xml"):
                    # Resource XML is expected to change.
                    continue
                if name not in patched: raise ValueError("Missing critical binary: "+name)
                if a.getinfo(name).CRC != b.getinfo(name).CRC or a.read(name)!=b.read(name):
                    changed.append(name)
                checked+=1
        if changed:
            raise ValueError("SMAPI/CLR payload modified: "+repr(changed[:25]))
        if checked<50:
            raise ValueError("Too few protected runtime files validated: "+str(checked))
        lib_entries=[n for n in patched if n.startswith("lib/arm64-v8a/") and n.endswith(".so")]
        if not lib_entries:
            raise ValueError("No arm64 native runtime libraries in APK")
        smapi=[n for n in patched if "StardewModdingAPI.dll" in n]
        if not smapi:
            raise ValueError("Bundled SMAPI assembly missing from APK")
        license_notice=[n for n in patched if "license" in n.lower() or "third-party-notices" in n.lower()]
        if len(license_notice)<5: raise ValueError("GPL/LGPL/source notices missing")
        for name in patched:
            if name.lower().rsplit("/",1)[-1] in COMMERCIAL:
                raise ValueError("Paid game assembly embedded in distributed APK: "+name)
        if derived.stat().st_size<MIN_LARGE:
            raise ValueError("Derived APK unexpectedly tiny; SMAPI runtime missing")
    print(f"PASS: {checked} runtime payload files byte-identical; {len(smapi)} SMAPI assemblies; {len(lib_entries)} arm64 libraries")
    print("Note: This verifies archive contents, not on-device launch or game support.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("upstream",type=Path)
    p.add_argument("derived",type=Path)
    a=p.parse_args()
    check(a.upstream,a.derived)
