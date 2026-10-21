"""Packaging gates: original .NET main activity, bundled Mods tabs and Aurora light/dark palette."""
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from inject_v40 import patch, UPDATE_CENTER, COOP, ROOMS, CATALOG, HUB, SAFETY, NETWORK, RECOVERY, UDP_CHECK, MOD_AUDIT, UNIFIED, A, LAUNCHER, WORKSHOP, OVERVIEW, BACKUP


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


class V40Integration(unittest.TestCase):
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
        self.assertEqual(names.count(UPDATE_CENTER), 1)
        self.assertEqual(names.count(COOP), 1)
        self.assertEqual(names.count(ROOMS), 1)
        self.assertEqual(names.count(CATALOG), 1)
        self.assertEqual(names.count(HUB), 1)
        self.assertEqual(names.count(SAFETY), 1)
        self.assertEqual(names.count(NETWORK), 1)
        self.assertEqual(names.count(RECOVERY), 1)
        self.assertEqual(names.count(UDP_CHECK), 1)
        self.assertEqual(names.count(MOD_AUDIT), 1)
        self.assertEqual(names.count(UNIFIED), 1)
        queries = root.find('queries')
        self.assertIsNotNone(queries)
        packages = [p.get(A + "name") for p in queries.findall('package')]
        self.assertIn('com.chucklefish.stardewvalley', packages)
        self.assertNotIn('android.permission.QUERY_ALL_PACKAGES',
                         [p.get(A + "name") for p in root.findall('uses-permission')])
        perms=[p.get('{http://schemas.android.com/apk/res/android}name')
               for p in root.findall('uses-permission')]
        self.assertIn('android.permission.ACCESS_NETWORK_STATE',perms)
        self.assertEqual(len([
            c for a in activities for i in a.findall("intent-filter")
            for c in i.findall("category") if c.get(A + "name") ==
            "android.intent.category.LAUNCHER"]), 1)
        layout = (self.root / "res/layout/fragment_mods.xml").read_text()
        self.assertEqual(layout.count("AuroraWorkshopTabsView"), 1)
        self.assertIn('android:layout_height="152dp"', layout)
        self.assertIn("mods_inventory_count", layout)
        yml = (self.root / "apktool.yml").read_text()
        self.assertIn("versionCode: 400", yml)
        self.assertIn("versionName: 4.0.0-rc.1", yml)
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
        verify_only=(root / "v14/AuroraBackupActivity.java").read_text()
        update=(root / "v14/AuroraUpdateCenterActivity.java").read_text()
        tabs=(root / "v14/AuroraWorkshopTabsView.java").read_text()
        self.assertIn('verifyArchive(uri)', verify_only)
        self.assertIn('Aurora Coop', update)
        self.assertIn('Multiplayer: not implemented', update)
        self.assertIn('AuroraUpdateCenterActivity.class', tabs)
        self.assertNotIn('commitRestore(',verify_only)
        self.assertNotIn('renameTo(',verify_only)
        self.assertNotIn('new FileOutputStream(target)',verify_only)
        self.assertNotIn('setPositiveButton("Подтвердить замену"',verify_only)
        self.assertIn('int verified=verifyArchive(uri)',verify_only)

        self.assertIn('if(!hadSaves && saved.isDirectory()', backup)


    def test_real_android_lan_preflight_and_honest_game_connect(self):
        root = Path(__file__).resolve().parents[1]
        coop = (root / "v18/AuroraCoopActivity.java").read_text()
        update = (root / "v18/AuroraUpdateCenterActivity.java").read_text()
        self.assertIn('validPrivateIPv4(', coop)
        self.assertIn('new InetSocketAddress(ip,AURORA_PORT)',coop)
        self.assertIn('TIMEOUT_MS',coop)
        self.assertIn('aurora-coop-status/v2', (root / "v18/AuroraCoopCompatibility.java").read_text())
        self.assertIn('UDP 24642',coop)
        self.assertIn('AuroraCoopActivity.class',update)
        self.assertIn('Co-op',coop)
        self.assertNotIn('VpnService',coop)
        self.assertNotIn('android.permission.BIND_VPN_SERVICE',coop)
        self.assertIn('AURORA_DISCOVER_V2 ',coop)
        self.assertIn('AURORA_HERE_V2 ',coop)
        self.assertIn('discoverLan()',coop)
        self.assertIn('validPrivateIPv4(address)',coop)
        self.assertIn('AuroraCoopCompatibility.compare(this,data)',coop)
        comp=(root / "v18/AuroraCoopCompatibility.java").read_text()
        self.assertIn('junimogate-mod-profile/v2',comp)
        self.assertIn('junimogate-mod-library/v1',comp)
        self.assertIn('smapi_version',comp)
        self.assertIn('game_version',comp)
        self.assertIn('manifest.getString("uniqueId")',comp)


    def test_room_invites_and_workshop_guards(self):
        root = Path(__file__).resolve().parents[1]
        room = (root / "v21/AuroraRoomActivity.java").read_text()
        catalog = (root / "v21/AuroraWorkshopCatalogActivity.java").read_text()
        update = (root / "v21/AuroraUpdateCenterActivity.java").read_text()
        workshop = (root / "v21/AuroraWorkshopActivity.java").read_text()
        for text in ('AURORA2', 'AURORA_ROOM_V1 ', 'allowedIPv4',
                     '100.64', 'AuroraCoopCompatibility.compare'):
            self.assertIn(text, room)
        self.assertIn('AuroraRoomActivity.class', update)
        self.assertIn('AuroraWorkshopCatalogActivity.class', workshop)
        self.assertIn('AuroraDirectDownloads.CURATED[0]', catalog)
        self.assertIn('AuroraWorkshopTabsView.requestOriginalZipImport()', catalog)
        self.assertIn('https://www.nexusmods.com/stardewvalley/mods/1915', catalog)
        self.assertIn('https://www.nexusmods.com/stardewvalley/mods/5098', catalog)
        self.assertNotIn('VpnService', room)
        self.assertNotIn('ProcessBuilder', room)

    def test_v25_native_ui_safety_vpn_and_workshop(self):
        root = Path(__file__).resolve().parents[1]
        safety = (root / "v25/AuroraSafetyActivity.java").read_text()
        net = (root / "v25/AuroraNetworkActivity.java").read_text()
        hub = (root / "v25/AuroraHubActivity.java").read_text()
        catalog = (root / "v25/AuroraWorkshopCatalogActivity.java").read_text()
        tabs = (root / "v25/AuroraWorkshopTabsView.java").read_text()
        for phrase in ("GET_SIGNING_CERTIFICATES","MessageDigest.getInstance(\"SHA-256\")",
                       "AuroraBackupActivity.class"):
            self.assertIn(phrase,safety)
        self.assertNotIn('deletePackage(',safety)
        self.assertIn('NetworkCapabilities.TRANSPORT_VPN',net)
        self.assertIn('AuroraRoomActivity.class',net)
        self.assertNotIn('VpnService',net)
        self.assertIn('AuroraSafetyActivity.class',hub)
        self.assertIn('AuroraNetworkActivity.class',hub)
        self.assertIn('AuroraHubActivity.class',tabs)
        for phrase in ('new EditText(this)','renderListings()','getPreferences(MODE_PRIVATE)',
                       'https://www.nexusmods.com/stardewvalley/mods/1063'):
            self.assertIn(phrase,catalog)
        self.assertNotIn('api.nexusmods.com',catalog)
        self.assertIn('AuroraDirectDownloads.CURATED[0]',catalog)

    def test_v30_recovery_udp_audit_ui_and_safe_signatures(self):
        root=Path(__file__).resolve().parents[1]
        recovery=(root / "v30/AuroraRecoveryPreviewActivity.java").read_text()
        udp=(root / "v30/AuroraUdpDiagnosticActivity.java").read_text()
        audit=(root / "v30/AuroraModAuditActivity.java").read_text()
        hub=(root / "v30/AuroraHubActivity.java").read_text()
        room=(root / "v30/AuroraRoomActivity.java").read_text()
        for c in ("AuroraBackupActivity.class","AuroraSafetyActivity.class"):
            self.assertIn(c,recovery)
        self.assertNotIn("FileOutputStream",recovery)
        self.assertNotIn("commitRestore",recovery)
        self.assertIn("AURORA_UDP_V1 ",udp)
        self.assertIn("AURORA_UDP_OK_V1 ",udp)
        self.assertIn("24645",udp)
        self.assertIn("24642",udp)
        self.assertIn("AuroraRoomActivity.parse(",udp)
        self.assertIn("AuroraCoopCompatibility.activeMods(this)",audit)
        self.assertIn("AuroraModAuditActivity.class",hub)
        self.assertIn("AuroraRecoveryPreviewActivity.class",hub)
        self.assertIn("AuroraUdpDiagnosticActivity.class",room)
        self.assertIn("CONTROL 4.0",hub)
        self.assertNotIn("VpnService",udp)
        self.assertNotIn("getExternalStorageDirectory",recovery)

    def test_v4_one_pass_tcp_udp_game_mod_wizard_and_hub(self):
        root=Path(__file__).resolve().parents[1]
        wizard=(root/"v40/AuroraUnifiedActivity.java").read_text()
        hub=(root/"v40/AuroraHubActivity.java").read_text()
        updates=(root/"v40/AuroraUpdateCenterActivity.java").read_text()
        for token in ("AURORA_ROOM_V1 ", "AURORA_UDP_V1 ",
                      "AURORA_UDP_OK_V1 ", "AuroraCoopCompatibility.compare(this,metadata)",
                      "Игровой UDP 24642: НЕ проверялся."):
            self.assertIn(token,wizard)
        self.assertIn("AuroraUnifiedActivity.class",hub)
        self.assertIn("AuroraUnifiedActivity.class",updates)
        self.assertIn("output.setText(latest)",wizard)
        self.assertNotIn("VpnService",wizard)
        self.assertNotIn("FileOutputStream",wizard)
        self.assertIn("com.chucklefish.stardewvalley",
            (root/"v40/inject_v40.py").read_text())

    def test_missing_night_colors_fails(self):
        (self.root / "res/values-night/colors.xml").unlink()
        with self.assertRaises(FileNotFoundError):
            patch(self.root)


if __name__ == "__main__":
    unittest.main()
