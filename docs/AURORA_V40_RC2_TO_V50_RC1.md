# SMAPI Aurora v4.0 RC2 → v5.0 RC1 — combined paired release

All four **real binaries** were built, signed where applicable, regression-tested in GitHub Actions and published on 2026-10-21. All four are **Release Candidates**, NOT Stable, because real Android↔Windows multiplayer and same-signature Android upgrade/restore remain unverified.

## Verified assets

| Platform | Version | Size | SHA-256 |
|---|---|---:|---|
| [Aurora Android v4.0.0 RC2 APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v4.0.0-rc.2/SMAPI-Aurora-v4.0.0-rc.2-arm64-QA.apk) | 4.0.0-rc.2 ARM64 | 123,488,680 bytes | `1be8c990868799a4f18c8fe43e9584ebdc6887bb45e6a3bb8697cebe7ef30d7e` |
| [Aurora PC v4.0.0 RC2 EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v4.0.0-pc-rc.2/Aurora-SMAPI-PC-v4.0.0-rc.2.exe) | 4.0.0-rc.2 Windows x64 | 11,508,317 bytes | `8ec9cccd767965f4e2e8884d8bbee550549099d5e415f50c3753494b33a2cb5e` |
| [Aurora Android v5.0.0 RC1 APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v5.0.0-rc.1/SMAPI-Aurora-v5.0.0-rc.1-arm64-QA.apk) | 5.0.0-rc.1 ARM64 | 123,492,776 bytes | `ddc0510c51858b028c880fda96018629b1d8acf43ac6097a01cd8858297143ef` |
| [Aurora PC v5.0.0 RC1 EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v5.0.0-pc-rc.1/Aurora-SMAPI-PC-v5.0.0-rc.1.exe) | 5.0.0-rc.1 Windows x64 | 20,633,101 bytes | `dd9efd4ad69264ad7cba145df410c7172198629da5c37d9ac9bc1c4088aa1db6` |

CI evidence: [Android v4 RC2](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39541740244), [Windows v4 RC2](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39541581625), [Android v5 RC1](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39541746467), [Windows v5 RC1](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39541584969).

## v4.0.0 RC2 — Stability

**Windows:** scroll mouse wheel works over the tall Unified Control Center on smaller displays. If an Aurora Coop room fails to bind its TCP/UDP listeners, the launcher now closes partially opened resources and clears the invitation state instead of leaving a misleading active room.

**Android:** Unified diagnostics preserve an already-redacted textual report after screen rotation without persisting the room bearer token. The same Aurora Coop/Workshop/mod/audit/game-launch basics are retained. SMAPI/GameHost original managed and native assets stay unchanged, CI-verified.

## v4.1.0 — Aurora Link (bundled in v5 RC1)

- **Windows:** an offline QR code of the currently opened `AURORA2|IP|128-bit token` room invitation. The code contains a secret, so share it only with a trusted person. On room close/reopen, the token changes. Windows also retains existing invite copy/paste and private-LAN/VPN IP controls.
- **Android:** Aurora Link screen accepts/pastes a room invite and opens Aurora Unified with a transient token. After a successful authenticated PC status preflight, the Android app remembers the **last five private host IPs**, but does not store tokens/passwords or make identity assurances. A **new invitation is required** after the room has been re-opened. Entries can be cleared.
- **Not implemented:** a built-in Android camera QR scanner or cross-Internet friendship service. A user can share the text invitation directly; the QR can be scanned with a separate trusted reader if desired.

## v4.2.0 — Network 3.0 compatibility (preflight only)

Aurora 5.0 carries forward Tailscale-aware Windows diagnostics, the automatic LAN discovery from earlier releases and the one-pass Windows↔Android TCP 24643 and UDP 24645 Aurora preflight. In an already connected secured VPN the invite may contain the VPN's 100.64.0.0/10 address. A successful Aurora UDP echo only proves Aurora diagnostic service reachability. **It does not test Stardew Valley game UDP 24642** or prove multiplayer works.

Aurora **does not** create a new VPN, assign network interfaces, configure NAT, open router/firewall ports automatically, perform remote relay or join a farm. This remains a deliberately scoped compatibility/integration feature rather than the originally envisioned fully built-in equivalent of Radmin VPN.

## v4.3.0 — Workshop 5.0

**Windows:** `Экспорт метаданных профиля` exports a bounded JSON report of selected active profile's SMAPI UniqueIDs, version strings and required dependency warnings. `Сравнить с отчётом друга` loads a separately selected validated JSON report to show missing IDs and mismatched versions. This action **never** imports or copies DLL/ZIP mod files, overwrites Mods or reads saved games.

**Android:** Workshop 5.0 continues official, user-directed Nexus publisher pages for Content Patcher, Generic Mod Config Menu, Stardew Valley Expanded, Automate, Lookup Anything and NPC Map Locations, and adds a filter for installed/active mod IDs plus a shortcut to the original read-only Android Mod Manager audit. The original archive installer remains the only means of installing mods; no Nexus API/key bypass, scraping/unauthorized mod redistribution or automatic third-party downloads. Matching IDs/versions do **not** guarantee Android DLL runtime compatibility.

## v4.4.0 — Safe Installer Preflight (not automatic updates)

**Android:** Open `Aurora Hub → Safe Installer 4.4`, select a downloaded APK using Android's Documents picker. The new read-only verifier streams the candidate (max. 512 MiB) to a temporary cache file, computes SHA-256, asks Android's `PackageManager` for the candidate's ID and signer certificate, and compares that signer against the running Aurora package. **It does not install, uninstall, modify Stardew or bypass signature checks.** When Android cannot read the APK's signing information, the report deliberately declines to declare it safe. Even exact signer equality is *not* a complete guarantee of save/config migration, package update acceptance or successful game launch.

The v5 RC1 APK is still signed by a **new ephemeral QA key**; no persistent Android release signing key has been deployed or proved compatible with old QA certificates. Previous working Aurora APKs may reject a v5 in-place install. **Never uninstall a working Aurora before independently verifying complete copies of app-private mods, profiles, settings and game saves plus a tested restore path.** The Android Recovery Preview still *cannot* restore these app-private data.

Windows EXE is unsigned and may show a SmartScreen warning; users must supply their own legally installed game and Windows SMAPI.

## v5.0.0 — Aurora Next Generation RC1

**Windows:** new unified v5 title/UI, real offline QR code generator bundled with EXE, existing game/SMAPI launch, isolated profile backup/recovery, updated mod metadata exchange, Tailscale diagnosis, Coop rooms with ephemeral tokens and unified readiness report.

**Android:** v5 Aurora Hub adds shortcuts to Link 4.1, Workshop 5.0, Safe Installer 4.4 and Unified v5. Unified preflight checks PC room authentication, reads only mod/version metadata and sends an Aurora-only diagnostic UDP challenge; redact the room token from shareable report. Core JunimoGate SMAPI, GameHost and transactional mod manager are retained byte-identically to the pinned game-host baseline in automated QA.

### Steps to use

1. On Windows launch Aurora PC 5.0, select your *own installed* Stardew Valley + SMAPI and selected Mods profile.
2. Optionally compare/export a friend's mod profiles in Workshop 5.0; check current VPN status if playing across different networks.
3. On Windows open an Aurora Coop room, then copy the invitation or show QR. The invited Android player pastes the full code using `Aurora Hub → Aurora Link`.
4. Android Unified checks TCP 24643, mod metadata and Aurora UDP 24645. If checks fail, read the message; do not open public router ports to troubleshoot.
5. The PC host still creates the Stardew farm **in the game** and the phone joins via the game's experimental Co-op interface. This requires a real compatible game build, SMAPI environment and working **Stardew UDP 24642** route. Not tested in this QA release.

## Verified vs. blocked Stable

CI **PASS**: Windows Python tests including room, UDP and mod metadata invariants; bundled QR/Pillow modules into Windows PyInstaller EXE; Java activity compilation; AndroidManifest registration; Android QA APK signature verification; original SMAPI/GameHost assets parity.

**Not proven on physical hardware**: Android↔PC gameplay; real Wi-Fi/VPN path; one-click app update using a persistent signing certificate; Android-private mods/saves export+restore; shared farm save/reload; QR handoff as actually experienced by two users.

Because these blockers remain, v5.0.0 is **RC1 only**. It must not be called v5.0.0 Stable. We retain the existing manual stable-release QA gate, which itself never publishes a stable binary.

Project/source: [marocto1/SMAPI-Aurora](https://github.com/marocto1/SMAPI-Aurora). Android portion is derived from JunimoGate (GPL-3.0); no paid game, SMAPI proprietary component, third-party Nexus mod ZIP or font file is included in the standalone Windows EXE.
