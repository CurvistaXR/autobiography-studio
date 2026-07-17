#!/usr/bin/env python3
"""Create a local-only metadata inventory for autobiography source files."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Iterable


CHUNK_SIZE = 1024 * 1024
DEFAULT_EXCLUDED_DIRS = {".git", ".worktrees", "__pycache__"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def iter_files(source: Path, output: Path, excluded_names: set[str]) -> Iterable[Path]:
    output_parent = output.parent.resolve()
    excluded_output_tree = output_parent if output_parent != source else None

    for current, directories, files in os.walk(source, followlinks=False):
        current_path = Path(current)
        kept_directories = []
        for name in sorted(directories):
            candidate = current_path / name
            if name in excluded_names or candidate.is_symlink():
                continue
            resolved = candidate.resolve()
            if excluded_output_tree and (
                resolved == excluded_output_tree
                or is_relative_to(resolved, excluded_output_tree)
            ):
                continue
            kept_directories.append(name)
        directories[:] = kept_directories

        for name in sorted(files):
            candidate = current_path / name
            if candidate.is_symlink():
                continue
            resolved = candidate.resolve()
            if resolved == output or resolved == output.with_suffix(output.suffix + ".tmp"):
                continue
            yield candidate


def build_inventory(source: Path, output: Path, extra_excludes: list[str]) -> dict:
    excluded_names = DEFAULT_EXCLUDED_DIRS | set(extra_excludes)
    paths = sorted(
        iter_files(source, output, excluded_names),
        key=lambda path: path.relative_to(source).as_posix().casefold(),
    )

    files = []
    first_by_hash: dict[str, str] = {}
    total_bytes = 0
    errors = 0
    duplicates = 0

    for path in paths:
        relative = path.relative_to(source).as_posix()
        try:
            stat = path.stat()
            digest = sha256_file(path)
            duplicate_of = first_by_hash.get(digest)
            if duplicate_of is None:
                first_by_hash[digest] = relative
            else:
                duplicates += 1
            total_bytes += stat.st_size
            files.append(
                {
                    "path": relative,
                    "extension": path.suffix.lower(),
                    "size": stat.st_size,
                    "modified_utc": iso_utc(stat.st_mtime),
                    "sha256": digest,
                    "duplicate_of": duplicate_of,
                    "status": "inventoried",
                }
            )
        except (OSError, PermissionError) as exc:
            errors += 1
            files.append(
                {
                    "path": relative,
                    "extension": path.suffix.lower(),
                    "status": "unreadable",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    return {
        "schema_version": 1,
        "source": str(source),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": {
            "files": len(files),
            "duplicates": duplicates,
            "unreadable": errors,
            "total_bytes": total_bytes,
        },
        "files": files,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory local autobiography source files without extracting content."
    )
    parser.add_argument("source", type=Path, help="Source directory to inventory")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON path")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="DIRNAME",
        help="Additional directory name to exclude; may be repeated",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()

    if not source.is_dir():
        print(f"error: source directory does not exist: {source}", file=sys.stderr)
        return 2
    if output == source or is_relative_to(source, output):
        print("error: output must be a file path outside the source path itself", file=sys.stderr)
        return 2

    payload = build_inventory(source, output, args.exclude)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
