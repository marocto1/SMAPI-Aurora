# SMAPI Aurora v1.0.0 — Release candidate status

**Recommended current build:** [v1.0.0 RC2](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v1.0.0-rc.2). ARM64 QA APK built by [verified GitHub Actions](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39334613128).

**Critical:** v1.0.0 RC2 is a **prerelease**, not a validated stable release. CI compilation and binary consistency passed; Android in-game backup/restore, new visual/navigation screens and real upgrade migration are **not** verified on a physical device. The historical working v0.9.5 had a different temporary signing certificate. Android will not upgrade the existing installation in place when the signatures differ.

## v0.9.6 — Backup & Restore

- Native **Backup & Restore** screen accessible from the existing **Моды** tab
- SAF `ACTION_CREATE_DOCUMENT` export to user-selected ZIP, not app-private cache
- Includes both original JunimoGate private `no_backup/junimogate/user-data` (library, groups/profiles, configs, backup catalogs) and **separate** app-specific external `Saves` root
- Per-file SHA-256 integrity metadata in `aurora-backup-manifest.json`
- Explicit archive-path checks, 30,000-file/2 GiB total, 512 MiB per-file limits and original file symlink rejection
- Restore first validates archive to sibling staging directories; performs user-confirmed swap, attempts rollback on errors and **retains previous folders** for recovery
- Refuses an archive that omits mod data or game Saves when the device already has nonempty roots; no auto-delete
- **Known risk:** a crash or storage failure during a two-directory commit may require recovery; the process is not a cross-volume atomic transaction. Do not entrust your only copy of saves to this unverified RC.

## v0.9.7 — Workshop / Direct Download

- Uses the native Workshop inside **Моды**
- Nexus Mods opened in an in-app browser **without Nexus API key**, API scraping, mirroring or bypassing download rules
- Curated **author-controlled** GitHub Release ZIP download with a pinned SHA-256, HTTPS host allowlist, redirect/size/ZIP preflight
- Verified archive saved in `Downloads/Aurora` and handed to the **original .NET Mods → Import** file picker; user selects and confirms the ZIP
- No misleading “one-click installed” status; no general auto-install from Nexus. Compatibility is determined by SMAPI log.

## v0.9.8 — Game Version Manager

- Native **Версии игры** entry in the existing Mods tab
- Detects installed game version and supports importing the user's own APKS archive
- Version page no longer presents Google Drive download/source UI
- No redistribution or mirroring of paid Stardew Valley APKs
- The original build-specific signature and split-APK validation remains intact. No bypass of Android package signing.

## v0.9.9 — Visual Identity

- New app label **SMAPI Aurora**
- Native Aurora teal/midnight-violet Material palette updated in both normal and night Android resources
- Original Mods tabs now **Установленные | Workshop | Backup & Restore | Версии игры**
- Original working C# game launcher, SMAPI, stock Mods transactional code and native game library assets remain byte-for-byte identical to user-tested v0.8.9. This is an **Aurora recolor/navigation integration of existing JunimoGate visual components**, not an independently created UI design from scratch.

## v1.0.0 stable signing policy

A [fail-closed stable release workflow](https://github.com/marocto1/SMAPI-Aurora/blob/main/.github/workflows/aurora-v100-stable-gated.yml) has been prepared but **cannot release** until:
1. Real phone QA for save export/import, game launch, Workshop and version manager is independently completed and the repository variable `AURORA_V1_ONDEVICE_QA_APPROVED` is explicitly set to `true`.
2. A **persistent** Android APK release signing key has been created and securely installed in GitHub Actions repository secrets: `AURORA_RELEASE_KEYSTORE_B64`, `AURORA_RELEASE_KEYSTORE_PASSWORD`, `AURORA_RELEASE_KEY_PASSWORD`, `AURORA_RELEASE_KEY_ALIAS`, `AURORA_RELEASE_CERT_SHA256`. No private key is committed or uploaded as a public artifact.
3. The stable workflow verifies the **actual** signing certificate fingerprint and package metadata, and rechecks unchanged SMAPI runtime.

**No migration magic:** the private signing key of old, temporary QA builds was not retained; a future permanent key does not enable an Android in-place upgrade from those earlier APKs. **Do not uninstall a working version to try RC2 until mods, private configs/profiles and game saves have been independently exported and verified.** A new version's backup feature cannot retrieve private data after the old installation has already been removed.

## Credits and license

SMAPI Aurora is derived from [leontismaro/JunimoGate](https://github.com/leontismaro/JunimoGate), licensed **GPL-3.0**; original UI layout, themes, main menu and majority of managed mod/SMAPI framework derive from JunimoGate. New Aurora additions implement the Workshop navigator, native download and backup tools, color changes and QA packaging. The derivative must preserve appropriate attribution, GPL-3.0 licensing and corresponding source availability.

**User input remains required before calling this stable:** test RC2 on a device with safely backed-up data, note which features actually worked and provide anonymized crash/SMAPI logs for failures.
