"""Parser for .env files — extracts key-value pairs and detects suspicious values."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Patterns that suggest a value might be a real secret (not a placeholder)
SECRET_PATTERNS = [
    re.compile(r"[A-Za-z0-9+/]{32,}={0,2}"),   # base64-ish long strings
    re.compile(r"[0-9a-fA-F]{32,}"),             # hex tokens / hashes
    re.compile(r"sk-[A-Za-z0-9]{20,}"),          # OpenAI-style keys
    re.compile(r"ghp_[A-Za-z0-9]{36}"),          # GitHub personal access tokens
    re.compile(r"AKIA[0-9A-Z]{16}"),             # AWS access key IDs
]

PLACEHOLDER_PATTERN = re.compile(
    r"^(your[_-]|<|\{|TODO|CHANGE|REPLACE|EXAMPLE|PLACEHOLDER|xxx|changeme)",
    re.IGNORECASE,
)


@dataclass
class EnvEntry:
    key: str
    value: str
    line_number: int
    is_comment: bool = False
    is_empty: bool = False
    flagged: bool = False
    flag_reason: Optional[str] = None


@dataclass
class ParsedEnvFile:
    path: Path
    entries: list[EnvEntry] = field(default_factory=list)

    @property
    def keys(self) -> set[str]:
        return {e.key for e in self.entries if not e.is_comment and not e.is_empty}

    @property
    def flagged_entries(self) -> list[EnvEntry]:
        return [e for e in self.entries if e.flagged]


def _looks_like_secret(value: str) -> Optional[str]:
    """Return a reason string if the value looks like a real secret, else None."""
    if not value or PLACEHOLDER_PATTERN.match(value):
        return None
    for pattern in SECRET_PATTERNS:
        if pattern.search(value):
            return f"matches secret pattern: {pattern.pattern[:30]}"
    return None


def parse_env_file(path: Path) -> ParsedEnvFile:
    """Parse a .env file and return a ParsedEnvFile with flagged entries."""
    result = ParsedEnvFile(path=path)

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()

        if not stripped:
            result.entries.append(EnvEntry(key="", value="", line_number=lineno, is_empty=True))
            continue

        if stripped.startswith("#"):
            result.entries.append(EnvEntry(key=stripped, value="", line_number=lineno, is_comment=True))
            continue

        if "=" not in stripped:
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        reason = _looks_like_secret(value)
        entry = EnvEntry(
            key=key,
            value=value,
            line_number=lineno,
            flagged=reason is not None,
            flag_reason=reason,
        )
        result.entries.append(entry)

    return result
