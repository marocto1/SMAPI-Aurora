# SMAPI Aurora 1.7.0 + 1.8.0 — LAN discovery and compatibility preview

**Both deliverables built and verified with CI:**

- Android ARM64: [SMAPI Aurora v1.8.0 RC1 APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v1.8.0-rc.1/SMAPI-Aurora-v1.8.0-rc.1-arm64-QA.apk), SHA-256 `cb95049796a459678a079329dbfa32f120ae436a0eaf1a4d877474b8e36f4980`, [Android QA PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39523263532).
- Windows x64: [Aurora SMAPI PC v1.8.0 Preview.1 EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v1.8.0-pc-preview.1/Aurora-SMAPI-PC-v1.8.0-preview.1.exe), SHA-256 `dc0e6bac7cb85f15f968eae86bebda3b0fb5a50e1d74af4ae72500cb3f9222da`, [Windows tests/EXE PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39523111667).

## v1.7.0 — automatic PC discovery

1. On a Windows PC, launch **Aurora SMAPI PC v1.8.0 Preview.1**, select the Stardew Valley folder, and click **Включить автопоиск Aurora**. This is opt-in; when disabled, neither Aurora discovery server is running.
2. Android Aurora v1.8.0: **Моды → Обновления → Aurora Coop → Найти компьютеры с Aurora**.
3. Aurora Android sends an ephemeral 16-character nonce probe `AURORA_DISCOVER_V2` to local IPv4 UDP broadcast port **24644**. The PC replies `AURORA_HERE_V2 <nonce> 24643`. Android checks the nonce and the responding private IPv4 and lists found PCs.
4. Select a discovered PC to run the read-only TCP compatibility test on **24643**. Manual private IPv4 input remains available as a fallback if guest Wi-Fi client isolation or Windows Firewall blocks broadcast.

Use both devices on the **same trusted private local network**. On Windows, approve Aurora's incoming **TCP 24643 and UDP 24644 only for Private network profile**. Do **not** configure port forwarding or expose the discovery ports to the public internet. This protocol is **not authenticated or encrypted**; while enabled, any device able to reach the local service may inspect the advertised mod IDs/versions. Do not enable it on shared/untrusted Wi-Fi.

## v1.8.0 — compatibility report

PC Aurora's TCP status now includes:

- Launcher version, Windows platform and currently selected Mods profile
- Presence of Stardew Valley.exe and StardewModdingAPI.exe
- PC's active selected mod profile's `manifest.json` UniqueID/version pairs (maximum 180); **not** mod files or saves
- Optional **manually supplied** PC game and SMAPI version labels. These are *not* verified against running Stardew/SMAPI and must not be called automatic version detection

Android compares those fields against its known package version (if visible to PackageManager), Aurora's **SMAPI 4.5.2 packaging baseline** (not a live runtime attestation) and the enabled mod IDs/versions in the active JunimoGate mod profile from app-private `mods/library-index.json` + `profiles/<activeProfileId>/profile.json`. Android's mod metadata remains on-device; it does not upload profiles to the PC.

The report distinguishes exact matches, different versions, mod IDs present on only one platform and missing/unreadable metadata. A match is **NOT** a guarantee that PC DLLs, Android SMAPI, Content Patcher or the actual game's multiplayer protocol will work together. Successful TCP pairing is **NOT** a successful game session.

To join a game, the PC must host a farm in Stardew Valley's built-in Co-op menu, and the Android experimental multiplayer client must use its built-in Join option with the PC's IP. **Stardew UDP 24642** is distinct from Aurora's 24643/24644 ports. Aurora does **not** emulate a VPN, establish an internet overlay, bypass NAT, create a game host, or automatically join the farm.

## What is verified / what is not

- **PASS**: native Java compile, Android APK signing, unchanged source SMAPI/GameHost binary audit, static Android discovery and compatibility checks; Python LAN TCP/UDP tests, Windows PyInstaller EXE build, safe mod profile/import unit tests.
- **UNTESTED on physical devices**: real router broadcast behavior, Windows Firewall prompts, Android-to-Windows connection, actual game Co-op Join with the Android SMAPI build, safe save roundtrip in multiplayer. If TCP works but the game join fails, the launcher cannot declare multiplayer supported.
- **Android signing:** RC1 is freshly QA-signed with an ephemeral certificate, so it likely **cannot install over the previously installed Aurora**. Do not uninstall working Aurora unless *all* private mods, groups, configs and game saves have a separately verified backup and a confirmed restoration path. This project does not support bypassing Android package signatures; a persistent release key remains future work.
- **Windows signing:** EXE is unsigned and may trigger SmartScreen. No commercial Stardew binaries or SMAPI are bundled.

## Technical files

Windows: `aurora-pc/coop_v18.py`, `aurora-pc/aurora_pc_v18.py`, tests `aurora-pc/test_coop_v18.py`.

Android: `junimogate-bridge/v18/AuroraCoopActivity.java`, `AuroraCoopCompatibility.java`, `AuroraUpdateCenterActivity.java`, `inject_v18.py`; CI: `.github/workflows/aurora-v180-auto-coop-qa.yml`.

The PC utility is a front-end to user-installed Windows SMAPI and legal Stardew files. The Android project continues to derive from [JunimoGate](https://github.com/leontismaro/JunimoGate) (GPL-3.0); preserve upstream credit and license.
