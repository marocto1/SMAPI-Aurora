# Aurora Android v1.5.0 and Aurora SMAPI PC v1.6.0 — paired previews

**Both downloads built and published (CI green):**

- [Android Aurora v1.5.0 RC1](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v1.5.0-rc.1) (Android ARM64; APK SHA-256 `f187dc44f59cf94fad332409e640c8214cced7c37d0b718b5658bdac3a24635d`; [CI](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39521876188))
- [Windows Aurora SMAPI PC v1.6.0 Preview.1](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v1.6.0-pc-preview.1) (Windows 10/11 x64; portable EXE SHA-256 `a63db87eb92656c6e9b6a3bf572782a0287af30b95b73eb8cd25dacb0ea876f3`; [CI](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39521823596))

## How to use on one Wi-Fi / local network

1. **PC:** Install Stardew Valley (owned game) and Windows SMAPI using their official installers. Aurora PC does NOT bundle paid game files or SMAPI. Launch `Aurora-SMAPI-PC-v1.6.0-preview.1.exe`, choose the game folder containing `StardewModdingAPI.exe`. It also supports launching `Stardew Valley.exe` without mods.
2. Optionally create a custom mods profile and import one SMAPI mod ZIP. The manager validates archives, refuses path traversal/symlinks, imposes decompression caps and **will not overwrite an installed mod**. The `Default` profile uses Stardew Valley's installed `Mods` folder. Other profiles store mods in user AppData and launch SMAPI using documented `--mods-path`.
3. **PC:** click **Включить обнаружение Aurora**. The application starts a manually activated LAN-only-information service listening on **TCP 24643**. It shows the PC's IP. If prompted by Windows Firewall, allow Aurora only on **private networks**. Never use port forwarding for this Aurora discovery port.
4. **Android:** Aurora → **Моды → Обновления → Aurora Coop · Подключиться к ПК**. Enter the PC's private IPv4 shown by the Windows launcher (e.g. `192.168.1.100`), click **Проверить подключение к Aurora PC**. On success it confirms the PC Aurora status, its launcher version and SMAPI installed state. This verifies **TCP 24643 only**. It does **not** verify Stardew Valley gameplay, mod compatibility or UDP game traffic.
5. **PC:** click `Играть с модами / SMAPI`, select **Co-op → Host** in the actual game, open a multiplayer farm with an available cabin.
6. **Android:** from the game title screen, reveal the *official experimental mobile co-op* if not already visible. On Stardew Valley's logo, tap the four leaf groups **↑ ↑ ↓ ↓ ← → ← →**, tap **?**, exit the question mark menu. Then select **Co-op → Join** and enter the **same PC IP**. This is the **game's built-in join process**; Aurora does not automate it.

Official resources: [Stardew Valley mobile multiplayer guide](https://www.stardewvalley.net/mobile-multiplayer-guide/) and [multiplayer troubleshooting guide](https://www.stardewvalley.net/multiplayer-troubleshooting-guide/).

## Networking reality

| Purpose | Protocol / port | Implementation |
| --- | --- | --- |
| Aurora PC launcher discovery (manual opt-in) | TCP 24643 | Aurora PC responds with limited status JSON `aurora-coop-status/v1`; Android validates it |
| Actual Stardew Valley farm traffic | UDP 24642 | The game itself, NOT Aurora; host must have an active farm |
| Automatic virtual LAN / VPN | — | **Not implemented** |
| NAT traversal / public rendezvous / automatic match | — | **Not implemented** |
| Automatically entering a farm from launcher | — | **Not implemented** |

The game's mobile multiplayer is **experimental**; the official guide recommends a PC-hosted farm with a phone on the same Wi-Fi and warns to back up saves before testing. Game builds and mod sets must be compatible. Crucially, the Android SMAPI-derived Aurora game runtime used here has **not yet been verified in a live Android-to-PC Stardew multiplayer session**; pairing can succeed while the game still rejects the session.

## Windows launcher feature scope

`aurora-pc/aurora_core.py` is an independent Windows-friendly utility:
- Detect common Steam/GOG install locations or choose a folder manually;
- Launch preinstalled original `Stardew Valley.exe` or `StardewModdingAPI.exe`;
- Isolated mod profiles via official SMAPI `--mods-path` argument; safe single-mod ZIP importer; read-only manifest-based mods overview;
- Opt-in TCP status server showing non-secret launcher, selected profile and whether game/SMAPI executables exist.

The GUI is implemented with Python's Tk and packaged into a standalone native Windows EXE using PyInstaller. It is **unsigned**, so SmartScreen might display a publisher warning. No administrator rights, USB debugging, ADB, game downloads or Google Drive are required. It is a PC front-end for the **existing Windows SMAPI**: not a binary rewrite of Android's JunimoGate runtime.

## Android installation and signing

Every Android QA release is signed with a different temporary certificate. The v1.5.0 RC APK **cannot normally replace previously installed v1.4/v1.3 QA builds in place**. Do **not uninstall a working Aurora** without an independently verified backup of all app-private mods/profiles/configs and saved games. `v1.4` offers **verified backup ZIP export**, but it has no enabled safe automatic restore; therefore, **do not use an untested backup procedure as the only migration plan**. Windows PC preview has no such Android certificate problem.

## QA completed vs not completed

- GitHub Windows CI: Python unit tests (ZIP safety, profile separation, SMAPI command arguments, status server), compilation, PyInstaller one-file EXE — **passed**.
- GitHub Android CI: Java compilation, resource packaging, app signature and original SMAPI/game libraries integrity audit — **passed**.
- A real PC with real Stardew/SMAPI, Android handset-to-Windows TCP pairing, actual cross-play Stardew farm joining and full backup/restore migration — **not yet verified**.

## Attribution

This is a GPL-3.0 derived project built on [JunimoGate](https://github.com/leontismaro/JunimoGate). Neither Stardew Valley nor SMAPI binaries are distributed in the Windows preview. It invokes user-installed binaries and follows upstream licensing.
