"""Filter parsed env files by key pattern, tag, or secret status."""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv_audit.parser import EnvEntry, ParsedEnvFile


@dataclass
class FilterResult:
    source: str
    matched: List[EnvEntry] = field(default_factory=list)
    total: int = 0

    @property
    def match_count(self) -> int:
        return len(self.matched)

    def summary(self) -> str:
        return (
            f"{self.source}: {self.match_count}/{self.total} keys matched"
        )


def _matches_pattern(key: str, pattern: str) -> bool:
    """Return True if *key* matches a glob or regex pattern."""
    if pattern.startswith("re:"):
        return bool(re.search(pattern[3:], key))
    return fnmatch.fnmatch(key, pattern)


def filter_env_file(
    parsed: ParsedEnvFile,
    *,
    pattern: Optional[str] = None,
    secrets_only: bool = False,
    empty_only: bool = False,
) -> FilterResult:
    """Return a FilterResult containing only entries that satisfy all criteria."""
    entries = list(parsed.entries)
    total = len(entries)

    if pattern:
        entries = [e for e in entries if _matches_pattern(e.key, pattern)]

    if secrets_only:
        entries = [e for e in entries if e.flagged_reason is not None]

    if empty_only:
        entries = [e for e in entries if not e.value.strip()]

    return FilterResult(source=parsed.path, matched=entries, total=total)


def filter_many(
    files: List[ParsedEnvFile],
    *,
    pattern: Optional[str] = None,
    secrets_only: bool = False,
    empty_only: bool = False,
) -> List[FilterResult]:
    """Apply filter_env_file across multiple parsed files."""
    return [
        filter_env_file(
            f,
            pattern=pattern,
            secrets_only=secrets_only,
            empty_only=empty_only,
        )
        for f in files
    ]
