#!/usr/bin/env python3
"""Resource-only branded build overlay for the *official* JunimoGate v0.3.1 APK.

Important: this does not rebuild GameHost, change its C# or patch game
signature checks. It's explicitly a QA bridge made from the licensed upstream
binary, with corresponding source available via the pinned upstream repository.
"""
from pathlib import Path
import argparse
import importlib.util
import re
from xml.sax.saxutils import escape

CURRENT = Path(__file__).resolve().with_name("apply_aurora.py")
spec=importlib.util.spec_from_file_location("aurora_junimo_bridge",CURRENT)
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

# Resource compilation must not change the Android package or class names;
# .NET-for-Android Java/CLR startup metadata is sensitive to those names.
ORIGINAL_PACKAGE = "org.junimogate.app"
ANDROID_VERSION = "0.7.0-aurora-smapi-qa"
BRANDING = {
    "app_name": "SMAPI Aurora",
    "about_summary": "SMAPI Aurora runs the original JunimoGate SMAPI Android GameHost. This build is a GPLv3 resource-only adaptation; original developer: leontismaro.",
    "about_author_value": "Aurora UI: Marocto | SMAPI GameHost: JunimoGate by leontismaro",
    "open_source_notice_title": "SMAPI Aurora is open source",
    "open_source_notice_message": "A GPLv3 adaptation of JunimoGate's v0.3.1 APK. GameHost and signer checks are unmodified; its upstream authors, licenses and source remain credited.",
}
AURORA_COLORS = bridge.PALETTE
LANGUAGE = bridge.RU_STRINGS


def android_escape(value):
    return escape(value, {'"': '\\"', "'": "\\'"}).replace("\\n", "\\\\n")

def change_resource(xml, kind, values):
    """Modify existing Android resource values but don't delete or reorder IDs."""
    changed=[]
    for name,value in values.items():
        pattern=re.compile(
            r'(<'+kind+r'\b(?=[^>]*\bname="'+re.escape(name)+r'")'
            r'[^>]*>)(.*?)(</'+kind+r'>)',re.DOTALL)
        value=android_escape(value)
        if pattern.search(xml):
            xml,count=pattern.subn(lambda m: m.group(1)+value+m.group(3),xml,count=1)
            if count!=1: raise ValueError("Nonunique resource "+name)
            changed.append(name)
    return xml,changed

def apply(directory:Path):
    directory=directory.resolve()
    manifest=directory/"AndroidManifest.xml"
    if not manifest.is_file(): raise ValueError("Missing decoded AndroidManifest.xml")
    src=manifest.read_text(encoding="utf-8")
    if ORIGINAL_PACKAGE not in src: raise ValueError("Upstream APK manifest unexpected; package identity changed")
    # The original manifest carries an application-level literal "JunimoGate".
    # Updating only @string/app_name changes the Activity label but not the
    # launcher-visible application name in Android settings.
    application_label=re.compile(
        r'(<application\\b[^>]*\\bandroid:label=")([^"]+)(")', re.DOTALL)
    src,count=application_label.subn(
        lambda m:m.group(1)+"SMAPI Aurora"+m.group(3),src,count=1)
    if count!=1:
        raise ValueError("Upstream application label not found; cannot safely brand APK")
    # Some APKtool versions omit a manifest versionName when the source APK
    # stores the display version in its aapt resources. Keep it unchanged
    # rather than inventing a new attribute that can break Xamarin metadata.
    if 'android:versionName=' in src:
        src,n=re.subn(r'android:versionName="[^"]+"',f'android:versionName="{ANDROID_VERSION}"',src,count=1)
        if n!=1: raise ValueError("Android versionName not changed")
    manifest.write_text(src,encoding="utf-8")
    modified={"manifest":1}
    for qualifier in ("values","values-night"):
        path=directory/"res"/qualifier/"colors.xml"
        if not path.is_file():raise ValueError("Expected upstream colors not found: "+str(path))
        s=path.read_text(encoding="utf-8")
        patched,keys=change_resource(s,"color",AURORA_COLORS)
        if len(keys)<30 or "junimo_primary" not in keys:
            raise ValueError("Upstream Material3 color IDs changed; refusing broken reskin: "+str(keys))
        path.write_text(patched,encoding="utf-8")
        modified[qualifier+"_colors"]=len(keys)

    path=directory/"res/values/strings.xml"
    if not path.is_file():raise ValueError("Missing English Android strings")
    s=path.read_text(encoding="utf-8")
    new,keys=change_resource(s,"string",BRANDING)
    if "app_name" not in keys or "about_author_value" not in keys:
        raise ValueError("Expected brand strings not in official upstream APK")
    path.write_text(new,encoding="utf-8")
    modified["branding"]=len(keys)

    # Values-ru locale is only used when the device is configured for Russian.
    # Upstream manual language menu still provides System/Chinese/English only.
    locale=directory/"res/values-ru/strings.xml"
    locale.parent.mkdir(parents=True,exist_ok=True)
    contents=['<?xml version="1.0" encoding="utf-8"?>','<resources>']
    count=0
    sourcekeys=set(re.findall(r'<string\b[^>]*\bname="([^"]+)"',s))
    for key,val in LANGUAGE.items():
        if key in sourcekeys:
            if key=="app_name": val="SMAPI Aurora"
            contents.append(f'    <string name="{key}">{android_escape(val)}</string>')
            count+=1
    contents.append('</resources>')
    if count<225: raise ValueError("Unexpectedly few Russian strings: "+str(count))
    locale.write_text("\n".join(contents)+"\n",encoding="utf-8")
    modified["russian"]=count

    # The CLR assembly and game host binary payload remain unmodified, as
    # does the upstream Android manifest's package/application components.
    manifesttext=manifest.read_text(encoding="utf-8")
    if ORIGINAL_PACKAGE not in manifesttext:raise ValueError("Application ID modified")
    print("PASS: resource-only Aurora overlay",modified)


if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("directory",type=Path)
    args=arg.parse_args()
    apply(args.directory)
