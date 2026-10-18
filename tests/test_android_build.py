"""Offline tests for private compilation reference intake (no game files needed)."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.prepare_android_build import REQUIRED, stage_references


class ReferenceBundleTests(unittest.TestCase):
    def build_zip(self, name: Path, entries: dict[str, bytes]) -> None:
        with zipfile.ZipFile(name, "w") as package:
            for entry, content in entries.items():
                package.writestr(entry, content)

    def test_accepts_exact_three_dlls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "references.zip"
            self.build_zip(archive, {item: b"placeholder binary" for item in REQUIRED})
            staged = stage_references(archive, root / "refs")
            self.assertEqual(set(staged), REQUIRED)
            for filename in REQUIRED:
                self.assertEqual((root / "refs" / filename).read_bytes(), b"placeholder binary")

    def test_accepts_nested_dependencies_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "references.zip"
            self.build_zip(archive, {"DependenciesDll/" + item: b"binary" for item in REQUIRED})
            self.assertEqual(set(stage_references(archive, root / "refs")), REQUIRED)

    def test_rejects_incomplete_reference_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "references.zip"
            self.build_zip(archive, {"StardewValley.dll": b"binary"})
            with self.assertRaisesRegex(ValueError, "Missing required"):
                stage_references(archive, root / "refs")

    def test_rejects_other_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "references.zip"
            entries = {item: b"binary" for item in REQUIRED}
            entries["../malicious.txt"] = b"x"
            self.build_zip(archive, entries)
            with self.assertRaises(ValueError):
                stage_references(archive, root / "refs")

    def test_rejects_duplicate_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "references.zip"
            entries = {item: b"binary" for item in REQUIRED}
            entries["DependenciesDll/StardewValley.dll"] = b"duplicate"
            self.build_zip(archive, entries)
            with self.assertRaisesRegex(ValueError, "duplicated"):
                stage_references(archive, root / "refs")


if __name__ == "__main__":
    unittest.main()
