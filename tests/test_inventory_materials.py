from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "autobiography-studio" / "scripts" / "inventory_materials.py"


class InventoryTests(unittest.TestCase):
    def run_inventory(self, source: Path, output: Path):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(source), "--output", str(output)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_inventory_is_sorted_and_marks_duplicates(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.txt").write_text("same", encoding="utf-8")
            (root / "a.txt").write_text("same", encoding="utf-8")
            output = root / "work" / "material-index.json"

            result = self.run_inventory(root, output)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            files = payload["files"]
            self.assertEqual(["a.txt", "b.txt"], [item["path"] for item in files])
            self.assertIsNone(files[0]["duplicate_of"])
            self.assertEqual("a.txt", files[1]["duplicate_of"])
            self.assertEqual(2, payload["summary"]["files"])
            self.assertEqual(1, payload["summary"]["duplicates"])

    def test_output_and_git_directory_are_excluded(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git" / "secret").write_text("x", encoding="utf-8")
            (root / "entry.md").write_text("memory", encoding="utf-8")
            output = root / "work" / "material-index.json"

            result = self.run_inventory(root, output)

            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(["entry.md"], [item["path"] for item in payload["files"]])

    def test_missing_source_returns_structured_error(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "material-index.json"

            result = self.run_inventory(root / "missing", output)

            self.assertEqual(2, result.returncode)
            self.assertIn("source directory does not exist", result.stderr.lower())
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
