"""Risk scoring for parsed .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.linter import lint_file, LintResult


# Weights assigned to each signal
_SECRET_WEIGHT = 10
_LINT_WEIGHT = 3
_EMPTY_VALUE_WEIGHT = 1
_MAX_SCORE = 100


@dataclass
class FileScore:
    path: str
    secret_count: int
    lint_issue_count: int
    empty_value_count: int
    score: int
    level: str  # "low" | "medium" | "high" | "critical"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.path}: {self.level.upper()} (score={self.score})"


def _level(score: int) -> str:
    if score == 0:
        return "low"
    if score < 15:
        return "medium"
    if score < 40:
        return "high"
    return "critical"


def score_file(parsed: ParsedEnvFile) -> FileScore:
    """Compute a risk score for a single parsed env file."""
    secrets = list(parsed.flagged_entries())
    lint: LintResult = lint_file(parsed)
    empty = [e for e in parsed.entries if e.value == ""]

    raw = (
        len(secrets) * _SECRET_WEIGHT
        + lint.issue_count * _LINT_WEIGHT
        + len(empty) * _EMPTY_VALUE_WEIGHT
    )
    clamped = min(raw, _MAX_SCORE)
    return FileScore(
        path=parsed.path,
        secret_count=len(secrets),
        lint_issue_count=lint.issue_count,
        empty_value_count=len(empty),
        score=clamped,
        level=_level(clamped),
    )


def score_many(files: List[ParsedEnvFile]) -> List[FileScore]:
    """Score a list of parsed env files, sorted highest risk first."""
    return sorted(
        (score_file(f) for f in files),
        key=lambda s: s.score,
        reverse=True,
    )
