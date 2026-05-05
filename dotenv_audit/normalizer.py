"""Normalizer: strips quotes, trims whitespace, and expands common
value aliases so downstream checks work on clean data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

# Aliases treated as logically-empty / placeholder values
_EMPTY_ALIASES = frozenset(
    {"null", "none", "nil", "undefined", "n/a", "na", "", "false", "true"}
)

_QUOTE_RE = re.compile(r'^(["\'])(.*?)\1$', re.DOTALL)


@dataclass
class NormalizedEntry:
    original: EnvEntry
    normalized_value: str
    was_quoted: bool
    is_empty_alias: bool

    def __str__(self) -> str:  # pragma: no cover
        tag = " [empty-alias]" if self.is_empty_alias else ""
        q = " [quoted]" if self.was_quoted else ""
        return f"{self.original.key}={self.normalized_value!r}{q}{tag}"


@dataclass
class NormalizedEnvFile:
    source: ParsedEnvFile
    entries: List[NormalizedEntry]

    @property
    def keys(self) -> List[str]:
        return [e.original.key for e in self.entries]

    @property
    def empty_alias_keys(self) -> List[str]:
        return [e.original.key for e in self.entries if e.is_empty_alias]

    @property
    def quoted_keys(self) -> List[str]:
        return [e.original.key for e in self.entries if e.was_quoted]


def _normalize_value(raw: str) -> tuple[str, bool]:
    """Return (stripped_value, was_quoted)."""
    stripped = raw.strip()
    m = _QUOTE_RE.match(stripped)
    if m:
        return m.group(2), True
    return stripped, False


def normalize_entry(entry: EnvEntry) -> NormalizedEntry:
    value, was_quoted = _normalize_value(entry.value)
    is_alias = value.lower() in _EMPTY_ALIASES
    return NormalizedEntry(
        original=entry,
        normalized_value=value,
        was_quoted=was_quoted,
        is_empty_alias=is_alias,
    )


def normalize_file(parsed: ParsedEnvFile) -> NormalizedEnvFile:
    return NormalizedEnvFile(
        source=parsed,
        entries=[normalize_entry(e) for e in parsed.entries],
    )
