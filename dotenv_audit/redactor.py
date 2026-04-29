"""Redact secret values from .env files for safe output or logging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

_REDACTED = "***REDACTED***"
_PLACEHOLDER_MASK = "<value>"


@dataclass
class RedactedEntry:
    key: str
    original_value: str
    display_value: str
    was_redacted: bool

    def __str__(self) -> str:
        return f"{self.key}={self.display_value}"


@dataclass
class RedactedEnvFile:
    path: str
    entries: List[RedactedEntry]

    def lines(self) -> List[str]:
        """Return redacted key=value lines suitable for display."""
        return [str(e) for e in self.entries]

    def redacted_keys(self) -> List[str]:
        """Return keys whose values were redacted."""
        return [e.key for e in self.entries if e.was_redacted]


def redact_entry(entry: EnvEntry) -> RedactedEntry:
    """Produce a RedactedEntry, masking the value if it looks like a secret."""
    from dotenv_audit.parser import _looks_like_secret  # local import to avoid cycles

    flagged = _looks_like_secret(entry.key, entry.value)
    if flagged is not None:
        display = _REDACTED
        redacted = True
    elif not entry.value or entry.value.startswith("<"):
        display = entry.value or _PLACEHOLDER_MASK
        redacted = False
    else:
        display = entry.value
        redacted = False

    return RedactedEntry(
        key=entry.key,
        original_value=entry.value,
        display_value=display,
        was_redacted=redacted,
    )


def redact_file(parsed: ParsedEnvFile) -> RedactedEnvFile:
    """Redact all secret-looking entries in a ParsedEnvFile."""
    redacted_entries = [redact_entry(e) for e in parsed.entries]
    return RedactedEnvFile(path=parsed.path, entries=redacted_entries)
