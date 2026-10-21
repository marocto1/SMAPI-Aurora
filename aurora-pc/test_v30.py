"""Aurora v3.0 RC: recovery integrity, authenticated UDP preflight and mods QA."""
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
import zipfile

import aurora_core as core
import safety_v22 as safety
import recovery_v26 as recovery
import coop_v27 as udp
import modaudit_v28 as audit


class V30Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.game=self.root/"SDV"
        self.mods=self.game/"Mods"
        (self.mods/"ExampleMod").mkdir(parents=True)
        (self.mods/"ExampleMod"/"manifest.json").write_text(json.dumps({
            "UniqueID":"example.Mod","Name":"ExampleMod","Version":"1.2.0"
        }),encoding="utf8")
        (self.mods/"ExampleMod"/"assets.txt").write_bytes(b"hello")
        (self.game/"Stardew Valley.exe").write_bytes(b"test-game")

    def test_recovery_creates_new_profile_only(self):
        archive=self.root/"external.zip"
        self.assertEqual(safety.backup_profile(self.mods,archive),2)
        self.assertEqual(len(recovery.preview_archive(archive)),2)
        recovered=recovery.restore_new_profile(archive,"Recovered CoOp",self.root)
        self.assertEqual((recovered/"ExampleMod"/"assets.txt").read_bytes(),b"hello")
        self.assertEqual((self.mods/"ExampleMod"/"assets.txt").read_bytes(),b"hello")
        self.assertTrue((recovered/"ExampleMod"/"manifest.json").is_file())
        with self.assertRaises(FileExistsError):
            recovery.restore_new_profile(archive,"Recovered CoOp",self.root)
        with self.assertRaises(ValueError):
            recovery.restore_new_profile(archive,"Default",self.root)
        self.assertEqual(core.available_profiles(self.root),["Default","Recovered CoOp"])

    def test_damaged_zip_rejected_without_creating_new_profile(self):
        archive=self.root/"altered.zip"
        data=b"evil"
        with zipfile.ZipFile(archive,"w") as z:
            z.writestr("ExampleMod/manifest.json",data)
            z.writestr(safety.MANIFEST,json.dumps({
                "schema":"aurora-pc-mod-backup/v1",
                "files":[{"path":"ExampleMod/manifest.json","bytes":len(data),
                          "sha256":"0"*64}]
            }))
        with self.assertRaises(ValueError):
            recovery.restore_new_profile(archive,"Tampered",self.root)
        self.assertFalse((self.root/"profiles"/"Tampered").exists())

    def test_archive_traversal_and_case_collision_rejected(self):
        for entries in (
            [("../evil.txt",b"x")],
            [("M/file.txt",b"a"),("m/FILE.txt",b"b")]
        ):
            with zipfile.ZipFile(self.root/"invalid.zip","w") as z:
                for n,value in entries:z.writestr(n,value)
                z.writestr(safety.MANIFEST,json.dumps({
                    "schema":"aurora-pc-mod-backup/v1","files":[]
                }))
            with self.assertRaises(ValueError):
                recovery.preview_archive(self.root/"invalid.zip")

    def test_auth_udp_echo_and_wrong_invite_denied(self):
        token="0f"*16
        nonce=b"deadbeef12345678"
        payload=udp.CHALLENGE+token.encode()+b" "+nonce
        self.assertEqual(udp.reply_challenge(payload,"192.168.5.3",token),
                         udp.RESPONSE+nonce)
        self.assertIsNone(udp.reply_challenge(payload,"192.168.5.3","a"*32))
        self.assertIsNone(udp.reply_challenge(payload,"8.8.8.8",token))
        service=udp.CoopAdvancedService(self.game,tcp_port=0,udp_port=0,diag_port=0)
        try:
            service.start()
            port=service._diagnostic_sock.getsockname()[1]
            key=service.room_token
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as client:
                client.settimeout(2)
                client.sendto(udp.CHALLENGE+key.encode()+b" "+nonce,
                              ("127.0.0.1",port))
                response,_=client.recvfrom(128)
                self.assertEqual(response,udp.RESPONSE+nonce)
        finally:
            service.stop()

    def test_readonly_mod_profile_difference(self):
        empty=core.profile_folder("Friend",self.root)
        empty.mkdir(parents=True)
        result=audit.compare_profiles(self.game,"Default","Friend",self.root)
        self.assertIn("example.mod",result["only_left"])
        self.assertFalse(result["verified_runtime"])
        self.assertIn("manifest-only",result["note"])
        self.assertIn("Different",audit.summarize(result).replace("Разные версии","Different"))


if __name__ == "__main__":
    unittest.main()
