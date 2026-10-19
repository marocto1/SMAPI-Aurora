# SMAPI Aurora — Native In-App Workshop (No Nexus API)

Release candidate: **v0.9.4.1-workshop-inapp-qa**. Status: **GitHub build/packaging QA only** until user confirms device startup, game launch and Workshop.

## Native integration inside original Mods page

Aurora 0.9.4.1 injects one custom Java view `org.junimogate.aurora.AuroraWorkshopTabsView` into the **existing** compiled Android resource `res/layout/fragment_mods.xml`, immediately before `mods_inventory_count`. This is a visible `Установленные | Workshop` control in the existing **Моды** screen. When the user taps Workshop, the separate Workshop screen is displayed *within the same Aurora Android application*, with an embedded WebView.

The Workshop screen uses the original JunimoGate/Aurora semantic theme colors `junimo_surface`, `junimo_primary`, `junimo_primary_container`, etc., not the old hardcoded near-black palette. Its Activity uses `@style/Theme.JunimoGate`.

Android app-icon long-press shortcuts and original Home/SMAPI/GameHost are unchanged. **No compiled .NET code is patched** and all runtime native/managed libraries must compare byte-for-byte with v0.8.9.

## How Nexus works, WITHOUT API

1. **Моды → Workshop**, visible in the original Mods tab.
2. Search or browse the official `https://www.nexusmods.com/stardewvalley/mods/` website in Aurora's WebView. The website may require sign-in or may refuse WebView; `В браузере` is the supported fallback.
3. **Files → Manual Download** on Nexus. The resulting download is delegated to the user's browser for site-provided confirmation and to honor original author file restrictions and account entitlements. The app does not scrape, synthesize download URLs, call an unofficial API or bypass download tiers.
4. Press **Импорт ZIP** in Aurora. The Workshop Activity returns to the existing Mods page and (when it was opened from that page) invokes the existing `mods_import` button. This opens the original, safe archive picker. The user chooses their downloaded ZIP and confirms installation.
5. The original C# `ModArchiveInstallTransaction` is responsible for archive scanning, safe paths, content index commits and errors. The original Mod Groups editor controls active profile membership.
6. Check SMAPI logs for runtime compatibility — an archive import alone does not guarantee the mod runs.

**Not yet one-tap mod installation:** this implementation does NOT intercept Nexus downloads into the private mod library. A browser-downloaded ZIP must be selected and confirmed in the original importer.

## Nexus limitations

[Nexus API acceptable use policy](https://help.nexusmods.com/article/114-api-acceptable-use-policy) requires public applications using its API to register. Their [Terms of Service](https://help.nexusmods.com/article/18-terms-of-service) prohibit abnormally automated/excessive downloads. The Nexus [Mod Manager Download flow](https://nexus-mods.github.io/NexusMods.App/users/gettingstarted/DownloadAMod/) relies on an `nxm://` protocol integration. Simply interpreting an `nxm://` URL without authorized download resolution cannot produce the actual archive. This implementation has no Nexus API keys or registered identity, so it tells users to use Manual Download.

## Honest future options to reach direct installation

**Option A — authors opt into an open Aurora Workshop index** (best no-Nexus-API route). For mods distributed under author-approved direct HTTPS URLs (e.g., public GitHub Releases), maintain a signed or audited catalog of mod ID, version, dependencies, compatible Android SMAPI version, HTTPS archive URL, size and SHA-256. On explicit user install:
- download to Aurora's **staging** area with size caps, stream hashing and cancellation;
- validate ZIP safety using **existing C# ModArchiveInstallTransaction** (no separate Java mutator);
- review dependencies and verify correct archive structure;
- commit to Mod Library transaction, then ask user whether to enable it in active group;
- keep rollback/old versions, never edit saves and never overwrite mods silently.

**Option B — Nexus official manager integration**. Apply for Nexus app registration and supported SSO/`nxm://` file-download flow, respecting standard/free versus premium restrictions and author permissions. Then pass the received file to the same existing safe importer. This is the only serious route to fully direct Nexus installation without scraping.

**Option C — Android user share/open file**. After the browser downloads a ZIP, a registered `ACTION_SEND` or `ACTION_VIEW` handler can route its content URI to Aurora's C# importer (must be implemented and tested with full Android lifecycle handling). No Nexus API is needed; user action still confirms each file.

Avoid creating a private Nexus mirror, bypassing signed links/queues, putting personal Nexus credentials into public builds, or writing to `library-index.json` from the Workshop.

## Package safety and test status

- QA APK is **re-signed with a new temporary certificate**. Android cannot normally upgrade installed v0.8.9 in place. **Do not uninstall the stable version unless Aurora-private mods, profiles, configs and saves have been exported and proven recoverable.** Never uninstall the separate Stardew Valley app for an Aurora update.
- CI verifies the original SMAPI app, managed libraries, original mod manager and all native libraries are byte-identical to the phone-tested v0.8.9; only Android XML resources/manifest and auxiliary DEX are allowed to change.
- Physical Android UI and WebView interaction remain unverified until the user tests them.
