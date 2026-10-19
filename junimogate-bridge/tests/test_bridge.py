"""Unit tests for the JunimoGate-to-Aurora source transformation.

These tests use synthesized XML only; no game files or proprietary libraries.
Run via: python3 -m unittest discover -s junimogate-bridge/tests -v
"""
import importlib.util
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

SCRIPT = Path(__file__).resolve().parents[1] / "apply_aurora.py"
spec = importlib.util.spec_from_file_location("aurora_junimo_bridge", SCRIPT)
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)


class BridgeTests(unittest.TestCase):
    def test_upstream_pinned_and_package_distinct(self):
        self.assertEqual(len(bridge.UPSTREAM_SHA), 40)
        self.assertNotEqual(bridge.PACKAGE, "org.junimogate.app")
        self.assertNotEqual(bridge.PACKAGE, "com.marocto.smapi.aurora.preview")

    def test_replace_one_fail_closed(self):
        self.assertEqual(bridge.replace_one("a=1", "a=1", "b=2", "fixture"), "b=2")
        with self.assertRaises(ValueError):
            bridge.replace_one("none", "not-here", "x", "fixture")
        with self.assertRaises(ValueError):
            bridge.replace_one("abc abc", "abc", "x", "fixture")

    def test_dark_palette_preserves_material_ids(self):
        source = "<resources>" + "".join(
            f'<color name="{name}">#FFFFFF</color>' for name in bridge.PALETTE
        ) + "</resources>"
        output = bridge.patch_colors(source)
        root = ET.fromstring(output)
        for key, color in bridge.PALETTE.items():
            self.assertEqual(root.find(f"color[@name='{key}']").text, color)
        self.assertEqual(root.find("color[@name='aurora_launcher_bg']").text, "#0B0D19")

    def test_palette_schema_rejected_if_missing(self):
        with self.assertRaises(ValueError):
            bridge.patch_colors("<resources><color name='a'>#FFFFFF</color></resources>")

    def test_string_values_keep_format_placeholders(self):
        src = """<resources>
        <string name="app_name">Old</string>
        <string name="launcher_failed">Original %1$s</string>
        </resources>"""
        result = bridge.patch_strings(src, {
            "app_name": "SMAPI Aurora",
            "launcher_failed": "Ошибка: %1$s",
        })
        root = ET.fromstring(result)
        self.assertEqual(root.find("string[@name='launcher_failed']").text, "Ошибка: %1$s")
        with self.assertRaises(ValueError):
            bridge.patch_strings(src, {"no_key": "bad"})

    def test_russian_locale_validated_against_default_resources(self):
        src = "<resources>" + "".join(
            f'<string name="{name}">{value}</string>'
            for name, value in bridge.RU_STRINGS.items()
        ) + "</resources>"
        root = ET.fromstring(bridge.make_ru_resources(src))
        self.assertEqual(root.find("string[@name='nav_mods']").text, "Моды")
        with self.assertRaises(ValueError):
            bridge.make_ru_resources("<resources/>")

    def test_mismatched_android_format_argument_rejected(self):
        source = "<resources>" + "".join(
            f'<string name="{name}">{value}</string>'
            for name, value in bridge.RU_STRINGS.items()
        ) + "</resources>"
        source = source.replace("%1$s", "%1$d", 1)
        with self.assertRaisesRegex(ValueError, "format args"):
            bridge.make_ru_resources(source)

    def test_mark_and_backdrop_are_android_xml(self):
        self.assertTrue(ET.fromstring(bridge.MARK).tag.endswith("vector"))
        self.assertTrue(ET.fromstring(bridge.BACKDROP).tag.endswith("shape"))
        self.assertTrue(ET.fromstring(bridge.LAUNCHER).tag.endswith("adaptive-icon"))

    def test_upstream_license_is_not_an_overlay_target(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("GameHost", source)
        self.assertNotIn('changes[Path("LICENSE")]', source)
        self.assertNotIn("PatchAll()", source)


if __name__ == "__main__":
    unittest.main()
