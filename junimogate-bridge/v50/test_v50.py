import unittest
from pathlib import Path
from inject_v50 import LINK, SAFE_APK, UNIFIED, HUB, patch

class V50QA(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).resolve().parents[1]
    def test_transient_link_and_verified_peer_history(self):
        link=(self.root/"v50/AuroraLinkActivity.java").read_text()
        wizard=(self.root/"v50/AuroraUnifiedActivity.java").read_text()
        self.assertIn('new Intent(this,AuroraUnifiedActivity.class)',link)
        self.assertIn('AuroraRoomActivity.parse(value)',link)
        self.assertIn('AuroraLinkActivity.rememberCheckedPeer(this,code.ip)',wizard)
        self.assertIn('getStringExtra("aurora-invite-transient")',wizard)
        self.assertIn('AURORA_UDP_V1 ',wizard)
        self.assertIn('AURORA_ROOM_V1 ',wizard)
        self.assertNotIn('putString("room-token"',link)
    def test_safe_apk_only_reads_saf(self):
        src=(self.root/"v50/AuroraApkPreflightActivity.java").read_text()
        for token in ('ACTION_OPEN_DOCUMENT','getPackageArchiveInfo',
                      'getPackageName().equals(candidate.packageName)',
                      'MessageDigest.isEqual','SHA-256','MAX_APK','temp.delete()'):
            self.assertIn(token,src)
        for forbidden in ('ACTION_INSTALL_PACKAGE','ACTION_DELETE','getExternalStorageDirectory'):
            self.assertNotIn(forbidden,src)
    def test_workshop_installed_filter_and_original_import(self):
        src=(self.root/"v50/AuroraWorkshopCatalogActivity.java").read_text()
        self.assertIn('Включённые моды',src)
        self.assertIn('AuroraModAuditActivity.class',src)
        self.assertIn('AuroraWorkshopTabsView.requestOriginalZipImport()',src)
        self.assertNotIn('api.nexusmods.com',src)
    def test_v50_registered_and_original_smapi_preserved(self):
        src=(self.root/"v50/inject_v50.py").read_text()
        for field in (LINK,SAFE_APK,UNIFIED,HUB):
            self.assertIn(field,src)
        self.assertIn('"500"',src)
        self.assertIn('5.0.0-rc.1',src)
        self.assertNotIn('network_permission.set(A + "name", "android.permission.QUERY_ALL_PACKAGES")',src)

if __name__=="__main__":
    unittest.main()
