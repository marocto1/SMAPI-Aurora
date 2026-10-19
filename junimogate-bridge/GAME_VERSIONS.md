# Aurora Game Versions — implementation scope

## Stage 1 — implemented in pinned Android *source* overlay

The source overlay `junimogate-bridge/game_version_ui.py` adds a **Stardew Valley versions** button to Aurora's Home screen, with:

1. **Get/update from Google Play** — launches the Android market app for `com.chucklefish.stardewvalley`, falling back to the official HTTPS Google Play listing. Google Play decides which version to deliver to the device; this is not a specific-version binary download.
2. **Choose APK on this phone** — launches Android's system document picker and, after a warning and explicit approval, offers to open the standard Android package installer. Installation, signing checks and unknown-source permissions remain Android-controlled. It does **not** extract, mirror, rewrite, silently install, or distribute paid game APKs.
3. **SMAPI compatibility information** — explains the need for original package/signing identity, the distinction between APK and split APK sets, and that version numbers alone are not enough to certify mod compatibility.

The source patch adds `REQUEST_INSTALL_PACKAGES` to Aurora's Android manifest solely for **user-initiated local APK installation**. Official Google Play distribution policies may restrict such permissions. Review publishing policy before offering the modified app via Play.

Translated resource entries are included in both English and Russian. CI must pass pinned upstream source-check, Android AAPT2 resources, and the new static contract tests.

**Status: Source UI, not yet present in the published `v0.7.0-runtime-qa` APK.** That APK is a resource-only repackaging of the original JunimoGate runtime, without new C# interactions. Shipping this feature in an integrated APK requires the full source-based JunimoGate Android GameHost build, which is blocked on compatible user-provided private Android game compilation references. Do not claim the button works in an older QA APK.

## Stage 2 — tailor to one user-supplied Stardew Android APK

The next user-provided input should be a **legitimately obtained APK from the user's own installation**, and, for split installations, the matching **base APK, ARM64 split, and content split**. Send these privately in this conversation — do not commit, attach to public GitHub issues, or place them in GitHub Actions artifacts or releases.

Inspect locally for:
- App package ID, versionName, versionCode, target API, ABI;
- Current signer certificate digest and its comparison to JunimoGate's known tested signing identities;
- base/split roles and AssemblyStore format (v1/v2), installed-game Content;
- Mobile-specific `StardewValley.dll`, `StardewValley.GameData.dll`, `BmFont.dll`, `Lidgren.Network.dll`, `xTile.dll` metadata extracted **locally for compile references**, without uploading these to public repositories;
- mobile `MainActivity` and lifecycle method signatures;
- Semantic compatibility recipe findings and isolated GameHost preparation tests.

Report support status based on the actual signer and structural findings, **not** on versionName alone. Do not bypass game license/signature validation.

## Version catalog design

- **Official current release**: always a verified Google Play link, no mirrored paid binary.
- **User-owned local APK**: file picker and Android system confirmation; no silent install.
- **Previously tested supported builds**: records of *version, ABI, package ID, signer evidence and compatible SMAPI runtime*, not downloadable commercial game files.
- **Older official versions**: cannot generally be chosen directly by the consumer in Google Play; no fake download buttons.
- **No destructive automatic downgrade**: if a different-signature install or downgrade is blocked by Android, explain the block and tell the user to back up data before making any manual changes.
