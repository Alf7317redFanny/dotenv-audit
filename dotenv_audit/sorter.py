"""Sort keys in .env files alphabetically or by custom order."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from dotenv_audit.parser import EnvEntry, ParsedEnvFile


@dataclass
class SortResult:
    path: str
    original_order: List[str]
    sorted_order: List[str]
    changed: bool

    def __str__(self) -> str:
        if not self.changed:
            return f"{self.path}: already sorted"
        moved = [
            k for i, (k, s) in enumerate(zip(self.original_order, self.sorted_order))
            if k != s
        ]
        return f"{self.path}: reordered {len(moved)} key(s)"


def _entry_sort_key(entry: EnvEntry, group_comments: bool) -> tuple:
    """Return a sort key for an entry, optionally grouping by inline comment prefix."""
    if group_comments and entry.comment:
        prefix = entry.comment.lstrip("# ").split()[0].lower() if entry.comment.strip() else ""
    else:
        prefix = ""
    return (prefix, entry.key.lower())


def sort_env_file(
    parsed: ParsedEnvFile,
    group_comments: bool = False,
    reverse: bool = False,
) -> SortResult:
    """Return a SortResult describing the reordering needed for *parsed*."""
    entries = parsed.entries
    original_order = [e.key for e in entries]
    sorted_entries = sorted(
        entries,
        key=lambda e: _entry_sort_key(e, group_comments),
        reverse=reverse,
    )
    sorted_order = [e.key for e in sorted_entries]
    changed = original_order != sorted_order
    return SortResult(
        path=parsed.path,
        original_order=original_order,
        sorted_order=sorted_order,
        changed=changed,
    )


def rewrite_sorted(parsed: ParsedEnvFile, result: SortResult) -> List[str]:
    """Return lines for *parsed* reordered according to *result*."""
    entry_map = {e.key: e for e in parsed.entries}
    lines: List[str] = []
    for key in result.sorted_order:
        entry = entry_map[key]
        if entry.comment:
            lines.append(f"# {entry.comment.lstrip('# ')}")
        lines.append(f"{entry.key}={entry.value}")
    return lines


def sort_many(
    files: List[ParsedEnvFile],
    group_comments: bool = False,
    reverse: bool = False,
) -> List[SortResult]:
    """Sort multiple env files and return a list of SortResults."""
    return [sort_env_file(f, group_comments=group_comments, reverse=reverse) for f in files]
