from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "autobiography-studio"


class SkillContractTests(unittest.TestCase):
    def test_required_runtime_files_exist(self):
        required = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/intake-privacy.md",
            "references/interview-styles.md",
            "references/research-production.md",
            "assets/templates/project-status.json",
            "assets/templates/fact-ledger.md",
            "assets/templates/manuscript.md",
            "assets/typographic-cover.svg",
        ]
        missing = [item for item in required if not (SKILL / item).is_file()]
        self.assertEqual([], missing)

    def test_frontmatter_is_discoverable_and_minimal(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name: autobiography-studio$")
        self.assertRegex(frontmatter, r"(?m)^description: Use when ")
        keys = re.findall(r"(?m)^([a-zA-Z0-9_-]+):", frontmatter)
        self.assertEqual(["name", "description"], keys)

    def test_core_safety_and_delivery_gates_are_explicit(self):
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]
        ).lower()
        required_phrases = [
            "do not log into",
            "user confirmation",
            "namesake",
            "living author",
            "do not rename",
            ".docx",
            ".pdf",
            "public-ready",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, corpus)


if __name__ == "__main__":
    unittest.main()
