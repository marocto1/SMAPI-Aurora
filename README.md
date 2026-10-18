# SMAPI Aurora — Android launcher

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