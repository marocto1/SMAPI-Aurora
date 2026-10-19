# SMAPI Aurora v0.7.0 — Full SMAPI Runtime QA

**Experimental Android ARM64 APK with a complete SMAPI runtime included. This is NOT a stable or device-tested release.**

This binary is a **resource-only Aurora-branded adaptation** of the publicly released [JunimoGate v0.3.1](https://github.com/leontismaro/JunimoGate/releases/tag/v0.3.1), not the independently rebuilt Aurora/JunimoGate C# GameHost.

## What's inside

- The complete original JunimoGate SMAPI Android runtime and `StardewModdingAPI.dll`, instead of the vanilla-game-only Aurora Preview.
- Aurora's midnight-violet/mint color palette and SMAPI Aurora app branding.
- Russian translations for much of the launcher, mods, logs and settings.
- All original executable DEX, native libraries and managed SMAPI runtime files maintained unchanged. The QA workflow compared **358 runtime payload files** byte for byte.
- Original upstream game package/signer verification **has not been bypassed**. A compatible, lawfully installed Stardew Valley Android copy is required.
- Re-signed by our QA build certificate. The APK still uses the **`org.junimogate.app` Android package identifier** to preserve upstream .NET interoperability. It **cannot update an existing JunimoGate install signed by a different certificate**; back up mod/saves before any uninstall. Future QA builds may have different signing keys.
- No proprietary game DLLs are included.

## What has been tested

Android packaging and archive integrity, SMAPI binary presence, signature, namespace/Activity, Android color/resource compilation, original-vs-Aurora runtime byte equality, and original GPL/LGPL license notices.

## Not yet tested

Startup on a physical Android phone, actual loading of a compatible purchased Stardew Valley installation, SMAPI log creation, save-game preservation and individual mod compatibility. APK availability is **not a guarantee that mods work on your phone**.

## Build reproducibility and attribution

- Aurora modifications and resource-only build: [SMAPI-Aurora / junimogate-bridge](https://github.com/marocto1/SMAPI-Aurora/tree/main/junimogate-bridge)
- [Original JunimoGate v0.3.1 source (GPLv3 and explicit MonoGame exception)](https://github.com/leontismaro/JunimoGate/tree/v0.3.1)
- [JunimoGate's SMAPI fork (LGPLv3)](https://github.com/leontismaro/JunimoGate-SMAPI)
- [CI build logs](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39181321232)
- Original JunimoGate APK SHA-256: `49bcce760ceda4b9080237000f713cfbd9485e5b237be4c38ed8b95b522295b4`
- Aurora QA APK SHA-256: `869367b6918d51063ce4e7e5c279d972aa04f05976cfb142cd81604c92c94cc3`

**Do not install over JunimoGate or uninstall any existing launcher without backing up app-private data first.**