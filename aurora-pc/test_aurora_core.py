"""Pure Python QA of Aurora SMAPI PC without commercial Stardew/SMAPI assets."""
import io
import json
from pathlib import Path
import socket
import tempfile
import unittest
import zipfile

import aurora_core as aurora


class TestAuroraPC(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "Stardew Valley"
        self.game.mkdir()
        (self.game / "Stardew Valley.exe").write_bytes(b"stub")
        (self.game / "StardewModdingAPI.exe").write_bytes(b"stub")

    def test_settings_and_profiles_are_isolated_from_game(self):
        aurora.save_settings({"game_directory": str(self.game), "profile": "Default"}, self.root)
        self.assertEqual(aurora.load_settings(self.root)["game_directory"], str(self.game))
        self.assertEqual(aurora.available_profiles(self.root), ["Default"])
        folder=aurora.profile_folder("Coop Team", self.root)
        folder.mkdir(parents=True)
        self.assertEqual(aurora.available_profiles(self.root), ["Default","Coop Team"])
        for invalid in ("../../home", "X/Y", "", ".", "../mods", "CON/"):
            with self.assertRaises(ValueError):
                aurora.profile_folder(invalid,self.root)

    def test_modded_launch_uses_real_smapi_binary_and_mods_path(self):
        calls=[]
        def fake_popen(args, cwd):
            calls.append((args,cwd))
            class Proc: pid=12
            return Proc()
        aurora.launch_game(self.game, True, "Coop Team", self.root, spawn=fake_popen)
        self.assertEqual(Path(calls[0][0][0]), self.game / "StardewModdingAPI.exe")
        self.assertEqual(calls[0][0][1], "--mods-path")
        self.assertTrue(Path(calls[0][0][2]).is_dir())
        aurora.launch_game(self.game, False, "Coop Team", self.root, spawn=fake_popen)
        self.assertEqual(len(calls[1][0]),1)

    def _make_zip(self, items):
        archive=self.root / "mod.zip"
        with zipfile.ZipFile(archive,"w") as z:
            for name,content in items:
                z.writestr(name,content)
        return archive

    def test_installs_single_safe_mod_without_overwriting(self):
        manifest=json.dumps({"Name":"Test Mod","UniqueID":"aurora.TestMod","Version":"1.0.0"})
        z=self._make_zip([
            ("TestMod/manifest.json",manifest),
            ("TestMod/data/file.txt","works"),
        ])
        target=aurora.import_zip(z,self.game,root=self.root)
        self.assertEqual(target.name,"aurora.TestMod")
        self.assertEqual((target/"data/file.txt").read_text(),"works")
        self.assertEqual(len(aurora.get_mods(self.game)),1)
        with self.assertRaises(FileExistsError):
            aurora.import_zip(z,self.game,root=self.root)
        self.assertEqual((target/"data/file.txt").read_text(),"works")

    def test_rejects_zip_traversal_and_multiple_mods(self):
        manifest=json.dumps({"Name":"Test Mod","UniqueID":"aurora.Test","Version":"1.0"})
        for items in [
            [("../manifest.json",manifest)],
            [("test/manifest.json",manifest),("other/secret.txt","bad")],
            [("test/manifest.json",manifest),("test/a/../../hidden","bad")],
            [("one/manifest.json",manifest),("two/manifest.json",manifest)],
        ]:
            z=self._make_zip(items)
            with self.assertRaises(ValueError):
                aurora.import_zip(z,self.game,root=self.root)
        self.assertFalse((self.root/"secret.txt").exists())

    def test_detect_no_downloads_and_lan_status_only(self):
        with aurora.socketserver.ThreadingTCPServer(("127.0.0.1",0),aurora._StatusHandler) as s:
            s.status_callback=lambda:aurora.status_data(self.game,"Default")
            import threading
            t=threading.Thread(target=s.serve_forever,daemon=True)
            t.start()
            with socket.create_connection(s.server_address,timeout=2) as client:
                client.settimeout(2)
                raw=client.recv(4096)
            s.shutdown();t.join(timeout=3)
        value=json.loads(raw.decode())
        self.assertEqual(value["schema"],aurora.SCHEMA)
        self.assertEqual(value["platform"],"windows")
        self.assertIn("NOT proof",value["note"])
        self.assertNotIn("password",value)

    def test_missing_smapi_fails_without_modifications(self):
        (self.game / "StardewModdingAPI.exe").unlink()
        with self.assertRaises(FileNotFoundError):
            aurora.launch_game(self.game,True,root=self.root)


if __name__ == "__main__":
    unittest.main()
