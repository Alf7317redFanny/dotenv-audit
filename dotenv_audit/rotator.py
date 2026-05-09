"""Key rotation support: detect stale secrets and suggest replacements."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class RotationEntry:
    key: str
    current_value: str
    last_rotated: Optional[datetime]
    is_stale: bool
    reason: str

    def __str__(self) -> str:
        ts = self.last_rotated.isoformat() if self.last_rotated else "unknown"
        return f"{self.key}: last_rotated={ts} stale={self.is_stale} ({self.reason})"


@dataclass
class RotationReport:
    source: str
    entries: List[RotationEntry] = field(default_factory=list)

    @property
    def has_stale(self) -> bool:
        return any(e.is_stale for e in self.entries)

    @property
    def stale_keys(self) -> List[str]:
        return [e.key for e in self.entries if e.is_stale]

    def summary(self) -> str:
        if not self.entries:
            return f"{self.source}: no tracked keys"
        stale = len(self.stale_keys)
        total = len(self.entries)
        if stale == 0:
            return f"{self.source}: all {total} key(s) up-to-date"
        return f"{self.source}: {stale}/{total} key(s) stale — {', '.join(self.stale_keys)}"


def _parse_timestamp(value: str) -> Optional[datetime]:
    """Try to extract an ISO-8601 timestamp embedded in a value comment or metadata."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def check_rotation(
    parsed: ParsedEnvFile,
    rotation_map: Dict[str, datetime],
    max_age_days: int = 90,
) -> RotationReport:
    """Build a RotationReport for *parsed* using *rotation_map* timestamps.

    Args:
        parsed: The parsed env file to inspect.
        rotation_map: Mapping of key -> last-rotated datetime (UTC).
        max_age_days: Keys older than this are considered stale.
    """
    now = datetime.now(tz=timezone.utc)
    entries: List[RotationEntry] = []

    for entry in parsed.entries:  # type: ignore[attr-defined]
        if not entry.value:
            continue
        last_rotated = rotation_map.get(entry.key)
        if last_rotated is None:
            entries.append(
                RotationEntry(
                    key=entry.key,
                    current_value=entry.value,
                    last_rotated=None,
                    is_stale=True,
                    reason="no rotation record found",
                )
            )
        else:
            age_days = (now - last_rotated).days
            stale = age_days > max_age_days
            entries.append(
                RotationEntry(
                    key=entry.key,
                    current_value=entry.value,
                    last_rotated=last_rotated,
                    is_stale=stale,
                    reason=f"age {age_days}d > {max_age_days}d limit" if stale else f"age {age_days}d ok",
                )
            )

    return RotationReport(source=parsed.path, entries=entries)
