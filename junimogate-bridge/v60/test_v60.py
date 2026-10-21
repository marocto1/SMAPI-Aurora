"""Aurora 6.0 Android: temporary share handoff and untouched SMAPI."""
import unittest
from pathlib import Path
from inject_v60 import LINK, UNIFIED, HUB, patch


class AndroidV60Tests(unittest.TestCase):
    def setUp(self):
        self.dir=Path(__file__).resolve().parent

    def test_share_invite_is_user_initiated_and_ephemeral(self):
        source=(self.dir/"AuroraLinkActivity.java").read_text(encoding="utf8")
        self.assertIn("Intent.ACTION_SEND.equals",source)
        self.assertIn("Intent.EXTRA_TEXT",source)
        self.assertIn("AuroraRoomActivity.parse(candidate.trim())",source)
        self.assertNotIn('putString("room-token"',source)
        self.assertIn("Встроенный сканер камеры пока отсутствует",source)

    def test_game_address_is_only_copied_after_authenticated_tcp(self):
        source=(self.dir/"AuroraUnifiedActivity.java").read_text(encoding="utf8")
        self.assertIn("checkedHost=hostChecked?code.ip:null",source)
        self.assertIn("copyHost.setEnabled(hostChecked)",source)
        self.assertIn("copyHost.setEnabled(false)",source)
        self.assertIn('newPlainText("Stardew Co-op Host IP",checkedHost)',source)
        self.assertIn("НЕ проверялся",source)

    def test_injector_registers_share_target_without_touching_game(self):
        source=(self.dir/"inject_v60.py").read_text(encoding="utf8")
        self.assertIn("android.intent.action.SEND",source)
        self.assertIn("android.intent.category.DEFAULT",source)
        self.assertIn("text/plain",source)
        self.assertIn('6.0.0-rc.1',source)
        self.assertIn('"600"',source)
        self.assertIn('if activity_name == LINK:',source)


if __name__=="__main__":unittest.main()
