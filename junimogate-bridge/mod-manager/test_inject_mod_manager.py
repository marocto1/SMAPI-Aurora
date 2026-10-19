import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from inject_mod_manager import A, OVERVIEW, WORKSHOP, LAUNCHER, patch


class ModManagerPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "res/xml").mkdir(parents=True)
        (self.root / "res/values").mkdir(parents=True)
        (self.root / "res/layout").mkdir(parents=True)
        (self.root / "res/layout/fragment_mods.xml").write_text("""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android">
    <TextView
            android:id="@+id/mods_inventory_count"
            android:layout_width="match_parent"
            android:layout_height="32dp" />
</LinearLayout>
""", encoding="utf-8")
        (self.root / "apktool.yml").write_text(
            "versionInfo:\n  versionCode: 20\n  versionName: 0.8.9-boot-recovery-qa\n"
        )
        (self.root / "AndroidManifest.xml").write_text(
            '''<manifest xmlns:android="http://schemas.android.com/apk/res/android"
                package="org.junimogate.app"><application>
                <activity android:name="org.junimogate.app.MainActivity" android:exported="true">
                  <intent-filter>
                    <action android:name="android.intent.action.MAIN" />
                    <category android:name="android.intent.category.LAUNCHER" />
                  </intent-filter>
                </activity>
                <activity android:name="org.junimogate.aurora.AuroraVersionActivity"
                    android:exported="false" />
                </application></manifest>'''
        )

    def test_valid_patch_retains_single_main_launcher_and_version_manager(self):
        patch(self.root)
        root = ET.parse(self.root / "AndroidManifest.xml").getroot()
        activities = root.find("application").findall("activity")
        self.assertEqual([a.get(A + "name") for a in activities].count(LAUNCHER), 1)
        self.assertEqual([a.get(A + "name") for a in activities].count(OVERVIEW), 1)
        self.assertEqual([a.get(A + "name") for a in activities].count(WORKSHOP), 1)
        self.assertEqual(
            len([a for a in activities if a.get(A + "name") ==
                 "org.junimogate.aurora.AuroraVersionActivity"]), 1)
        self.assertEqual(len([node for a in activities for node in a.findall("intent-filter")
                              if any(c.get(A + "name") == "android.intent.category.LAUNCHER"
                                     for c in node.findall("category"))]), 1)
        main = next(a for a in activities if a.get(A + "name") == LAUNCHER)
        shortcuts = [m for m in main.findall("meta-data")
                     if m.get(A + "name") == "android.app.shortcuts"]
        self.assertEqual(len(shortcuts), 1)
        self.assertEqual(shortcuts[0].get(A + "resource"), "@xml/aurora_mod_shortcuts")
        shortcut = ET.parse(self.root / "res/xml/aurora_mod_shortcuts.xml").getroot()
        self.assertEqual(shortcut[0][0].get(A + "targetClass"), OVERVIEW)
        self.assertEqual(len(shortcut), 2)
        self.assertEqual(shortcut[1][0].get(A + "targetClass"), WORKSHOP)
        strings = ET.parse(self.root / "res/values/aurora_mod_manager_strings.xml").getroot()
        self.assertEqual(len(strings), 4)
        layout = (self.root / "res/layout/fragment_mods.xml").read_text()
        self.assertEqual(layout.count("AuroraWorkshopTabsView"), 1)
        self.assertIn("mods_inventory_count", layout)
        self.assertIn("@style/Theme.JunimoGate", (self.root / "AndroidManifest.xml").read_text())
        self.assertIn("0.9.5-direct-download-qa", (self.root / "apktool.yml").read_text())

    def test_apktool_normalized_mods_layout(self):
        p = self.root / "res/layout/fragment_mods.xml"
        text = p.read_text().replace('@+id/mods_inventory_count',
                                     '@id/mods_inventory_count')
        p.write_text(text)
        patch(self.root)
        self.assertEqual(p.read_text().count("AuroraWorkshopTabsView"), 1)

    def test_patch_rejects_duplicates_instead_of_corrupting_manifest(self):
        patch(self.root)
        with self.assertRaises(ValueError):
            patch(self.root)

    def test_patch_rejects_missing_managed_launcher(self):
        manifest = self.root / "AndroidManifest.xml"
        manifest.write_text(manifest.read_text().replace(LAUNCHER, "wrong.Activity"))
        with self.assertRaises(ValueError):
            patch(self.root)


if __name__ == "__main__":
    unittest.main()
