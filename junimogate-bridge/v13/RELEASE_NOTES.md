# SMAPI Aurora v1.3.0 — unified RC2

**APK:** [SMAPI-Aurora-v1.3.0-rc.2-arm64-QA.apk](https://github.com/marocto1/SMAPI-Aurora/releases/download/v1.3.0-rc.2/SMAPI-Aurora-v1.3.0-rc.2-arm64-QA.apk)

**Release:** [v1.3.0-rc.2](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v1.3.0-rc.2)

**Release file SHA-256:** `14d6674b96207370885e5cc980c2f6bc66daf00c367d4eabed443bfe286c4063`

**Verified GitHub build:** [39367951818](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39368328165) (successful Android Java/d8, apktool, zipalign, apksigner, asset parity).

## Delivered in the v1.0.0–v1.3.0 consolidated APK

- **v1.0 baseline:** original v0.8.9 SMAPI/GameHost and C# Mods/Groups remain byte-identical to the version confirmed working on a device. Native Aurora sections for Backup & Restore, Versions and Workshop remain in the original Mods tab. Full local backup considers both private `no_backup/junimogate/user-data` and external app-specific `Saves` (not just mod profiles); SAF ZIP archive, manifest with per-file SHA-256, staged restore, explicit replacement prompt and recovery folders. Do not regard an unverified restore operation as a safe migration route.
- **v1.1 Workshop:** official Nexus web pages inside Aurora (no API key), optional opening in browser, category name search, favorite Nexus pages kept locally, curated author-owned GitHub Release ZIP download with pinned file SHA-256, bounded size, path screening, staging. Standard C# Mods Import remains the **only** mod installer.
- **v1.2 Smart Mod Manager:** in-app diagnostic overview, active group and enabled/missing/outdated required dependency status derived from mod manifests; buttons for **Все / Активные / Проблемы / Выключены**; SAF export of non-destructive text report to user-chosen document. This is metadata validation, **not** a promise that the DLL will load on Android or that SMAPI found no runtime errors.
- **v1.3 Aurora UI 2.0:** brand label SMAPI Aurora, sapphire + teal/blue palette for Android light/dark native Material resources, updated color integration in Mod Overview, navigation to Mods/Workshop/Backup/Versions/Diagnostics in one app. Main game launcher, critical C# libraries and mod transactions are still the upstream JunimoGate ones.

## Nexus and other source limitations

- Nexus browsing is **not** an automated unlimited mirror. Download links are controlled by the official site and its policies, user sessions and file permissions. There is **no** bypass, unauthorized scraping or automatic protected-file download.
- Curated GitHub verified install currently exposes **one first-party SMAPI smoke-test mod**. The button downloads and verifies a ZIP into Android Downloads/Aurora and then opens the original Mods file picker; the user must select/confirm the ZIP. More curated mods require authors' permission and validated release hashes. It is inaccurate to describe this as a complete public Workshop catalog or one-click Nexus installer.
- Installed third-party mods might not function on Android. Verify logs and dependencies.

## Android upgrade and save safety

**IMPORTANT: v1.3.0 RC2 has a NEW ephemeral QA signing certificate**, different from earlier versions. Android does not permit installing it over differently signed same-package APKs. Do **not** uninstall your confirmed-working installation to try RC2 without a verified external backup of mods, groups and game saves. Backups that exist only in the old Aurora app-private directory can disappear when it is uninstalled.

A [stable release workflow](https://github.com/marocto1/SMAPI-Aurora/blob/main/.github/workflows/aurora-v100-stable-gated.yml) is gated on on-device QA and a secured, persistent Android signing key. v1.3.0 RC2 is **NOT** a stable, safely upgradeable production release. An archived QA build cannot itself solve signing-key rotation.

## On-device acceptance checks

1. Open Mods → Workshop; search, categories and favorites.
2. Check game + Content Patcher mod startup and repeated save-load. Compare SMAPI log for missing dependencies.
3. Open Mods → Диагностика; toggle status filters and export report using Android picker.
4. Independently back up saves **before** testing Backup/Restore. Exercise export and checksum inspection on **nonessential test data**, not your only live farm.
5. Open Versions; inspect installed version and optionally test only a personally obtained compatible APKS (avoid changing a working paid game unnecessarily).
6. Verify no new fatal crashes and that original gameplay/save remains functional.

## Credit, original design and open-source license

This repository is based on [leontismaro/JunimoGate](https://github.com/leontismaro/JunimoGate) (GPL-3.0). Most base application layouts, the original managed Mods UI, main launcher and underlying SMAPI integration derive from JunimoGate. Aurora-specific additions include the in-app Workshop, download/backup utilities, mod-health interface, release QA, and custom palette changes. Preserve the upstream project's GPL-3.0 license and attribution.

RC2 corrects newlines in the diagnostic report's saved text; it does not change SMAPI or the game runtime.\n\nThis file documents actual implemented differences; the marketing version number does not replace the device acceptance process.
