#!/usr/bin/env python3
"""Wire Aurora native read-only Mod Overview into an existing decoded v0.8.9 APK.

Primary original Xamarin/SMAPI launcher stays unchanged. Static app shortcut
("long press Aurora icon" -> "Моды") opens the optional read-only native view.
All actual installs, enables, deletes and group edits remain on JunimoGate's
original fully transactional Mods/Groups implementation.
"""
import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ANDROID = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID + "}"
LAUNCHER = "org.junimogate.app.MainActivity"
OVERVIEW = "org.junimogate.aurora.AuroraModOverviewActivity"
SHORTCUT_XML = """<?xml version="1.0" encoding="utf-8"?>
<shortcuts xmlns:android="http://schemas.android.com/apk/res/android">
    <shortcut android:shortcutId="aurora-mod-overview"
        android:enabled="true"
        android:icon="@mipmap/ic_launcher"
        android:shortcutShortLabel="@string/aurora_mod_shortcut"
        android:shortcutLongLabel="@string/aurora_mod_shortcut_long">
        <intent android:action="android.intent.action.VIEW"
            android:targetPackage="org.junimogate.app"
            android:targetClass="org.junimogate.aurora.AuroraModOverviewActivity" />
    </shortcut>
</shortcuts>
"""
STRINGS_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="aurora_mod_shortcut">Моды Aurora</string>
    <string name="aurora_mod_shortcut_long">Обзор модов и зависимостей</string>
</resources>
"""


def patch(root: Path) -> None:
    manifest = root / "AndroidManifest.xml"
    apktool = root / "apktool.yml"
    if not manifest.is_file() or not apktool.is_file():
        raise FileNotFoundError("Decoded APK files missing")
    ET.register_namespace("android", ANDROID)
    tree = ET.parse(manifest)
    package = tree.getroot()
    if package.tag != "manifest" or package.get("package") != "org.junimogate.app":
        raise ValueError("Unexpected Android package")
    app = package.find("application")
    if app is None:
        raise ValueError("Android application missing")
    main = [a for a in app.findall("activity") if a.get(A + "name") == LAUNCHER]
    if len(main) != 1:
        raise ValueError("Original SMAPI MainActivity missing")
    if any(a.get(A + "name") == OVERVIEW for a in app.findall("activity")):
        raise ValueError("Already patched; refusing duplicate activity")
    launcher_filters = [
        i for i in main[0].findall("intent-filter")
        if any(a.get(A + "name") == "android.intent.action.MAIN" for a in i.findall("action"))
        and any(c.get(A + "name") == "android.intent.category.LAUNCHER" for c in i.findall("category"))
    ]
    if len(launcher_filters) != 1:
        raise ValueError("Original SMAPI launcher not sole app launcher")

    meta = ET.SubElement(main[0], "meta-data")
    meta.set(A + "name", "android.app.shortcuts")
    meta.set(A + "resource", "@xml/aurora_mod_shortcuts")
    activity = ET.SubElement(app, "activity")
    activity.set(A + "name", OVERVIEW)
    activity.set(A + "exported", "true")
    activity.set(A + "label", "@string/aurora_mod_shortcut")
    activity.set(A + "theme", "@android:style/Theme.Material.NoActionBar")
    # Optional external launcher action; no MAIN/LAUNCHER filter and no second app icon.
    tree.write(manifest, encoding="utf-8", xml_declaration=True)

    xml_dir = root / "res" / "xml"
    values_dir = root / "res" / "values"
    if not xml_dir.is_dir() or not values_dir.is_dir():
        raise ValueError("Decoded resources missing")
    shortcut_path = xml_dir / "aurora_mod_shortcuts.xml"
    string_path = values_dir / "aurora_mod_manager_strings.xml"
    if shortcut_path.exists() or string_path.exists():
        raise ValueError("Resources already patched")
    shortcut_path.write_text(SHORTCUT_XML, encoding="utf-8")
    string_path.write_text(STRINGS_XML, encoding="utf-8")

    yml = apktool.read_text(encoding="utf-8")
    yml, count = re.subn(r"(?m)^(\s*versionCode:\s*)([^\n]+)$",
                         lambda m: m[1] + "22", yml, count=1)
    if count != 1:
        raise ValueError("Missing APK versionCode")
    yml, count = re.subn(r"(?m)^(\s*versionName:\s*)([^\n]+)$",
                         lambda m: m[1] + "0.9.1-mod-manager-qa2", yml, count=1)
    if count != 1:
        raise ValueError("Missing APK versionName")
    apktool.write_text(yml, encoding="utf-8")
    print("PASS: original launcher preserved, read-only overview shortcut injected")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    patch(parser.parse_args().decoded_apk)
