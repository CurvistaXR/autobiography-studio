# Autobiography Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, validate, package, publish, and submit a privacy-first SkillHub skill that turns a person's voluntarily supplied life materials and guided interviews into a sourced autobiography with cover, table of contents, DOCX, and PDF outputs.

**Architecture:** A lean `autobiography-studio/` runtime bundle uses `SKILL.md` as the workflow state machine, three on-demand references for detailed judgment rules, reusable project templates, and two standard-library Python scripts for deterministic inventory and completion validation. Repository-only tests and marketplace files stay outside the release ZIP; the release ZIP places `SKILL.md` at its root and contains no personal test data.

**Tech Stack:** Markdown, YAML, Python 3 standard library, `unittest`, PowerShell, Git/GitHub CLI, SkillHub web dashboard.

---

## File map

- `autobiography-studio/SKILL.md`: trigger metadata, workflow, gates, capability routing, and reference loading rules.
- `autobiography-studio/agents/openai.yaml`: compatible host UI metadata.
- `autobiography-studio/references/intake-privacy.md`: consent, source intake, evidence states, and sensitive-data rules.
- `autobiography-studio/references/interview-styles.md`: adaptive interviews, style templates, titles, and outline approval.
- `autobiography-studio/references/research-production.md`: public-source research, drafting, cover, DOCX/PDF production, and verification.
- `autobiography-studio/assets/templates/*.md|json`: project ledger and manuscript scaffolds copied into a user's project.
- `autobiography-studio/assets/typographic-cover.svg`: safe fallback cover template.
- `autobiography-studio/scripts/inventory_materials.py`: deterministic, local-only source inventory.
- `autobiography-studio/scripts/validate_project.py`: stage and deliverable gate validator.
- `tests/test_skill_contract.py`: Skill package and safety-contract tests.
- `tests/test_inventory_materials.py`: inventory unit tests.
- `tests/test_validate_project.py`: project-gate unit tests.
- `tests/test_release_package.py`: ZIP structure, size, and privacy tests.
- `tools/package_skill.ps1`: builds the reproducible SkillHub ZIP and SHA-256 checksum.
- `marketplace/listing.zh-CN.md`: public SkillHub listing copy and reviewer instructions.
- `marketplace/claim-checklist.md`: exact import/claim field values and action-time checks.
- `README.md`, `LICENSE`: public repository documentation and license.

### Task 1: Establish the failing Skill contract

**Files:**
- Create: `tests/test_skill_contract.py`

- [ ] **Step 1: Write the failing contract test**

```python
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
```

- [ ] **Step 2: Run the contract test and verify RED**

Run: `python -m unittest tests.test_skill_contract -v`

Expected: FAIL because `autobiography-studio/` and its required files do not exist.

- [ ] **Step 3: Record the baseline failure**

Save the failing command and missing-path output in the implementation log section of the commit message or terminal evidence; do not create the Skill before observing this failure.

### Task 2: Create the minimal Skill runtime bundle

**Files:**
- Create: `autobiography-studio/SKILL.md`
- Create: `autobiography-studio/agents/openai.yaml`
- Create: `autobiography-studio/references/intake-privacy.md`
- Create: `autobiography-studio/references/interview-styles.md`
- Create: `autobiography-studio/references/research-production.md`
- Create: `autobiography-studio/assets/templates/project-status.json`
- Create: `autobiography-studio/assets/templates/fact-ledger.md`
- Create: `autobiography-studio/assets/templates/manuscript.md`
- Create: `autobiography-studio/assets/typographic-cover.svg`

- [ ] **Step 1: Initialize the Skill with the official scaffold**

Run:

```powershell
python C:\Users\Cao\.codex\skills\.system\skill-creator\scripts\init_skill.py autobiography-studio `
  --path E:\著书立传 `
  --resources scripts,references,assets `
  --interface 'display_name=人生自传成书' `
  --interface 'short_description=从个人资料与访谈生成可信、可编辑的自传' `
  --interface 'default_prompt=使用 $autobiography-studio 帮我整理个人材料、补充访谈并制作自传。'
```

Expected: a new `autobiography-studio/` folder with `SKILL.md`, `agents/openai.yaml`, and resource directories.

- [ ] **Step 2: Write the minimal orchestration instructions**

`SKILL.md` must contain this state model and no duplicated reference details:

```markdown
---
name: autobiography-studio
description: Use when a person wants to organize their own朋友圈 exports, diaries, documents, photos, memories, or public records into an autobiography, memoir, life story, family edition, Word book, or PDF book.
---

# Autobiography Studio

Build the book from evidence and explicit decisions. Never trade factual integrity or privacy for narrative smoothness.

## Start

1. Confirm the subject is the user and inputs are voluntarily provided.
2. Explain that the Skill does not log into or scrape private accounts.
3. Create a separate project directory and copy the templates into it.
4. Detect file, web, image, document, and PDF capabilities. Name missing capabilities.

## Workflow

Run these stages in order: intake, preferences, interview, optional research, outline approval, chapter drafting, cover approval, final approval, production, verification.

Do not cross these user confirmation gates: public-source adoption, outline approval, sensitive-content inclusion, cover selection, final export.

Read `references/intake-privacy.md` before intake. Read `references/interview-styles.md` before preferences or interviews. Read `references/research-production.md` before public research, drafting, cover work, or document production.

## Resume

Resume from project artifacts, not chat memory. Validate the project before drafting and again before final delivery.
```

- [ ] **Step 3: Add focused references and templates**

Implement the exact rules from the approved design: evidence states, dynamic interview rounds, five style templates, public-source confirmation, namesake disambiguation, living-author non-imitation, sensitive-data decisions, three cover routes, genuine DOCX/PDF production, reopening/render verification, and public-ready separation.

- [ ] **Step 4: Run the contract test and verify GREEN**

Run: `python -m unittest tests.test_skill_contract -v`

Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```powershell
git add autobiography-studio tests/test_skill_contract.py
git commit -m "feat: scaffold autobiography studio skill"
```

### Task 3: Implement deterministic material inventory with TDD

**Files:**
- Create: `tests/test_inventory_materials.py`
- Create: `autobiography-studio/scripts/inventory_materials.py`

- [ ] **Step 1: Write failing inventory tests**

```python
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
            text=True, capture_output=True, check=False
        )

    def test_inventory_is_sorted_and_marks_duplicates(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.txt").write_text("same", encoding="utf-8")
            (root / "a.txt").write_text("same", encoding="utf-8")
            output = root / "work" / "material-index.json"
            result = self.run_inventory(root, output)
            self.assertEqual(0, result.returncode, result.stderr)
            files = json.loads(output.read_text(encoding="utf-8"))["files"]
            self.assertEqual(["a.txt", "b.txt"], [item["path"] for item in files])
            self.assertIsNone(files[0]["duplicate_of"])
            self.assertEqual("a.txt", files[1]["duplicate_of"])

    def test_output_git_and_symlinks_are_not_followed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git" / "secret").write_text("x", encoding="utf-8")
            (root / "entry.md").write_text("memory", encoding="utf-8")
            output = root / "work" / "material-index.json"
            result = self.run_inventory(root, output)
            self.assertEqual(0, result.returncode, result.stderr)
            paths = [x["path"] for x in json.loads(output.read_text(encoding="utf-8"))["files"]]
            self.assertEqual(["entry.md"], paths)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run inventory tests and verify RED**

Run: `python -m unittest tests.test_inventory_materials -v`

Expected: FAIL because the CLI does not yet create the inventory.

- [ ] **Step 3: Implement the minimum inventory CLI**

Implement `main()`, SHA-256 streaming, UTC timestamps, normalized relative paths, deterministic sorting, duplicate linking, `.git` exclusion, output-directory exclusion, and no symlink traversal. Write JSON atomically using a sibling temporary file and `Path.replace()`.

- [ ] **Step 4: Run inventory tests and verify GREEN**

Run: `python -m unittest tests.test_inventory_materials -v`

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```powershell
git add autobiography-studio/scripts/inventory_materials.py tests/test_inventory_materials.py
git commit -m "feat: add local material inventory"
```

### Task 4: Implement project-gate validation with TDD

**Files:**
- Create: `tests/test_validate_project.py`
- Create: `autobiography-studio/scripts/validate_project.py`

- [ ] **Step 1: Write failing validation tests**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "autobiography-studio" / "scripts" / "validate_project.py"


class ProjectValidationTests(unittest.TestCase):
    def run_validator(self, project: Path, stage: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(project), "--stage", stage],
            text=True, capture_output=True, check=False
        )

    def test_draft_requires_consent_outline_and_working_ledgers(self):
        with TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "project-status.json").write_text(
                json.dumps({"approvals": {"consent": True, "outline": False}}),
                encoding="utf-8"
            )
            result = self.run_validator(project, "draft")
            self.assertNotEqual(0, result.returncode)
            report = json.loads(result.stdout)
            self.assertIn("approval:outline", report["missing"])
            self.assertIn("fact-ledger.md", report["missing"])

    def test_final_requires_real_docx_pdf_and_final_approval(self):
        with TemporaryDirectory() as tmp:
            project = Path(tmp)
            for name in ["fact-ledger.md", "timeline.md", "privacy-decisions.md", "manuscript.md"]:
                (project / name).write_text("ready", encoding="utf-8")
            (project / "project-status.json").write_text(
                json.dumps({"approvals": {"consent": True, "outline": True, "sensitive_content": True, "cover": True, "final_export": False}}),
                encoding="utf-8"
            )
            (project / "output").mkdir()
            (project / "output" / "book.docx").write_bytes(b"not-a-zip")
            (project / "output" / "book.pdf").write_bytes(b"not-a-pdf")
            result = self.run_validator(project, "final")
            report = json.loads(result.stdout)
            self.assertIn("approval:final_export", report["missing"])
            self.assertIn("valid-docx", report["invalid"])
            self.assertIn("valid-pdf", report["invalid"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run validator tests and verify RED**

Run: `python -m unittest tests.test_validate_project -v`

Expected: FAIL because stage validation is not implemented.

- [ ] **Step 3: Implement the validator**

Support `intake`, `draft`, and `final`. Emit one JSON report with `ok`, `stage`, `missing`, and `invalid`; return `0` only when valid. Verify DOCX by ZIP signature and PDF by `%PDF-` header, not by extension alone.

- [ ] **Step 4: Run validator tests and verify GREEN**

Run: `python -m unittest tests.test_validate_project -v`

Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```powershell
git add autobiography-studio/scripts/validate_project.py tests/test_validate_project.py
git commit -m "feat: validate autobiography project gates"
```

### Task 5: Add repository documentation and marketplace materials

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `marketplace/listing.zh-CN.md`
- Create: `marketplace/claim-checklist.md`
- Create: `marketplace/icon.png`
- Create: `marketplace/listing-cover.png`

- [ ] **Step 1: Write public documentation**

Document installation, example prompts, local-first privacy model, supported input sources, host-capability requirements, output tree, limitations, and a synthetic-data demo. Keep all real private materials out of the repository.

- [ ] **Step 2: Add an MIT license**

Use year `2026` and copyright holder `CurvistaXR`.

- [ ] **Step 3: Write SkillHub listing copy**

Include display name, identifier, version `1.0.0`, short description under 1024 characters, full description, example triggers, privacy disclosure, host dependencies, reviewer steps, and change note. State that it does not access WeChat automatically.

- [ ] **Step 4: Create marketplace art**

Generate a restrained square icon and horizontal listing cover using an original visual system: an open book, a timeline/ribbon, and a subtle portrait silhouette; no real person, platform logo, text-heavy composition, or misleading certification badge.

- [ ] **Step 5: Verify image dimensions and repository privacy**

Run:

```powershell
Get-ChildItem marketplace\*.png | Select-Object Name,Length
rg -n -i "password|token|api[_-]?key|身份证|手机号|家庭住址" . --glob '!docs/superpowers/**'
```

Expected: both PNGs exist; no credential or real-person fixture is present.

- [ ] **Step 6: Commit**

```powershell
git add README.md LICENSE marketplace
git commit -m "docs: add SkillHub listing materials"
```

### Task 6: Build and verify the release package with TDD

**Files:**
- Create: `tests/test_release_package.py`
- Create: `tools/package_skill.ps1`
- Create during build: `dist/autobiography-studio-1.0.0.zip`
- Create during build: `dist/autobiography-studio-1.0.0.zip.sha256`

- [ ] **Step 1: Write the failing package test**

```python
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "dist" / "autobiography-studio-1.0.0.zip"


class ReleasePackageTests(unittest.TestCase):
    def test_skillhub_zip_contract(self):
        self.assertTrue(ZIP.is_file())
        self.assertLessEqual(ZIP.stat().st_size, 10 * 1024 * 1024)
        with zipfile.ZipFile(ZIP) as archive:
            names = set(archive.namelist())
            self.assertIn("SKILL.md", names)
            self.assertFalse(any(name.startswith("autobiography-studio/") for name in names))
            self.assertFalse(any(name.startswith(("tests/", "marketplace/", "docs/")) for name in names))
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the package test and verify RED**

Run: `python -m unittest tests.test_release_package -v`

Expected: FAIL because the ZIP does not exist.

- [ ] **Step 3: Implement the reproducible package script**

Resolve exact workspace paths, remove only the explicit `dist/autobiography-studio-1.0.0.zip` target when rebuilding, stage the runtime contents in a temporary directory, exclude caches, create a root-level ZIP, enforce the 10MB limit, and write a SHA-256 checksum.

- [ ] **Step 4: Build and verify GREEN**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File tools\package_skill.ps1
python -m unittest discover -s tests -v
```

Expected: ZIP and checksum created; all tests pass.

- [ ] **Step 5: Run the official Skill validator**

Run:

```powershell
python C:\Users\Cao\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\著书立传\autobiography-studio
```

Expected: validation succeeds with no YAML or naming errors.

- [ ] **Step 6: Commit**

```powershell
git add tools/package_skill.ps1 tests/test_release_package.py dist
git commit -m "build: package SkillHub release"
```

### Task 7: Run a synthetic end-to-end acceptance check

**Files:**
- Create temporarily: a synthetic autobiography project outside tracked paths
- Modify if required: Skill runtime or tests associated with any discovered defect

- [ ] **Step 1: Create synthetic source material**

Use fictional entries only: two diary notes, one duplicate file, one approximate date conflict, and one namesake search candidate. Do not use a real person's private data.

- [ ] **Step 2: Run inventory and intake validation**

Run the inventory CLI, inspect `material-index.json`, copy project templates, and run `validate_project.py --stage intake`.

Expected: deterministic inventory, duplicate link, and a valid intake stage after consent is marked true.

- [ ] **Step 3: Exercise the behavioral contract**

Check that the Skill instructions reject automatic WeChat login, require namesake confirmation, allow sensitive questions to be skipped, refuse close imitation of a living author, stop before unapproved outline/export, and do not fake DOCX/PDF files when document capability is absent.

- [ ] **Step 4: Verify generated artifacts when capabilities are available**

Generate a short synthetic manuscript, typographic cover, DOCX, and PDF. Reopen the DOCX and render/inspect the PDF. If the host cannot create these formats in the test environment, record that exact limitation in the marketplace reviewer notes and keep the contract honest.

- [ ] **Step 5: Run the complete verification suite**

Run:

```powershell
python -m unittest discover -s tests -v
python C:\Users\Cao\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\著书立传\autobiography-studio
powershell -ExecutionPolicy Bypass -File tools\package_skill.ps1
git diff --check
git status --short
```

Expected: all tests and validators pass; only intentional release or documentation changes appear.

### Task 8: Publish to GitHub and submit to SkillHub

**Files:**
- No new runtime files unless platform validation identifies a defect.

- [ ] **Step 1: Read the GitHub publishing skill and verify account state**

Run:

```powershell
gh auth status
gh repo view CurvistaXR/autobiography-studio
git remote -v
```

Expected: authenticated account has write access to `CurvistaXR`; determine whether the target repository already exists before creating or pushing.

- [ ] **Step 2: Publish without overwriting unrelated history**

If the repository is absent, create a public repository from this workspace and push `main`. If it exists and has independent history, stop and choose a branch/PR integration path rather than force-pushing.

```powershell
gh repo create CurvistaXR/autobiography-studio --public --source . --remote origin --push
```

- [ ] **Step 3: Create the v1.0.0 release**

```powershell
git tag -a v1.0.0 -m "Autobiography Studio 1.0.0"
git push origin v1.0.0
gh release create v1.0.0 dist/autobiography-studio-1.0.0.zip dist/autobiography-studio-1.0.0.zip.sha256 --title "Autobiography Studio 1.0.0" --notes "Initial privacy-first SkillHub release."
```

- [ ] **Step 4: Verify remote evidence**

Run:

```powershell
gh repo view CurvistaXR/autobiography-studio --json url,visibility,defaultBranchRef
gh release view v1.0.0 --json url,assets
git status --short --branch
```

Expected: public repository, `main` default branch, two release assets, and local branch tracking the remote.

- [ ] **Step 5: Open SkillHub dashboard and prepare import/claim**

Navigate to `https://skillhub.cn/dashboard`, sign in if needed, select repository import/claim, use `CurvistaXR/autobiography-studio`, and compare parsed fields with `marketplace/claim-checklist.md`.

- [ ] **Step 6: Confirm the final external submission at action time**

Before the button that uploads/claims/submits the Skill for security review, state the exact repository, version, public listing name, and destination account to the user. Submit only after the required confirmation.

- [ ] **Step 7: Verify the resulting status**

Record the SkillHub item URL or dashboard identifier, parsed version, and actual state: imported, under review, approved, or rejected. If rejected, capture the exact reason, add a failing regression test where applicable, fix, rebuild, publish a higher semantic version, and resubmit.
