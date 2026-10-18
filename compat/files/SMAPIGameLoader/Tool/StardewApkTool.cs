using Android.App;
using Android.Content;
using Android.Content.PM;
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;

namespace SMAPIGameLoader;

// Compatibility-oriented game discovery: installed app package, not the app store.
// This intentionally does NOT patch entitlement / licence / DRM checks.
internal static class StardewApkTool
{
    public const string GamePlayStorePackageName = "com.chucklefish.stardewvalley";
    public const string GameGalaxyStorePackageName = "com.chucklefish.stardewvalleysamsung";
    private const string PreferencesName = "SMAPILauncherGameSelection";
    private const string SelectedPackageKey = "gamePackage";
    private static PackageInfo? _currentPackageInfo;

    internal sealed class GameCandidate
    {
        public string PackageName { get; }
        public string Label { get; }
        public GameCandidate(string packageName, string label)
        {
            PackageName = packageName;
            Label = label;
        }
    }

    static StardewApkTool()
    {
        var preferred = Application.Context
            .GetSharedPreferences(PreferencesName, FileCreationMode.Private)?
            .GetString(SelectedPackageKey, null);

        if (!string.IsNullOrEmpty(preferred))
            _currentPackageInfo = ApkTool.GetPackageInfo(preferred);

        _currentPackageInfo ??= ApkTool.GetPackageInfo(GameGalaxyStorePackageName);
        _currentPackageInfo ??= ApkTool.GetPackageInfo(GamePlayStorePackageName);
    }

    public static PackageInfo? CurrentPackageInfo => _currentPackageInfo;
    public static Android.Content.Context GetContext => Application.Context;
    public static string? BaseApkPath => CurrentPackageInfo?.ApplicationInfo?.PublicSourceDir;

    // Not every distribution splits assets and assemblies in the same way.
    // Prefer base.apk, then use whatever split APKs are present.
    public static IReadOnlyList<string> GameApkPaths
    {
        get
        {
            var paths = new List<string>();
            var basePath = BaseApkPath;
            if (!string.IsNullOrEmpty(basePath) && File.Exists(basePath))
                paths.Add(basePath);

            var splits = CurrentPackageInfo?.ApplicationInfo?.SplitSourceDirs;
            if (splits != null)
            {
                foreach (var path in splits)
                {
                    if (!string.IsNullOrWhiteSpace(path) && File.Exists(path)
                        && !paths.Contains(path, StringComparer.Ordinal))
                        paths.Add(path);
                }
            }
            return paths;
        }
    }

    private static bool ContainsEntry(string filePath, Func<string, bool> predicate)
    {
        try
        {
            using var zip = ZipFile.OpenRead(filePath);
            return zip.Entries.Any(e => predicate(e.FullName));
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Unable to inspect APK {filePath}: {ex.Message}");
            return false;
        }
    }

    private static bool HasGameContent(string path) => ContainsEntry(path,
        name => name.StartsWith("assets/Content/", StringComparison.OrdinalIgnoreCase));

    private static bool HasAssemblyStore(string path) => ContainsEntry(path,
        name => (name.StartsWith("assemblies/", StringComparison.OrdinalIgnoreCase)
                    && name.EndsWith(".blob", StringComparison.OrdinalIgnoreCase))
             || (name.StartsWith("lib/", StringComparison.OrdinalIgnoreCase)
                    && name.IndexOf("libassemblies.", StringComparison.OrdinalIgnoreCase) >= 0
                    && name.EndsWith(".blob.so", StringComparison.OrdinalIgnoreCase)));

    public static string? ContentApkPath => GameApkPaths.FirstOrDefault(HasGameContent);
    public static string? Arm64ApkPath => GameApkPaths.FirstOrDefault(HasAssemblyStore);

    // Structural check only. It doesn't establish ownership or guarantee that a
    // modified APK is safe or compatible with a particular Android SMAPI build.
    public static bool IsInstalled => CurrentPackageInfo != null
        && ContentApkPath != null && Arm64ApkPath != null;

    public static Version GameVersionSupport => new(1, 6, 15, 3);

    public static Version CurrentGameVersion
    {
        get
        {
            var versionText = CurrentPackageInfo?.VersionName;
            return Version.TryParse(versionText, out var result)
                ? result : new Version(0, 0, 0, 0);
        }
    }

    public static bool IsGameVersionSupport => IsInstalled
        && CurrentGameVersion >= GameVersionSupport;

    public static string GameApkFingerprint
    {
        get
        {
            var prefix = CurrentPackageInfo?.PackageName ?? "none";
            var parts = GameApkPaths.Select(path =>
            {
                var file = new FileInfo(path);
                return $"{path}:{file.Length}:{file.LastWriteTimeUtc.Ticks}";
            });
            return prefix + "|" + string.Join("|", parts);
        }
    }

    public static IReadOnlyList<GameCandidate> GetSelectableApplications()
    {
        var manager = Application.Context.PackageManager;
        var intent = new Intent(Intent.ActionMain);
        intent.AddCategory(Intent.CategoryLauncher);
        var visible = manager.QueryIntentActivities(intent, PackageInfoFlags.MatchAll);
        var candidates = visible
            .Where(item => item.ActivityInfo?.PackageName != null)
            .GroupBy(item => item.ActivityInfo!.PackageName, StringComparer.Ordinal)
            .Select(group =>
            {
                var item = group.First();
                var label = item.LoadLabel(manager)?.ToString();
                return new GameCandidate(group.Key, string.IsNullOrWhiteSpace(label) ? group.Key : label);
            })
            .OrderByDescending(c => c.PackageName == GamePlayStorePackageName
                || c.PackageName == GameGalaxyStorePackageName
                || c.Label.IndexOf("Stardew", StringComparison.OrdinalIgnoreCase) >= 0
                || c.PackageName.IndexOf("stardew", StringComparison.OrdinalIgnoreCase) >= 0)
            .ThenBy(c => c.Label)
            .ToList();

        // Some official installs may not be returned by the launcher intent query.
        foreach (var officialId in new[] { GamePlayStorePackageName, GameGalaxyStorePackageName })
        {
            if (candidates.All(c => c.PackageName != officialId) && ApkTool.IsInstalled(officialId))
                candidates.Insert(0, new GameCandidate(officialId, "Stardew Valley"));
        }
        return candidates;
    }

    public static void SelectInstalledGame(string packageName)
    {
        var info = ApkTool.GetPackageInfo(packageName)
            ?? throw new InvalidOperationException("The selected Android package is not accessible.");
        var previous = _currentPackageInfo;
        try
        {
            _currentPackageInfo = info;
            if (!IsInstalled)
                throw new InvalidDataException(
                    "Selected app does not contain a supported Stardew Valley Content folder and .NET assembly store.");

            var prefs = Application.Context.GetSharedPreferences(PreferencesName, FileCreationMode.Private);
            prefs?.Edit()?.PutString(SelectedPackageKey, packageName)?.Apply();
        }
        catch
        {
            _currentPackageInfo = previous;
            throw;
        }
    }
}
