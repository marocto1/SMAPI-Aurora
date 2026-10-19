"""Static contract for the source-only game-version chooser UI.

This is not an Android install/runtime test.
"""
from pathlib import Path
import importlib.util
import unittest
import xml.etree.ElementTree as ET

FILE=Path(__file__).resolve().parents[1]/"game_version_ui.py"
s=importlib.util.spec_from_file_location("game_version_ui", FILE)
ui=importlib.util.module_from_spec(s)
s.loader.exec_module(ui)

class GameVersionUiTests(unittest.TestCase):
    def test_translations_have_consistent_keys(self):
        self.assertEqual(set(ui.EN)-{"aurora_version_store_unavailable"},set(ui.RU))
        self.assertIn("Google Play",ui.RU["aurora_version_store"])
        self.assertIn("APK",ui.RU["aurora_version_choose_apk"])

    def test_no_unlicensed_paid_game_download_host(self):
        src=ui.ACTIVITY_SRC
        self.assertIn("market://details?id=com.chucklefish.stardewvalley",src)
        self.assertIn("https://play.google.com/store/apps/details?id=com.chucklefish.stardewvalley",src)
        self.assertNotIn("DownloadManager",src)
        self.assertNotIn("HttpClient",src)
        self.assertNotIn("googleplay.apk",src)
        self.assertIn("Intent.ActionOpenDocument",src)

    def test_explicit_consent_not_silent_install(self):
        src=ui.ACTIVITY_SRC
        self.assertIn("dialog.SetPositiveButton(Resource.String.aurora_version_install_action",src)
        self.assertIn("Resource.String.aurora_version_install_question",src)
        self.assertIn("CanRequestPackageInstalls",src)
        self.assertIn("ActivityFlags.GrantReadUriPermission",src)
        self.assertIn("Intent.ActionView",src)
        self.assertNotIn("PackageInstaller.Session",src)
        self.assertNotIn("InstallPackage(",src)

    def test_source_patch_references_existing_parts(self):
        src=FILE.read_text(encoding="utf-8")
        self.assertIn("HomeFragment.cs",src)
        self.assertIn("fragment_home.xml",src)
        self.assertIn("AndroidManifest.xml",src)
        self.assertIn("values-ru/strings.xml",src)
        self.assertIn("android.permission.REQUEST_INSTALL_PACKAGES",src)
        self.assertIn("@+id/aurora_game_versions",src)

    def test_ru_resources_xml_serializable(self):
        root=ET.Element("resources")
        for k,v in ui.RU.items():
            ET.SubElement(root,"string",{"name":k}).text=v
        self.assertEqual(len(ET.fromstring(ET.tostring(root)).findall("string")),len(ui.RU))

if __name__=="__main__":
    unittest.main()
