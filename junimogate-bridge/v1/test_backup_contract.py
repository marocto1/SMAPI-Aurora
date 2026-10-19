import unittest
from pathlib import Path

HERE = Path(__file__).parent
BACKUP = (HERE / "AuroraBackupActivity.java").read_text()
VERSION = (HERE / "AuroraVersionActivity.java").read_text()


class BackupWorkflowTests(unittest.TestCase):
    def test_both_data_roots_included(self):
        for marker in (
            'getNoBackupFilesDir()', '"junimogate"', '"user-data"',
            'getExternalFilesDir(null)', '"Saves"', 'ROOT_USER = "userdata/"',
            'ROOT_SAVES = "saves/"',
        ):
            self.assertIn(marker, BACKUP)

    def test_requires_explicit_user_saftree_and_confirmed_restore(self):
        for marker in (
            'Intent.ACTION_CREATE_DOCUMENT', 'Intent.ACTION_OPEN_DOCUMENT',
            'getContentResolver().openOutputStream',
            'getContentResolver().openInputStream',
            'setPositiveButton("Подтвердить замену"',
            'setNegativeButton("Отмена"',
            'smapi-aurora-full-backup/v1',
        ):
            self.assertIn(marker, BACKUP)

    def test_archive_defenses(self):
        for marker in (
            'MAX_', 'LIMIT_ENTRIES', 'LIMIT_BYTES', 'LIMIT_SINGLE_FILE',
            'Files.isSymbolicLink(', 'sha256', 'MessageDigest.getInstance("SHA-256")',
            'validateName(', 'canonical.startsWith(', 'ZipInputStream',
            'if(overall>LIMIT_BYTES)', 'found.containsKey(name)',
        ):
            self.assertIn(marker, BACKUP)

    def test_rollback_originals_not_silently_discarded(self):
        for marker in (
            '".aurora-previous-user-"', '".aurora-previous-saves-"',
            'bu.renameTo(oldU)', 'bs.renameTo(oldS)',
            'boolean movedU=false,movedS=false,installedU=false,installedS=false',
        ):
            self.assertIn(marker, BACKUP)

    def test_v1_version_settings_hides_google_drive_download_ui(self):
        main = VERSION[VERSION.index("private void buildVersionsPage("):
                       VERSION.index("private String gameVersion(")]
        self.assertIn('button(catalogue, "Выбрать свой архив .apks"', main)
        self.assertNotIn("this::downloadAndInstallFromDrive", main)
        self.assertNotIn("this::editSavedLink", main)
        self.assertIn("не распространяет платные игровые APK", main)


if __name__ == "__main__":
    unittest.main()
