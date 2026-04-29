"""Lint individual .env files for common style and correctness issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class LintIssue:
    line_number: int
    key: str
    message: str

    def __str__(self) -> str:
        return f"  line {self.line_number}: [{self.key}] {self.message}"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def summary(self) -> str:
        if not self.has_issues:
            return f"{self.path}: OK"
        lines = [f"{self.path}: {len(self.issues)} issue(s)"]
        lines.extend(str(i) for i in self.issues)
        return "\n".join(lines)


_UPPERCASE_HINT = "key should be UPPER_SNAKE_CASE"
_EMPTY_VALUE_HINT = "value is empty — consider adding a placeholder like 'changeme'"
_SPACE_IN_KEY_HINT = "key contains spaces"
_DUPLICATE_KEY_HINT = "duplicate key detected"


def lint_env_file(parsed: ParsedEnvFile) -> LintResult:
    result = LintResult(path=parsed.path)
    seen_keys: dict[str, int] = {}

    for entry in parsed.entries:
        ln = entry.line_number
        k = entry.key

        if " " in k:
            result.issues.append(LintIssue(ln, k, _SPACE_IN_KEY_HINT))

        if k != k.upper():
            result.issues.append(LintIssue(ln, k, _UPPERCASE_HINT))

        if entry.value == "":
            result.issues.append(LintIssue(ln, k, _EMPTY_VALUE_HINT))

        if k in seen_keys:
            result.issues.append(
                LintIssue(ln, k, f"{_DUPLICATE_KEY_HINT} (first at line {seen_keys[k]})")
            )
        else:
            seen_keys[k] = ln

    return result
