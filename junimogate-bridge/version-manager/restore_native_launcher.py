#!/usr/bin/env python3
"""Restore original JunimoGate/SMAPI MainActivity as the sole Android launcher.

AuroraVersionActivity remains registered, but is used only when the native
SMAPI Settings page explicitly opens its version-manager screen. The original
game host, installed-game compatibility policy, and SMAPI binaries are untouched.
"""
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET

ANDROID = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID + "}"
MAIN = "org.junimogate.app.MainActivity"
VERSIONS = "org.junimogate.aurora.AuroraVersionActivity"
ACT_MAIN = "android.intent.action.MAIN"
CAT_LAUNCHER = "android.intent.category.LAUNCHER"

def launchers(activity: ET.Element) -> list[ET.Element]:
    return [
        node for node in activity.findall("intent-filter")
        if ACT_MAIN in {x.get(A + "name") for x in node.findall("action")}
        and CAT_LAUNCHER in {x.get(A + "name") for x in node.findall("category")}
    ]

def restore(decoded_dir: Path) -> None:
    manifest = decoded_dir / "AndroidManifest.xml"
    if not manifest.is_file():
        raise ValueError("Decoded AndroidManifest.xml is missing")
    ET.register_namespace("android", ANDROID)
    tree = ET.parse(manifest)
    root = tree.getroot()
    if root.tag != "manifest" or root.get("package") != "org.junimogate.app":
        raise ValueError("Unexpected package identifier")
    app = root.find("application")
    if app is None:
        raise ValueError("Android application entry is missing")
    acts = app.findall("activity")
    main = [x for x in acts if x.get(A + "name") == MAIN]
    versions = [x for x in acts if x.get(A + "name") == VERSIONS]
    if len(main) != 1 or len(versions) != 1:
        raise ValueError("Expected exactly one native SMAPI and Aurora version activity")
    main, versions = main[0], versions[0]
    if len(launchers(main)) != 0 or len(launchers(versions)) != 1:
        raise ValueError("Unexpected launcher state: refusing silent duplicate entrypoints")
    original_filter = launchers(versions)[0]
    versions.remove(original_filter)
    main.append(original_filter)
    main.set(A + "exported", "true")
    versions.set(A + "exported", "false")
    if len(launchers(main)) != 1 or len(launchers(versions)) != 0:
        raise ValueError("Launcher transition validation failed")
    tree.write(manifest, encoding="utf-8", xml_declaration=True)
    print("PASS: launchable MainActivity is the original managed SMAPI home")
    print("PASS: AuroraVersionActivity remains only an internal Settings > Versions destination")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_dir", type=Path)
    args = parser.parse_args()
    restore(args.decoded_dir)

if __name__ == "__main__":
    main()
