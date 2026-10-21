# SMAPI Aurora v2.2 + v2.3 + v2.4 + v2.5 — Unified QA

The features are included in the single Windows **v2.5.0 Preview.1** and Android **v2.5.0 RC2** (RC2 supersedes RC1 due to Mods toolbar height). These are **pre-release builds**. CI coverage is not equivalent to physical handset or Android↔PC gameplay verification.

## Windows

[Windows EXE v2.5.0 Preview.1](https://github.com/marocto1/SMAPI-Aurora/releases/download/v2.5.0-pc-preview.1/Aurora-SMAPI-PC-v2.5.0-preview.1.exe) — Windows 10/11 x64, 11,490,950 bytes, SHA-256 `b096dc0317bd7c44d90c476bc4343dd6346f744f6d320bd2b48ca219e404a2f8`; [CI PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39531137453).

- v2.2: **Резервная копия профиля** exports the selected PC **mods profile only** to a user-selected new ZIP outside the Mods directory, checks every entry against SHA-256 on a second read, and refuses to overwrite a previous backup. **Game saves are not included; restore is not implemented.**
- v2.3: refreshed Aurora Control Center UI 3.0 while retaining Stardew vanilla/SMAPI game launch and original mod profile functionality.
- v2.4: local `tailscale status --json` diagnostic through an already installed executable with a four-second timeout, no remote token/API, login, administrator access, connection or VPN installation. If a valid Tailscale 100.64.0.0/10 IPv4 exists, the UI can fill the room address. **It does not test game traffic or prove UDP 24642 reachability.**
- v2.5: Workshop 4.0 search and category filters with six official Nexus pages and read-only SMAPI manifest dependency checks. Third-party mod downloads remain on publisher-authorized websites.

EXE remains unsigned and is a frontend for the user's separately installed game/SMAPI, which are not bundled.

## Android

[Android v2.5.0 RC2 release](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v2.5.0-rc.2) and [Android RC2 CI](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39531509290). Android ARM64 only.

**Interface:** `Aurora → Моды → ✦ Aurora Hub` opens the new native Control Center, whose cards include:
- Играть → existing game launcher
- Моды и Workshop 4.0 → native six-source official Nexus catalog
- Aurora Coop → existing invite-room UI
- Aurora Network 2.0 → read-only VPN transport/local IPv4 status
- Безопасность и обновления → own installed APK signature fingerprint and existing external ZIP backup/verification
- Диагностика модов → existing metadata audit

**Workshop 4.0:** `Моды → Workshop → Workshop 4.0 · Поиск и совместимость`. Search, category selection, private local favorites, mod metadata diagnostics, official publisher download pages for Content Patcher, Generic Mod Config Menu, Stardew Valley Expanded, Automate, Lookup Anything, NPC Map Locations. **Do not interpret catalog presence as verified Android runtime compatibility**. One pinned first-party Aurora smoke-test mod is downloadable with SHA-256; it is installed only by manually confirming the existing transactional Aurora ZIP import.

**Network 2.0:** Android `ConnectivityManager` reports whether VPN transport is present, including available local IPv4 addresses (if permitted by Android). `ACCESS_NETWORK_STATE` is requested; **no VPN permission, VPN service, system overrides, relay or automatic tunnel**. To play over the internet on separate networks, users must first install/join their own trusted VPN and use the existing Aurora Coop Rooms invitation. The game itself handles multiplayer UDP 24642, not Aurora.

**v2.2 signing limitation:** The Safe Update screen shows the SHA-256 of the *currently installed* app signing certificate via Android `PackageManager`. Android's actual update path requires that a future APK signature be compatible with the installed one. CI's QA APK uses a **fresh ephemeral signing certificate per release**; RC2 **cannot be claimed as an in-place update** over a previously signed working Aurora. Never uninstall that working installation unless **all** private mod profiles, settings and game saves have been independently backed up and a reliable restore process is available and validated. The v1.4+ SAF backup re-verifies a ZIP, but automated restoration is **disabled**; showing a fingerprint does not fix key mismatch.

A production signing stream still requires securely provisioned *persistent* Android release signing secrets and explicit real-device QA. Android signature checks must never be bypassed.

## Verified vs unverified

- Verified: Java compilation, activity/permission injection, APK signing, app binary parity for original SMAPI/GameHost, Windows Python unit tests, PyInstaller Windows EXE.
- Not verified: installing RC2 over a user's existing differently signed Aurora; real handset UI/rendering, actual SAF backup/restore migration, working Tailscale on both devices, Android↔Windows game session, mod cross-platform DLL compatibility and saving/reloading shared farm.
- Coop pairing is still a **launcher-level preflight**. Even with an operational external VPN and token-protected room, joining the farm must occur inside Stardew Valley on both devices.

## Credits and license

Based on [JunimoGate](https://github.com/leontismaro/JunimoGate) (GPL-3.0), with source available in this repository. Windows frontend never bundles Stardew Valley or SMAPI binaries. No ADB, USB debugging, Google Drive or unofficial paid game download is needed.
