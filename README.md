# SMAPI Aurora (Android)

**Prototype v0.2 — source patch, not a compiled APK.**

A community Android-only UI and installed-game compatibility experiment based on [NRTnarathip/SMAPILoader](https://github.com/NRTnarathip/SMAPILoader), upstream `master` commit `092c6864838dd2118d216cb3e03f3c731ad17c08`.

## Features in the patch

- Graphite/purple/mint Android launcher design with animated navigation and buttons.
- Mod list search, enabled/disabled counters and ZIP mod installation UI.
- Installed application selection with a broader search for game content and .NET assemblies in base or split APKs.
- Performance improvement to UI-thread synchronization and additional ZIP extraction path validation.

## Status

This repository contains **patch source** to apply to the original Android loader, **not** a complete, tested APK. No compiled release has been published. Device testing and compilation are still necessary. The patch does not include Stardew Valley, purchased game assets, DRM bypasses, or guarantees for modified builds. Support depends on game format and SMAPI Android compatibility.

## Apply to upstream source

```bash
git clone https://github.com/NRTnarathip/SMAPILoader.git
python3 apply_aurora.py ./SMAPILoader --dry-run
python3 apply_aurora.py ./SMAPILoader
```

For a compiled Android application, see [upstream build instructions](https://github.com/NRTnarathip/SMAPILoader/blob/master/docs/building.md). A real build requires .NET 9, Android SDK, JDK 17, custom Mono runtime and legitimate game dependencies. No Windows app is included.

## License and attribution

Based on NRTnarathip's [SMAPILoader](https://github.com/NRTnarathip/SMAPILoader). Retain attribution and comply with **GPL-3.0** and third-party library licenses when redistributing modifications. This project is not affiliated with ConcernedApe or the original launcher author.

## Project files

- `apply_aurora.py` — source integrator with backups and dry run.
- `compat/` — installed APK detection/compatibility patch.
- `overrides/` — Android UI replacement source.
- `tests/` — basic offline patch validation.

No game data or signing keys are distributed.
