"""Drift detection: compare current env files against a saved baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotenv_audit.baseline import load_baseline
from dotenv_audit.parser import ParsedEnvFile, parse_env_file
from dotenv_audit.scanner import scan_directory


@dataclass
class DriftReport:
    """Holds the drift results for a single env file vs the baseline."""

    env_path: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return ", ".join(parts) if parts else "no drift"


def detect_drift(directory: str, baseline_path: str) -> List[DriftReport]:
    """Scan *directory* and compare every env file against *baseline_path*."""
    baseline: Dict[str, Dict[str, str]] = load_baseline(baseline_path)
    env_files = scan_directory(directory)
    reports: List[DriftReport] = []

    for env_path in env_files:
        parsed: ParsedEnvFile = parse_env_file(env_path)
        rel = str(Path(env_path).resolve().relative_to(Path(directory).resolve()))
        saved = baseline.get(rel, {})

        current_keys = set(parsed.keys())
        saved_keys = set(saved.keys())

        added = sorted(current_keys - saved_keys)
        removed = sorted(saved_keys - current_keys)
        changed = sorted(
            k for k in current_keys & saved_keys
            if parsed._entries_by_key().get(k, "") != saved[k]
        )

        reports.append(DriftReport(
            env_path=rel,
            added=added,
            removed=removed,
            changed=changed,
        ))

    return reports
