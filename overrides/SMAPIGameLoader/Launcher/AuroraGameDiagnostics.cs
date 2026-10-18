using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;

namespace SMAPIGameLoader.Launcher;

/// <summary>Read-only structural preflight for an installed Android game package.</summary>
internal static class AuroraGameDiagnostics
{
    internal sealed class Result
    {
        public string PackageName = "";
        public Version Version = new Version(0, 0);
        public string ContentApk = "";
        public readonly List<string> AssemblyApks = new();
        public readonly List<string> Problems = new();
        public int ScannedApks;
        public bool Ready => Problems.Count == 0;
        public string Summary => Ready ? "Compatible APK layout found" : Problems[0];

        public string Format()
        {
            var output = new StringBuilder();
            output.AppendLine("Installed package: " + (PackageName.Length == 0 ? "None" : PackageName));
            output.AppendLine("Game version: " + Version);
            output.AppendLine("APK files checked: " + ScannedApks);
            output.AppendLine("Content: " + (ContentApk.Length == 0 ? "Missing" : Path.GetFileName(ContentApk)));
            output.AppendLine("Assemblies: " + (AssemblyApks.Count == 0 ? "Missing" :
                string.Join(", ", AssemblyApks.Select(Path.GetFileName))));
            foreach (var problem in Problems)
                output.AppendLine("• " + problem);
            output.AppendLine();
            output.AppendLine("This checks installed file structure only. Actual Android compatibility requires device testing.");
            return output.ToString();
        }
    }

    internal static Result Scan()
    {
        var result = new Result();
        try
        {
            StardewApkTool.RefreshCurrentPackage();
            var info = StardewApkTool.CurrentPackageInfo;
            if (info == null)
            {
                result.Problems.Add("No selected game installation is accessible.");
                return result;
            }
            result.PackageName = info.PackageName ?? "";
            result.Version = StardewApkTool.CurrentGameVersion;
            var apkPaths = StardewApkTool.GameApkPaths;
            if (apkPaths.Count == 0)
            {
                result.Problems.Add("No readable base or split APK files found.");
                return result;
            }
            foreach (var path in apkPaths)
            {
                try
                {
                    using var archive = ZipFile.OpenRead(path);
                    bool content = false;
                    bool assemblies = false;
                    foreach (var entry in archive.Entries)
                    {
                        var name = entry.FullName;
                        content |= name.StartsWith("assets/Content/", StringComparison.OrdinalIgnoreCase);
                        assemblies |= name.StartsWith("assemblies/", StringComparison.OrdinalIgnoreCase)
                            && name.EndsWith(".blob", StringComparison.OrdinalIgnoreCase);
                        assemblies |= name.StartsWith("lib/", StringComparison.OrdinalIgnoreCase)
                            && name.IndexOf("libassemblies.", StringComparison.OrdinalIgnoreCase) >= 0
                            && name.EndsWith(".blob.so", StringComparison.OrdinalIgnoreCase);
                    }
                    result.ScannedApks++;
                    if (content && result.ContentApk.Length == 0)
                        result.ContentApk = path;
                    if (assemblies) result.AssemblyApks.Add(path);
                }
                catch (IOException ex)
                {
                    result.Problems.Add("Unreadable " + Path.GetFileName(path) + ": " + ex.Message);
                }
                catch (InvalidDataException ex)
                {
                    result.Problems.Add("Invalid APK " + Path.GetFileName(path) + ": " + ex.Message);
                }
            }
            if (result.ContentApk.Length == 0)
                result.Problems.Add("The required assets/Content folder is missing.");
            if (result.AssemblyApks.Count == 0)
                result.Problems.Add("No supported .NET assembly store found.");
            if (result.Version < StardewApkTool.GameVersionSupport)
                result.Problems.Add("Game is older than supported version " +
                    StardewApkTool.GameVersionSupport + ".");
        }
        catch (Exception ex)
        {
            result.Problems.Add("APK inspection error: " + ex.Message);
        }
        return result;
    }
}
