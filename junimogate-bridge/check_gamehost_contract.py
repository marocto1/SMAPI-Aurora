#!/usr/bin/env python3
"""Static integration contract before the private-reference GameHost build.

This is NOT a compile/test of SMAPI and cannot certify Android gameplay.
"""
from pathlib import Path
import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

PIN="029eafed917ae853d6c0a59330ee273524168296"
GAME_FILES={
    "StardewValley.dll","StardewValley.GameData.dll","BmFont.dll",
    "Lidgren.Network.dll","xTile.dll",
}
AURORA_APP_ID="com.marocto.smapi.aurora.jg"


def verify(root:Path) -> None:
    if not root.is_dir():
        raise RuntimeError("JunimoGate checkout does not exist")
    # git still points at original immutable upstream commit after Aurora overlay.
    sha=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    if sha!=PIN: raise RuntimeError(f"Upstream pin mismatch {sha}")
    app=root/"src/JunimoGate.App/JunimoGate.App.csproj"
    game=root/"src/JunimoGate.GameHost/JunimoGate.GameHost.csproj"
    activity=root/"src/JunimoGate.GameHost/SmapiGameActivity.cs"
    for file in (app,game,activity,root/"LICENSE",root/"LICENSE-EXCEPTION",
                 root/"THIRD-PARTY-NOTICES.md"):
        if not file.is_file() or file.is_symlink():
            raise RuntimeError("Missing/symlinked required source: "+str(file.relative_to(root)))
    a=ET.parse(app).getroot()
    g=ET.parse(game).getroot()
    def prop(xml,key):
        e=xml.find(f".//PropertyGroup/{key}")
        return None if e is None else (e.text or "").strip()
    if prop(a,"ApplicationId")!=AURORA_APP_ID:
        raise RuntimeError("Aurora Android app identity mismatch")
    if prop(g,"TargetFramework")!="net9.0-android35.0":
        raise RuntimeError("GameHost Android target mismatch")
    if prop(g,"JunimoGateRequiresSmapi")!="true":
        raise RuntimeError("GameHost no longer requests SMAPI")
    if prop(a,"JunimoGateRequiresSmapi")!="true":
        raise RuntimeError("Android app no longer requests SMAPI")
    if prop(a,"AndroidUseAssemblyStore")!="false":
        raise RuntimeError("Unexpected Android managed assembly packaging mode")
    refs=[e.attrib.get("Include","") for e in g.findall(".//ProjectReference")]
    if "../../smapi/src/SMAPI/SMAPI.csproj" not in refs:
        raise RuntimeError("SMAPI C# project link missing")
    if "../JunimoGate.Android/JunimoGate.Android.csproj" not in refs:
        raise RuntimeError("Android GameHost bridge project link missing")
    if "../JunimoGate.Rewriter/JunimoGate.Rewriter.csproj" not in refs:
        raise RuntimeError("GameHost rewriter project link missing")

    csharp=activity.read_text(encoding="utf-8")
    assertions={
        "separate game process": 'Process = ":game"',
        "bound SMAPI implementation": "StardewModdingAPI.AndroidHost",
        "game assembly loaded from on-device workspace": "loader.LoadGameAssembly()",
        "snapshot gate": "PreparedRuntimeFiles.BuildAndValidate",
        "controlled launch registry": "GameLaunchRegistry.ConsumeAsync",
        "SMAPI session started": "CreateAndRunSession",
        "game host bridge attaches": "GameHostBridge.Attach",
    }
    for description,source in assertions.items():
        if source not in csharp:
            raise RuntimeError("GameHost runtime contract changed: "+description)
    # Game DLLs must be references only, never packaged directly.
    packed_game_references=set()
    for e in a.findall(".//ResolvedAssemblies"):
        if e.attrib.get("AndroidSkipAddToPackage")=="true":
            include=e.attrib.get("Include","").replace("\\","/")
            for filename in GAME_FILES:
                if include.endswith("/"+filename):
                    packed_game_references.add(filename)
    if packed_game_references!=GAME_FILES:
        raise RuntimeError("Android APK linker may package commercial game refs. Missing skip flags: "+
                           repr(sorted(GAME_FILES-packed_game_references)))
    app_manifest=root/"src/JunimoGate.App/Properties/AndroidManifest.xml"
    manifest=ET.parse(app_manifest).getroot()
    ns="{http://schemas.android.com/apk/res/android}"
    queries=manifest.find("queries")
    ids={e.get(ns+"name") for e in queries.findall("package")}
    if ids!={"com.chucklefish.stardewvalley","com.chucklefish.stardewvalleysamsung"}:
        raise RuntimeError("Upstream package/signing visibility policy unexpectedly changed")
    application=manifest.find("application")
    if application.get(ns+"label")!="@string/app_name":
        raise RuntimeError("Aurora app identity not set in manifest")
    forbidden={
        "android.permission.QUERY_ALL_PACKAGES",
        "android.permission.MANAGE_EXTERNAL_STORAGE",
    }
    for e in manifest.findall("uses-permission"):
        if e.get(ns+"name") in forbidden and e.get("{http://schemas.android.com/tools}node")!="remove":
            raise RuntimeError("Overbroad Android permission in manifest")
    # Only UI adaptation: this check ignores new resource files in git status but
    # verifies that source-tracked GameHost / licensing files have no local edits.
    diff=subprocess.check_output(["git","-C",str(root),"diff","--name-only"],text=True)
    blocked=re.compile(r"^(src/JunimoGate\.(GameHost|Android|Mods|Core|Extraction|Rewriter)/|smapi/|build/|licenses/|LICENSE|THIRD-PARTY-NOTICES)")
    for path in diff.splitlines():
        if blocked.search(path):
            raise RuntimeError("Aurora may not silently rewrite GameHost/runtime/license: "+path)
    print("PASS: upstream pinned, SMAPI/Android contracts present, five commercial reference SKIP flags, no runtime changes")
    print("NOT BUILT: full GameHost cannot compile until private compatible Android references and patched native packages are present")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    args=parser.parse_args()
    try: verify(args.source.resolve())
    except (OSError,ValueError,ET.ParseError,RuntimeError,subprocess.CalledProcessError) as ex:
        print("BLOCKED: "+str(ex),file=sys.stderr);raise SystemExit(1)
