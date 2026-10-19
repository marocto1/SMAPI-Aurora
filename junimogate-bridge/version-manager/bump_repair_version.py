#!/usr/bin/env python3
"""Advance QA metadata in an already configured Aurora launcher APK.

Does not change Android package identity or any native SMAPI assets.
"""
from pathlib import Path
import re
import sys

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: bump_repair_version.py <decoded-apk-dir>")
    root=Path(sys.argv[1])
    decoded=root/"apktool.yml"
    content=decoded.read_text(encoding="utf-8")
    needle=r"(?m)^(\s*versionCode:\s*)([^\n]+)$"
    content,count=re.subn(needle,lambda m:m[1]+"15",content)
    if count!=1: raise ValueError("APK versionCode missing")
    needle=r"(?m)^(\s*versionName:\s*)([^\n]+)$"
    content,count=re.subn(needle,lambda m:m[1]+"0.8.4-comfort-launch-qa",content)
    if count!=1: raise ValueError("APK versionName missing")
    decoded.write_text(content,encoding="utf-8")
    manifest=(root/"AndroidManifest.xml").read_text(encoding="utf-8")
    if 'org.junimogate.aurora.AuroraVersionActivity' not in manifest:
        raise ValueError("The existing Aurora version manager Activity was lost")
    if 'org.junimogate.app.MainActivity' not in manifest:
        raise ValueError("The original SMAPI launcher Activity was lost")
    print("PASS: Aurora v0.8.4 manifest lineage preserved, Android versionCode=15")

if __name__=="__main__":main()
