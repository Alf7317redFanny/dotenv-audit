"""Detect and resolve variable interpolation references in .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

_REF_START = "${"
_REF_END = "}"


def _extract_refs(value: str) -> List[str]:
    """Return all variable names referenced via ${VAR} syntax."""
    refs: List[str] = []
    rest = value
    while _REF_START in rest:
        start = rest.index(_REF_START) + len(_REF_START)
        if _REF_END not in rest[start:]:
            break
        end = rest.index(_REF_END, start)
        refs.append(rest[start:end])
        rest = rest[end + 1 :]
    return refs


@dataclass
class InterpolationIssue:
    key: str
    ref: str
    kind: str  # "undefined" | "circular"

    def __str__(self) -> str:
        return f"{self.key} -> ${{{self.ref}}}: {self.kind} reference"


@dataclass
class InterpolationResult:
    file_path: str
    issues: List[InterpolationIssue] = field(default_factory=list)
    resolved: Dict[str, str] = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        if not self.has_issues:
            return f"{self.file_path}: no interpolation issues"
        lines = [f"{self.file_path}: {len(self.issues)} interpolation issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def _resolve(
    key: str,
    values: Dict[str, str],
    visited: Optional[List[str]] = None,
) -> Optional[str]:
    """Recursively resolve a key, returning None if circular or undefined."""
    if visited is None:
        visited = []
    if key not in values:
        return None
    if key in visited:
        return None  # circular
    raw = values[key]
    refs = _extract_refs(raw)
    result = raw
    for ref in refs:
        resolved = _resolve(ref, values, visited + [key])
        if resolved is None:
            return None
        result = result.replace(f"${{{ref}}}", resolved)
    return result


def interpolate_env_file(parsed: ParsedEnvFile) -> InterpolationResult:
    """Analyse a parsed .env file for interpolation issues."""
    raw: Dict[str, str] = {e.key: e.value for e in parsed.entries if e.value is not None}
    issues: List[InterpolationIssue] = []
    resolved: Dict[str, str] = {}

    for entry in parsed.entries:
        if entry.value is None:
            continue
        refs = _extract_refs(entry.value)
        for ref in refs:
            if ref not in raw:
                issues.append(InterpolationIssue(entry.key, ref, "undefined"))
            else:
                val = _resolve(ref, raw, [entry.key])
                if val is None:
                    issues.append(InterpolationIssue(entry.key, ref, "circular"))
        r = _resolve(entry.key, raw)
        if r is not None:
            resolved[entry.key] = r

    return InterpolationResult(file_path=parsed.path, issues=issues, resolved=resolved)
