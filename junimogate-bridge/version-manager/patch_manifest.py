#!/usr/bin/env python3
"""Add an Android Java first-screen launcher without rewriting .NET game code."""
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import re

NS="http://schemas.android.com/apk/res/android"
A="{"+NS+"}"
VERSION_ACTIVITY="org.junimogate.aurora.AuroraVersionActivity"
ORIGINAL_ACTIVITY="org.junimogate.app.MainActivity"
GAME_ID="org.junimogate.app"

def install(decoded:Path):
    manifest=decoded/"AndroidManifest.xml"
    text=manifest.read_text(encoding="utf-8")
    if GAME_ID not in text:
        raise ValueError("Unexpected application package identity")
    ET.register_namespace("android", NS)
    ET.register_namespace("tools", "http://schemas.android.com/tools")
    tree=ET.parse(manifest)
    root=tree.getroot()
    app=root.find("application")
    if app is None: raise ValueError("Application entry not found")
    activities=app.findall("activity")
    main=[a for a in activities if a.get(A+"name")==ORIGINAL_ACTIVITY]
    if len(main)!=1: raise ValueError("Original CLR launcher Activity missing")
    launcher=main[0]
    moved=0
    for child in list(launcher.findall("intent-filter")):
        actions={a.get(A+"name") for a in child.findall("action")}
        categories={c.get(A+"name") for c in child.findall("category")}
        if "android.intent.action.MAIN" in actions and "android.intent.category.LAUNCHER" in categories:
            launcher.remove(child)
            moved+=1
    if moved!=1: raise ValueError("Expected one original Android launcher entry")
    if any(a.get(A+"name")==VERSION_ACTIVITY for a in activities):
        raise ValueError("Version manager Activity already registered")
    front=ET.Element("activity",{
        A+"name":VERSION_ACTIVITY,
        A+"exported":"true",
        A+"launchMode":"singleTop",
        A+"label":"SMAPI Aurora",
        A+"theme":"@android:style/Theme.Material.NoActionBar",
    })
    intent=ET.SubElement(front,"intent-filter")
    ET.SubElement(intent,"action",{A+"name":"android.intent.action.MAIN"})
    ET.SubElement(intent,"category",{A+"name":"android.intent.category.LAUNCHER"})
    app.insert(list(app).index(launcher)+1,front)
    if not any(p.get(A+"name")=="android.permission.REQUEST_INSTALL_PACKAGES"
               for p in root.findall("uses-permission")):
        root.insert(0,ET.Element("uses-permission",{
            A+"name":"android.permission.REQUEST_INSTALL_PACKAGES"}))
    ET.indent(tree,space="    ")
    tree.write(manifest,encoding="utf-8",xml_declaration=True)
    # Apktool uses apktool.yml as the authority for Android app versioning.
    config=decoded/"apktool.yml"
    cfg=config.read_text(encoding="utf-8")
    pattern=r"(?m)^(\s*versionCode:\s*)([^\n]+)$"
    cfg,n=re.subn(pattern,r"\g<1>12",cfg,count=1)
    if n!=1:raise ValueError("Unable to increment QA Android app versionCode")
    pattern=r"(?m)^(\s*versionName:\s*)([^\n]+)$"
    cfg,n=re.subn(pattern,r"\g<1>0.8.0-aurora-version-qa",cfg,count=1)
    if n!=1:raise ValueError("Unable to change QA Android app versionName")
    config.write_text(cfg,encoding="utf-8")

    tree=ET.parse(manifest)
    app=tree.getroot().find("application")
    assert app is not None
    activities=app.findall("activity")
    candidates=[a for a in activities if a.get(A+"name")==VERSION_ACTIVITY]
    assert len(candidates)==1
    assert len(candidates[0].findall("intent-filter"))==1
    print("PASS: Aurora version manager is the launcher; original SMAPI Activity retained")
    print("No changes to compiled .NET managed/native binaries.")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded",type=Path)
    args=parser.parse_args()
    install(args.decoded.resolve())
