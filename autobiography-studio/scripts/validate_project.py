#!/usr/bin/env python3
"""Validate autobiography project artifacts and recorded confirmation gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile


STAGE_APPROVALS = {
    "intake": ["consent"],
    "draft": ["consent", "outline"],
    "final": ["consent", "outline", "sensitive_content", "cover", "final_export"],
}

STAGE_FILES = {
    "intake": ["project-status.json"],
    "draft": [
        "project-status.json",
        "fact-ledger.md",
        "timeline.md",
        "people.md",
        "interview-notes.md",
        "privacy-decisions.md",
        "manuscript.md",
    ],
    "final": [
        "project-status.json",
        "fact-ledger.md",
        "timeline.md",
        "people.md",
        "interview-notes.md",
        "privacy-decisions.md",
        "manuscript.md",
        "output/book.docx",
        "output/book.pdf",
    ],
}


def valid_docx(path: Path) -> bool:
    if not path.is_file() or not zipfile.is_zipfile(path):
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return False
    return {"[Content_Types].xml", "word/document.xml"}.issubset(names)


def valid_pdf(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open("rb") as stream:
            header = stream.read(8)
            stream.seek(0, 2)
            size = stream.tell()
            tail_size = min(size, 1024)
            stream.seek(-tail_size, 2)
            tail = stream.read(tail_size)
    except OSError:
        return False
    return header.startswith(b"%PDF-") and b"%%EOF" in tail


def load_status(path: Path, invalid: list[str]) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        invalid.append("project-status.json")
        return {}
    if not isinstance(payload, dict) or not isinstance(payload.get("approvals"), dict):
        invalid.append("project-status.json")
        return {}
    return payload


def validate(project: Path, stage: str) -> dict:
    missing: list[str] = []
    invalid: list[str] = []

    for relative in STAGE_FILES[stage]:
        if not (project / relative).is_file():
            missing.append(relative)

    status = load_status(project / "project-status.json", invalid)
    approvals = status.get("approvals", {})
    for approval in STAGE_APPROVALS[stage]:
        if approvals.get(approval) is not True:
            missing.append(f"approval:{approval}")

    if stage == "final":
        if not valid_docx(project / "output" / "book.docx"):
            invalid.append("valid-docx")
        if not valid_pdf(project / "output" / "book.pdf"):
            invalid.append("valid-pdf")

    return {
        "ok": not missing and not invalid,
        "stage": stage,
        "project": str(project),
        "missing": sorted(set(missing)),
        "invalid": sorted(set(invalid)),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate autobiography project files and approval gates."
    )
    parser.add_argument("project", type=Path, help="Autobiography project directory")
    parser.add_argument(
        "--stage", choices=sorted(STAGE_FILES), required=True, help="Validation stage"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        print(f"error: project directory does not exist: {project}", file=sys.stderr)
        return 2

    report = validate(project, args.stage)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
