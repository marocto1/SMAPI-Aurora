"""Aurora Next 5.0: Link/Workshop/room and report non-destructive QA."""
import json
import tempfile
import unittest
from pathlib import Path
import link_v41
import workshop_v43 as workshop


class V50Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game=Path(self.tmp.name)
        self.folder=self.game/"Mods"/"OneMod"
        self.folder.mkdir(parents=True)
        (self.folder/"manifest.json").write_text(json.dumps({
            "UniqueID":"QA.OneMod","Name":"One Mod","Version":"1.4.0",
            "Dependencies":[{"UniqueID":"QA.Missing","MinimumVersion":"2.0.0"}]
        }),encoding="utf8")

    def test_link_qr_payload_is_room_token_not_automated_game_join(self):
        invite="AURORA2|192.168.1.10|"+"a"*32
        self.assertEqual(link_v41.invite_qr_payload(invite),invite)
        for invalid in ("AURORA2|8.8.8.8|"+"a"*32,"AURORA2|192.168.1.3|fake"):
            with self.assertRaises(ValueError):
                link_v41.invite_qr_payload(invalid)

    def test_workshop_export_compare_and_no_overwrite(self):
        local=workshop.profile_report(self.game,"Default")
        self.assertEqual(local["mods"][0]["id"],"QA.OneMod")
        self.assertEqual(local["issues"][0]["dependency"],"QA.Missing")
        self.assertNotIn(str(self.game),json.dumps(local))
        dest=self.game/"report.json"
        workshop.export_report(local,dest)
        with self.assertRaises(FileExistsError):
            workshop.export_report(local,dest)
        imported=workshop.read_report(dest)
        self.assertEqual(imported["mods"],local["mods"])
        foreign={"schema":workshop.SCHEMA,"mods":[
            {"id":"QA.OneMod","version":"2.0.0"},
            {"id":"QA.Other","version":"1.0"}
        ]}
        diff=workshop.compare_reports(local,foreign)
        self.assertEqual(diff["version_mismatch"]["qa.onemod"]["local"],"1.4.0")
        self.assertEqual(diff["peer_only"],["qa.other"])
        self.assertFalse(diff["gameplay_verified"])
        self.assertTrue((self.folder/"manifest.json").is_file())

    def test_untrusted_metadata_rejects_escape_and_duplicates(self):
        examples=[
            {"schema":workshop.SCHEMA,"mods":[
                {"id":"OK.Valid","version":"1"},{"id":"ok.valid","version":"2"}]},
            {"schema":workshop.SCHEMA,"mods":[{"id":"../escape","version":"1"}]},
            {"schema":workshop.SCHEMA,"mods":[{"id":"Bad","version":"1\nv2"}]},
            {"schema":"invalid","mods":[]},
        ]
        for data in examples:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    workshop.validate_report(data)
        huge=self.game/"oversize.json"
        huge.write_bytes(b" "* (workshop.MAX_BYTES+1))
        with self.assertRaises(ValueError):
            workshop.read_report(huge)


if __name__=="__main__":
    unittest.main()
