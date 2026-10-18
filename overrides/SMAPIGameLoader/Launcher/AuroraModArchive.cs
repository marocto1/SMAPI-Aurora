using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;

namespace SMAPIGameLoader.Launcher;

/// <summary>Validate imported ZIP entries before extracting into the Mods directory.</summary>
internal static class AuroraModArchive
{
    private const int MaxEntries = 6000;
    private const long MaxEntryBytes = 128L * 1024 * 1024;
    private const long MaxTotalBytes = 512L * 1024 * 1024;

    public static void ExtractChecked(ZipArchive zip, string modsPath)
    {
        var root = Path.GetFullPath(modsPath)
            .TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        long totalBytes = 0;
        var seen = new HashSet<string>(StringComparer.Ordinal);
        if (zip.Entries.Count > MaxEntries)
            throw new InvalidDataException("This ZIP has too many entries.");

        foreach (var entry in zip.Entries)
        {
            var name = entry.FullName.Replace('\\', '/');
            if (name.Length == 0 || name.StartsWith("/") || name.Contains(":"))
                throw new InvalidDataException("Unsafe ZIP path: " + entry.FullName);

            var destination = Path.GetFullPath(Path.Combine(
                modsPath, name.Replace('/', Path.DirectorySeparatorChar)));
            if (!destination.StartsWith(root, StringComparison.Ordinal))
                throw new InvalidDataException("ZIP entry escapes Mods: " + entry.FullName);

            if (name.EndsWith("/"))
                continue;
            if (!seen.Add(destination))
                throw new InvalidDataException("Duplicate ZIP entry: " + entry.FullName);
            if (entry.Length > MaxEntryBytes)
                throw new InvalidDataException("Mod contains an unexpectedly large file.");
            checked { totalBytes += entry.Length; }
            if (totalBytes > MaxTotalBytes)
                throw new InvalidDataException("Mod archive is too large to import safely.");
        }

        Directory.CreateDirectory(modsPath);
        zip.ExtractToDirectory(modsPath, overwriteFiles: true);
    }
}
