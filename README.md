# SMAPI Aurora v0.4.0 — Android mod manager

**Android-only source overlay. Not a built or device-tested APK.**

Aurora extends [NRTnarathip/SMAPILoader](https://github.com/NRTnarathip/SMAPILoader) with a custom Android UI and improved source compatibility. The integration targets upstream [092c686](https://github.com/NRTnarathip/SMAPILoader/commit/092c6864838dd2118d216cb3e03f3c731ad17c08), under GPL-3.0. Original upstream developers retain attribution.

## New in v0.4 — Advanced Mod Manager

- New **Issues** filter, **Run dependency diagnostics** action, and per-mod warning counts.
- Read-only manifest checks: missing/disabled required dependencies, ContentPackFor framework, duplicate UniqueID, invalid manifests and minimum version mismatches.
- ZIP archive checks **before extraction**: path containment, entry-count and expanded-size caps, duplicate file paths.
- Mod deletion now rejects paths outside the Mods directory and correctly reports errors instead of false success.
- Optional mod-pack completion callback is now null-safe.
- Includes v0.3 interface, reduced-motion settings, game selection and SMAPI management.

**Limitations:** Local diagnostics are heuristic and do not guarantee Android mod compatibility. ZIP extraction is not transactional; imported files may overwrite existing mods. Back up game saves and Mods before using an experimental build. It does not bypass DRM or provide copyrighted game files.

## How to apply to the upstream source

```sh
git clone https://github.com/NRTnarathip/SMAPILoader.git
git -C SMAPILoader checkout 092c6864838dd2118d216cb3e03f3c731ad17c08
python3 apply_aurora.py SMAPILoader --dry-run
python3 apply_aurora.py SMAPILoader
```

Apply the overlay with Python 3.10 or later; source backups are created. Android package ID: `com.marocto.smapi.aurora`, version: `0.4.0`.

The CI checks Python syntax, mock integration and patch application to pinned upstream code. **It does not compile or test an Android APK.** A build additionally needs .NET 9, Android SDK, JDK, upstream patched Mono and compatible game-derived references. No APK or game DLLs are redistributed.

## Source layout

- `overrides/` — Android UI and mod inspection/archive safety helpers.
- `compat/` — compatible installed APK detection.
- `apply_aurora.py` — source patcher with file backups.
- `tests/` — offline integration checks.