# Android device test plan (after the first debug APK builds)

Aurora is an experimental source overlay. Only test with a game installation you are permitted to use. No DRM bypass, game files or modified APKs are supplied here.

## Before installing

1. Confirm your phone is **64-bit ARM64** and has enough free space for the game and extracted assets.
2. Back up Stardew Valley game saves and existing SMAPI mod settings outside the test folder. Use a test save, not your real farm.
3. Verify the GitHub Actions build **actually produced** an Android `.apk` file. A successful `source-tests` job alone does not mean an APK exists.
4. Install the `SMAPI-Aurora-Android-ARM64-debug` artifact's APK from the build workflow. This debug package is for testing, not a signed production release.

## Smoke checklist

- [ ] Launcher installs alongside the original SMAPILoader without replacing it.
- [ ] Launcher opens without crashing; Home, Mods, Settings tabs render.
- [ ] Dark theme, mod list and reduced-motion setting behave correctly.
- [ ] Installed Stardew Valley app is detected, or selectable via **Choose installed game**.
- [ ] **View game compatibility report** identifies game version, content and assembly archives.
- [ ] Incompatible APK layout produces an explanation and disables **Launch with SMAPI**.
- [ ] A compatible installed game and SMAPI Android are both recognized.
- [ ] On a disposable test save, launch enters the game and SMAPI initializes.
- [ ] Install a harmless test mod ZIP, enable/disable it, restart the app, and check persistence.
- [ ] Confirm deletion only removes the chosen mod directory.
- [ ] Confirm failure on malformed ZIP (path traversal / duplicate entries) without modifying other folders.
- [ ] Close/reopen launcher, rotate device, and verify UI state.
- [ ] Check that original saves and separate Stardew Valley installation remain unchanged.

## Bug reports

Collect the Android version, device architecture, game version, APK layout (base or split), SMAPI version, Aurora commit SHA, observed result and crash logs. Remove private paths, account identifiers, and any copyrighted game data before publicly posting logs.

**No device checkboxes are currently marked complete.** Never claim the APK is game-ready based only on source tests.
