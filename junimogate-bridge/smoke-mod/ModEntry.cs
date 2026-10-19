using System;
using StardewModdingAPI;

namespace Aurora.SmapiSmoke;

/// <summary>
/// Safe Android SMAPI smoke test: no save mutation, no network, no game hooks,
/// and no proprietary game references. Search the SMAPI log for AURORA_SMOKE.
/// </summary>
public sealed class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        Monitor.Log("AURORA_SMOKE_ENTRY: independent SMAPI DLL loaded successfully.", LogLevel.Info);
        helper.Events.GameLoop.GameLaunched += OnGameLaunched;
        helper.Events.GameLoop.SaveLoaded += OnSaveLoaded;
    }

    private void OnGameLaunched(object? sender, StardewModdingAPI.Events.GameLaunchedEventArgs e)
    {
        Monitor.Log("AURORA_SMOKE_GAME_LAUNCHED: the SMAPI game event fired.", LogLevel.Info);
    }

    private void OnSaveLoaded(object? sender, StardewModdingAPI.Events.SaveLoadedEventArgs e)
    {
        Monitor.Log("AURORA_SMOKE_SAVE_LOADED: a save was opened; no changes made.", LogLevel.Info);
    }
}
