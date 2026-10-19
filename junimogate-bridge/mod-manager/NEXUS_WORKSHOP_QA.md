# Aurora Nexus Workshop v0.9.3 — implementation and actual boundaries

**Status:** Android ARM64 QA APK packaged, compiled, signed and checked against v0.8.9 using GitHub Actions. **No physical phone test has been performed on v0.9.3.** SMAPI/game/managed Mods code remains byte-for-byte identical to v0.8.9.

## What is implemented

- New `AuroraWorkshopActivity` with a real native **Workshop** screen, and a button in `AuroraModOverviewActivity`.
- Android launcher icon **long-press shortcuts**: `Моды Aurora` and `Workshop` (home launcher support varies). The original Aurora/JunimoGate managed MainActivity and circular SMAPI launch button remain the only main app launcher.
- Nexus Stardew Valley official website **search**, **category-focused searches**, and full mod browsing via Android browser, without credentials.
- Opt-in **legacy Nexus Mods API** feed for a personally supplied test API key: `GET /v1/games/stardewvalley/mods/trending.json` and `latest_added.json`.
- API key only retained in this Activity's Java RAM, cleared when it is destroyed or user discards it; not logged or saved. Explicit requests go directly to `api.nexusmods.com` over HTTPS with `apikey`, `Application-Name` and `Application-Version` headers. Redirects explicitly disabled to prevent leaking the key. Network I/O is not on the main UI thread. JSON size cap and network timeouts.
- Real Nexus metadata cards open the mod's **official Files page**; users download with **Manual Download** in their browser. This honors Nexus authentication, any restrictions/download allowances, and any author file permissions.
- The user's ZIP is imported with the original Aurora **Mods → Import** UI, which has archive path protections, atomic transactions, dependency/group editor and file validation. **No native Java code edits the saved game, installed mod store, groups or game content.**

## Not yet implemented

- **No direct one-tap Nexus → installed mod transaction.** Official Nexus browser download + stock Aurora Mods/Import is needed. Do not present this app as automatically installing from Nexus.
- No application-registered Nexus OAuth/SSO (public release requires app registration with Nexus).
- No authenticated premium download-link request; no non-premium download bypass, no scraping or mirror.
- No guaranteed Android compatibility for arbitrary desktop Stardew mods; only SMAPI logs + on-device testing can confirm.
- No persistent signing key for the Aurora launcher QA series. Each QA APK is independently signed.

## Nexus requirements and trust

The [Nexus Mods API Acceptable Use Policy](https://help.nexusmods.com/article/114-api-acceptable-use-policy) permits personal keys in development tests but asks public applications to contact support@nexusmods.com for registration. A public application should not demand a personal API key as a permanent substitute for registered auth.

Do **not** solicit Nexus credentials from users in chat. The optional test key is entered only inside the private build. If it fails, browsing/search still works in the official website.

The Nexus website must handle downloads for users who cannot call the direct API; no bypassing account entitlements or no-automation rules.

## Device test protocol

1. Before installing any newly signed QA build, separately back up Aurora private mod configs, groups and any saves. Do not uninstall the phone-tested v0.8.9 if those private data cannot be exported.
2. For a device that can install the QA, long-press the Aurora launcher icon → Workshop. If the home screen suppresses static shortcuts, use `Моды Aurora` shortcut → `Workshop` in the overview screen.
3. Open Search with “interface”; verify it opens an official `www.nexusmods.com` page with the title parameter. Open files of a mod; do not force direct external URLs from unknown hosts.
4. Optionally use a personal API key in the QA-only `Nexus API` dialog; open Trending, then New. A `403`, `429` or invalid key should produce a user-facing error, not a crash.
5. Download a mod ZIP from official Nexus in the browser and **manually** import it through Aurora → Mods → Import. Confirm the mod is in the active group and is loaded in the SMAPI log.
6. Confirm ordinary launch and save/load still work. Use Aurora's own logs, no computer tools required.

- [QA release](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.9.3-workshop-qa)
- [Verified APK build and binary audit](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39220940033)

**Upgrade warning:** a differently signed Android APK generally cannot be installed over an existing application with the same package ID. Do not uninstall the existing working Aurora merely for the Workshop without an independently tested backup/recovery route. Do not uninstall the separate Stardew Valley game.
