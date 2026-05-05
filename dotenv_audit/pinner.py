"""Pin the current state of .env keys to a snapshot for change detection."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class PinEntry:
    key: str
    has_value: bool  # True if non-empty, False if empty/missing


@dataclass
class PinSnapshot:
    source: str  # relative path of the .env file
    entries: List[PinEntry] = field(default_factory=list)

    def key_set(self) -> set:
        return {e.key for e in self.entries}


@dataclass
class PinDiff:
    source: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    filled: List[str] = field(default_factory=list)   # was empty, now has value
    emptied: List[str] = field(default_factory=list)  # had value, now empty

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.filled or self.emptied)

    def summary(self) -> str:
        if not self.has_changes:
            return f"{self.source}: no changes"
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.filled:
            parts.append(f"{len(self.filled)} filled")
        if self.emptied:
            parts.append(f"{len(self.emptied)} emptied")
        return f"{self.source}: {', '.join(parts)}"


def snapshot_from_parsed(parsed: ParsedEnvFile) -> PinSnapshot:
    entries = [
        PinEntry(key=e.key, has_value=bool(e.value and e.value.strip()))
        for e in parsed.entries
        if e.key
    ]
    return PinSnapshot(source=str(parsed.path), entries=entries)


def save_pin(snapshot: PinSnapshot, pin_path: Path) -> None:
    data = {
        "source": snapshot.source,
        "entries": [{"key": e.key, "has_value": e.has_value} for e in snapshot.entries],
    }
    pin_path.write_text(json.dumps(data, indent=2, sort_keys=True))


def load_pin(pin_path: Path) -> PinSnapshot:
    if not pin_path.exists():
        return PinSnapshot(source="")
    raw = json.loads(pin_path.read_text())
    entries = [PinEntry(key=e["key"], has_value=e["has_value"]) for e in raw.get("entries", [])]
    return PinSnapshot(source=raw.get("source", ""), entries=entries)


def diff_pin(old: PinSnapshot, new: PinSnapshot) -> PinDiff:
    old_map: Dict[str, bool] = {e.key: e.has_value for e in old.entries}
    new_map: Dict[str, bool] = {e.key: e.has_value for e in new.entries}

    added = [k for k in new_map if k not in old_map]
    removed = [k for k in old_map if k not in new_map]
    filled = [k for k in new_map if k in old_map and not old_map[k] and new_map[k]]
    emptied = [k for k in new_map if k in old_map and old_map[k] and not new_map[k]]

    return PinDiff(
        source=new.source or old.source,
        added=sorted(added),
        removed=sorted(removed),
        filled=sorted(filled),
        emptied=sorted(emptied),
    )
