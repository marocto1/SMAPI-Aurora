"""Private Android GameHost compilation refs: safety and fail-closed tests."""
from pathlib import Path
import importlib.util
import io
import tempfile
import unittest
import zipfile

MODULE = Path(__file__).resolve().parents[1] / "verify_game_refs.py"
spec = importlib.util.spec_from_file_location("aurora_private_refs", MODULE)
refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refs)


def minimal_pe() -> bytes:
    # Structural synthetic PE marker; this is not a game library.
    b = bytearray(1024)
    b[:2] = b"MZ"
    b[0x3c:0x40] = (0x80).to_bytes(4, "little")
    b[0x80:0x84] = b"PE\x00\x00"
    b[0x80 + 20:0x80 + 22] = (224).to_bytes(2, "little")
    b[0x80 + 24:0x80 + 26] = (0x10b).to_bytes(2, "little")
    cli = 0x80 + 24 + 96 + 14 * 8
    b[cli:cli + 4] = (0x2000).to_bytes(4, "little")
    b[cli + 4:cli + 8] = (72).to_bytes(4, "little")
    return bytes(b)


def put_zip(destination, *, filenames=None, filedata=None):
    if filenames is None:
        filenames = sorted(refs.REQUIRED)
    data = minimal_pe() if filedata is None else filedata
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in filenames:
            z.writestr(name, data)


class PrivateReferenceTests(unittest.TestCase):
    def test_exact_five_dlls_can_be_checked_and_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "private.zip"
            put_zip(archive)
            out = Path(tmp) / "refs"
            sizes = refs.extract_private_references(archive, out, dry_run=True)
            self.assertEqual(set(sizes), refs.REQUIRED)
            self.assertFalse(out.exists())
            refs.extract_private_references(archive, out)
            self.assertEqual({p.name for p in out.iterdir()}, refs.REQUIRED)

    def test_dependencies_dll_prefix_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "private.zip"
            put_zip(archive, filenames=["DependenciesDll/" + name for name in refs.REQUIRED])
            self.assertEqual(len(refs.extract_private_references(
                archive, Path(tmp) / "out", dry_run=True)), 5)

    def test_extra_file_rejected_without_destination_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            put_zip(archive, filenames=[*refs.REQUIRED, "readme.txt"])
            out = Path(tmp) / "out"
            with self.assertRaises(refs.InvalidReferences):
                refs.extract_private_references(archive, out)
            self.assertFalse(out.exists())

    def test_zip_slip_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            bad = list(refs.REQUIRED)
            bad[0] = "../" + bad[0]
            put_zip(archive, filenames=bad)
            with self.assertRaises(refs.InvalidReferences):
                refs.extract_private_references(archive, Path(tmp) / "out")

    def test_fake_dll_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            put_zip(archive, filedata=b"Not a .NET DLL" * 100)
            with self.assertRaises(refs.InvalidReferences):
                refs.extract_private_references(archive, Path(tmp) / "out")

    def test_native_pe_without_cli_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "native-only.zip"
            data = bytearray(minimal_pe())
            cli = 0x80 + 24 + 96 + 14 * 8
            data[cli:cli + 8] = bytes(8)
            put_zip(archive, filedata=bytes(data))
            with self.assertRaises(refs.InvalidReferences):
                refs.extract_private_references(archive, Path(tmp) / "out")

    def test_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "valid.zip"
            put_zip(archive)
            out = Path(tmp) / "out"
            out.mkdir()
            (out / "keep.txt").write_text("protected")
            with self.assertRaises(refs.InvalidReferences):
                refs.extract_private_references(archive, out)
            self.assertEqual((out / "keep.txt").read_text(), "protected")

    def test_duplicate_entry_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            names=list(refs.REQUIRED)
            names[0]=names[1]
            put_zip(archive, filenames=names)
            with self.assertRaises(refs.InvalidReferences):
                refs.extract_private_references(archive, Path(tmp) / "out")


if __name__ == "__main__":
    unittest.main()
