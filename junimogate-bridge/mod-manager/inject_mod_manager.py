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
WORKSHOP = "org.junimogate.aurora.AuroraWorkshopActivity"
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
    <shortcut android:shortcutId="aurora-nexus-workshop"
        android:enabled="true"
        android:icon="@mipmap/ic_launcher"
        android:shortcutShortLabel="@string/aurora_workshop_shortcut"
        android:shortcutLongLabel="@string/aurora_workshop_shortcut_long">
        <intent android:action="android.intent.action.VIEW"
            android:targetPackage="org.junimogate.app"
            android:targetClass="org.junimogate.aurora.AuroraWorkshopActivity" />
    </shortcut>
</shortcuts>
"""
STRINGS_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="aurora_mod_shortcut">Моды Aurora</string>
    <string name="aurora_mod_shortcut_long">Обзор модов и зависимостей</string>
    <string name="aurora_workshop_shortcut">Workshop</string>
    <string name="aurora_workshop_shortcut_long">Nexus Mods · Workshop</string>
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
    if any(a.get(A + "name") in (OVERVIEW, WORKSHOP) for a in app.findall("activity")):
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
    workshop = ET.SubElement(app, "activity")
    workshop.set(A + "name", WORKSHOP)
    workshop.set(A + "exported", "true")
    workshop.set(A + "label", "@string/aurora_workshop_shortcut")
    workshop.set(A + "theme", "@style/Theme.JunimoGate")
    # Both extra Activities are launcher app-shortcut destinations, not MAIN launchers.
    # Keep the Workshop inside the EXISTING Mods tab via native XML view
    # inflation. The view has its own Android click handler, so we never
    # patch the original Xamarin/.NET ModsFragment bytecode.
    mods_layout = root / "res" / "layout" / "fragment_mods.xml"
    if not mods_layout.is_file():
        raise FileNotFoundError("Original Mods fragment layout missing")
    layout_data = mods_layout.read_text(encoding="utf-8")
    # Match both original source XML and Apktool-decoded layout indentation.
    matches = list(re.finditer(
        r'<TextView\s+android:id="@\+id/mods_inventory_count"', layout_data))
    if len(matches) != 1 or "AuroraWorkshopTabsView" in layout_data:
        raise ValueError("Original Mods layout anchor missing, ambiguous or already patched")
    entry = (
        '<org.junimogate.aurora.AuroraWorkshopTabsView\n'
        '            android:layout_width="match_parent"\n'
        '            android:layout_height="56dp"\n'
        '            android:contentDescription="Установленные моды или Workshop" />\n\n        '
    )
    layout_data = layout_data[:matches[0].start()] + entry + layout_data[matches[0].start():]
    ET.fromstring(layout_data)  # malformed layout must fail before any installation
    mods_layout.write_text(layout_data, encoding="utf-8")
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
                         lambda m: m[1] + "24", yml, count=1)
    if count != 1:
        raise ValueError("Missing APK versionCode")
    yml, count = re.subn(r"(?m)^(\s*versionName:\s*)([^\n]+)$",
                         lambda m: m[1] + "0.9.4-workshop-integrated-qa", yml, count=1)
    if count != 1:
        raise ValueError("Missing APK versionName")
    apktool.write_text(yml, encoding="utf-8")
    print("PASS: original launcher preserved, Workshop integrated into original Mods tab; managed SMAPI untouched")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    patch(parser.parse_args().decoded_apk)
