"""Merge multiple .env files into a single unified output.

Keys from later files override earlier ones; all unique keys are collected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from dotenv_audit.parser import EnvEntry, ParsedEnvFile


@dataclass
class MergeConflict:
    key: str
    sources: List[str]  # file paths that defined this key

    def __str__(self) -> str:
        paths = ", ".join(self.sources)
        return f"Conflict on '{self.key}': defined in [{paths}]"


@dataclass
class MergeResult:
    entries: Dict[str, EnvEntry] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    @property
    def summary(self) -> str:
        if not self.has_conflicts:
            return f"Merged {len(self.entries)} key(s) with no conflicts."
        lines = [f"Merged {len(self.entries)} key(s) with {len(self.conflicts)} conflict(s):"]
        for c in self.conflicts:
            lines.append(f"  {c}")
        return "\n".join(lines)

    def to_lines(self) -> List[str]:
        """Render the merged result as .env-style lines."""
        out = []
        for key, entry in sorted(self.entries.items()):
            comment = f"  # {entry.comment}" if entry.comment else ""
            out.append(f"{key}={entry.value}{comment}")
        return out


def merge_env_files(files: Sequence[ParsedEnvFile]) -> MergeResult:
    """Merge parsed env files in order; later files win on conflict."""
    seen: Dict[str, List[str]] = {}
    merged: Dict[str, EnvEntry] = {}

    for pf in files:
        for key, entry in pf.entries.items():
            seen.setdefault(key, [])
            seen[key].append(pf.path)
            merged[key] = entry

    conflicts = [
        MergeConflict(key=k, sources=v)
        for k, v in seen.items()
        if len(v) > 1
    ]

    return MergeResult(entries=merged, conflicts=conflicts)
