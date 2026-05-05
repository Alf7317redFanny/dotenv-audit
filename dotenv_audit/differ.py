"""Diff two .env files and report line-level changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class DiffLine:
    kind: str  # 'added' | 'removed' | 'changed' | 'unchanged'
    key: str
    old_value: str | None = None
    new_value: str | None = None

    def __str__(self) -> str:
        if self.kind == "added":
            return f"+ {self.key}={self.new_value}"
        if self.kind == "removed":
            return f"- {self.key}={self.old_value}"
        if self.kind == "changed":
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"  {self.key}={self.old_value}"


@dataclass
class DiffResult:
    left_path: str
    right_path: str
    lines: List[DiffLine] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(ln.kind != "unchanged" for ln in self.lines)

    @property
    def summary(self) -> str:
        added = sum(1 for ln in self.lines if ln.kind == "added")
        removed = sum(1 for ln in self.lines if ln.kind == "removed")
        changed = sum(1 for ln in self.lines if ln.kind == "changed")
        if not self.has_changes:
            return "No differences found."
        parts: List[str] = []
        if added:
            parts.append(f"{added} added")
        if removed:
            parts.append(f"{removed} removed")
        if changed:
            parts.append(f"{changed} changed")
        return ", ".join(parts) + "."


def diff_env_files(left: ParsedEnvFile, right: ParsedEnvFile) -> DiffResult:
    """Produce a DiffResult comparing *left* to *right*."""
    result = DiffResult(left_path=left.path, right_path=right.path)

    left_map = {e.key: e.value for e in left.entries if e.key}
    right_map = {e.key: e.value for e in right.entries if e.key}

    all_keys: List[str] = list(dict.fromkeys(list(left_map) + list(right_map)))

    for key in all_keys:
        in_left = key in left_map
        in_right = key in right_map
        if in_left and in_right:
            if left_map[key] == right_map[key]:
                result.lines.append(DiffLine("unchanged", key, left_map[key], right_map[key]))
            else:
                result.lines.append(DiffLine("changed", key, left_map[key], right_map[key]))
        elif in_left:
            result.lines.append(DiffLine("removed", key, old_value=left_map[key]))
        else:
            result.lines.append(DiffLine("added", key, new_value=right_map[key]))

    return result
