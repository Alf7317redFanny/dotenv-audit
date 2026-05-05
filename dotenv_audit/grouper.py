"""Group parsed env files by environment label inferred from filename."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from dotenv_audit.parser import ParsedEnvFile

# Patterns that map filenames to environment labels.
# Checked in order; first match wins.
_LABEL_PATTERNS: List[tuple[str, str]] = [
    (r"\.env\.prod(uction)?$", "production"),
    (r"\.env\.stag(ing)?$", "staging"),
    (r"\.env\.test(ing)?$", "test"),
    (r"\.env\.dev(elopment)?$", "development"),
    (r"\.env\.local$", "local"),
    (r"\.env\.example$", "example"),
    (r"(\.env|env\.txt)$", "default"),
]


def infer_label(path: str) -> str:
    """Return an environment label inferred from *path*'s filename."""
    name = path.replace("\\", "/").rsplit("/", 1)[-1]
    for pattern, label in _LABEL_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return label
    return "unknown"


@dataclass
class EnvGroup:
    """A collection of parsed env files sharing the same environment label."""

    label: str
    files: List[ParsedEnvFile] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------

    def all_keys(self) -> List[str]:
        """Sorted union of all keys across every file in the group."""
        seen: set[str] = set()
        for pf in self.files:
            seen.update(pf.keys())
        return sorted(seen)

    def files_missing_key(self, key: str) -> List[str]:
        """Return paths of files in this group that do not define *key*."""
        return [pf.path for pf in self.files if key not in pf.keys()]

    def __len__(self) -> int:  # pragma: no cover
        return len(self.files)


def group_env_files(parsed_files: List[ParsedEnvFile]) -> Dict[str, EnvGroup]:
    """Partition *parsed_files* into :class:`EnvGroup` objects by label.

    Returns a dict keyed by label, ordered by first occurrence.
    """
    groups: Dict[str, EnvGroup] = {}
    for pf in parsed_files:
        label = infer_label(pf.path)
        if label not in groups:
            groups[label] = EnvGroup(label=label)
        groups[label].files.append(pf)
    return groups
