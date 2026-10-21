import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from inject_v40_rc2 import patch, A, UNIFIED

class RC2QA(unittest.TestCase):
    def test_redacted_report_restored_but_not_invite(self):
        src=(Path(__file__).resolve().parents[1]/
             "v40rc2/AuroraUnifiedActivity.java").read_text()
        self.assertIn('saved.putString("aurora-redacted-report",latest)',src)
        self.assertIn('state.getString("aurora-redacted-report","")',src)
        self.assertNotIn('saved.putString("aurora-invite-',src)
        self.assertIn("AURORA_ROOM_V1 ",src)
    def test_version_and_activity_patch(self):
        # Full original layout/launcher fixtures are covered by v40 and CI.
        source=(Path(__file__).parent/"inject_v40_rc2.py").read_text()
        self.assertIn('"401"',source)
        self.assertIn('"4.0.0-rc.2"',source)
        self.assertIn("AuroraUnifiedActivity",source)

if __name__=="__main__":
    unittest.main()
