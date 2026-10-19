# Aurora Mod Manager v0.9.1 QA

**Status:** Android ARM64 QA APK compiled/published; not yet verified on the user's physical phone.

The **original JunimoGate .NET Mods / Groups manager** is retained entirely unchanged from the user's v0.8.9 phone-tested build. The existing manager is already comprehensive:

| Feature | Built-in stock Mods/Groups |
| --- | --- |
| Multi-ZIP installation with previews and confirmations | Yes |
| Library of installed mod versions and content packs | Yes |
| Active group selection and independent profiles | Yes |
| Enable/disable mods per group (single or batch) | Yes |
| Add dependencies, choose installed dependency version | Yes |
| Import/export mod groups, include mod configs | Yes |
| Edit config text files with save safety gate | Yes |
| Safe deletion and translation management | Yes |
| SMAPI logs, skipped mod diagnosis | Yes |
| Automatic online downloads/updates | **Not implemented** |

## New optional overview

`AuroraModOverviewActivity` adds a strictly **read-only** mod inventory and health view, accessible via **long press on the Aurora app icon** on supported Android home-screen launchers, then **"Моды Aurora"**. It reads the documented C# JSON index/profiles from `getNoBackupFilesDir()/junimogate/user-data/`; it shows:

- the selected active mod group and installed/enabled/issue counts;
- installed DLL mods versus Content Patcher packs, their IDs, versions, and search;
- which *exact installed library version* is selected by the active group;
- enabled/disabled/not-in-group/missing selections;
- missing/disabled/too-old required dependencies;
- mod detail dialogs and **"Открыть Aurora"** to edit using the original transactional Mods/Groups UI.

The dashboard **never writes/modifies** the mod index, group profiles, saves, game files, user config or translation files. Android compilation and package audits assert the original managed `.so` files and SMAPI assets remain byte-for-byte identical to v0.8.9. Version comparisons are basic numeric metadata checks: **the SMAPI log is authoritative** for actual mod loading/compatibility. This dashboard does not execute mod code.

## APK

- [v0.9.1 QA2 release](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.9.1-mod-manager-qa2)
- [GitHub Actions checks](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39216721419)
- [Direct ARM64 APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v0.9.1-mod-manager-qa2/SMAPI-Aurora-v0.9.1-Mod-Manager-arm64-QA.apk)

**Important:** Each QA APK uses a new temporary signing key. Android cannot upgrade the differently signed version over an installed Aurora. **Never uninstall the working v0.8.9 until app-private mods, group exports/configs and any game saves have been independently backed up and verified.** Do not uninstall Stardew Valley. Avoid misleading claims that v0.9.1 has passed device/gameplay tests before that occurs.

## Implementation

- `AuroraModOverviewActivity.java`: safe read-only inventory UI.
- `inject_mod_manager.py`: adds Android native Activity and a static app-icon shortcut (without adding another launcher icon).
- `test_inject_mod_manager.py`: manifest, shortcut, double injection protections.
- `.github/workflows/aurora-v091-mod-manager-qa.yml`: verified baseline APK, Java compilation, Android packaging, explicit binary integrity QA.

**Known limits:** No Android device test for shortcut availability; home-screen launchers may hide app shortcuts. No direct "Overview" navigation control inside the stock managed Mods tab, since injecting custom .NET methods broke the v0.8.7/8 boot path. Native screen does not replace transactional group edit commands. No remote online mod downloads/updates or live compatibility certification.


QA2 fixes null optional dependency metadata that could otherwise produce a false missing-dependency warning. QA1 is superseded; use QA2 for evaluation.
