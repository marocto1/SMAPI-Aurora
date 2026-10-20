# SMAPI Aurora v1.4.0 RC1 — Stability & Coop Readiness

**QA APK:** [SMAPI-Aurora-v1.4.0-rc.1-arm64-QA.apk](https://github.com/marocto1/SMAPI-Aurora/releases/download/v1.4.0-rc.1/SMAPI-Aurora-v1.4.0-rc.1-arm64-QA.apk)

- Release: [v1.4.0-rc.1](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v1.4.0-rc.1)
- Automated CI: [successful run 39504329805](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39504329805)
- QA APK SHA-256: `603d2483f7e7f075d3e106352ed3f51cbe6ea862ebf59c26845187fed7d1d02f`
- Android: ARM64. Runtime basis remains pinned at the **phone-tested v0.8.9** SMAPI/managed assets, which must pass the binary-identity CI audit.

## New functionality

### SAF full-backup verification, **not automatic restore**

`AuroraBackupActivity` for v1.4 reads the original Android-private JunimoGate `no_backup/junimogate/user-data` (mods, profiles, configs, backups) and Aurora game-specific external `Saves` directory. After user-selected SAF ZIP export, **reopens the ZIP using ContentResolver**, re-hashes every file with SHA-256 and checks the full manifest, sizes, duplicates, allowed roots and the total expanded-size limit. The UI claims backup completion **only after this second-pass verification**.

**Restoration is deliberately disabled** in this QA build. The user may open and verify a ZIP without touching their live mod library or Saves. Earlier RC2 included a two-root rename-based restore that was not crash-atomic; v1.4 removes that risk while testing a recoverable migration design. This is a *tradeoff*, not full Backup & Restore implementation.

This feature is not verified by a real handset test yet. In particular, SAF providers may differ in whether a newly written URI can immediately be reopened for reading. If that fails, Aurora reports the failure and does not say the archive was verified. Never treat a failed verification as a usable backup.

### Safe Update Center

Integrated inside existing `Моды` navigation. It displays the current Aurora app and detected Stardew game versions and shortcuts to the backup verifier, mod diagnostics and official Aurora GitHub releases. It **does not silently download, install, uninstall or overwrite any APK or app data**.

**Signing limitation:** QA APKs were each signed with *different ephemeral keys*. v1.4 is **not** a supported in-place upgrade over installed v1.3.0 RC2. To achieve persistent Android upgrades, the project needs a controlled release signing key retained outside the repository and an independently tested export/reinstall/restore path to migrate older QA installations. Merely renaming an APK or increasing `versionCode` cannot bypass Android's signing identity requirement. Do not remove a working Aurora until game Saves and app-private mod data have been independently exported **from the installed version** and verified.

### Aurora Coop: **informational preparation only**

The Update Center may share **non-secret version information** using Android's normal share sheet; this is useful for comparing target builds with a PC. It does not establish a tunnel, configure the LAN, match or synchronize mods, create a host session, or make Android and Windows Stardew multiplayer compatible. Cross-platform multiplayer implementation and verification are separate projects. No ADB, USB debugging, proprietary game download or Google Drive required.

## Preserved functions

- Native Workshop tab and official Nexus website browser without Nexus API/key, optional curated author-permitted GitHub mod ZIP download with SHA-256 screening and original Mods import confirmation.
- Original C# Mods/Groups manager for real mod installation, dependency management, profile enable/disable.
- Mod health diagnostic filters, exportable report, local favorites, Aurora sapphire/teal theme, and game version settings.
- Original tested SMAPI/GameHost managed binaries and core app launcher.

## Device test outline

On a phone with verified independent backup: run Aurora, open `Моды → Обновления`, confirm versions/release link; open `Копии`, **export** to a document location outside Aurora, **verify** the exported file through the separate verify button, then reopen a saved game as a read-only check. Do **not** uninstall the working build to test an incompatible QA certificate; restoring or changing the live game data is not part of v1.4. `Поделиться версиями` should open the Android share sheet, not a simulated VPN.

## Upstream and license

Based on [leontismaro/JunimoGate](https://github.com/leontismaro/JunimoGate), **GPL-3.0**. The base UI and managed game/mod runtime remain upstream-derived. Changes in this release add new first-party Aurora update/backup UI and build QA, retaining attribution and source availability.
