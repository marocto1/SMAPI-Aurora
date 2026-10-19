# Aurora Android signing, backups and v0.9.5 upgrade safety

**Current verified result:** the original user-tested v0.8.9 QA and newly published v0.9.5 QA have **different APK signing certificates**. An Android in-place install/upgrade of v0.9.5 over v0.8.9 is **not supported**.

The failure is verified by [Signing Compatibility Guard — successful negative test](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39229775288). This workflow downloads **immutable SHA-256 pinned release APKs**, runs Android `apksigner verify --print-certs` and compares the package name, monotonic versionCode and certificates. It reports `BLOCK — SIGNING MISMATCH` as expected. It deliberately returns green only because it has been told to **expect a mismatch**; it does not assert the APK can update.

## What's implemented

- `verify_upgrade.py` rejects package-ID mismatch, same-or-lower versionCode and different signing fingerprints; fails closed for unsigned/broken APKs.
- Regression tests enforce those failures and the positive matching-key upgrade case.
- CI compares **actual signed release APKs** rather than trusting filenames, version names or repository metadata.
- No APK/data deletion, signing-key removal, hidden migration or automatic uninstall.

## What is *not* yet solved

The v0.8.9 and v0.9.5 QA APKs used freshly generated **temporary private signing keys**. Retaining the certificate public digest cannot recreate its private key. Without the original installed application's private signing key, Android does not normally permit a same-package in-place update. A new permanent signing key will only enable **future** in-place upgrades from the first APK signed with that key; it does not convert prior QA installs in place.

## Real migration needed before safe stable v1.0

1. **Do not uninstall a working Aurora** until user data has been separately exported and the backup tested. App-private `no_backup/junimogate/user-data/mods` contains imported archives and metadata; `profiles` contains active groups; saved-game roots must be inventoried. Aurora's own group export is not necessarily a comprehensive backup of all app-private files or Stardew saves.
2. Implement and **device-test an export/import migration** flow in the already installed Aurora version, or provide a separate fully user-consented backup mechanism. Export into a user-selected location outside the app's private data partition. Validate ZIP paths, hashes and contents before restoration.
3. Generate a persistent signing key offline and secure it **outside the public GitHub repository** (e.g., Actions secrets with protected release workflow). Do not commit `.keystore`, private keys, passwords or encoded key files.
4. Sign the first new stable APK with that key, publish its SHA-256 certificate fingerprint and enforce it for every future stable release using `verify_upgrade.py`.
5. Test actual Android package update, save load, mod group restoration, workshop download and SMAPI gameplay on phone before a non-QA release.

**Never instruct users to uninstall Stardew Valley to update the Aurora launcher.**

## v0.9.5 Workshop scope

Aurora's new GitHub ZIP path downloads only a first-party test mod from a verified GitHub Release, checks a pinned SHA-256, screens the ZIP, saves the verified file in Android Downloads/Aurora and asks the stock Mods import picker to install it with user confirmation. It is a **real direct download** but **not fully automatic one-tap library installation**. Nexus remains website/manual-download without API. APK package build tests passed; real Android UI and download flow are not yet tested on the user's device.

[APK release](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.9.5-direct-download-qa) · [Full build QA](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39229050051)
