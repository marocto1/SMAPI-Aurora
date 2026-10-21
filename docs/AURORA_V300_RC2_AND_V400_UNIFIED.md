# Aurora SMAPI — v3.0 RC2 + v4.0 Unified RC1

Two paired pre-release tracks were built and published successfully by GitHub Actions on 2026-10-21. They are **not** production-Stable and do not prove the user-owned game's cross-platform multiplayer.

## Verified downloadable artifacts

| Platform | Version | SHA-256 | Size |
| --- | --- | --- | --- |
| [Windows Aurora PC v3.0 RC2 EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v3.0.0-pc-rc.2/Aurora-SMAPI-PC-v3.0.0-rc.2.exe) | v3.0.0-rc.2 | `c67d7a2c5fb8adbe52a0283e7d23a2f7206af0e180350ec99cd2517775433192` | 11,501,969 B |
| [Android Aurora v3.0 RC2 APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v3.0.0-rc.2/SMAPI-Aurora-v3.0.0-rc.2-arm64-QA.apk) | v3.0.0-rc.2 | `ffdad62db4f298fa30ea362c387181c88d8dcb830f756e18ed4f20d7d219ed61` | 123,488,680 B |
| [Windows Aurora PC v4.0 RC1 EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v4.0.0-pc-rc.1/Aurora-SMAPI-PC-v4.0.0-rc.1.exe) | v4.0.0-rc.1 | `5ea32246a305385d869f5324b29f077c91c80955a428e8e0c97f3b44fe23a544` | 11,507,185 B |
| [Android Aurora v4.0 RC1 APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v4.0.0-rc.1/SMAPI-Aurora-v4.0.0-rc.1-arm64-QA.apk) | v4.0.0-rc.1 | `6454f38193dac5ad1231df4461b13a8c3ca4aacc33933520eb524bc593980107` | 123,476,392 B |

Builds: [PC 3.0 RC2](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39538476302), [Android 3.0 RC2](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39538613684), [PC 4.0 RC1](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39538527784), [Android 4.0 RC1](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39538663971).

## v3.0.0 RC2 changes

- **Windows PC:** Aurora Control Center is scrollable on small screens. This corrects inaccessible bottom navigation on shorter laptop displays. Existing backup-to-ZIP, restoration to a **new** isolated mod profile, Workshop, mod profile difference audit and Aurora Coop rooms remain.
- **Android:** Manifest `<queries>` explicitly lists **only** the official Stardew Valley package `com.chucklefish.stardewvalley`. This enables Android 11+ installed-game version visibility checks under the normal package-visibility rules, without requesting `QUERY_ALL_PACKAGES`. The underlying SMAPI/GameHost/game asset binaries remain untouched, which is checked by CI.
- Note: package-visible versions are only metadata. Actual compatibility requires game/SMAPI launch, log inspection and gameplay checks on real hardware.

## v4.0.0 RC1 — Aurora Unified

### Windows PC

The new **Проверить готовность ПК** and **Скопировать отчёт** buttons summarize the existing game EXE, SMAPI EXE, chosen mod profile, its manifest count, required dependencies, **user-declared** versions and Aurora room status. These checks are grouped into one readable report.

The test does **not** send game traffic or claim that Stardew's multiplayer is running, that a user-declared version matches the installed executable, or that Android can load PC DLL mods. It does not copy or reveal the Aurora room invite token.

### Android

Inside **Моды → Aurora Hub → Aurora Unified · Проверить всё**, paste a copied code from Aurora SMAPI PC v4.0. The wizard sends a short-lived authenticated TCP status query to Windows Aurora on **TCP 24643**, reports PC-selected mod IDs/versions versus Android's active Aurora profile, then sends an authenticated nonce-bound diagnostic UDP probe on **UDP 24645**. The response includes a redacted, shareable text report.

The user can navigate directly from the wizard to Mod Manager Pro, Recovery Preview and network diagnostics. All network probes happen only after pressing the button and have bounded connection timeouts.

**Crucial:** Stardew itself uses **UDP 24642**. The unified wizard never opens or verifies that game's port and cannot confirm a hosted farm, a successful Join, cross-platform save sync or network crossplay. The Android player must still use the game's experimental Co-op Join screen, and the PC host must create a farm inside Stardew Valley.

### Trusted local network / existing VPN only

The protocol sends a 128-bit room bearer token in the TCP/UDP preflight and should be used only across a trusted LAN or an **already configured, encrypted** VPN (e.g., Tailscale). Aurora does **not** set up VPN accounts, tunnels or relay traffic. It does not automate actual Stardew game joining. Do not expose Aurora TCP/UDP ports to the public internet.

## Signing and backup WARNING

**Each Android QA build uses a newly generated, ephemeral signing certificate**, including RC2 and v4.0 RC1. Android's package manager therefore may reject installation over an older Aurora signed by a different certificate. **DO NOT uninstall an existing working Android Aurora for these RCs** unless you have independently verified backups of every app-private mod, profile, setting and Stardew save **and a tested, reliable restore path**. The Android Recovery Preview is *read-only*: it does not restore game/SMAPI app-private saves or mods. Installing a new QA release may not be safe as an upgrade from the current installation. There is no bypass of Android's signature checks. A long-lived signer for all future Stable releases requires independently secured signing credentials; it cannot be retroactively applied to previously QA-signed builds.

The Windows EXEs are **unsigned**, may trigger SmartScreen, and only launch the user's separately installed Stardew Valley and SMAPI. No commercial game binaries are bundled in those EXEs.

## Verified and unverified

**CI verified:** Python tests, unit-tested local ZIP recovery/manifest comparison/UDP echo, Windows one-file EXE via PyInstaller; Android Java compilation, AndroidManifest/activity registration, APK signature verification, original GameHost/SMAPI asset byte parity.

**Not verified on physical devices:** real Android device operation/rendering, pairwise TCP/UDP over real Wi-Fi/VPN, Stardew host + Android experimental Join on UDP 24642, real saves reload, Android reinstall/restore safety, and signed in-place upgrades.

These releases are **RC**, not v4 Stable. The stable gate remains in `.github/workflows/aurora-v300-stable-qa-gate.yml`; it requires genuine device evidence, matching long-lived Android signing and recovery validation before a future audited Stable build.

## License/credits

Project source: [marocto1/SMAPI-Aurora](https://github.com/marocto1/SMAPI-Aurora). Android work derives from JunimoGate (GPL-3.0); original Stardew Valley and SMAPI binaries are not distributed in Windows launcher.
