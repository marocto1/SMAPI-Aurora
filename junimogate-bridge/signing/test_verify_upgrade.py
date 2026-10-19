import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import verify_upgrade as verifier


class SigningGateTests(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile() as tmp1, tempfile.NamedTemporaryFile() as tmp2:
            self.old = Path(tmp1.name)
            self.new = Path(tmp2.name)
        # no file read by compare except fake downstream calls
        self.old = Path("/tmp/aurora-old.apk")
        self.new = Path("/tmp/aurora-new.apk")

    def test_cannot_update_when_signers_differ(self):
        with patch.object(verifier, "package_and_version",
                          side_effect=[("org.junimogate.app", 20, "0.8.9"),
                                       ("org.junimogate.app", 26, "0.9.5")]):
            with patch.object(verifier, "signing_ids",
                              side_effect=[("a" * 64,), ("b" * 64,)]):
                good, explanation = verifier.compare(self.old, self.new, "signer", "aapt")
        self.assertFalse(good)
        self.assertIn("SIGNING MISMATCH", explanation)

    def test_accepts_only_same_signer_with_higher_code(self):
        with patch.object(verifier, "package_and_version",
                          side_effect=[("org.junimogate.app", 26, "0.9.5"),
                                       ("org.junimogate.app", 27, "0.9.6")]):
            with patch.object(verifier, "signing_ids",
                              side_effect=[("a" * 64,), ("a" * 64,)]):
                good, explanation = verifier.compare(self.old, self.new, "signer", "aapt")
        self.assertTrue(good)

    def test_version_downgrade_rejected_without_checking_signer(self):
        with patch.object(verifier, "package_and_version",
                          side_effect=[("org.junimogate.app", 26, "0.9.5"),
                                       ("org.junimogate.app", 25, "0.9.4")]):
            with patch.object(verifier, "signing_ids") as signer:
                good, message = verifier.compare(self.old, self.new, "signer", "aapt")
        self.assertFalse(good)
        signer.assert_not_called()

    def test_package_mismatch_rejected(self):
        with patch.object(verifier, "package_and_version",
                          side_effect=[("org.junimogate.app", 20, "0.8.9"),
                                       ("other.application", 26, "0.9.5")]):
            good, _ = verifier.compare(self.old, self.new, "signer", "aapt")
        self.assertFalse(good)


if __name__ == "__main__":
    unittest.main()
