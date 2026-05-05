"""Profile .env files and produce per-file health metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.linter import lint_env_file, LintResult
from dotenv_audit.scorer import score_file, FileScore


@dataclass
class EnvProfile:
    """Aggregated health profile for a single .env file."""

    path: str
    total_keys: int
    empty_keys: int
    secret_keys: int
    lint_result: LintResult
    score: FileScore

    # --- convenience properties ---

    @property
    def empty_ratio(self) -> float:
        if self.total_keys == 0:
            return 0.0
        return self.empty_keys / self.total_keys

    @property
    def secret_ratio(self) -> float:
        if self.total_keys == 0:
            return 0.0
        return self.secret_keys / self.total_keys

    def summary(self) -> str:
        lines = [
            f"File   : {self.path}",
            f"Keys   : {self.total_keys}  (empty={self.empty_keys}, secrets={self.secret_keys})",
            f"Score  : {self.score}",
            f"Lint   : {self.lint_result.summary()}",
        ]
        return "\n".join(lines)


def profile_env_file(parsed: ParsedEnvFile) -> EnvProfile:
    """Build an :class:`EnvProfile` from a parsed .env file."""
    entries = parsed.entries
    total_keys = len(entries)
    empty_keys = sum(1 for e in entries if e.value == "")
    secret_keys = len(parsed.flagged_entries())
    lint_result = lint_env_file(parsed)
    score = score_file(parsed)
    return EnvProfile(
        path=parsed.path,
        total_keys=total_keys,
        empty_keys=empty_keys,
        secret_keys=secret_keys,
        lint_result=lint_result,
        score=score,
    )


def profile_many(parsed_files: List[ParsedEnvFile]) -> List[EnvProfile]:
    """Return profiles for each file, sorted by path."""
    return sorted(
        [profile_env_file(p) for p in parsed_files],
        key=lambda pr: pr.path,
    )
