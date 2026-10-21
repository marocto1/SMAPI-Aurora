import json
import tempfile
import unittest
from pathlib import Path
import workshop_v21 as workshop


class WorkshopPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/"Mods").mkdir()

    def _add(self,folder,metadata):
        f=self.root/"Mods"/folder
        f.mkdir()
        (f/"manifest.json").write_text(json.dumps(metadata),encoding="utf-8")

    def test_required_dependency_and_content_pack_missing(self):
        self._add("Example",{
            "Name":"Example", "UniqueID":"Example.Core","Version":"1.0.0",
            "Dependencies":[{"UniqueID":"Pathoschild.ContentPatcher",
                             "MinimumVersion":"2.0.0","IsRequired":True},
                            {"UniqueID":"Optional.Helper","IsRequired":False}]
        })
        missing=workshop.check_dependencies(self.root)
        self.assertEqual(len(missing),1)
        self.assertEqual(missing[0]["reason"],"missing")
        self._add("CP",{
            "Name":"Content Patcher", "UniqueID":"Pathoschild.ContentPatcher",
            "Version":"1.5.0"
        })
        old=workshop.check_dependencies(self.root)
        self.assertEqual(old[0]["reason"],"too-old")

    def test_known_mods_have_official_pages_no_auto_download(self):
        for name,category,url,unique in workshop.OFFICIAL_SOURCES:
            self.assertIn("https://www.nexusmods.com/stardewvalley/mods/",url)
        self.assertTrue(workshop.compare_numeric_version("2.0.0","1.9"))
        self.assertFalse(workshop.compare_numeric_version("1.2","1.3.0"))
        self.assertIsNone(workshop.compare_numeric_version("1.5-beta","1.5"))


if __name__=="__main__":
    unittest.main()
