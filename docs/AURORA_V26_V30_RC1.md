# SMAPI Aurora v2.6.0 + v2.7.0 + v2.8.0 + v2.9.0 + v3.0.0 RC1

Combined, versioned **release candidates**, not a validated Stable release. Both Windows EXE and Android ARM64 APK were built and published by GitHub Actions.

## Published binaries

- **Windows 10/11 x64**: [Aurora SMAPI PC v3.0.0 RC1 EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v3.0.0-pc-rc.1/Aurora-SMAPI-PC-v3.0.0-rc.1.exe), 11,504,429 bytes, SHA-256 `bb7a05685499f4cf75a0e2ce093158f7fea6da5169eef47f42a725b910e7b8e5`. [Windows CI](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39533699336).
- **Android ARM64**: [SMAPI Aurora v3.0.0 RC1 QA APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v3.0.0-rc.1/SMAPI-Aurora-v3.0.0-rc.1-arm64-QA.apk), 123,476,392 bytes, SHA-256 `a5c8158dd5493d7bc31b38ce7886f34ca85d9acd80f176d6969feb004100db33`. [Android CI](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39533773432).

## Implemented improvements

### v2.6.0 — Aurora Recovery

**PC:** The existing v2.2 backup creates a SHA-256 verified, single-profile ZIP outside the game's Mods folder. The new `aurora-pc/recovery_v26.py` offers: check all archive member names, manifest schemas, file counts, size limits and SHA-256 digests; then restore into a **new isolated** profile. The destination is staged separately and published only after every file passes verification. No existing profile is overwritten; `Default` is explicitly forbidden. Game saves are **not** included or restored. This path is covered by synthetically generated ZIP tests, **not yet real-user verified**.

**Android:** `Recovery Preview` opens the preexisting read-only SAF archive verification and explains signature/restore limitations. It does **not** unpack ZIP into live private Mods, settings or Saves. The Android safe-restore problem is therefore **not solved** and must not be misrepresented as completed.

### v2.7.0 — Aurora Coop Diagnostics

**PC:** Room service adds an opt-in small UDP 24645 echo endpoint that checks a per-room 128-bit invite token. Existing Aurora status over TCP 24643 and LAN discovery over UDP 24644 are retained. Server listens only while the user has opened the Aurora room; it supports RFC1918 LAN and IPv4 address ranges of an independently connected VPN.

**Android:** `Aurora Hub → Coop Diagnostics` accepts an existing `AURORA2|IPv4|token` invite, sends a limited UDP 24645 challenge with a random nonce and checks the corresponding Aurora PC reply. This tests connectivity to **Aurora UDP 24645 only**, not Stardew Valley's UDP 24642. A successful probe does **NOT** confirm that the farm is open, NAT traversal works for the game, mod DLLs are compatible or Android can join the farm.

No integrated VPN, automatic network provisioning, public relay or automatic game joining was added. For remote players an already connected, trusted VPN such as Tailscale remains necessary, separately on both platforms.

### v2.8.0 — Mod Manager Pro / health reports

**PC:** Offline comparison of two distinct mod profiles, showing IDs present only on either side, conflicting versions and required dependency warnings inferred from the local mod manifests. No user files are changed by this comparison. Installation/updates still use the original safe ZIP import, and third-party Nexus files remain on publisher-authorized pages.

**Android:** Read-only active JunimoGate profile audit, locally displayed mod IDs/versions, optional user-initiated report sharing, and a direct jump to Aurora Coop Rooms to compare Windows mod metadata. **This is a manifest audit, not a compatibility attestation for C# DLL runtime on Android.**

### v2.9.0 — UI 4.0

**Windows:** Aurora Control Center 4.0 integrates the new isolated Recovery, mod profile compare and Coop UDP diagnostics while keeping Windows vanilla/SMAPI launch, verified backup and Workshop 4.0.

**Android:** Aurora Hub 4.0 adds navigation cards for Recovery Preview, Coop UDP Diagnostics, Mod Manager Pro, VPN/network inspector, Workshop and signature. Includes a local hub accent toggle. The original JunimoGate Android game launcher, native Mods/Groups transactional features and game/SMAPI libraries are left untouched.

### v3.0.0 — Release Candidate QA and Stable release gate

- CI confirmed Java compilation, manifest/activity configuration, APK signing, expected Android app identity/version, byte-for-byte parity of original bundled game/SMAPI managed components, Windows Python unit tests and Windows PyInstaller executable generation.
- `.github/workflows/aurora-v300-stable-qa-gate.yml` is a **manual gate only**. It does not sign/publish Stable. It requires explicit real Android device QA, Windows real game and recovery QA, actual Stardew Android↔PC crossplay with save reload, Android backup/restore QA and provisioned long-lived Android release signing secrets.
- Until that evidence exists, the deliverables must remain **RC1**, not a misleading `v3.0.0 Stable` binary.

## Android APK signature — serious migration caution

Every QA APK (including 3.0 RC1) is built with a randomly generated per-build signing certificate. Android will not install a differently signed APK over the previous `org.junimogate.app` package without rejecting it. **Do not uninstall the Aurora installation which is already working** unless you have independently verified external copies of all private Mods, profiles, settings and saves and an actually tested restoration procedure. Current Android `Recovery Preview` does *not* restore. A release signing secret cannot retroactively replace a prior QA APK's certificate.

Use the Android RC1 only when its installation can be done safely without sacrificing existing personal data. No USB debugging, ADB, Google Drive, signature bypass or Google Play verification is requested.

## Real device acceptance still needed

1. Confirm the Android installation and app UI 4.0 actually render/operate on a physical ARM64 device, without losing original Mods/Groups.
2. Validate PC game launch with the actual user's Windows Stardew Valley and SMAPI. Test mod-profile Recovery into a new profile and compare restored SHA-256 checksums.
3. Test Android↔PC Aurora Room TCP 24643 authentication and UDP 24645 diagnostics on one Wi-Fi network and, separately, through a user-provided trusted VPN.
4. Test **actual Stardew Valley** game UDP 24642/experimental mobile multiplayer, opening/joining a hosted PC farm, matching game versions/mod dependencies, saving and reloading.
5. Configure long-lived release signing secrets in protected GitHub settings with pinned certificate hash, and prove a real **same-signature** Android upgrade and non-destructive migration.
6. Test any proposed Android restore through independent snapshots, isolated staging, power-failure/cancellation cases and rollback before enabling real data writes.

These checks are not claimed complete by automated CI.

## Source/license

Android source derives from [JunimoGate](https://github.com/leontismaro/JunimoGate) under GPL-3.0. Windows utility launches users' own installed PC Stardew Valley and SMAPI and distributes neither game binaries nor third-party Nexus mod packages. All project code and release process remain in [marocto1/SMAPI-Aurora](https://github.com/marocto1/SMAPI-Aurora).
