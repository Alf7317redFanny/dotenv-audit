"""sanitizer.py – strip or replace dangerous characters from env values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

# Characters that are unsafe in shell contexts or commonly cause parse issues
_UNSAFE_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_UNQUOTED_SPECIAL = re.compile(r'[\s\'"\\&#|;<>$`!]')


@dataclass
class SanitizeIssue:
    key: str
    original: str
    sanitized: str
    reason: str

    def __str__(self) -> str:  # noqa: D105
        return f"{self.key}: {self.reason} (was {self.original!r}, now {self.sanitized!r})"


@dataclass
class SanitizeResult:
    source: str
    issues: List[SanitizeIssue] = field(default_factory=list)
    clean_lines: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        if not self.has_issues:
            return f"{self.source}: no sanitization needed"
        lines = [f"{self.source}: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def _sanitize_value(value: str) -> tuple[str, str | None]:
    """Return (sanitized_value, reason) or (value, None) if clean."""
    if _UNSAFE_PATTERN.search(value):
        cleaned = _UNSAFE_PATTERN.sub("", value)
        return cleaned, "contains control characters"
    if not (value.startswith('"') or value.startswith("'")):
        if _UNQUOTED_SPECIAL.search(value):
            cleaned = f'"{value}"'
            return cleaned, "unquoted value contains special shell characters"
    return value, None


def sanitize_env_file(parsed: ParsedEnvFile) -> SanitizeResult:
    """Scan and sanitize all entries in *parsed*, returning a SanitizeResult."""
    result = SanitizeResult(source=parsed.path)
    for entry in parsed.entries:
        if entry.value is None:
            result.clean_lines.append(f"{entry.key}=")
            continue
        sanitized, reason = _sanitize_value(entry.value)
        if reason:
            result.issues.append(
                SanitizeIssue(
                    key=entry.key,
                    original=entry.value,
                    sanitized=sanitized,
                    reason=reason,
                )
            )
            result.clean_lines.append(f"{entry.key}={sanitized}")
        else:
            result.clean_lines.append(f"{entry.key}={entry.value}")
    return result
