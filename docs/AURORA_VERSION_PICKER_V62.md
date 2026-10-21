# Aurora v6.2 · Versions → Download & Install (private owner preview)

This replaces the former **Access Key ID / Secret Access Key entry screen** on
Android with a version chooser. Aurora mobile never receives R2 credentials.

## Working code path

1. Owner links their device once using a 3-minute invite from the private
   version service. This is **not** an R2 API key.
2. Aurora lists owner-authorized versions over HTTPS.
3. For the supported 1.6.15.3 build 245 archive, tapping
   **Скачать и установить** requests a 15-minute S3 presigned GET URL.
4. Aurora streams the file from Cloudflare R2 into its own private cache,
   comparing the full file length and SHA256 with the authenticated manifest.
5. Existing installer re-verifies **all three APK split hashes** from the known
   build and submits them via Android `PackageInstaller`.
6. Android prompts the user and enforces package name/signature. Installation
   may fail if APK signatures conflict or the build is incompatible.
7. The downloaded private cache file is deleted after handoff.

APK/APKS files never ship inside the Aurora launcher, and this feature does
not publish or redistribute commercial game files to the public.

## Real server

- Service: **aurora-versions-private** on Render (free plan).
- Admin setup: https://aurora-versions-private.onrender.com/admin
- Health: https://aurora-versions-private.onrender.com/health
- Dashboard: https://dashboard.render.com/web/srv-dbc8vnjrjlhs73b7o440
- Until environment secrets are configured, health returns `ready:false`
  and all private API endpoints return HTTP 503. **No live download is possible.**

### Owner-only one-time Render environment setup

Set environment variables **in Render**, never in the Android APK or chat:

| Variable | Value |
|--|--|
| `AURORA_R2_ACCOUNT_ID` | `d0ab9fdebeadcc640b3fc0324da411b3` |
| `AURORA_R2_BUCKET` | `aurora-downloads` |
| `AURORA_R2_ACCESS_KEY_ID` | A new Cloudflare R2 **Object Read** token limited to this bucket |
| `AURORA_R2_SECRET_ACCESS_KEY` | Secret value of the R2 Object Read token |
| `AURORA_ADMIN_TOKEN` | Independently generated strong owner admin secret >= 24 characters |
| `AURORA_SESSION_SECRET` | Independently generated strong random signing secret >= 32 characters |
| `AURORA_PRIVATE_CATALOG_JSON` | A JSON array of personally owned backup metadata (see below) |

The catalog includes only real archive versions uploaded to this **private**
bucket. To use the currently uploaded personal archive, substitute the exact
byte length and actual local SHA-256 of that file — do not guess either.

```json
[
  {
    "id": "sdv-1.6.15.3-b245",
    "version": "1.6.15.3.build.245",
    "object_key": "Stardew Valley_v1.6.15.3.build.245.apks",
    "size": 0,
    "sha256": "REPLACE_WITH_REAL_64_HEX_SHA256",
    "rights": "owner-private-backup"
  }
]
```

The example `size` and `sha256` are placeholders, **not valid configuration**.
On Windows the exact size/hash can be obtained from the lawfully acquired
local backup using built-in PowerShell `Get-Item` and `Get-FileHash -Algorithm
SHA256`. Never commit personal API credentials or backup files to GitHub.

### Pair a phone ONCE

1. Once the server health is `ready:true`, open the private service `/admin`
   page on your computer and enter the *server admin secret*, **not** the R2 key.
2. Click Create Invitation, and copy the `AURORAPAIR|https://...|...` code.
3. On your Android device, copy that code and open Aurora →
   **Версии** → **Привязать мою библиотеку (один раз)**.
4. For the next 30 days the mobile session is encrypted with Android Keystore.
   The normal user-facing screen is simply the version list and the
   **Скачать и установить** button. No R2 key entry.

## Tests and limitations

- Server local tests cover admin authentication, one-use pairing, private
  catalog validation, and expiring R2 URL signing.
- Android CI verifies Java compilation, Android manifest, APK assembly and
  immutable original SMAPI/GameHost binary assets, but **not on-device launch**.
- This first client enables installation only for the known build 245 split
  hashes already present in the older Aurora installer. A different game
  version requires an independently audited per-version APK manifest.
- No public redistribution of paid Stardew Valley.
- No silent installation or signature bypass. Android may ask the user to
  allow APK installation for Aurora before showing the system install prompt.
- The network download is not yet a resumable background task.
- **Do not uninstall any currently working Aurora**: the CI QA build uses an
  ephemeral signing key, which breaks in-place upgrades between signatures.
- Release remains a development candidate until the server is configured
  privately and the complete install is tested on an actual Android device.
