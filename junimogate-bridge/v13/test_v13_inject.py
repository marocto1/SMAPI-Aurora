"""Packaging gates: original .NET main activity, bundled Mods tabs and Aurora light/dark palette."""
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from inject_v13 import patch, A, LAUNCHER, WORKSHOP, OVERVIEW, BACKUP


COLORS = {
    "values": [
        "junimo_launcher_background", "junimo_primary", "junimo_on_primary",
        "junimo_primary_container", "junimo_on_primary_container",
        "junimo_secondary", "junimo_on_secondary", "junimo_secondary_container",
        "junimo_on_secondary_container", "junimo_tertiary", "junimo_on_tertiary",
        "junimo_tertiary_container", "junimo_on_tertiary_container",
        "junimo_surface", "junimo_surface_container_low",
        "junimo_surface_container", "junimo_surface_container_high",
        "junimo_on_surface", "junimo_on_surface_variant", "junimo_outline",
        "junimo_outline_variant",
    ],
    "values-night": [
        "junimo_primary", "junimo_on_primary", "junimo_primary_container",
        "junimo_on_primary_container", "junimo_secondary", "junimo_on_secondary",
        "junimo_secondary_container", "junimo_on_secondary_container",
        "junimo_tertiary", "junimo_on_tertiary", "junimo_tertiary_container",
        "junimo_on_tertiary_container", "junimo_surface",
        "junimo_surface_container_low", "junimo_surface_container",
        "junimo_surface_container_high", "junimo_on_surface",
        "junimo_on_surface_variant", "junimo_outline", "junimo_outline_variant",
    ],
}


class V13Integration(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "res/layout").mkdir(parents=True)
        (self.root / "res/xml").mkdir(parents=True)
        (self.root / "res/values").mkdir(parents=True)
        (self.root / "res/values-night").mkdir(parents=True)
        (self.root / "AndroidManifest.xml").write_text(
            """<manifest xmlns:android="http://schemas.android.com/apk/res/android"
                package="org.junimogate.app"><application android:label="JunimoGate">
                <activity android:name="org.junimogate.app.MainActivity">
                  <intent-filter>
                    <action android:name="android.intent.action.MAIN" />
                    <category android:name="android.intent.category.LAUNCHER" />
                  </intent-filter>
                </activity></application></manifest>""", encoding="utf-8")
        (self.root / "res/layout/fragment_mods.xml").write_text(
            """<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android">
            <TextView android:layout_width="match_parent"
              android:id="@id/mods_inventory_count"
              android:layout_height="wrap_content" /></LinearLayout>""", encoding="utf-8")
        (self.root / "apktool.yml").write_text(
            "versionInfo:\n  versionCode: 20\n  versionName: 0.8.9\n", encoding="utf-8")
        for folder, names in COLORS.items():
            lines = "<resources>" + "".join(
                f'<color name="{n}">#123456</color>' for n in names) + "</resources>"
            (self.root / "res" / folder / "colors.xml").write_text(lines)

    def test_integrates_backup_workshop_and_game_versions_without_extra_main(self):
        patch(self.root)
        root = ET.parse(self.root / "AndroidManifest.xml").getroot()
        app = root.find("application")
        self.assertEqual(app.get(A + "label"), "SMAPI Aurora")
        activities = app.findall("activity")
        names = [a.get(A + "name") for a in activities]
        self.assertEqual(names.count(LAUNCHER), 1)
        self.assertEqual(names.count(WORKSHOP), 1)
        self.assertEqual(names.count(OVERVIEW), 1)
        self.assertEqual(names.count(BACKUP), 1)
        self.assertEqual(len([
            c for a in activities for i in a.findall("intent-filter")
            for c in i.findall("category") if c.get(A + "name") ==
            "android.intent.category.LAUNCHER"]), 1)
        layout = (self.root / "res/layout/fragment_mods.xml").read_text()
        self.assertEqual(layout.count("AuroraWorkshopTabsView"), 1)
        self.assertIn('android:layout_height="100dp"', layout)
        self.assertIn("mods_inventory_count", layout)
        yml = (self.root / "apktool.yml").read_text()
        self.assertIn("versionCode: 130", yml)
        self.assertIn("versionName: 1.3.0-rc.1", yml)
        light = ET.parse(self.root / "res/values/colors.xml").getroot()
        dark = ET.parse(self.root / "res/values-night/colors.xml").getroot()
        self.assertNotEqual(next(c.text for c in light if c.get("name") ==
                            "junimo_primary"), "#123456")
        self.assertNotEqual(next(c.text for c in dark if c.get("name") ==
                            "junimo_primary"), "#123456")

    def test_refuses_duplicate_patch(self):
        patch(self.root)
        with self.assertRaises(ValueError):
            patch(self.root)


    def test_updated_mod_health_workshop_and_save_safety_contracts(self):
        root = Path(__file__).resolve().parents[1]
        mods = (root / "mod-manager/AuroraModOverviewActivity.java").read_text()
        workshop = (root / "mod-manager/AuroraWorkshopActivity.java").read_text()
        nav = (root / "mod-manager/AuroraWorkshopTabsView.java").read_text()
        backup = (root / "v1/AuroraBackupActivity.java").read_text()
        for marker in ('"Активные"', '"Проблемы"', '"Выключены"',
                       'Intent.ACTION_CREATE_DOCUMENT', 'REPORT_PICKER'):
            self.assertIn(marker, mods)
        for marker in ('showCategories', 'addFavorite', 'showFavorites',
                       'safeFavoriteUrl', 'www.nexusmods.com'):
            self.assertIn(marker, workshop)
        self.assertIn('"Диагностика"', nav)
        self.assertIn('AuroraModOverviewActivity.class', nav)
        self.assertIn('smapi-aurora-full-backup/v1', backup)
        self.assertIn('if(!hadSaves && saved.isDirectory()', backup)

    def test_missing_night_colors_fails(self):
        (self.root / "res/values-night/colors.xml").unlink()
        with self.assertRaises(FileNotFoundError):
            patch(self.root)


if __name__ == "__main__":
    unittest.main()
