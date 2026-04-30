"""Detect duplicate keys within a single .env file or across multiple files."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class DuplicateReport:
    """Result of a duplicate-key scan."""

    # file path -> list of keys that appear more than once in that file
    intra_file: Dict[str, List[str]] = field(default_factory=dict)
    # key -> list of file paths that define it (only keys in 2+ files)
    cross_file: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        return bool(self.intra_file) or bool(self.cross_file)

    def summary(self) -> str:
        if not self.has_issues:
            return "No duplicate keys found."
        lines: List[str] = []
        for path, keys in sorted(self.intra_file.items()):
            for k in sorted(keys):
                lines.append(f"  [intra]  {path}: '{k}' defined multiple times")
        for key, paths in sorted(self.cross_file.items()):
            joined = ", ".join(sorted(paths))
            lines.append(f"  [cross]  '{key}' found in: {joined}")
        return "\n".join(lines)


def find_intra_duplicates(parsed: ParsedEnvFile) -> List[str]:
    """Return keys that appear more than once inside a single ParsedEnvFile."""
    seen: Dict[str, int] = defaultdict(int)
    for entry in parsed.entries:
        seen[entry.key] += 1
    return [k for k, count in seen.items() if count > 1]


def detect_duplicates(files: List[ParsedEnvFile]) -> DuplicateReport:
    """Scan a list of parsed env files for intra- and cross-file duplicates."""
    intra: Dict[str, List[str]] = {}
    for pf in files:
        dupes = find_intra_duplicates(pf)
        if dupes:
            intra[pf.path] = dupes

    key_to_files: Dict[str, List[str]] = defaultdict(list)
    for pf in files:
        for key in {e.key for e in pf.entries}:
            key_to_files[key].append(pf.path)

    cross = {k: paths for k, paths in key_to_files.items() if len(paths) > 1}

    return DuplicateReport(intra_file=intra, cross_file=cross)
