"""Aurora Unified 4.0 checks; no commercial binaries or real game traffic."""
import json
from pathlib import Path
import tempfile
import unittest
import readiness_v40 as readiness


class UnifiedReadinessQA(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game=Path(self.temp.name)
        (self.game/"Mods").mkdir()
        mod=self.game/"Mods"/"Stub"
        mod.mkdir()
        (mod/"manifest.json").write_text(json.dumps({
            "Name":"Stub","UniqueID":"QA.Stub","Version":"1.0"
        }),encoding="utf8")

    def test_is_honest_when_game_and_smapi_missing(self):
        result=readiness.prepare_readiness(self.game,"Default",declared_game="1.6.15")
        keys={x["key"]:x for x in result["checks"]}
        self.assertEqual(keys["game"]["status"],"missing")
        self.assertEqual(keys["smapi"]["status"],"missing")
        self.assertEqual(keys["versions"]["status"],"unverified")
        self.assertFalse(result["game_udp_24642_checked"])
        self.assertFalse(result["android_crossplay_checked"])
        self.assertFalse(result["save_restore_checked"])
        report=readiness.format_report(result)
        self.assertIn("НЕ проверялся",report)
        self.assertNotIn("Готов к игре",report)

    def test_local_room_and_manifests_are_metadata_only(self):
        (self.game/"Stardew Valley.exe").write_bytes(b"stub")
        (self.game/"StardewModdingAPI.exe").write_bytes(b"stub")
        report=readiness.prepare_readiness(self.game,"Default",room_ip="192.168.1.4",
                                           room_open=True,declared_game="1.6.15")
        statuses={x["key"]:x["status"] for x in report["checks"]}
        self.assertEqual(statuses["room"],"ok")
        self.assertEqual(statuses["game"],"ok")
        self.assertEqual(report["mods_by_manifest"],1)
        self.assertTrue(report["versions_user_declared"])
        result=readiness.prepare_readiness(self.game,"Default",room_ip="8.8.8.8",
                                           room_open=True)
        self.assertEqual(
            {x["key"]:x["status"] for x in result["checks"]}["room"],"not-tested")


if __name__ == "__main__":
    unittest.main()
