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
BACKUP = "org.junimogate.aurora.AuroraBackupActivity"
UPDATE_CENTER = "org.junimogate.aurora.AuroraUpdateCenterActivity"
COOP = "org.junimogate.aurora.AuroraCoopActivity"
ROOMS = "org.junimogate.aurora.AuroraRoomActivity"
CATALOG = "org.junimogate.aurora.AuroraWorkshopCatalogActivity"
HUB = "org.junimogate.aurora.AuroraHubActivity"
SAFETY = "org.junimogate.aurora.AuroraSafetyActivity"
NETWORK = "org.junimogate.aurora.AuroraNetworkActivity"
RECOVERY = "org.junimogate.aurora.AuroraRecoveryPreviewActivity"
UDP_CHECK = "org.junimogate.aurora.AuroraUdpDiagnosticActivity"
MOD_AUDIT = "org.junimogate.aurora.AuroraModAuditActivity"
UNIFIED = "org.junimogate.aurora.AuroraUnifiedActivity"
LINK = "org.junimogate.aurora.AuroraLinkActivity"
SAFE_APK = "org.junimogate.aurora.AuroraApkPreflightActivity"
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
    if any(a.get(A + "name") in (OVERVIEW, WORKSHOP, BACKUP, UPDATE_CENTER, COOP, ROOMS, CATALOG, HUB, SAFETY, NETWORK, RECOVERY, UDP_CHECK, MOD_AUDIT, UNIFIED, LINK, SAFE_APK) for a in app.findall("activity")):
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
    activity.set(A + "theme", "@style/Theme.JunimoGate")
    workshop = ET.SubElement(app, "activity")
    workshop.set(A + "name", WORKSHOP)
    workshop.set(A + "exported", "true")
    workshop.set(A + "label", "@string/aurora_workshop_shortcut")
    workshop.set(A + "theme", "@style/Theme.JunimoGate")
    backup = ET.SubElement(app, "activity")
    backup.set(A + "name", BACKUP)
    backup.set(A + "exported", "false")
    backup.set(A + "label", "Aurora · Backup & Restore")
    backup.set(A + "theme", "@style/Theme.JunimoGate")
    updates = ET.SubElement(app, "activity")
    updates.set(A + "name", UPDATE_CENTER)
    updates.set(A + "exported", "false")
    updates.set(A + "label", "Aurora · Update Center")
    updates.set(A + "theme", "@style/Theme.JunimoGate")
    coop = ET.SubElement(app, "activity")
    coop.set(A + "name", COOP)
    coop.set(A + "exported", "false")
    coop.set(A + "label", "Aurora Coop LAN")
    coop.set(A + "theme", "@style/Theme.JunimoGate")
    rooms = ET.SubElement(app, "activity")
    rooms.set(A + "name", ROOMS)
    rooms.set(A + "exported", "false")
    rooms.set(A + "label", "Aurora Coop Rooms")
    rooms.set(A + "theme", "@style/Theme.JunimoGate")
    catalog = ET.SubElement(app, "activity")
    catalog.set(A + "name", CATALOG)
    catalog.set(A + "exported", "false")
    catalog.set(A + "label", "Aurora Workshop 3.0")
    catalog.set(A + "theme", "@style/Theme.JunimoGate")
    for activity_name, label in ((HUB, "Aurora Hub"),
                                 (SAFETY, "Aurora Safe Update"),
                                 (NETWORK, "Aurora Network 2.0"),
                                 (RECOVERY, "Aurora Recovery Preview"),
                                 (UDP_CHECK, "Aurora Coop UDP Diagnostics"),
                                 (MOD_AUDIT, "Aurora Mod Manager Pro"),
                                 (UNIFIED, "Aurora Unified 6.0"),
                                 (LINK, "Aurora Link 6.0"),
                                 (SAFE_APK, "Aurora Safe Installer 4.4")):
        new_activity = ET.SubElement(app, "activity")
        new_activity.set(A + "name", activity_name)
        new_activity.set(A + "exported", "false")
        new_activity.set(A + "label", label)
        new_activity.set(A + "theme", "@style/Theme.JunimoGate")
        if activity_name == LINK:
            # Explicit Android share target: third-party camera/QR reader can
            # share plain-text invites; never intercept other applications.
            new_activity.set(A + "exported", "true")
            share = ET.SubElement(new_activity, "intent-filter")
            ET.SubElement(share, "action", {A + "name": "android.intent.action.SEND"})
            ET.SubElement(share, "category", {A + "name": "android.intent.category.DEFAULT"})
            ET.SubElement(share, "data", {A + "mimeType": "text/plain"})
    # Read-only VPN transport/interface visibility, no VPN service permission.
    permissions = {e.get(A + "name") for e in package.findall("uses-permission")}
    if "android.permission.ACCESS_NETWORK_STATE" not in permissions:
        network_permission = ET.Element("uses-permission")
        network_permission.set(A + "name", "android.permission.ACCESS_NETWORK_STATE")
        package.insert(0,network_permission)
    # RC2: Android 11+ package visibility is mandatory for the installed
    # official game's version check. No QUERY_ALL_PACKAGES permission.
    game_queries = package.find("queries")
    if game_queries is None:
        game_queries = ET.Element("queries")
        package.insert(0, game_queries)
    if not any(q.get(A + "name") == "com.chucklefish.stardewvalley"
               for q in game_queries.findall("package")):
        game_pkg = ET.SubElement(game_queries, "package")
        game_pkg.set(A + "name", "com.chucklefish.stardewvalley")
    # Android INTERNET should already exist (Nexus WebView needs it).
    permissions=[e.get(A + "name") for e in package.findall("uses-permission")]
    if "android.permission.INTERNET" not in permissions:
        perm = ET.Element("uses-permission")
        perm.set(A+"name", "android.permission.INTERNET")
        package.insert(0,perm)
    # Only original SMAPI MainActivity owns Android MAIN/LAUNCHER.
    # Keep the Workshop inside the EXISTING Mods tab via native XML view
    # inflation. The view has its own Android click handler, so we never
    # patch the original Xamarin/.NET ModsFragment bytecode.
    mods_layout = root / "res" / "layout" / "fragment_mods.xml"
    if not mods_layout.is_file():
        raise FileNotFoundError("Original Mods fragment layout missing")
    layout_data = mods_layout.read_text(encoding="utf-8")
    # Match both original source XML and Apktool-decoded layout indentation.
    matches = list(re.finditer(
        r'<TextView\b[^>]*android:id="(?:@\+id|@id)/mods_inventory_count"[^>]*>', layout_data))
    if len(matches) != 1 or "AuroraWorkshopTabsView" in layout_data:
        raise ValueError(
            "Original Mods layout anchor missing/ambiguous/already patched: " +
            (layout_data[max(0, layout_data.find("mods_inventory_count")-140):
                         layout_data.find("mods_inventory_count")+140]
             if "mods_inventory_count" in layout_data else "inventory_count absent"))
    entry = (
        '<org.junimogate.aurora.AuroraWorkshopTabsView\n'
        '            android:layout_width="match_parent"\n'
        '            android:layout_height="152dp"\n'
        '            android:contentDescription="Установленные моды или Workshop" />\n\n        '
    )
    layout_data = layout_data[:matches[0].start()] + entry + layout_data[matches[0].start():]
    ET.fromstring(layout_data)  # malformed layout must fail before any installation
    mods_layout.write_text(layout_data, encoding="utf-8")
    # Keep original compiled game/runtime untouched. Branding applies to
    # Android Material color resources, including night mode.
    app.set(A + "label", "SMAPI Aurora")
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


    # Aurora v1 UI identity: teal/midnight colors for ALL stock Material3
    # screens and our native Workshop/Backup/Version toolbars.
    palette = {
      "values": {
        "junimo_launcher_background":"#18254E",
        "junimo_primary":"#4D55BA",
        "junimo_on_primary":"#FFFFFF",
        "junimo_primary_container":"#DBE1FF",
        "junimo_on_primary_container":"#141C55",
        "junimo_secondary":"#127D88",
        "junimo_on_secondary":"#FFFFFF",
        "junimo_secondary_container":"#C7F0F2",
        "junimo_on_secondary_container":"#09363D",
        "junimo_tertiary":"#8151AA",
        "junimo_on_tertiary":"#FFFFFF",
        "junimo_tertiary_container":"#EEDDFF",
        "junimo_on_tertiary_container":"#23174E",
        "junimo_surface":"#F6F9FB",
        "junimo_surface_container_low":"#EDF5F6",
        "junimo_surface_container":"#E6F0F2",
        "junimo_surface_container_high":"#DCE9ED",
        "junimo_on_surface":"#17272C",
        "junimo_on_surface_variant":"#4E666D",
        "junimo_outline":"#758D94",
        "junimo_outline_variant":"#C3D6D9",
      },
      "values-night": {
        "junimo_primary":"#B8C5FF",
        "junimo_on_primary":"#1B285E",
        "junimo_primary_container":"#343D8B",
        "junimo_on_primary_container":"#E5E7FF",
        "junimo_secondary":"#86D9E2",
        "junimo_on_secondary":"#07363E",
        "junimo_secondary_container":"#195561",
        "junimo_on_secondary_container":"#BAF0F4",
        "junimo_tertiary":"#C4B7FF",
        "junimo_on_tertiary":"#332361",
        "junimo_tertiary_container":"#493C78",
        "junimo_on_tertiary_container":"#E5DEFF",
        "junimo_surface":"#111422",
        "junimo_surface_container_low":"#1B2133",
        "junimo_surface_container":"#222B40",
        "junimo_surface_container_high":"#303A54",
        "junimo_on_surface":"#ECEEFA",
        "junimo_on_surface_variant":"#BFC5DE",
        "junimo_outline":"#80999E",
        "junimo_outline_variant":"#38525A",
      }
    }
    changed = []
    for qualifier, shades in palette.items():
        colors = root / "res" / qualifier / "colors.xml"
        if not colors.is_file():
            raise FileNotFoundError(f"Aurora palette missing base colors.xml: {qualifier}")
        colors_tree = ET.parse(colors)
        colors_root = colors_tree.getroot()
        found = set()
        for tag in colors_root.findall("color"):
            name = tag.get("name")
            if name in shades:
                tag.text = shades[name]
                found.add(name)
        missing = set(shades) - found
        if missing:
            raise ValueError(f"Aurora palette does not contain: {missing}")
        colors_tree.write(colors, encoding="utf-8", xml_declaration=True)
        changed.append(qualifier)
    print("PASS: Aurora 1.3 custom sapphire/teal light/dark Material palette:", ", ".join(changed))

    yml = apktool.read_text(encoding="utf-8")
    yml, count = re.subn(r"(?m)^(\s*versionCode:\s*)([^\n]+)$",
                         lambda m: m[1] + "600", yml, count=1)
    if count != 1:
        raise ValueError("Missing APK versionCode")
    yml, count = re.subn(r"(?m)^(\s*versionName:\s*)([^\n]+)$",
                         lambda m: m[1] + "6.0.0-rc.1", yml, count=1)
    if count != 1:
        raise ValueError("Missing APK versionName")
    apktool.write_text(yml, encoding="utf-8")
    print("PASS: Aurora Connection 6.0 RC1 Link, Workshop 5, signed APK preflight, Unified wizard and original SMAPI intact")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    patch(parser.parse_args().decoded_apk)
