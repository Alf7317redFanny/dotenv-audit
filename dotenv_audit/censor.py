"""Censor module: mask secret values in env files for safe display or logging."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

_MASK = "***"
_PARTIAL_VISIBLE = 4  # chars to keep at start when partially masking


@dataclass
class CensoredEntry:
    key: str
    original_value: str
    censored_value: str
    was_censored: bool

    def __str__(self) -> str:
        return f"{self.key}={self.censored_value}"


@dataclass
class CensoredEnvFile:
    source: str
    entries: List[CensoredEntry] = field(default_factory=list)

    @property
    def censored_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.was_censored]

    @property
    def lines(self) -> List[str]:
        return [str(e) for e in self.entries]

    def summary(self) -> str:
        n = len(self.censored_keys)
        if n == 0:
            return f"{self.source}: no values censored"
        return f"{self.source}: {n} value(s) censored"


def _censor_value(value: str, partial: bool = False) -> str:
    """Return a masked version of *value*.

    If *partial* is True and the value is long enough, keep the first
    _PARTIAL_VISIBLE characters and mask the rest.
    """
    if not value:
        return value
    if partial and len(value) > _PARTIAL_VISIBLE + 2:
        return value[:_PARTIAL_VISIBLE] + _MASK
    return _MASK


def censor_env_file(
    parsed: ParsedEnvFile,
    partial: bool = False,
) -> CensoredEnvFile:
    """Return a CensoredEnvFile where flagged entries have their values masked."""
    censored_entries: List[CensoredEntry] = []
    for entry in parsed.entries:
        is_secret = entry.flag is not None and bool(entry.value)
        if is_secret:
            cv = _censor_value(entry.value, partial=partial)
            censored_entries.append(
                CensoredEntry(
                    key=entry.key,
                    original_value=entry.value,
                    censored_value=cv,
                    was_censored=True,
                )
            )
        else:
            censored_entries.append(
                CensoredEntry(
                    key=entry.key,
                    original_value=entry.value,
                    censored_value=entry.value,
                    was_censored=False,
                )
            )
    return CensoredEnvFile(source=parsed.path, entries=censored_entries)


def censor_many(
    files: List[ParsedEnvFile],
    partial: bool = False,
) -> List[CensoredEnvFile]:
    return [censor_env_file(f, partial=partial) for f in files]
