#!/usr/bin/env python3
"""SMAPI Aurora Android-only source integration.

Apply to NRTnarathip/SMAPILoader master (2026-10-13). No game files or DRM.
Works on any platform with Python; output always targets .NET Android.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'compat'))
from compat_core import build_patches, replace_once  # type: ignore

OVERLAY_ROOT = ROOT / 'overrides'


def safe_advanced_patches(repo: Path, edits: dict[Path, str]) -> None:
    """Avoid archive path escape, eliminate CPU spin and restore task cleanup."""
    rel = Path('SMAPIGameLoader/Launcher/SMAPIInstaller.cs')
    content = (repo / rel).read_text(encoding='utf-8-sig')
    old = '''            foreach (var entry in zip.Entries)
            {
                //remove first dir name
                //example
                //from 'SMAPI-4.1.10.2/Hello.dll'
                //to 'Hello.dll'

                string entryDirName = Path.GetDirectoryName(entry.FullName);
                string[] directoryNames = entryDirName.Split(Path.DirectorySeparatorChar);
                var rootDirName = directoryNames[0];
                var newEntryFileName = entry.FullName.Remove(0, rootDirName.Length + 1);
                var destExtractFilePath = Path.Combine(stardewDir, newEntryFileName);
                ZipFileTool.Extract(entry, destExtractFilePath);
            }
'''
    new = '''            // Never trust file paths inside an imported SMAPI ZIP.
            var targetRoot = Path.GetFullPath(stardewDir)
                .TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            foreach (var entry in zip.Entries)
            {
                if (string.IsNullOrEmpty(entry.Name)) continue; // directory entry
                var zipPath = entry.FullName.Replace('\\\\', '/');
                var firstSlash = zipPath.IndexOf('/');
                if (firstSlash < 0 || firstSlash == zipPath.Length - 1)
                    throw new InvalidDataException("Invalid SMAPI ZIP structure: " + zipPath);
                var relativePath = zipPath.Substring(firstSlash + 1);
                var destination = Path.GetFullPath(Path.Combine(stardewDir, relativePath));
                if (!destination.StartsWith(targetRoot, StringComparison.Ordinal))
                    throw new InvalidDataException("ZIP entry escapes the SMAPI directory: " + zipPath);
                ZipFileTool.Extract(entry, destination);
            }
'''
    content = replace_once(content, old, new, str(rel))
    edits[rel] = content

    rel = Path('SMAPIGameLoader/Tool/TaskTool.cs')
    content = (repo / rel).read_text(encoding='utf-8-sig')
    content = replace_once(content, 'using System.Threading.Tasks;\n',
        'using System.Threading.Tasks;\nusing System.Threading;\n', str(rel))
    old = '''        LastTask = Task.Run(async () =>
        {
            ShowBusyDialog();
            await func();
            CloseBusyDialog();
        });'''
    new = '''        LastTask = Task.Run(async () =>
        {
            ShowBusyDialog();
            try { await func(); }
            finally { CloseBusyDialog(); }
        });'''
    content = replace_once(content, old, new, str(rel))
    old = '''        bool doneMainThread = false;
        if (MainThread.IsMainThread == false)
        {
            MainThread.BeginInvokeOnMainThread(() =>
            {
                func();
                doneMainThread = true;
            });
        }
        else
        {
            func();
            doneMainThread = true;
        }

        while (!doneMainThread)
        {

        }'''
    new = '''        if (MainThread.IsMainThread)
        {
            func();
            return;
        }

        // Block efficiently instead of spinning at 100% CPU on Android.
        var signal = new ManualResetEventSlim(false);
        Exception? callbackError = null;
        MainThread.BeginInvokeOnMainThread(() =>
        {
            try { func(); }
            catch (Exception e) { callbackError = e; }
            finally { signal.Set(); }
        });
        if (!signal.Wait(TimeSpan.FromSeconds(20)))
            throw new TimeoutException("Android UI thread did not respond in time.");
        signal.Dispose();
        if (callbackError != null)
            throw new InvalidOperationException("Android UI callback failed.", callbackError);'''
    content = replace_once(content, old, new, str(rel))
    edits[rel] = content


def plan(repo: Path) -> dict[Path, str]:
    # Validates source code anchors before any changes are made.
    patches = build_patches(repo)
    safe_advanced_patches(repo, patches)
    # Standalone Aurora package ID, so the original launcher can coexist.
    project = Path('SMAPIGameLoader/SMAPIGameLoader.csproj')
    original = (repo / project).read_text(encoding='utf-8-sig')
    original = replace_once(original,
        '<ApplicationId>com.companyname.SMAPIGameLoader</ApplicationId>',
        '<ApplicationId>com.marocto.smapi.aurora</ApplicationId>', str(project))
    original = replace_once(original,
        '<ApplicationDisplayVersion>1.1.7</ApplicationDisplayVersion>',
        '<ApplicationDisplayVersion>0.3.0</ApplicationDisplayVersion>', str(project))
    patches[project] = original
    for overlay in OVERLAY_ROOT.rglob('*.cs'):
        rel = overlay.relative_to(OVERLAY_ROOT)
        patches[rel] = overlay.read_text(encoding='utf-8-sig')
    return patches


def main() -> None:
    p = argparse.ArgumentParser(description='Apply SMAPI Aurora UI + flexible installed-APK source support.')
    p.add_argument('repo', type=Path, help='Root folder of the source repository')
    p.add_argument('--dry-run', action='store_true', help='Validate without making changes')
    args = p.parse_args()
    repo = args.repo.expanduser().resolve()
    if not (repo / 'SMAPILoader.sln').is_file():
        raise SystemExit(f'Not a SMAPILoader source tree: {repo}')
    updates = plan(repo)
    if args.dry_run:
        print(f'PASS: prepared changes for {len(updates)} source files.')
        return
    backup = repo / 'aurora_backups' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for rel in updates:
        original = repo / rel
        if original.exists():
            target = backup / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, target)
    for rel, code in updates.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code, encoding='utf-8')
        print('PATCHED', rel)
    print('Backup:', backup)
    print('Android target: net9.0-android; this source patch is not an APK.')


if __name__ == '__main__':
    main()