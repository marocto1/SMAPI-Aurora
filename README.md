# SMAPI Aurora v0.3.0 — Android launcher prototype

**Android-only source patch; no APK has been built or verified yet.**

Aurora is a community UI and compatibility overlay for [NRTnarathip/SMAPILoader](https://github.com/NRTnarathip/SMAPILoader), tested against upstream commit [`092c686`](https://github.com/NRTnarathip/SMAPILoader/commit/092c6864838dd2118d216cb3e03f3c731ad17c08). It retains the original project's GPL-3.0 attribution and license.

## What's new in v0.3

- Updated Android home screen, gradient play panel, readiness state and clearer setup steps.
- Game compatibility verification runs outside of the UI thread, to reduce freezes during APK scanning.
- A new Settings tab with an option to disable motion; animations respect Android's animator duration scale.
- Mod manager now filters All / Enabled / Disabled; searches are case-insensitive and the list is sorted by name.
- Improved navigation and tab restoration after activity recreation (e.g. rotations).
- Separate Android application ID `com.marocto.smapi.aurora`, display version `0.3.0`.
- Source CI now checks the patch against **real pinned upstream code**, not only mock fixtures.

## Features retained from v0.2

- Installation/source selection of compatible installed Stardew Valley APKs, including single APK and split APK layout recognition.
- SMAPI Android ZIP install/remove UI, mod import, toggle and delete operations.
- Avoid CPU busy-spin in UI dispatcher, reject ZIP entries that escape the target folder.

## Reproduce the source integration

```sh
git clone https://github.com/NRTnarathip/SMAPILoader.git
cd SMAPILoader && git checkout 092c6864838dd2118d216cb3e03f3c731ad17c08 && cd ..
python3 apply_aurora.py SMAPILoader --dry-run
python3 apply_aurora.py SMAPILoader
```

This is an **overlay/patch project**, not the complete upstream tree or a downloadable working launcher. Building a signed APK needs a properly configured .NET 9 / Android SDK toolchain, upstream custom Mono and compatible dependencies including game-derived .NET references. Do not upload copyrighted game DLLs to a public repository. The CI workflow verifies patch application, **not compilation or device behavior**.

The package selector is not a DRM bypass and cannot guarantee support for modified or unauthorized game copies. No game data, APKs, decryption keys or credentials are provided. Redistribution is subject to GPL-3.0 and third-party license obligations.

## Layout

- `apply_aurora.py` — applies overlays and source compatibility fixes with backups.
- `overrides/` — new UI screens and activity changes.
- `compat/` — installed APK recognition and extraction improvements.
- `tests/` — mock-source smoke tests.
- `.github/workflows/source-tests.yml` — pinned upstream integration verification.