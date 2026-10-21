"""Aurora 2.2-2.5 targeted regression tests."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
import network_v24 as network
import safety_v22 as safety
import workshop_v25 as workshop


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.mods=self.root/"game"/"Mods"
        self.mods.mkdir(parents=True)
        m=self.mods/"Example"
        m.mkdir()
        (m/"manifest.json").write_text(json.dumps({
            "Name":"Example","UniqueID":"Example.Test","Version":"1.0.0",
            "Dependencies":[{"UniqueID":"Pathoschild.ContentPatcher","IsRequired":True}]
        }),encoding="utf-8")
        (m/"data.txt").write_text("test",encoding="utf-8")

    def test_mod_backup_readback_and_no_overwrite(self):
        output=self.root/"outside"/"mods.zip"
        count=safety.backup_profile(self.mods,output)
        self.assertEqual(count,2)
        with zipfile.ZipFile(output) as zip:
            self.assertEqual(zip.testzip(),None)
            manifest=json.loads(zip.read(safety.MANIFEST))
            self.assertEqual(len(manifest["files"]),2)
        with self.assertRaises(FileExistsError):
            safety.backup_profile(self.mods,output)
        with self.assertRaises(ValueError):
            safety.backup_profile(self.mods,self.mods/"bad.zip")
        self.assertTrue((self.mods/"Example"/"data.txt").exists())

    def test_network_diagnostics_bounded_and_readonly(self):
        class Result:
            returncode=0
            stdout=json.dumps({"BackendState":"Running",
                 "Self":{"TailscaleIPs":["100.87.3.4","fd7a:115c:a1e0::1"]}})
        calls=[]
        def fake_run(command, **options):
            calls.append((command,options))
            return Result()
        status=network.tailscale_state(which=lambda x:"C:/Tailscale/tailscale.exe",runner=fake_run)
        self.assertTrue(status["running"])
        self.assertEqual(status["ipv4"],["100.87.3.4"])
        self.assertEqual(calls[0][0][1:],["status","--json"])
        self.assertFalse(calls[0][1].get("shell",False))
        self.assertFalse(network.tailscale_state(which=lambda x:None)["running"])

    def test_workshop_sources_and_dependency_audit(self):
        self.assertGreaterEqual(len(workshop.OFFICIAL_SOURCES),6)
        self.assertTrue(all(x[2].startswith("https://www.nexusmods.com/stardewvalley/mods/")
                            for x in workshop.OFFICIAL_SOURCES))
        report=workshop.check_dependencies(self.root/"game")
        self.assertEqual(report[0]["reason"],"missing")
        self.assertFalse(workshop.compare_numeric_version("1.2.0","1.3"))
        self.assertTrue(workshop.compare_numeric_version("1.3.0","1.3"))


if __name__=="__main__":
    unittest.main()
