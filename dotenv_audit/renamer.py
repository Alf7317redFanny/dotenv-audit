"""Rename keys across one or more .env files with optional dry-run support."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from dotenv_audit.parser import ParsedEnvFile, parse_env_file


@dataclass
class RenameResult:
    path: Path
    old_key: str
    new_key: str
    renamed: bool  # False when key was not found in this file

    def __str__(self) -> str:
        status = "renamed" if self.renamed else "not found"
        return f"{self.path}: {self.old_key} -> {self.new_key} ({status})"


@dataclass
class RenameReport:
    results: List[RenameResult] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(r.renamed for r in self.results)

    @property
    def summary(self) -> str:
        changed = sum(1 for r in self.results if r.renamed)
        total = len(self.results)
        return f"{changed}/{total} file(s) had key renamed."


def _rewrite_lines(lines: List[str], old_key: str, new_key: str) -> Tuple[List[str], bool]:
    """Return updated lines and whether a replacement occurred."""
    new_lines: List[str] = []
    renamed = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(f"{old_key}=") or stripped.startswith(f"{old_key} ="):
            new_lines.append(line.replace(old_key, new_key, 1))
            renamed = True
        else:
            new_lines.append(line)
    return new_lines, renamed


def rename_key_in_file(
    path: Path, old_key: str, new_key: str, dry_run: bool = False
) -> RenameResult:
    """Rename *old_key* to *new_key* inside a single .env file."""
    raw_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines, renamed = _rewrite_lines(raw_lines, old_key, new_key)
    if renamed and not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")
    return RenameResult(path=path, old_key=old_key, new_key=new_key, renamed=renamed)


def rename_key_in_directory(
    directory: Path, old_key: str, new_key: str, dry_run: bool = False
) -> RenameReport:
    """Walk *directory* and rename *old_key* to *new_key* in every .env file found."""
    from dotenv_audit.scanner import scan_directory

    report = RenameReport()
    for env_path in scan_directory(directory):
        result = rename_key_in_file(env_path, old_key, new_key, dry_run=dry_run)
        report.results.append(result)
    return report
