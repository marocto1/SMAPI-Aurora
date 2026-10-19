## SMAPI Aurora v0.8.6 — Settings → Version Settings (experimental QA)

[**Download v0.8.6 Android ARM64 APK**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.6-version-settings-qa) · [GitHub Actions packaging and integrity audit](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39201191210)

The Aurora **Java entry screen** now includes an actual navigable `Настройки` → `Настройки версий` page, not just a diagnostic button on the home page. It displays the installed Stardew version, catalogues the one currently SHA-256-verified `1.6.15.3 build 245` ARM64 archive, and provides the existing in-app Google Drive downloader, source configuration, and local `.apks` installer. The home screen retains **Играть с модами**, which does not require a game download.

**Important scope:** this is Aurora's outer Java Settings screen. The separately bundled native/managed `JunimoGate.App` Settings tab is **not modified** by this QA release. The existing v0.8.5 installed-game Core policy, SMAPI/GameHost and Android 16 split fix remain unchanged, confirmed by the payload audit. Other game versions are not falsely marked compatible.

Optional Drive download still needs a previously configured personal source. The previously shared exact Drive URL could not be recovered from the available project state and is not embedded in the public APK. Game execution/device gameplay remains unverified. New disposable QA signing keys may prevent in-place updates of earlier Aurora releases. Back up saves, mods and launcher settings before changing the installed launcher.

## SMAPI Aurora v0.8.5 — user-installed Stardew Valley compatibility (experimental QA)

[**Download the v0.8.5 Android ARM64 APK**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.5-installed-game-qa) · [GitHub Actions build & APK payload audit](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39199603931)

This experimental release **rebuilds and replaces exactly JunimoGate.Core's managed ARM64 ELF** with a source-level policy that accepts Android-verified **single-signer** installed `com.chucklefish.stardewvalley` even when the signer differs from the tested Play signer. It retains the upstream package-name boundary, PackageManager-installed identity, snapshot revalidation, APK source ZIP hashing, ABI checks, original GameHost/SMAPI and v0.8.1 Android 16 split-source repair. The launch screen remains simplified as in v0.8.4.

**Scope and limitations:**

- **PASS:** .NET 9 policy source compiles; signer-policy smoke tests pass; the repacked APK passes its integrity audit (only `lib/arm64-v8a/lib_JunimoGate.Core.dll.so` and `AndroidManifest.xml` changed). No game binaries are bundled.
- **UNVERIFIED:** launch and modded gameplay on the affected Android 16 device. Other incompatibilities may remain, including source layout or version differences. No broad claim is made about every third-party APK or other Android package names.
- Other Android signing protections still apply. The APK comes from a user-selected Android installation; an unknown signer does **not** guarantee authenticity or safety. Avoid untrusted game files.
- **Automatic Drive download remains unconfigured on a fresh install:** the exact private Drive URL was not recoverable and was not embedded in a public APK. This is not required when the game is already installed. A separately configured source is required for optional download/reinstall.
- **Launcher update caveat:** experimental APKs use new test signing keys each release; Android may block installing v0.8.5 over older Aurora/JunimoGate packages with the same ID. Back up saves, mods and app-private data before any uninstall. There is not yet a production-grade stable update-signing process.

Source: [local installed signer patch](junimogate-bridge/allow_installed_signer.py), [Core ELF repacker](junimogate-bridge/version-manager/rewrap_managed_core_elf.py), [packaging workflow](.github/workflows/aurora-v085-installed-game-qa.yml).

## SMAPI Aurora v0.8.4 — comfort launch (experimental QA)

[**Aurora v0.8.4 APK / release**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.4-comfort-launch-qa)

This changes **Aurora's Java front-end**, not its bundled managed GameHost:

- Makes **Играть с модами** the primary button: use the already installed game; no Drive download or reinstall is required merely to attempt a launch.
- Adds a clearly labeled **Запустить обычную Stardew Valley** fallback.
- Removes Aurora's own signer-mismatch hard-stop from the SMAPI launch and APKS installation buttons and hides technical certificate diagnostics from the default screen.
- Keeps the optional in-app Google Drive APKS download flow from v0.8.3. A **private URL still needs one-time configuration if it was not already saved on the device**. The actual previously shared Google Drive file ID was not recoverable, and is not embedded in this public release.
- Android still enforces package update signatures. The **unchanged JunimoGate GameHost** may still reject a game signed with a certificate other than its tested Play build with `game_certificate_unrecognized`. This front-end QA release does *not* fix that managed restriction, and has not passed an on-device modded launch.
- This QA APK is signed with a new, disposable test key. It may be blocked as an in-place update to an earlier Aurora build. Back up saves, mods and private app data before any uninstall.

## SMAPI Aurora v0.8.3 — in-app Google Drive auto-download (QA)

[**Download v0.8.3 Android ARM64 QA**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.3-drive-autodownload-qa).

- The **Download and install automatically** button now downloads the owner's configured `Stardew Valley_v1.6.15.3.build.245.apks` inside Aurora, shows download progress, validates the exact three APK entries and per-file SHA-256, and starts the standard Android PackageInstaller confirmation. No browser or document picker is needed for that path.
- Source URL remains private in Android SharedPreferences. **No personal Google Drive URL is baked into public source or APK**. Because the previously supplied URL/ID was not recoverable from the available project state, fresh installs with no stored source still need a one-time private source configuration. This is a known limit; do not mistake the APK alone for a preconfigured personal download link.
- Google Drive must permit HTTPS download for the selected share link; account-required or HTML confirmation flows may fail with a clear status instead of installing HTML.
- Android signing integrity remains enforced. A differently signed existing Stardew Valley installation will still block compatible replacement until the user safely backs up game data and resolves the signature conflict through Android. Aurora will not uninstall/re-sign the game.
- This is experimental QA: GitHub Actions compilation and payload audits are not an Android device gameplay test. The v0.8.3 QA APK has a newly generated signing certificate, so it may be incompatible as an in-place update to earlier QA launchers. Back up saves, mods and app-private settings first.

## SMAPI Aurora v0.8.2 — installed Stardew certificate diagnosis (QA)

[**Download v0.8.2 QA**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.2-certificate-diagnostics-qa).

The latest Android 16 `launcher-current.txt` shows that v0.8.1 **fixed the original split APK alignment exception**. The remaining error is `game_certificate_unrecognized` because the installed game's Android signing identity differs from JunimoGate's tested Google Play certificate.

Aurora v0.8.2 now reads and displays the installed game's SHA-256 signing certificate and offers safe Google Play / game-app-settings actions. It warns against futile installation over a differently signed copy rather than attempting to bypass Android/SMAPI security. The **Android16 split-source hotfix and all original SMAPI/GameHost binaries are preserved**, with only the Java version chooser DEX and Android app version metadata changed. [QA build and integrity check PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39195297699).

**Android hardware behavior and gameplay have not been verified. The installed Stardew game's signer cannot be changed by updating Aurora; use an appropriately signed game installation and back up saves before replacing anything.** v0.8.2 uses a disposable APK QA signing certificate and can conflict with prior Aurora builds under the same app ID. [Detailed release notes](junimogate-bridge/CERTIFICATE_QA_V082.md).

## Android 16 crash fix — SMAPI Aurora v0.8.1 QA

[**Download v0.8.1 Android 16 split APK preparation hotfix**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.1-android16-split-fix-qa).

The user-provided `launcher-current.txt` isolated `game_preparation_failed` to
`AndroidPackageInstallationSnapshotProvider.ReadSources()` with the exception
`Split APK names and source paths are not aligned`, *before any game APK was opened*.
Aurora's v0.8.1 APK recompiles **only** the Android package-source snapshot provider:
it pairs `ApplicationInfo.SplitNames` with `ApplicationInfo.SplitSourceDirs`, as
required by the Android SDK, with a strict count-checked fallback. No game
signature/entitlement checks were relaxed. The existing Aurora v0.8 Java version
manager, full SMAPI/GameHost runtime and all other APK code/resource contents
were preserved byte-for-byte; CI verifies exactly one changed library.

[CI build and APK integrity audit PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39190650579).
**Real on-device startup remains unverified; the old preparation error should be
retested.** The experimental APK has a different QA signing certificate from
older Aurora/JunimoGate releases while retaining the same Android package name.
Back up app-private data/mods/saves *before* any uninstall or replacement.
[Detailed diagnostics and source patch](junimogate-bridge/ANDROID16_HOTFIX_NOTES.md).

## SMAPI Aurora v0.8 — version manager QA APK

[**Download SMAPI Aurora v0.8.0 Version Manager + full SMAPI APK (123 MB)**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.8.0-version-manager-qa).

This QA build starts in a new Java Android version chooser embedded in the existing full JunimoGate SMAPI APK. It includes the original unchanged SMAPI/GameHost runtime plus a user-configured personal Google Drive download link slot, verified Stardew Valley 1.6.15.3 build 245 three-split `.apks` installation flow via Android PackageInstaller, official Play Store link, and button opening the original SMAPI launcher. No paid game binaries or public paid-download links are bundled.

The Android APK and installer UI compiled successfully, APK is signed and audited, and 358 original runtime files match byte-for-byte. **Physical device/game preparation has not yet been tested; `game_preparation_failed` may still occur.** This version uses a new QA certificate and cannot directly update an existing differently signed Aurora/JunimoGate installation. Back up your private app data and saves before any uninstall. [Details and licensing](junimogate-bridge/VERSION_MANAGER_RELEASE_NOTES.md).

# SMAPI Aurora — Android launcher

## New experimental complete-SMAPI Android binary (19 October 2026)

[**SMAPI Aurora v0.7.0 Runtime QA APK — 123 MB**](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.7.0-runtime-qa) has been built and SHA256-verified. It includes the complete original JunimoGate v0.3.1 SMAPI Android GameHost and retains all 358 checked runtime payload files byte-for-byte, while applying Aurora app branding, resource palette and Russian UI strings through a documented APK resource-only adaptation.

**Important limitations:** This is not our C# source-rebuilt full GameHost, and **its startup or mods have not been tested on a physical Android device**. It is a QA prerelease, not a guaranteed functional release. The Android application ID remains `org.junimogate.app` to preserve original .NET runtime binary references, and it has an independent QA certificate; it cannot update an existing JunimoGate installation without uninstalling it, which can delete private app data. Back up saves and mods first. The upstream game-package/signer checks remain unchanged.

- [Resource-only Aurora APK patch](junimogate-bridge/brand_upstream_apk.py)
- [Original/runtime byte-equivalence auditor](junimogate-bridge/audit_runtime_apk.py)
- [Successful Android build and QA](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39181321232)
- [Source correspondence and full limitations](junimogate-bridge/RUNTIME_QA_RELEASE_NOTES.md)



## New development path: Aurora with JunimoGate SMAPI runtime

The old SMAPILoader source overlay is now retained for reference and existing
v0.6.1 Preview releases. The active full-runtime migration is the
[JunimoGate bridge](junimogate-bridge/README.md): it applies the Aurora app
identity, theme and Russian UI onto pinned open-source JunimoGate, while
preserving its actual SMAPI GameHost, mod management, and Android game checks.

- [Pinned bridge source patch](junimogate-bridge/apply_aurora.py)
- [Integration and XML validation workflow](.github/workflows/junimogate-bridge.yml)
- [Licensing, limitations and build prerequisites](junimogate-bridge/README.md)

**Important:** This is a source migration, **not** a ready-to-install
Aurora SMAPI release. The full Android build and real-device mod tests have
not yet been completed, and genuine mobile game compiler references remain
necessary. JunimoGate also validates installed-game signer identity.


**Latest installable companion:** [v0.6.1 Preview APK](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.6.1-preview). It manages a selected mod folder but does **not** load SMAPI into the game.

**Full SMAPI Aurora launcher:** source overlay targeting .NET 9 Android; **NOT YET A WORKING RELEASE**. The complete game-launching runtime has not passed Android compilation and device tests.

## Building the full SMAPI launcher

The [Android ARM64 build workflow](.github/workflows/android-build.yml) now supports an optional automatic, legally published **API-only reference** fallback from [StardewModders/mod-reference-assemblies](https://github.com/StardewModders/mod-reference-assemblies), plus the open-source MonoGame Android NuGet package. This can test compilation without installed game binaries, but **does not contain Android-specific game APIs and is insufficient for a working SMAPI APK**.

The original launcher still needs genuine compatible Android `StardewValley.dll`, `StardewValley.GameData.dll`, and `MonoGame.Framework.dll` as private compile-time references, plus a modified Mono runtime and verified SMAPI Android binaries. Paid game assemblies must never be published in this source repository or distributed in the launcher APK.

Read [BUILD_STATUS.md](BUILD_STATUS.md) for verified failure logs, build modes and remaining blockers. See [Android device test plan](docs/ANDROID_DEVICE_TEST_PLAN.md) before considering a non-preview release.



SMAPI Aurora extends [NRTnarathip/SMAPILoader](https://github.com/NRTnarathip/SMAPILoader) using a source overlay tested against upstream commit [`092c686`](https://github.com/NRTnarathip/SMAPILoader/commit/092c6864838dd2118d216cb3e03f3c731ad17c08). Original copyright notices and GPL-3.0 apply.

## What's new in v0.5

- Game-source diagnostics from the **Home → View game compatibility report** button.
- Read-only examination of an installed Android application's base/split APKs: required `assets/Content/`, .NET assembly-store markers, reported game version, unreadable APKs and actionable reasons for incompatibility.
- Refresh installed package metadata during diagnostics, including after updating the game.
- Only APKs containing .NET assembly-store markers are sent to the game assembly extractor; content-only splits are skipped.
- Clearer game-card readiness feedback and version labels updated to v0.5.0.

## Retained from v0.4

- Dark responsive Android UI, reduced-motion settings, mod manager search and filters.
- Manifest dependency diagnostics, archive import safeguards and safer mod deletion.
- Select a compatible installed Android game package without requiring a specific app store.

## Integrate

```sh
git clone https://github.com/NRTnarathip/SMAPILoader.git
git -C SMAPILoader checkout 092c6864838dd2118d216cb3e03f3c731ad17c08
python3 apply_aurora.py SMAPILoader --dry-run
python3 apply_aurora.py SMAPILoader
```

Requires Python 3.10+. The overlay targets Android .NET 9 with application ID `com.marocto.smapi.aurora`. Source modifications create backup files.

**Important limitations:** A compatible APK layout does not prove a version is safe, authentic, licensed or executable. The diagnostic is a structural preflight only. Aurora does not provide copyrighted game data or modify purchase checks. Runtime testing is required for any modified builds. The Android app must still be compiled with the correct .NET 9 Android toolchain, custom Mono runtime and compatible game-derived references. CI validates source integration only; it does **not** compile or test an APK.

## Contents

- `overrides/` — launcher UI, APK diagnostics, mod manager, archive checks.
- `compat/` — game package detection and APK extraction integration.
- `apply_aurora.py` — pinned upstream source patcher.
- `tests/` — mock-source integration tests.
- `.github/workflows/source-tests.yml` — source patch validation.