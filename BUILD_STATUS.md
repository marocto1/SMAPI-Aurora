# SMAPI Aurora full Android release — build status

**State: NOT READY FOR RELEASE.** The native v0.6.1 preview builds, but it does not inject SMAPI into Stardew Valley. The true .NET 9 Aurora runtime has not compiled or passed device/game/mod testing.

## What we investigated on 19 October 2026

We found publicly distributed **compile-only** API references in [StardewModders/mod-reference-assemblies](https://github.com/StardewModders/mod-reference-assemblies), pinned to commit `0141355fecb8536715ecff22f99374b5e632cbed`. These support PC Stardew Valley 1.6.15 mod CI **without a game installation** and are not playable game DLLs.

For MonoGame Android APIs we used the open-source NuGet package [MonoGame.Framework.Android 3.8.6](https://www.nuget.org/packages/MonoGame.Framework.Android/3.8.6).

- [First compile attempt](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39174775813): failed because desktop MonoGame does not define `AndroidGameActivity`.
- [Second compile attempt](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39174973409): reached C# and found **mobile-only Stardew Valley APIs missing from PC reference assemblies**. These include the mobile `MainActivity`, `Game1.OnAppResume`, `Game1.OnAppPause`, `Game1.emergencyBackup`, `Game1.xEdge`, `Game1.toolbarPaddingX`, and mobile MonoGame members. This proves the public PC reference set is insufficient for the actual Android launcher.
- Four independent Aurora Android UI C# binding errors were fixed in commit `d405f283a00e5f910b8f7d71a74c6a0d22a4b9a1` (`SetIncludeFontPadding`, view orientation, `SetSingleLine`, `SetClipToPadding`).

**Do not replace missing mobile API types with dummy runtime classes**: a resulting APK could compile but would not be a functional SMAPI/game integration.

## How the build workflow works now

`.github/workflows/android-build.yml` has two modes:

1. **Mobile references via private GitHub secrets** `AURORA_GAME_REFS_URL` and `AURORA_GAME_REFS_SHA256`: SHA-256-check and unpack compile references from a private ZIP containing `StardewValley.dll`, `StardewValley.GameData.dll`, and `MonoGame.Framework.dll` taken from a legally installed **compatible Android** version. Compiles **Release** to avoid the upstream `#if DEBUG` block that intentionally refuses game startup. This still requires Android QA and is not automatically production-ready.
2. **No private references**: automatically fetches pinned public PC reference assemblies and official Android MonoGame to run **compile diagnostics**, compiling Debug. This does not prove Android mobile API compatibility and must not be published as a functional release.

The build also needs the .NET 9 Android workload, custom Mono runtime, Harmony/MonoMod compatibility, and compatible SMAPI Android distribution. A successful compile would not verify those at runtime.

## Conditions before we call it a full release

- Build Aurora .NET launcher with correct Android game API references.
- Verify the generated APK is installable, correctly signed, and targets Android ARM64.
- Ensure the game assemblies are read at runtime from the installed, legitimately owned game (do not embed or publicly redistribute paid game assets).
- Confirm that the selected game's base/split APKs work with asset extraction and assembly rewriting.
- Test the actual Stardew Valley startup and loaded SMAPI version on physical Android hardware.
- Install and run representative SMAPI mods on a disposable test save; protect originals.
- Inspect crash/SMAPI logs; resolve regressions; only then publish a non-preview release.

## Existing deliverables

- [Aurora v0.6.1 Preview](https://github.com/marocto1/SMAPI-Aurora/releases/tag/v0.6.1-preview) — installable native companion, **not** the game mod runtime.
- [Aurora source](https://github.com/marocto1/SMAPI-Aurora) — contains the .NET 9 launcher overlay and CI attempts.

There is no working full Aurora release APK yet.
