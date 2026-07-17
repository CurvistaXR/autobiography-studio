from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "autobiography-studio" / "scripts" / "validate_project.py"


class ProjectValidationTests(unittest.TestCase):
    def run_validator(self, project: Path, stage: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(project), "--stage", stage],
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def write_status(project: Path, approvals: dict[str, bool]):
        (project / "project-status.json").write_text(
            json.dumps({"schema_version": 1, "approvals": approvals}),
            encoding="utf-8",
        )

    @staticmethod
    def write_working_files(project: Path):
        for name in [
            "fact-ledger.md",
            "timeline.md",
            "people.md",
            "interview-notes.md",
            "privacy-decisions.md",
            "manuscript.md",
        ]:
            (project / name).write_text("ready", encoding="utf-8")

    def test_draft_requires_consent_outline_and_working_ledgers(self):
        with TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_status(project, {"consent": True, "outline": False})

            result = self.run_validator(project, "draft")

            self.assertEqual(1, result.returncode)
            report = json.loads(result.stdout)
            self.assertFalse(report["ok"])
            self.assertIn("approval:outline", report["missing"])
            self.assertIn("fact-ledger.md", report["missing"])

    def test_final_rejects_fake_docx_pdf_and_missing_final_approval(self):
        with TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_working_files(project)
            self.write_status(
                project,
                {
                    "consent": True,
                    "outline": True,
                    "sensitive_content": True,
                    "cover": True,
                    "final_export": False,
                },
            )
            (project / "output").mkdir()
            (project / "output" / "book.docx").write_bytes(b"not-a-zip")
            (project / "output" / "book.pdf").write_bytes(b"not-a-pdf")

            result = self.run_validator(project, "final")

            self.assertEqual(1, result.returncode)
            report = json.loads(result.stdout)
            self.assertIn("approval:final_export", report["missing"])
            self.assertIn("valid-docx", report["invalid"])
            self.assertIn("valid-pdf", report["invalid"])

    def test_final_accepts_minimal_real_file_signatures(self):
        with TemporaryDirectory() as tmp:
            project = Path(tmp)
            self.write_working_files(project)
            self.write_status(
                project,
                {
                    "consent": True,
                    "outline": True,
                    "sensitive_content": True,
                    "cover": True,
                    "final_export": True,
                },
            )
            output = project / "output"
            output.mkdir()
            with zipfile.ZipFile(output / "book.docx", "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
                archive.writestr("word/document.xml", "<document/>")
            (output / "book.pdf").write_bytes(b"%PDF-1.7\n%%EOF\n")

            result = self.run_validator(project, "final")

            self.assertEqual(0, result.returncode, result.stderr or result.stdout)
            self.assertTrue(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
