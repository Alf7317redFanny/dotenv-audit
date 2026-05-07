"""Detect and report key aliases across env files.

An alias is when two different keys in the same (or different) env files
share an identical non-empty value, suggesting one may be a duplicate
or legacy rename of the other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class AliasGroup:
    """A set of keys that share the same value."""

    value: str
    keys: List[Tuple[str, str]]  # (source_path, key_name)

    def __str__(self) -> str:  # pragma: no cover
        pairs = ", ".join(f"{src}:{k}" for src, k in self.keys)
        return f"[alias value={self.value!r}] {pairs}"


@dataclass
class AliasReport:
    groups: List[AliasGroup] = field(default_factory=list)

    @property
    def has_aliases(self) -> bool:
        return len(self.groups) > 0

    @property
    def summary(self) -> str:
        if not self.has_aliases:
            return "No aliases detected."
        lines = [f"{len(self.groups)} alias group(s) found:"]
        for g in self.groups:
            key_list = ", ".join(f"{src}:{k}" for src, k in g.keys)
            lines.append(f"  value={g.value!r} -> {key_list}")
        return "\n".join(lines)


def detect_aliases(parsed_files: List[ParsedEnvFile]) -> AliasReport:
    """Find keys across *parsed_files* that share identical non-empty values."""
    # Map value -> list of (source, key)
    value_map: Dict[str, List[Tuple[str, str]]] = {}

    for pf in parsed_files:
        for entry in pf.entries:
            v = entry.value.strip()
            if not v:
                continue
            value_map.setdefault(v, []).append((pf.path, entry.key))

    groups = [
        AliasGroup(value=v, keys=owners)
        for v, owners in value_map.items()
        if len(owners) > 1
    ]
    # Sort for deterministic output
    groups.sort(key=lambda g: g.value)
    return AliasReport(groups=groups)
