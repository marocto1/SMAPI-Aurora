# SMAPI Aurora v6.0.0 RC1 — connection flow and host visibility

Release candidate, not Stable. v6.0 groups the v5.1–v5.5 convenience and
network-readiness work into one cross-platform RC; it does not claim game co-op.

## Windows

- Prefer the existing active Tailscale private IP (otherwise LAN) via
  "Выбрать адрес автоматически". No VPN installation or login automation.
- New "Копировать IP фермы" copies only the room IP for entering in-game.
- On user request, query the local Windows UDP 24642 listener via read-only
  Get-NetUDPEndpoint. Listener presence does not establish inbound routing,
  actual Stardew server state, mod compatibility or Android connectivity.
- The authenticated TCP 24643 / diagnostic UDP 24645 protocol and ephemeral
  room invitation remain compatible with v5.

## Android

- Aurora Link receives **only** explicit ACTION_SEND text/plain invitations
  shared by a camera/QR app. It parses and pre-fills a valid invite but does not
  connect automatically or save its bearer token. No integrated camera scanner.
- Aurora Unified provides a copy-IP-for-game button **only after** successful
  token-authenticated room status preflight. It never copies token to the game
  clipboard, and still explicitly marks the game UDP 24642 as untested.
- The original SMAPI, GameHost, mod installer, and game assets remain untouched
  in the release pipeline's binary parity audit.

## NOT in v6 RC1

- No embedded VPN, private relay or NAT traversal.
- No direct Android→Windows game traffic interception or Stardew join API.
- No confirmed crossplay or verified Android app-private backup/restore.
- Android builds are still QA-signed with a *new ephemeral certificate* and
  are NOT in-place upgrades from older mismatched signer releases.
- No ADB, USB debugging, Google Drive, Google Play verification, or game APK.

## Manual hardware acceptance required before Stable

1. Test Aurora PC game launch and actual Co-op host.
2. Test Android game launch/experimental Join with the same compatible version.
3. Verify real Android↔Windows joined farm, save/reload, and stability.
4. Validate private LAN and separately secured VPN, including UDP 24642.
5. Establish persistent Android signing identity and test data export/restore
   before uninstalling or replacing any working Aurora.
