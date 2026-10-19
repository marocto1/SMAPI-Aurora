# SMAPI Aurora v0.8.2 — certificate-aware game installation (Android 16 QA)

**Android ARM64 experimental QA. Built and signed, but not yet tested on the user's device.** This release does **not** make an unknown or differently signed Stardew Valley APK compatible with SMAPI.

## Why this release exists

The user's latest `launcher-current.txt` for Android 16 confirms:

- Old `game_preparation_failed` / `Split APK names and source paths are not aligned` **no longer occurs** on v0.8.1.
- Preparation now returns `Unsupported code=game_certificate_unrecognized`.
- The installed game source has 418,067,679 bytes hashed from one APK source; it does not present the same split installation as the verified 3-part source archive.
- JunimoGate checks the installed Android package's **signer certificate** before it can execute its managed game code. Simply changing the Android split-source fix cannot change the installed game's certificate.

## Changes from v0.8.1

The Java **Version Manager** now:
- Reads the installed `com.chucklefish.stardewvalley` package certificate from Android's `PackageManager`, including Android-verified signing rotation when available.
- Shows the actual SHA-256 signer digest and compares it to JunimoGate's tested Google Play identity `c7b27f1faf2f350e3c117875bde2353cea837ebe1b3c2ce23513bb191d95852d`.
- On a nonmatching signer, explains why the original GameHost rejects the game and prevents futile SMAPI launch / split-package-overwrite attempts. No unknown signer is added to the SMAPI allowlist.
- Gives user-directed actions for **Stardew Valley app details** and **official Google Play listing**.
- Never silently uninstalls Stardew Valley, rewrites or signs the game, wipes save files, or disables the SMAPI integrity boundary.
- Refreshes the installed signature when the user returns from Android system installation/settings.
- Retains the existing version 1.6.15.3 (245) private-link slot and the SHA256-bound, user-confirmed 3-part `.apks` installer for installations without a signature conflict.

## Compile and integrity

- [Android QA APK build and audit](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39195297699): **PASS**.
- Android app `org.junimogate.app`, version code 13.
- 0 additional SMAPI managed/native code changes. Existing v0.8.1 Android 16 split-array fix retained.
- CI proves all APK payload entries unchanged except `classes3.dex` (new version manager) and `AndroidManifest.xml` (version metadata); regenerated signing metadata excluded.
- Full original GameHost, 358 SMAPI-related runtime assets, and native libraries present.
- Signed APK SHA-256: `20a6793a3eb6f18200229fd0b73a47995feac3fd293e79daffda866cb627389b`.
- Contains no game APKs/DLLs.
- **Not tested on the affected Android 16 device.**

## What actually resolves the mismatch

The user must have the **appropriately signed** and supported Stardew Valley installation. If Android reports a different certificate for an already installed game, attempting an APK update signed with the tested certificate will generally fail with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. Back up your saves; install or restore a legitimate matching signed game through Android or the official store. You cannot fix the currently installed game's signer by updating only SMAPI, and Aurora will not bypass source trust or signature checks.

**Do not uninstall the game or launcher without first verifying save/mod backups.** Experimental Aurora v0.8.2 is signed with a disposable test key different from v0.8.1 and cannot necessarily update that prior APK without reinstalling. Android app ID remains unchanged; uninstall can remove private data.

Sources: [Java version manager](https://github.com/marocto1/SMAPI-Aurora/blob/main/junimogate-bridge/version-manager/AuroraVersionActivity.java), [v0.8.2 reproducible build](https://github.com/marocto1/SMAPI-Aurora/blob/main/.github/workflows/aurora-v082-certificate-qa.yml), [Android16 patch](https://github.com/marocto1/SMAPI-Aurora/blob/main/junimogate-bridge/android-split-source-fix.patch).
