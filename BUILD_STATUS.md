# Android APK build status

**State: BLOCKED — required private game compilation references are not configured.**

Last pipeline attempt: [GitHub Actions #39114396985](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39114396985).

## What is already automated

- Clone upstream SMAPILoader at commit `092c686`.
- Apply Aurora v0.5 overlay and check source anchors.
- Verify SHA-256 checksum of a privately hosted references ZIP.
- Accept *only* `StardewValley.dll`, `StardewValley.GameData.dll`, and `MonoGame.Framework.dll`.
- Install Java 17, Android SDK, .NET SDK 9.0.312 and Android workload on GitHub's Linux runner.
- Attempt a debug Android ARM64 APK build and publish the result as a private run artifact if successful.

## Required private GitHub Actions secrets

Open repository **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Meaning |
| --- | --- |
| `AURORA_GAME_REFS_URL` | HTTPS URL of your **private, access-controlled** ZIP containing the three compilation DLLs from a legitimately installed compatible game. |
| `AURORA_GAME_REFS_SHA256` | Expected 64-character SHA-256 hex digest of that ZIP. |

The URL must be reachable by the GitHub Actions runner with any credentials *already embedded securely in the secret*, e.g. a short-lived signed URL. Do not post the URL in issues, README, workflows, commits or chat. The workflow never uploads or includes reference ZIPs in build artifacts. Never store game binaries in a public repository.

The ZIP must contain exactly the three required DLLs, either at root or in a single `DependenciesDll/` directory. The files are **compile-time references**, not a replacement for a genuine game installation. GitHub cannot extract them from your phone automatically. Don't use third-party or untrusted DLL download websites.

Once the secrets are available, open **Actions → Build SMAPI Aurora Android APK → Run workflow**. A successful run should contain an artifact named `SMAPI-Aurora-Android-ARM64-debug`.

## What is NOT yet verified

- The project has not yet passed full Android compilation with game references.
- The app has not yet run on an Android device.
- No released, installable APK is available.
- A structurally compatible APK is not guaranteed to be playable; Aurora does not bypass DRM or license checks.

The upstream project also uses a patched Mono runtime; other build errors may appear after the DLL preflight. Preserve build logs and fix those separately. Do not call a source-patch validation success an Android build success.

## Device smoke testing after an APK exists

See [Android device testing plan](docs/ANDROID_DEVICE_TEST_PLAN.md) for testing with an isolated save and real device logs.
