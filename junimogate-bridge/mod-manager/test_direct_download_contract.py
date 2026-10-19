"""Static safety checks for the first-party, checksum-pinned Workshop ZIP path."""
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOWNLOADER = (HERE / "AuroraDirectDownloads.java").read_text(encoding="utf-8")
WORKSHOP = (HERE / "AuroraWorkshopActivity.java").read_text(encoding="utf-8")


class DownloadSafetyTests(unittest.TestCase):
    def test_owner_controlled_source_and_exact_sha256(self):
        self.assertIn("github.com/marocto1/SMAPI-Aurora/releases/download/", DOWNLOADER)
        self.assertIn(
            "c314427ab39d5c061938fccf50a089c811040a8087a7cd946489d69561e67268",
            DOWNLOADER,
        )
        self.assertIn("Aurora-SMAPI-Smoke-Mod-v1.0.0.zip", DOWNLOADER)

    def test_secure_transport_and_bound_download(self):
        for required in (
            "allowedGithubReleaseHost(link)",
            'host.equals("github.com")',
            'host.equals("release-assets.githubusercontent.com")',
            "connection.setInstanceFollowRedirects(false)",
            "MAX_REDIRECTS",
            "MAX_ZIP_BYTES",
            "MAX_UNCOMPRESSED_BYTES",
            "validateArchive(outputFile)",
            "MessageDigest.isEqual(",
            "SHA-256",
        ):
            self.assertIn(required, DOWNLOADER)

    def test_android_download_published_only_after_verification(self):
        self.assertLess(DOWNLOADER.index("downloadVerified(item, stage)"),
                        DOWNLOADER.index("resolver.insert("))
        self.assertIn("values.put(MediaStore.Downloads.IS_PENDING, 1)", DOWNLOADER)
        self.assertIn("values.put(MediaStore.Downloads.IS_PENDING, 0)", DOWNLOADER)
        self.assertIn("activity.getContentResolver().delete(record, null, null)", DOWNLOADER)
        self.assertNotIn("library-index.json", DOWNLOADER)
        self.assertNotIn("active-profile.json", DOWNLOADER)
        self.assertNotIn("profile.json", DOWNLOADER)

    def test_original_mods_picker_is_sole_installer(self):
        self.assertIn("AuroraWorkshopTabsView.requestOriginalZipImport()", WORKSHOP)
        self.assertIn("Мод ещё НЕ установлен", WORKSHOP)
        self.assertIn("Проверенные моды · Скачать из GitHub", WORKSHOP)
        self.assertNotIn("api.nexusmods.com", WORKSHOP)
        self.assertNotIn("apikey", WORKSHOP.lower())


if __name__ == "__main__":
    unittest.main()
