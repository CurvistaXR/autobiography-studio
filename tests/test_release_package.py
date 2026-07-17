from pathlib import Path
import hashlib
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "dist" / "autobiography-studio-1.0.0.zip"
CHECKSUM = ROOT / "dist" / "autobiography-studio-1.0.0.zip.sha256"


class ReleasePackageTests(unittest.TestCase):
    def test_skillhub_zip_contract(self):
        self.assertTrue(ZIP.is_file())
        self.assertLessEqual(ZIP.stat().st_size, 10 * 1024 * 1024)

        with zipfile.ZipFile(ZIP) as archive:
            names = set(archive.namelist())
            self.assertIn("SKILL.md", names)
            self.assertFalse(
                any(name.startswith("autobiography-studio/") for name in names)
            )
            self.assertFalse(
                any(name.startswith(("tests/", "marketplace/", "docs/")) for name in names)
            )
            self.assertFalse(
                any("__pycache__" in name or name.endswith(".pyc") for name in names)
            )
            self.assertFalse(any(name.endswith(".tmp") for name in names))

    def test_checksum_matches_release(self):
        self.assertTrue(CHECKSUM.is_file())
        expected = hashlib.sha256(ZIP.read_bytes()).hexdigest()
        actual = CHECKSUM.read_text(encoding="utf-8").split()[0]
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
