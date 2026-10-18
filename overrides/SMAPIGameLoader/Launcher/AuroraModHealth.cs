using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace SMAPIGameLoader.Launcher;

/// <summary>Read-only local mod manifest diagnostics. Not a guarantee of Android compatibility.</summary>
internal static class AuroraModHealth
{
    private sealed class Item
    {
        public ModInfo Mod = null!;
        public string? UniqueId;
        public JObject? Manifest;
        public readonly List<string> Warnings = new();
    }

    private static readonly Dictionary<string, List<string>> Current =
        new(StringComparer.Ordinal);

    public static IReadOnlyList<string> GetIssues(ModInfo mod) =>
        Current.TryGetValue(mod.ModFolderPath, out var issues)
            ? issues : Array.Empty<string>();

    public static void Scan(IReadOnlyList<ModInfo> mods)
    {
        Current.Clear();
        var entries = new List<Item>();
        foreach (var mod in mods)
        {
            var item = new Item { Mod = mod };
            try
            {
                var file = Path.Combine(mod.ModFolderPath, "manifest.json");
                item.Manifest = JObject.Parse(File.ReadAllText(file));
                item.UniqueId = item.Manifest["UniqueID"]?.ToString()?.Trim();
                if (string.IsNullOrWhiteSpace(item.UniqueId))
                    item.Warnings.Add("manifest.json is missing UniqueID");
            }
            catch (Exception e)
            {
                item.Warnings.Add("Unable to read manifest.json: " + e.Message);
            }
            entries.Add(item);
        }

        var byId = entries
            .Where(m => !string.IsNullOrWhiteSpace(m.UniqueId))
            .GroupBy(m => m.UniqueId!, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(g => g.Key, g => g.ToList(), StringComparer.OrdinalIgnoreCase);

        var gameVersion = StardewApkTool.CurrentGameVersion;
        var apiVersion = SMAPIInstaller.GetCurrentVersion();
        foreach (var item in entries)
        {
            var manifest = item.Manifest;
            if (manifest != null)
            {
                if (item.UniqueId != null &&
                    byId.TryGetValue(item.UniqueId, out var duplicates) &&
                    duplicates.Count > 1)
                    item.Warnings.Add("Duplicate UniqueID: " + item.UniqueId);

                CheckMinimum(manifest, "MinimumGameVersion", gameVersion,
                    "Stardew Valley", item.Warnings);
                if (SMAPIInstaller.IsInstalled)
                    CheckMinimum(manifest, "MinimumApiVersion", apiVersion,
                        "SMAPI", item.Warnings);

                if (manifest["Dependencies"] is JArray dependencies)
                {
                    foreach (var dependency in dependencies.OfType<JObject>())
                    {
                        var id = dependency["UniqueID"]?.ToString();
                        var flag = dependency["IsRequired"];
                        var isRequired = flag == null ||
                            (flag.Type == JTokenType.Boolean && flag.Value<bool>());
                        if (flag != null && flag.Type != JTokenType.Boolean)
                            item.Warnings.Add("Invalid IsRequired flag in dependency: " + id);
                        if (isRequired && !string.IsNullOrWhiteSpace(id))
                            CheckReference(byId, id, item.Warnings);
                    }
                }

                if (manifest["ContentPackFor"] is JObject contentPack)
                {
                    var framework = contentPack["UniqueID"]?.ToString();
                    if (!string.IsNullOrWhiteSpace(framework))
                        CheckReference(byId, framework, item.Warnings);
                }
            }
            Current[item.Mod.ModFolderPath] = item.Warnings;
        }
    }

    private static void CheckMinimum(JObject manifest, string field,
        Version actual, string product, List<string> issues)
    {
        var requested = manifest[field]?.ToString();
        if (string.IsNullOrWhiteSpace(requested))
            return;
        if (!Version.TryParse(requested, out var minimum))
        {
            issues.Add("Invalid " + field + ": " + requested);
            return;
        }
        if (actual > new Version(0, 0) && actual < minimum)
            issues.Add(product + " " + minimum + " required (installed " + actual + ")");
    }

    private static void CheckReference(Dictionary<string, List<Item>> index,
        string identifier, List<string> warnings)
    {
        if (!index.TryGetValue(identifier, out var mods))
        {
            warnings.Add("Missing required mod: " + identifier);
            return;
        }
        if (!mods.Any(m => m.Mod.Enabled))
            warnings.Add("Required mod is disabled: " + identifier);
    }
}
