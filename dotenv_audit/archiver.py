"""Archive snapshots of .env files for historical comparison."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


_DEFAULT_ARCHIVE = ".env-audit-archive.json"


@dataclass
class ArchiveEntry:
    path: str
    keys: List[str]
    secret_count: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "keys": self.keys,
            "secret_count": self.secret_count,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ArchiveEntry":
        return cls(
            path=d["path"],
            keys=d["keys"],
            secret_count=d["secret_count"],
            timestamp=d["timestamp"],
        )


@dataclass
class Archive:
    entries: List[ArchiveEntry] = field(default_factory=list)

    def add(self, entry: ArchiveEntry) -> None:
        self.entries.append(entry)

    def latest_for(self, path: str) -> Optional[ArchiveEntry]:
        matches = [e for e in self.entries if e.path == path]
        return max(matches, key=lambda e: e.timestamp) if matches else None

    def history_for(self, path: str) -> List[ArchiveEntry]:
        return sorted(
            [e for e in self.entries if e.path == path],
            key=lambda e: e.timestamp,
        )


def save_archive(archive: Archive, dest: Path) -> None:
    dest.write_text(
        json.dumps([e.to_dict() for e in archive.entries], indent=2),
        encoding="utf-8",
    )


def load_archive(src: Path) -> Archive:
    if not src.exists():
        return Archive()
    data = json.loads(src.read_text(encoding="utf-8"))
    return Archive(entries=[ArchiveEntry.from_dict(d) for d in data])


def snapshot_directory(directory: Path) -> List[ArchiveEntry]:
    """Scan *directory* and build one ArchiveEntry per .env file found."""
    from dotenv_audit.scanner import scan_directory
    from dotenv_audit.parser import parse_env_file

    entries: List[ArchiveEntry] = []
    for env_path in scan_directory(directory):
        parsed = parse_env_file(Path(env_path))
        secret_count = len(parsed.flagged_entries())
        entries.append(
            ArchiveEntry(
                path=str(Path(env_path).relative_to(directory)),
                keys=list(parsed.keys()),
                secret_count=secret_count,
            )
        )
    return entries
