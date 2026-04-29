"""Summarizer: produce a high-level audit summary across all env files in a directory."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv_audit.scanner import scan_directory
from dotenv_audit.parser import ParsedEnvFile, parse_env_file
from dotenv_audit.comparator import compare_many, ComparisonResult
from dotenv_audit.linter import lint, LintResult


@dataclass
class AuditSummary:
    directory: Path
    parsed_files: List[ParsedEnvFile] = field(default_factory=list)
    lint_results: List[LintResult] = field(default_factory=list)
    comparison: ComparisonResult | None = None

    @property
    def total_files(self) -> int:
        return len(self.parsed_files)

    @property
    def total_secrets(self) -> int:
        return sum(len(pf.flagged_entries) for pf in self.parsed_files)

    @property
    def total_lint_issues(self) -> int:
        return sum(len(lr.issues) for lr in self.lint_results)

    @property
    def has_issues(self) -> bool:
        if self.total_secrets > 0 or self.total_lint_issues > 0:
            return True
        if self.comparison is not None and self.comparison.has_issues:
            return True
        return False

    def summary(self) -> str:
        lines = [
            f"Directory : {self.directory}",
            f"Env files : {self.total_files}",
            f"Secrets   : {self.total_secrets}",
            f"Lint issues: {self.total_lint_issues}",
        ]
        if self.comparison is not None:
            lines.append(f"Comparison: {self.comparison.summary()}")
        status = "ISSUES FOUND" if self.has_issues else "OK"
        lines.append(f"Status    : {status}")
        return "\n".join(lines)


def build_summary(directory: str | Path) -> AuditSummary:
    """Scan *directory*, parse every env file, lint each one, and compare them all."""
    root = Path(directory)
    paths = scan_directory(root)

    parsed: List[ParsedEnvFile] = []
    lint_results: List[LintResult] = []

    for p in paths:
        pf = parse_env_file(p)
        parsed.append(pf)
        lint_results.append(lint(pf))

    comparison: ComparisonResult | None = compare_many(parsed) if len(parsed) >= 2 else None

    return AuditSummary(
        directory=root,
        parsed_files=parsed,
        lint_results=lint_results,
        comparison=comparison,
    )
