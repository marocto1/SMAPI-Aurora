# Aurora Game Versions — implementation scope

## 1.6.15.3 build 245 — verified user-owned APKS sample (19 October 2026)

The user provided a 299,297,288-byte `.apks` archive. The archive's ZIP CRCs passed.
Three entries are present; no additional files:

| Component | Bytes | SHA-256 |
|---|---:|---|
| `base.apk` | 4,858,693 | `763c2dc5681ec8f079d0b8be590b77d12c76027769ccef957f3ae4357c120837` |
| `split_config.arm64_v8a.apk` | 53,857,797 | `efa488b4ba5d5bead3924276a565eb992f022e11e03c7688b6921a484612eeb3` |
| `split_content.apk` | 361,158,047 | `a90797b428249e040ecfc724168ba1310858855990136b5f813da6d456872d25` |

Whole `.apks` SHA-256: `f340c6a40fe545e79b44e65f1214b74367cea5bc3e47bca372009551411a27d2`.

These three component hashes exactly match the **Google Play Android test sample** listed in
[JunimoGate's game-discovery acceptance document](https://github.com/leontismaro/JunimoGate/blob/main/docs/game-discovery-result.md).
That is strong structural provenance evidence; it does not by itself prove the user's APK signatures, license status,
actual SMAPI game launch, or ability to install on a given handset.

The source menu has a version card for **1.6.15.3 build 245 / ARM64** and allows the user to save **their own private Drive download link** in Android `SharedPreferences`; no commercial APK or public download URL is tracked in this repository. On selecting the source it opens the user's supplied HTTPS Google Drive link in a browser. Drive may require the user to confirm download or authenticate; Aurora does not claim background downloads.

A downloaded `.apks` file can be selected via Android's document picker. The `AuroraSplitApkInstaller.cs` path stages all **three** components with `PackageInstaller.Session`, checks their expected sizes and SHA256 hashes while streaming, and waits for Android's package-install confirmation. It does not bypass package names, signature identities, downgrade protection or licensing checks. This is source-only until the entire host can be compiled and tested on device; build and resource tests are not gameplay validation.

Important: this format is *not* installable using the ordinary single-APK Android `ACTION_VIEW` intent; a split-package installer session is required. Keep backups and sufficient storage (around 1 GB during install).


## Stage 1 — implemented in pinned Android *source* overlay

The source overlay `junimogate-bridge/game_version_ui.py` adds a **Stardew Valley versions** button to Aurora's Home screen, with:

1. **Get/update from Google Play** — launches the Android market app for `com.chucklefish.stardewvalley`, falling back to the official HTTPS Google Play listing. Google Play decides which version to deliver to the device; this is not a specific-version binary download.
2. **Choose APK on this phone** — launches Android's system document picker and, after a warning and explicit approval, offers to open the standard Android package installer. Installation, signing checks and unknown-source permissions remain Android-controlled. It does **not** extract, mirror, rewrite, silently install, or distribute paid game APKs.
3. **SMAPI compatibility information** — explains the need for original package/signing identity, the distinction between APK and split APK sets, and that version numbers alone are not enough to certify mod compatibility.
4. **Known version 1.6.15.3 (245)** — personal Drive link slot and SHA256-bound split-APKS install preparation, always subject to Android system install approval.

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
