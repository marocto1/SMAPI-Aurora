"""Aurora 6.2 version UX: no S3 secrets in the game-version UI."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

class VersionUXTests(unittest.TestCase):
    def test_version_picker_only_shows_versions_and_system_install(self):
        ui=(HERE/"AuroraOwnerVersionsActivity.java").read_text(encoding="utf-8")
        hub=(HERE/"AuroraHubActivity.java").read_text(encoding="utf-8")
        installer=(HERE/"AuroraVersionActivity.java").read_text(encoding="utf-8")
        injector=(HERE/"inject_v62.py").read_text(encoding="utf-8")
        self.assertIn("Скачать и установить",ui)
        self.assertIn("AuroraOwnerVersionsActivity.class",hub)
        self.assertIn("AuroraOwnerVersionsActivity.class",
            (HERE/"AuroraWorkshopTabsView.java").read_text(encoding="utf-8"))
        self.assertNotIn("AuroraR2PrivateActivity.class",hub)
        for s in (ui,hub):
            self.assertNotIn("Access Key ID",s)
            self.assertNotIn("Secret Access Key",s)
        self.assertIn('R2_HOST.equals(host)',ui)
        self.assertIn("MessageDigest.getInstance(\"SHA-256\")",ui)
        self.assertIn("aurora-owner-verified-archive",ui)
        self.assertIn("startVerifiedOwnerArchive",installer)
        self.assertIn("installVerifiedBuild(content)",installer)
        self.assertIn("PackageInstaller",installer)
        self.assertIn('app.remove(node)',injector)
        self.assertIn('REQUEST_INSTALL_PACKAGES',injector)
        self.assertIn('6.2.0-rc.1',injector)

    def test_backend_tokens_and_signed_urls_are_private(self):
        source=(ROOT/"services/aurora-versions/app.py").read_text(encoding="utf-8")
        for marker in ('AURORA_ADMIN_TOKEN','AURORA_SESSION_SECRET',
                       'AURORA_PRIVATE_CATALOG_JSON','rights',
                       'owner-private-backup','X-Amz-Expires','UNSIGNED-PAYLOAD',
                       'hmac.compare_digest','PAIRINGS.pop(code,0)'):
            self.assertIn(marker,source)
        self.assertNotIn('Access-Control-Allow-Origin: *',source)
        self.assertNotIn("PUBLIC_GAME_APKS",source)

if __name__=="__main__":unittest.main()
