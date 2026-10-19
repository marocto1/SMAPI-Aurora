# SMAPI Aurora v0.8.0 — Android Version Manager (QA)

**This is an experimental, unsigned-for-production, Android ARM64 QA build with the complete original JunimoGate/SMAPI runtime. It has NOT passed physical Android device/gameplay tests.**

## What's new

- New **Aurora Version Manager** opens before the existing SMAPI launcher.
- Dedicated card for Stardew Valley Android **1.6.15.3 / build 245 / ARM64**, matching the private game-archive sample provided for analysis.
- View the game's currently installed version from Android PackageManager.
- **Download from my Google Drive** opens a personal, user-entered `drive.google.com/file/d/…` link in a browser. This personal URL is **not built into the APK** or distributed. The user must enter the link once. There is no background authenticated Drive download.
- **Choose downloaded .apks** opens Android's document picker. The Java installer verifies an exact three-split set (`base.apk`, `split_config.arm64_v8a.apk`, `split_content.apk`) and SHA-256 of each original component before committing an Android `PackageInstaller.Session`. Android still displays its own install approval and enforces signing/version safety.
- **Update via Google Play** opens the game's official Play listing.
- **Launch SMAPI Aurora** starts the existing, unmodified JunimoGate .NET SMAPI launcher.

## QA outcome

- [Android build / APK packaging run](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39189042374): PASS.
- Package ID: `org.junimogate.app` (preserved to avoid breaking CLR bindings).
- Version code: `12`; version name: `0.8.0-aurora-version-qa`.
- Main launcher: `org.junimogate.aurora.AuroraVersionActivity` (Java).
- Existing managed and native files **358 checked files byte-for-byte identical** to the v0.7.0 QA baseline, including bundled SMAPI/JunimoGate GameHost.
- Contains no paid Stardew Valley APKs or game DLLs.
- SHA-256 of QA APK: `14ee61ecce19d3f8efdd891b9342ab8814e893136ace51d2aac3add1caef33e5`.
- Android device launch, Google Drive browser roundtrip, and actual split install **not yet tested**.
- The earlier `game_preparation_failed` may still occur because the C# SMAPI/GameHost execution path is unchanged.

## Installation warnings

**Back up all private app data, mods and saves before changing any launcher installation.** This QA build has the same Android package ID as official JunimoGate and earlier Aurora runtime builds, but a different signing certificate. Android will reject an update over an installation signed by a different certificate. Uninstalling can erase app-private data; do not uninstall until backups are verified.

For Stardew Valley, replacing or downgrading an installed game can be refused by Android. Never delete or overwrite game data merely to change game versions. If installation fails, capture the Android error, without bypassing package/signer verification.

## License/source

- [SMAPI Aurora version manager Java source](https://github.com/marocto1/SMAPI-Aurora/tree/main/junimogate-bridge/version-manager)
- [Reproducible QA APK build workflow](https://github.com/marocto1/SMAPI-Aurora/blob/main/.github/workflows/aurora-version-manager-apk.yml)
- [JunimoGate upstream source (GPL-3.0 and exception)](https://github.com/leontismaro/JunimoGate)
- [SMAPI Android fork (LGPL-3.0)](https://github.com/leontismaro/JunimoGate-SMAPI)
