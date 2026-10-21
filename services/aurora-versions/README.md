# Aurora private version service (owner-only)

This is deliberately **not a public distributor of Stardew Valley**.
No R2 credentials appear in APKs or browser URLs except temporary signed GET
links valid 15 minutes, returned only to a paired owner device.

Railway service needs environment secrets (set in dashboard, never commit):
- AURORA_R2_ACCOUNT_ID, AURORA_R2_BUCKET
- AURORA_R2_ACCESS_KEY_ID, AURORA_R2_SECRET_ACCESS_KEY
  (**R2 Object Read** scoped to the personal bucket)
- AURORA_ADMIN_TOKEN (random >=24 bytes), AURORA_SESSION_SECRET (random >=32 bytes)
- AURORA_PRIVATE_CATALOG_JSON (array of personal lawful-backup entries with
  id, version, object_key, size in bytes, 64-character SHA256,
  rights="owner-private-backup")

The administrator calls POST /v1/pair/create with Authorization: Bearer
<admin token>, then authorizes the owner's phone once with short-lived pairing
code POST /v1/pair/claim; the phone stores a 30-day session securely. Version
selection and short-lived direct R2 downloads thereafter require no R2 key
input. Pairing codes stored in memory and expire in 3 minutes; use 1 replica.
The app must never offer a shareable public, unauthenticated game-APK feed.

GET /health, GET /v1/versions, GET /v1/download?id=..., and pairing endpoints.
Railway should terminate TLS. Never grant WRITE on the download token.

Only owner-supplied backup archives belong here; do not publish or mirror
commercial game APKs for general download without rights.
