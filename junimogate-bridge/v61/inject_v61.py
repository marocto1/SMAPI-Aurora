#!/usr/bin/env python3
"""Aurora 6.1: optional *private* R2 download UI on the tested v6.0 baseline.

Reuses the v6.0 patch: never touches managed SMAPI/GameHost binaries, game data,
system install policy, or existing private profiles.
"""
from pathlib import Path
import argparse
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "v60"))
from inject_v60 import patch as patch_v60, A, ANDROID

ACTIVITY = "org.junimogate.aurora.AuroraR2PrivateActivity"

def patch(root: Path) -> None:
    patch_v60(root)
    manifest = root / "AndroidManifest.xml"
    ET.register_namespace("android", ANDROID)
    tree = ET.parse(manifest)
    app = tree.getroot().find("application")
    if app is None:
        raise ValueError("Missing Aurora application")
    if any(x.get(A+"name")==ACTIVITY for x in app.findall("activity")):
        raise ValueError("Duplicate Aurora private downloads")
    node=ET.SubElement(app,"activity")
    node.set(A+"name",ACTIVITY)
    node.set(A+"exported","false")
    node.set(A+"label","Aurora · Private Downloads")
    node.set(A+"theme","@style/Theme.JunimoGate")
    tree.write(manifest,encoding="utf-8",xml_declaration=True)

    yml=root/"apktool.yml"
    content=yml.read_text(encoding="utf-8")
    content,num=re.subn(r"(?m)^(\s*versionCode:\s*)600\s*$",
                        r"\g<1>610",content,count=1)
    if num!=1:raise ValueError("Unexpected v6.0 versionCode")
    content,num=re.subn(r"(?m)^(\s*versionName:\s*)6\.0\.0-rc\.1\s*$",
                        r"\g<1>6.1.0-rc.1",content,count=1)
    if num!=1:raise ValueError("Unexpected v6.0 versionName")
    yml.write_text(content,encoding="utf-8")
    print("PASS: Aurora 6.1 private R2 UI wired; SMAPI/GameHost not touched")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk",type=Path)
    patch(parser.parse_args().decoded_apk)
