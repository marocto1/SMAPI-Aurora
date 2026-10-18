"""Offline smoke tests for the source patch. Does NOT compile an APK."""
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import apply_aurora as aurora


def fixture() -> dict[str, str]:
    return {
      'SMAPILoader.sln': 'Microsoft Visual Studio Solution File',
      'SMAPIGameLoader/SMAPIGameLoader.csproj': '''<Project><ApplicationId>com.companyname.SMAPIGameLoader</ApplicationId><ApplicationDisplayVersion>1.1.7</ApplicationDisplayVersion>
<Reference Include="MonoGame.Framework">
			<HintPath>..\\..\\SMAPI-Android-1.6\\src\\DependenciesDll\\MonoGame.Framework.dll</HintPath>
		</Reference></Project>''',
      'SMAPIGameLoader/AndroidManifest.xml': '<manifest>\n\t<queries>\n\t</queries>\n</manifest>',
      'SMAPIGameLoader/Launcher/LauncherActivity.cs': '''using System;
class LauncherActivity {
        if (AssetGameVerify() == false)
        {
            Finish();
            return;
        }
}''',
      'SMAPIGameLoader/Game/EntryGame.cs': '''using System;
class EntryGame {
        try
        {
            if (StardewApkTool.IsGameVersionSupport == false)
        }
}''',
      'SMAPIGameLoader/Launcher/GameCloner.cs': '''class GameCloner {
        public string LastGameVersionString { get; set; } = "0.0.0.0";
            this.LastGameVersionString = StardewApkTool.CurrentGameVersion.ToString();
            //don't clone game again
            return false;
}''',
      'SMAPIGameLoader/Game/GameAssetManager.cs': '''class GameAssetManager {
        var baseContentApk = StardewApkTool.ContentApkPath;
}''',
      'SMAPIGameLoader/Game/GameAssemblyManager.cs': '''class GameAssemblyManager {
            //clone dlls Stardew Valley - try base APK first, then arm64 split APK for .NET 9+
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
}''',
      'SMAPIGameLoader/Launcher/Pages/HomePage.cs': '''using System;
class HomePage {
        body.AddView(SmapiCard, cardLayoutParam);
    private void InstallSMAPIButton_Click(object sender, EventArgs e)
}''',
      'SMAPIGameLoader/Launcher/SMAPIInstaller.cs': '''using System;
class SMAPIInstaller {
            foreach (var entry in zip.Entries)
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
}''',
      'SMAPIGameLoader/Launcher/ModInstaller.cs': '''class ModInstaller {
        zip.ExtractToDirectory(outputDir, true);
                OnInstalledCallback.Invoke();
            if (ModsDirPath == folderPath)
                return false;
            ErrorDialogTool.Show(ex);
            return true;
}''',
      'SMAPIGameLoader/Tool/TaskTool.cs': '''using System.Threading.Tasks;
class TaskTool {
        LastTask = Task.Run(async () =>
        {
            ShowBusyDialog();
            await func();
            CloseBusyDialog();
        });
        bool doneMainThread = false;
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

        }
}'''
    }


def run():
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp)
        for filename, content in fixture().items():
            path = repo / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        patch = aurora.plan(repo)
        assert len(patch) == 21, len(patch)
        assert 'Choose installed game' in patch[Path('SMAPIGameLoader/Launcher/Pages/HomePage.cs')]
        assert 'SMAPI Aurora' in patch[Path('SMAPIGameLoader/Launcher/LauncherActivity.cs')]
        assert 'SettingsPage' in patch[Path('SMAPIGameLoader/Launcher/LauncherActivity.cs')]
        assert 'Smooth animations' in patch[Path('SMAPIGameLoader/Launcher/Pages/SettingsPage.cs')]
        assert 'CheckAsync' in patch[Path('SMAPIGameLoader/Launcher/GameCardInfo.cs')]
        assert '0.5.0' in patch[Path('SMAPIGameLoader/SMAPIGameLoader.csproj')]
        assert '<Private>False</Private>' in patch[Path('SMAPIGameLoader/SMAPIGameLoader.csproj')]
        assert 'AuroraGameDiagnostics.Scan' in patch[Path('SMAPIGameLoader/Launcher/GameCardInfo.cs')]
        assert 'View game compatibility report' in patch[Path('SMAPIGameLoader/Launcher/Pages/HomePage.cs')]
        assert 'RefreshCurrentPackage' in patch[Path('SMAPIGameLoader/Tool/StardewApkTool.cs')]
        assert 'AssemblyApkPaths' in patch[Path('SMAPIGameLoader/Game/GameAssemblyManager.cs')]
        assert 'No supported .NET assembly store found.' in patch[Path('SMAPIGameLoader/Launcher/AuroraGameDiagnostics.cs')]
        assert 'AuroraModArchive.ExtractChecked' in patch[Path('SMAPIGameLoader/Launcher/ModInstaller.cs')]
        assert 'Duplicate UniqueID' in patch[Path('SMAPIGameLoader/Launcher/AuroraModHealth.cs')]
        assert 'MaxTotalBytes' in patch[Path('SMAPIGameLoader/Launcher/AuroraModArchive.cs')]
        assert 'Run dependency diagnostics' in patch[Path('SMAPIGameLoader/Launcher/Pages/ModManagerPage.cs')]
        assert 'ManualResetEventSlim' in patch[Path('SMAPIGameLoader/Tool/TaskTool.cs')]
        assert 'destination.StartsWith(targetRoot' in patch[Path('SMAPIGameLoader/Launcher/SMAPIInstaller.cs')]
        assert 'GameApkPaths' in patch[Path('SMAPIGameLoader/Tool/StardewApkTool.cs')]
        print('PASS: mock upstream anchors, UI overrides, game discovery, ZIP safety and no busy-spin; files=', len(patch))

if __name__ == '__main__':
    run()