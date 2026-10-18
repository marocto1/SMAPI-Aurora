# SMAPI Aurora v0.6.0 Preview

**An installable native Android companion APK, not yet a full SMAPI runtime.**

The Android Preview provides Aurora's custom interface, installed Android game selection, structural base/split APK diagnostics, and **launching the ordinary game without SMAPI**.

## Mod Manager in v0.6

- Use Android Files to select a Mods workspace folder you can read and write.
- Import compatible mod ZIPs with path and size validation.
- Read manifests and display required dependency warnings and duplicate UniqueIDs.
- Filter installed mods by All / Enabled / Disabled / Issues.
- Enable or disable a mod by renaming its folder to remove/add a leading dot.
- Delete a selected mod folder only after explicit confirmation. The selected workspace root cannot be deleted or toggled.
- All operations depend on Storage Access Framework permissions; Android 11+ often restricts Android/data access.

The package ID is `com.marocto.smapi.aurora.preview06`, separate from v0.5.1 due to ephemeral debug signing keys. Preview APKs are experimental and device behavior has not yet been verified.

See [the real .NET build blocker](../BUILD_STATUS.md) for the full SMAPI launcher. The native preview cannot load SMAPI mods **inside Stardew Valley**.
