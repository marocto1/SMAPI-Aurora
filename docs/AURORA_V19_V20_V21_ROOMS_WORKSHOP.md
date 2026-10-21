# SMAPI Aurora v1.9 + v2.0 + v2.1 — combined preview release

## Downloads (verified GitHub Actions artifacts)

- **Android v2.1.0 RC1 (ARM64)**: [APK](https://github.com/marocto1/SMAPI-Aurora/releases/download/v2.1.0-rc.1/SMAPI-Aurora-v2.1.0-rc.1-arm64-QA.apk). SHA-256 `2f71597ec0d383a7be50dbc450a67e8bbc8f4b957b0dfcedfb8ca5a889eeff2f`. [Android CI PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39524747297).
- **Aurora SMAPI PC v2.1.0 Preview.1 (Windows 10/11 x64)**: [EXE](https://github.com/marocto1/SMAPI-Aurora/releases/download/v2.1.0-pc-preview.1/Aurora-SMAPI-PC-v2.1.0-preview.1.exe). SHA-256 `cd74ff94c32147ae6289ab6c89f5cdc41f643e0a5531449ecb47b3c5a67c3c87`. [PC tests and EXE build PASS](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39524577433).

**Preview, not stable.** Tests used synthetic game/SMAPI files for Windows and code/binary-identity checks for Android. Cross-platform coop was **not** physically verified by these pipelines.

## v1.9.0 — Aurora Network preparation, not native VPN

The new Windows room UI allows the host to enter its LAN IPv4 or the IPv4 of an **already-connected secure virtual network**. The Android room screen accepts RFC1918 private LAN and CGNAT 100.64.0.0/10 addresses (except the specific reserved 100.100.100.100 segment). Addresses such as 100.x.y.z can be assigned by a provider such as Tailscale **after its independently installed apps are connected**.

Aurora does **not** bundle Tailscale, create a VPN, authenticate to a VPN provider, relay traffic over a public server, configure port forwarding, bypass Android signatures, or provide NAT traversal. UDP game traffic still runs exclusively through Stardew Valley on UDP 24642, requiring the chosen network to carry it. In particular, successful Aurora TCP connectivity does NOT mean that the Stardew Valley game can cross-play.

For remote friends, first install/connect an existing provider such as [Tailscale](https://tailscale.com/) on **both Windows and Android** and confirm the endpoints can reach each other. Android offers only one VPN slot for ordinary VPN providers; Aurora does not request that slot itself. Do not expose TCP 24643 or UDP 24644 to the public internet.

## v2.0.0 — Aurora Coop Rooms

1. Windows: open `Aurora-SMAPI-PC-v2.1.0-preview.1.exe`. Select the locally installed Stardew Valley folder. Choose a mod profile and optionally enter **user-declared** Stardew and SMAPI version strings.
2. Windows: enter a reachable **private LAN or existing VPN** IPv4 (use the actual current address, not a placeholder), then click **Открыть комнату Aurora**.
3. Aurora generates a **random 128-bit session token** (32 hex characters) and an invite in the format `AURORA2|IPv4|token`. Click **Копировать** and share it privately with your friend.
4. Android: `Моды → Обновления → Aurora Coop Rooms → Присоединиться`. Paste the entire code and choose **Проверить комнату и моды**.
5. Android connects to Windows Aurora on TCP 24643 and sends the current room token. The Windows launcher discloses mod IDs/versions and declared game/SMAPI version labels **only when the token matches**. Closing/reopening the PC room generates a different token.
6. **In game**, the PC host opens Stardew Valley's Co-op → Host. On Android use the experimental Co-op → Join interface and enter the PC IP from the invite. Stardew's game-specific UDP 24642 is separate and cannot be verified from an Aurora room status query.

Existing automatic same-Wi-Fi discovery (UDP 24644) and the older `Aurora Coop · Автопоиск и совместимость` screen are preserved separately for LAN users. Private LAN and private VPN modes do not use a public Aurora server.

### Important security limitations

The invitation is a bearer secret; share it only with trusted participants. Room status uses a small **unencrypted TCP protocol** and checks its token in constant time. On a **trusted Wi-Fi LAN** the token is not designed to resist hostile network observers; use an independently encrypted VPN for connections over the internet. It authenticates access to Aurora **metadata only**, not Stardew gameplay or a peer's personal identity. The UDP discovery response doesn't contain the room token. No saves, ZIP files, binaries, passwords or user account data are transmitted by this feature.

For any suspicious/incorrect invitation or unreachable host, Android does not modify the game or mod library.

## v2.1.0 — Workshop 3.0

**Android:** `Моды → Workshop → Workshop 3.0 · Каталог и совместимость`. The locally bundled catalogue points to **official Nexus mod pages** for [Content Patcher](https://www.nexusmods.com/stardewvalley/mods/1915), [Generic Mod Config Menu](https://www.nexusmods.com/stardewvalley/mods/5098), and [Stardew Valley Expanded](https://www.nexusmods.com/stardewvalley/mods/3753). It reports known installed active mod IDs/versions from JunimoGate's own read-only library index. It **does not** claim those mods will work on Android and doesn't automatically import protected Nexus files. Follow authors' requirements manually.

The sole supported one-click **download** is still the **first-party Aurora SMAPI smoke test ZIP**, hash-pinned and checked. After download, the user must confirm import using Aurora's original C# mod transaction UI. More direct sources require publisher consent and pinned release hashes.

**Windows:** open Aurora SMAPI PC → **Workshop 3.0**. It provides the same official links and runs a non-destructive local manifest dependency audit for the currently selected PC profile. Missing or too-old mandatory dependencies show as issues (numeric version comparison only; prereleases flagged for manual review). It does not execute unknown mod files, pull a marketplace API or auto-delete anything.

## Unchanged requirements and verification boundaries

- Android SMAPI/GameHost and existing transactional Mods/Groups system stay byte-identical to the pinned, earlier user-tested JunimoGate v0.8.9 basis; APK CI auditable.
- The test APK is signed with a **new temporary certificate**. Android will not normally install it over differently signed previous QA builds. **Do not uninstall a working Android Aurora without independently exported and verified backups of private mods, profiles, configs and saves and a tested restore route.** v1.4+ deliberately disabled destructive automatic restore pending on-device validation.
- The Windows EXE is currently **unsigned** and may prompt a Windows SmartScreen warning. Do not download from third-party mirrors.
- v2.1.0 is not a verified game-multiplayer success story. The following remain to be demonstrated on actual Windows/Android hardware: VPN connectivity, UDP 24642 game traffic, matching game versions/mod runtime, entry into the hosted farm, saving/reloading a multiplayer farm, and recovery after reinstall.

## Credits

SMAPI Aurora Android is based on [JunimoGate](https://github.com/leontismaro/JunimoGate) (GPL-3.0). Windows Aurora is a front-end for the user's separately installed Windows Stardew Valley and SMAPI; it does **not** ship game/SMAPI binaries or redistribute third-party Nexus mods. Credit and source remain available under the project's GPL-3.0 license.
