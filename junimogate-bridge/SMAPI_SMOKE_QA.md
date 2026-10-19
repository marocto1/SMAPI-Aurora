# Aurora 0.8.8 — SMAPI/Mods device smoke validation

**Result as of 19 October 2026:** Aurora 0.8.8 APK is assembled and contains SMAPI/GameHost, and the original JunimoGate Android home is restored, but real Android 16 gameplay is still **not verified**. The user's last launcher log reached `Ready` and did not contain a GameHost attempt, mod load, or SMAPI game-running signal.

## Automated evidence

[Source test run](https://github.com/marocto1/SMAPI-Aurora/actions/runs/39205266406) executed **all 251 real executable host tests** from the pinned upstream JunimoGate commit:
- Core: 39/39
- Extraction: 58/58
- Rewriter: 12/12
- Mods: 142/142

The prior `dotnet test` workflow on console executable harnesses could return successful build/test commands without visibly executing the actual `TestHarness.Run` methods. The new workflow uses `dotnet run --project ...` and checks each expected `N/N passed` line before declaring success.

The same workflow compiled a standalone mod against `assets/smapi-managed/StardewModdingAPI.dll` **extracted from the checksum-verified v0.8.8 APK**, confirming source/API compatibility against the distributed DLL. It never needed or distributed paid Stardew Valley DLLs or game assets.

## Safe on-device experiment

Download the [diagnostic smoke mod ZIP](https://github.com/marocto1/SMAPI-Aurora/releases/download/v0.8.8-smapi-smoke-qa/Aurora-SMAPI-Smoke-Mod-v1.0.0.zip).

1. Launch Aurora v0.8.8; observe the original screen with the circular SMAPI button.
2. **First**, select the existing **no Mods** group and press the circular SMAPI launch button. Note whether the title/menu opens.
3. If it launches, import the unextracted diagnostic ZIP through the launcher's Mods manager, enable the `Aurora SMAPI Launch Smoke Test` mod in the active mod group (not the no-Mods group), and press the same SMAPI button.
4. Read SMAPI logs and look for these exact markers:
   - `AURORA_SMOKE_ENTRY`: the independent .NET mod DLL was created and entered by SMAPI.
   - `AURORA_SMOKE_GAME_LAUNCHED`: SMAPI's GameLaunched event was delivered to the mod.
   - `AURORA_SMOKE_SAVE_LOADED`: the user opened a save; no game content was modified by this test.
5. Export `launcher-current.txt` and the latest SMAPI log from the Logs section, especially if the app closes unexpectedly.

### Interpretation

| Evidence | What is verified | What is not yet verified |
| --- | --- | --- |
| Launcher log says `Ready` | Game workspace/launcher is ready | SMAPI/game/mod load |
| Game menu opens without mods | Baseline game runtime starts | SMAPI plugin loader |
| `AURORA_SMOKE_ENTRY` | SMAPI discovered and loaded an independent code mod | Every third-party mod will work |
| `AURORA_SMOKE_GAME_LAUNCHED` | The game launched far enough to fire SMAPI event | Long session stability |
| `AURORA_SMOKE_SAVE_LOADED` | SaveLoaded event is functional | Arbitrary mod compatibility |

**Limitations:** PC-only mods, native-library or Harmony-dependent mods, mods requiring APIs not present on Android, or mods built for mismatched SMAPI/Stardew versions may still fail individually. The smoke test cannot prove all mods work, and no Android emulator/physical-device gameplay was run in GitHub Actions. Do not uninstall the separate Stardew Valley APK or modify precious saves to conduct the test. Aurora QA builds may have different app signing keys; preserve your app data before reinstalling the launcher.
