#!/usr/bin/env python3
"""Aurora 6.2: owner-only Versions → Download and Install (no R2 key UI)."""
import argparse
from pathlib import Path
import sys
import re
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"v61"))
from inject_v61 import patch as previous_patch, A, ANDROID, ACTIVITY as OLD_PRIVATE

VERSIONS="org.junimogate.aurora.AuroraOwnerVersionsActivity"
INSTALLER="org.junimogate.aurora.AuroraVersionActivity"

def patch(root: Path) -> None:
    previous_patch(root)
    manifest=root/"AndroidManifest.xml"
    ET.register_namespace("android",ANDROID)
    tree=ET.parse(manifest)
    pkg=tree.getroot()
    app=pkg.find("application")
    if app is None:raise ValueError("Missing manifest application")
    for node in list(app.findall("activity")):
        if node.get(A+"name")==OLD_PRIVATE:
            app.remove(node)  # remove obsolete R2 access/secret UI entirely
    for name,label in ((VERSIONS,"Aurora · Версии"),
                       (INSTALLER,"Aurora · Установка")):
        found=[a for a in app.findall("activity") if a.get(A+"name")==name]
        if len(found)>1 or (found and name==VERSIONS):
            raise ValueError("Duplicate installer / version activity")
        # Older Aurora injectors may already register the original installer.
        # Reuse that registration for the newly compiled compatible class.
        node=found[0] if found else ET.SubElement(app,"activity")
        node.set(A+"name",name)
        node.set(A+"exported","false")
        node.set(A+"label",label)
        node.set(A+"theme","@style/Theme.JunimoGate")
    permissions={x.get(A+"name") for x in pkg.findall("uses-permission")}
    if "android.permission.REQUEST_INSTALL_PACKAGES" not in permissions:
        element=ET.Element("uses-permission")
        element.set(A+"name","android.permission.REQUEST_INSTALL_PACKAGES")
        pkg.insert(0,element)
    tree.write(manifest,encoding="utf-8",xml_declaration=True)
    yml=root/"apktool.yml"
    data=yml.read_text(encoding="utf-8")
    data,count=re.subn(r"(?m)^(\s*versionCode:\s*)610\s*$",
        r"\g<1>620",data,count=1)
    if count!=1:raise ValueError("Expected Aurora 6.1 version code")
    data,count=re.subn(r"(?m)^(\s*versionName:\s*)6\.1\.0-rc\.1\s*$",
        r"\g<1>6.2.0-rc.1",data,count=1)
    if count!=1:raise ValueError("Expected Aurora 6.1 version name")
    yml.write_text(data,encoding="utf-8")
    print("PASS: 6.2 owner-only version chooser, Android installer, no R2 key UI")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk",type=Path)
    patch(parser.parse_args().decoded_apk)
