#!/usr/bin/env python3
"""Aurora source-only compatibility policy for user-installed Android games.

Targets JunimoGate commit 029eafed917ae853d6c0a59330ee273524168296.
This does NOT patch a release APK or SMAPI AOT library; the managed host must
be rebuilt, tested and signed separately using legitimate mobile references.
Android's own APK certificate verification and installer protections remain.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

POLICY = Path("src/JunimoGate.Core/KnownGameCertificate.cs")

OLD_ENUM = """    /// <summary>The package certificate is unrelated to the certificate tested by JunimoGate.</summary>
    Unrecognized,"""
NEW_ENUM = """    /// <summary>A user-installed Android-verified single-signer Stardew Valley package.</summary>
    AuroraUserInstalled,

""" + OLD_ENUM

OLD_ALLOWED = """        Status is GameCertificateStatus.KnownTested or GameCertificateStatus.KnownTestedAfterRotation;"""
NEW_ALLOWED = """        Status is GameCertificateStatus.KnownTested or GameCertificateStatus.KnownTestedAfterRotation
            or GameCertificateStatus.AuroraUserInstalled;"""

OLD_RETURN = """        return new GameCertificateVerification(GameCertificateStatus.Unrecognized, null);
    }
}"""
NEW_RETURN = """        // Aurora accepts the game's Android-installed package identity rather than
        // requiring a single Google Play test certificate. Only the exact known
        // Stardew Valley package name (checked above) and a single Android-verified
        // signer qualify. Package/ZIP/ABI validation and live source revalidation
        // remain in JunimoGate and are not weakened by this policy.
        if (currentSigners.Count == 1 && currentSigners[0].IsValid)
        {
            return new GameCertificateVerification(GameCertificateStatus.AuroraUserInstalled, null);
        }

        return new GameCertificateVerification(GameCertificateStatus.Unrecognized, null);
    }
}"""

def apply_policy(src: str) -> str:
    out = src
    for before, after in [(OLD_ENUM, NEW_ENUM), (OLD_ALLOWED, NEW_ALLOWED), (OLD_RETURN, NEW_RETURN)]:
        if out.count(before) != 1:
            raise ValueError("Upstream JunimoGate policy changed; refusing an unsafe partial patch")
        out = out.replace(before, after, 1)
    assert out.count("GameCertificateStatus.AuroraUserInstalled") == 2
    return out

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("checkout", type=Path, help="JunimoGate source root, pinned to the supported commit")
    p.add_argument("--apply", action="store_true", help="Write the source patch, default is dry-run")
    args = p.parse_args()
    target = args.checkout / POLICY
    if target.is_symlink() or not target.is_file():
        p.error(f"Required source file missing: {target}")
    original = target.read_text(encoding="utf-8")
    if "AuroraUserInstalled" in original:
        p.error("The Aurora policy is already present")
    modified = apply_policy(original)
    if args.apply:
        target.write_text(modified, encoding="utf-8")
        print(f"Patched source: {target}")
    else:
        print(f"DRY-RUN PASS: source can be patched: {target}")
    print("Build and device verification remain required. No APK binaries were altered.")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
