#!/usr/bin/env python3
"""Apply source-only installed APK compatibility edits to SMAPILoader master.
Requires no game APKs. Makes a timestamped backup of every modified file.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parent


def replace_once(content: str, old: str, new: str, filename: str) -> str:
    hits = content.count(old)
    if hits != 1:
        raise RuntimeError(f'{filename}: expected exactly one code anchor, found {hits}: {old[:110]!r}')
    return content.replace(old, new, 1)


def build_patches(repo: Path) -> dict[Path, str]:
    edits: dict[Path, str] = {}
    tool_file = Path('SMAPIGameLoader/Tool/StardewApkTool.cs')
    edits[tool_file] = (ROOT / 'files' / tool_file).read_text(encoding='utf-8-sig')

    rel = Path('SMAPIGameLoader/AndroidManifest.xml')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    s = replace_once(s, '\t<queries>\n', '''\t<queries>
        <!-- Show installed launchable apps in the manual game selector.
             No QUERY_ALL_PACKAGES permission is needed. -->
        <intent>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent>
''', str(rel))
    edits[rel] = s

    rel = Path('SMAPIGameLoader/Launcher/LauncherActivity.cs')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    s = replace_once(s, '''        if (AssetGameVerify() == false)
        {
            Finish();
            return;
        }
''', '''        // Keep the launcher open so a user can select a supported installed
        // copy of the game with a non-default Android package ID.
        if (AssetGameVerify() == false)
        {
            ToastNotifyTool.Notify("Select your installed Stardew Valley from Home.");
        }
''', str(rel))
    edits[rel] = s

    rel = Path('SMAPIGameLoader/Game/EntryGame.cs')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    s = replace_once(s, '''        try
        {
            if (StardewApkTool.IsGameVersionSupport == false)
''', '''        try
        {
            if (!StardewApkTool.IsInstalled)
            {
                ToastNotifyTool.Notify("Select a compatible installed Stardew Valley in the launcher first.");
                return;
            }
            if (StardewApkTool.IsGameVersionSupport == false)
''', str(rel))
    edits[rel] = s

    rel = Path('SMAPIGameLoader/Launcher/GameCloner.cs')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    s = replace_once(s, '''        public string LastGameVersionString { get; set; } = "0.0.0.0";
''', '''        public string LastGameVersionString { get; set; } = "0.0.0.0";
        public string LastGameFingerprint { get; set; } = "";
''', str(rel))
    s = replace_once(s, '''            this.LastGameVersionString = StardewApkTool.CurrentGameVersion.ToString();
''', '''            this.LastGameVersionString = StardewApkTool.CurrentGameVersion.ToString();
            this.LastGameFingerprint = StardewApkTool.GameApkFingerprint;
''', str(rel))
    s = replace_once(s, '''            //don't clone game again
            return false;
''', '''            // Changing the selected app, replacing a sideloaded APK, or a
            // changed split layout must re-extract game assemblies/assets.
            if (LastGameFingerprint != StardewApkTool.GameApkFingerprint)
                return true;

            //don't clone game again
            return false;
''', str(rel))
    edits[rel] = s

    rel = Path('SMAPIGameLoader/Game/GameAssetManager.cs')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    s = replace_once(s, '''        var baseContentApk = StardewApkTool.ContentApkPath;
''', '''        var baseContentApk = StardewApkTool.ContentApkPath
            ?? throw new InvalidDataException("No assets/Content directory found in the installed game's APKs.");
''', str(rel))
    edits[rel] = s

    rel = Path('SMAPIGameLoader/Game/GameAssemblyManager.cs')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    old = '''            //clone dlls Stardew Valley - try base APK first, then arm64 split APK for .NET 9+
            var store = new AssemblyStoreExplorer(StardewApkTool.BaseApkPath, keepStoreInMemory: true);
            if (store.Assemblies.Count == 0 && StardewApkTool.Arm64ApkPath != null)
            {
                Console.WriteLine("No assemblies in base APK, trying arm64 split APK");
                store = new AssemblyStoreExplorer(StardewApkTool.Arm64ApkPath, keepStoreInMemory: true);
            }
            foreach (var asm in store.Assemblies)
            {
                asm.ExtractImage(assembliesOutputDirPath);
            }
'''
    new = '''            // The assembly store may be in base.apk, arm64 split, or another split.
            // Inspect every installed APK; only extract from APKs with assembly stores.
            var assemblyApks = StardewApkTool.GameApkPaths;
            foreach (var gameApk in assemblyApks)
            {
                Console.WriteLine("Looking for .NET assemblies in: " + gameApk);
                var store = new AssemblyStoreExplorer(gameApk, keepStoreInMemory: true);
                foreach (var asm in store.Assemblies)
                    asm.ExtractImage(assembliesOutputDirPath);
            }
            if (!File.Exists(StardewValleyFilePath)
                || !File.Exists(Path.Combine(assembliesOutputDirPath, MonoGameDLLFileName)))
                throw new InvalidDataException("Stardew Valley assemblies were not found in the selected APK set.");
'''
    s = replace_once(s, old, new, str(rel))
    edits[rel] = s

    rel = Path('SMAPIGameLoader/Launcher/Pages/HomePage.cs')
    s = (repo / rel).read_text(encoding='utf-8-sig')
    s = replace_once(s, '''using System;
''', '''using System;
using System.Linq;
''', str(rel))
    s = replace_once(s, '''        body.AddView(SmapiCard, cardLayoutParam);
''', '''        body.AddView(SmapiCard, cardLayoutParam);

        var chooseGameButton = CreateButton(context, "Select installed game", "#455A64");
        chooseGameButton.Click += ChooseGameButton_Click;
        body.AddView(chooseGameButton);
''', str(rel))
    marker = '''    private void InstallSMAPIButton_Click(object sender, EventArgs e)
'''
    chooser = '''    private void ChooseGameButton_Click(object sender, EventArgs e)
    {
        try
        {
            var apps = StardewApkTool.GetSelectableApplications();
            if (apps.Count == 0)
            {
                Toast.MakeText(Context, "No visible installed applications found", ToastLength.Long)?.Show();
                return;
            }
            var labels = apps.Select(a => a.Label + " (" + a.PackageName + ")").ToArray();
            new AndroidX.AppCompat.App.AlertDialog.Builder(Context)
                .SetTitle("Choose installed Stardew Valley")
                .SetItems(labels, (_, args) =>
                {
                    try
                    {
                        StardewApkTool.SelectInstalledGame(apps[args.Which].PackageName);
                        LauncherActivity.Instance.Recreate();
                    }
                    catch (Exception ex)
                    {
                        Toast.MakeText(Context, ex.Message, ToastLength.Long)?.Show();
                    }
                })
                .SetNegativeButton("Cancel", (_, __) => { })
                .Show();
        }
        catch (Exception ex)
        {
            Toast.MakeText(Context, ex.Message, ToastLength.Long)?.Show();
        }
    }

'''
    s = replace_once(s, marker, chooser + marker, str(rel))
    edits[rel] = s
    return edits


def main() -> None:
    parser = argparse.ArgumentParser(description='Patch SMAPILoader source, with file backups.')
    parser.add_argument('repo', type=Path, help='Path to the cloned SMAPILoader repository root')
    parser.add_argument('--dry-run', action='store_true', help='Check expected code anchors only')
    args = parser.parse_args()
    repo = args.repo.expanduser().resolve()
    if not (repo / 'SMAPILoader.sln').exists():
        raise SystemExit(f'Not a SMAPILoader repo root: {repo}')

    edits = build_patches(repo)  # Fail before touching any files if sources differ.
    if args.dry_run:
        print(f'PASS: {len(edits)} files matched expected master source layout.')
        return
    backup_dir = repo / 'compat_patch_backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
    for rel, new_content in edits.items():
        source = repo / rel
        backup = backup_dir / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup)
    for rel, new_content in edits.items():
        (repo / rel).write_text(new_content, encoding='utf-8')
        print(f'PATCHED {rel}')
    print('Backup:', backup_dir)
    print('Next: build the Android app (README.md). No game files are included.')


if __name__ == '__main__':
    main()
