#!/usr/bin/env python3
"""Fail-closed Android APK upgrade signing audit for SMAPI Aurora.

Does not install, remove, resign or modify APKs or user data. Must be used
before labeling any build an in-place upgrade. Android typically rejects an
update whose app signing cert does not match the installed package's signer.
"""
import argparse
import re
import subprocess
from pathlib import Path


def _capture(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise ValueError(f"APK verification failed: {command[0]} exited {result.returncode}")
    return result.stdout


def signing_ids(apk: Path, apksigner: str) -> tuple[str, ...]:
    if not apk.is_file():
        raise FileNotFoundError(apk)
    output = _capture([apksigner, "verify", "--verbose", "--print-certs", str(apk)])
    # Android build-tools vary in whitespace, casing and colon separators.
    digest = []
    for line in output.splitlines():
        if not re.search(r"Signer\s*#\d+.*certificate\s+SHA-256\s+digest", line, re.I):
            continue
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        candidate = parts[1].strip().lower().replace(":", "")
        if re.fullmatch(r"[a-f0-9]{64}", candidate):
            digest.append(candidate)
    if not digest:
        raise ValueError("No verified Android signing identity")
    return tuple(sorted(set(x.lower() for x in digest)))


def package_and_version(apk: Path, aapt: str) -> tuple[str, int, str]:
    output = _capture([aapt, "dump", "badging", str(apk)])
    match = re.search(
        r"^package:\s+name='([^']+)'\s+versionCode='(\d+)'\s+versionName='([^']*)'",
        output, flags=re.MULTILINE,
    )
    if not match:
        raise ValueError("APK package metadata unavailable")
    return match.group(1), int(match.group(2)), match.group(3)


def compare(old: Path, new: Path, apksigner: str, aapt: str) -> tuple[bool, str]:
    old_name, old_code, _ = package_and_version(old, aapt)
    new_name, new_code, _ = package_and_version(new, aapt)
    if old_name != "org.junimogate.app" or new_name != old_name:
        return False, "Package ID mismatch: this is NOT an Aurora update"
    if new_code <= old_code:
        return False, "New APK versionCode is not greater"
    old_signing = signing_ids(old, apksigner)
    new_signing = signing_ids(new, apksigner)
    if old_signing != new_signing:
        return False, (
            "SIGNING MISMATCH: Cannot safely update installed Aurora in place. "
            "Do NOT uninstall without separately verified backup of private "
            "mods, profiles, configs and saves."
        )
    return True, "Signing identity and versionCode permit an in-place Android upgrade."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installed_apk", type=Path)
    parser.add_argument("candidate_apk", type=Path)
    parser.add_argument("--apksigner", default="apksigner")
    parser.add_argument("--aapt", default="aapt")
    parser.add_argument(
        "--expect-mismatch", action="store_true",
        help="CI negative test: succeed only if compatibility is refused",
    )
    args = parser.parse_args()
    good, reason = compare(args.installed_apk, args.candidate_apk,
                           args.apksigner, args.aapt)
    print("PASS — " + reason if good else "BLOCK — " + reason)
    if args.expect_mismatch:
        return 0 if not good else 1
    return 0 if good else 2


if __name__ == "__main__":
    raise SystemExit(main())
