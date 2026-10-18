# SMAPI Aurora v0.5.0 — Android game compatibility diagnostics

**Android-only source patch. Not a compiled or device-tested APK.**

## Android APK build (GitHub Actions)

An [Android ARM64 debug APK build workflow](.github/workflows/android-build.yml) is now included. It uses a GitHub-hosted Linux runner, Java 17, .NET 9.0.312 and the Android workload, so **no Windows machine is required**. The workflow automatically checks out the pinned original launcher, applies Aurora, and builds a debug APK when its private build requirements are present.

**Current blocker:** the original loader requires three game-derived reference DLLs that are not provided in this public repository. The [first APK build attempt](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39114396985) failed at the dependency preflight, not at C# compilation. An APK has **not** been produced.

Read [BUILD_STATUS.md](BUILD_STATUS.md) for precise secret names and private archive requirements, and [Android device test plan](docs/ANDROID_DEVICE_TEST_PLAN.md) for testing once a binary exists. Do not upload paid game assets into public GitHub source or artifact archives.



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