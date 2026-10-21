# Aurora Private Downloads v6.1.0 RC1

## Scope

The optional **Aurora Cloud / Private R2** screen in the Android hub
allows the owner of a Cloudflare R2 bucket to **list up to 100 private objects**
and download an object to a user-selected file via Android's Storage Access
Framework. This is intended for **private, lawfully acquired backups** and
original Aurora artifacts. It does **not** publish the bucket or distribute
Stardew Valley to other people.

### Bucket for this project

- Account: d0ab9fdebeadcc640b3fc0324da411b3 (public account identifier,
  **not** an Access Key ID).
- Bucket: aurora-downloads
- Endpoint: https://d0ab9fdebeadcc640b3fc0324da411b3.r2.cloudflarestorage.com
- Region: auto
- Public access: leave **disabled**.

## One-time setup on user's phone

1. Cloudflare Dashboard -> R2 Object Storage -> Overview -> **Manage R2 API Tokens**.
2. Create a **NEW** token granting only **Object Read** access to
   **aurora-downloads**. The Cyberduck **write** token is not appropriate.
3. Install a compatible *test build* only after independently validated backup
   and restore of all app-private Aurora/mod/game data. v6.1 CI APK uses an
   **ephemeral signer** and is NOT an in-place upgrade from v6.0 QA APK.
4. Aurora Hub -> **Aurora Cloud / Private R2**. The public Account ID and
   bucket are prepopulated; enter the new read-only Access Key ID and Secret.
5. Save the local encrypted connection; press Refresh. Choose a file.
6. Android asks where to save it via ACTION_CREATE_DOCUMENT; wait until
   the download finishes. The displayed SHA256 is the hash of the received
   bytes, not authenticity verification against a trusted release manifest.
7. Use Disconnect to remove ciphertext and local credential metadata.

**Never send API secrets to GitHub, in chat, or include them in public APKs.**

## Security/limitations

- Only HTTPS host \`<32-hex-account>.r2.cloudflarestorage.com\`, with no
  redirects, is accepted by the S3 SigV4 client.
- The read-only token is stored locally in encrypted preferences using a
  non-exportable Android Keystore AES-GCM key. The token isn't built into
  the APK. Other apps cannot access Aurora's sandbox without a compromise.
- Android connection sends signed GET requests directly to R2; no Railway
  or Cloudflare Worker is involved. No R2 server keys are embedded.
- The UI never uploads, writes, deletes or changes private R2 objects.
- Downloads are streamed to an explicit user-created SAF document. Partial
  documents are deleted on error where the selected document provider permits.
- The code currently expects the user to leave Aurora in the foreground for
  large downloads; a background foreground-service worker is future work.
- Only the first 100 items are shown (continuation pagination pending).
- There is **no** automatic APKS/split installer, APK signer bypass, DRM
  bypass, live R2 test with user credentials, real-device game launch test,
  or app-private backup/restore implementation in this feature.
- APK or APKS backups of a paid game should remain private and should not be
  publicly served without rights to redistribute.

### Test matrix

CI checks native Java compilation/dexing, independent S3 SigV4 test vectors,
Android manifest registration, version badge, APK baseline parity and the
existing tests. CI does not validate that the Android UI starts on a real
device or that a 299+ MB file succeeds on unreliable cellular connections.

**Do not call this Stable until real-device testing confirms launch,
large-file SAF download, recovery, and signing continuity.**
