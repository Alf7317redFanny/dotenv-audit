"""Baseline management: save and load a known-good snapshot of env key sets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

DEFAULT_BASELINE_FILE = ".env-audit-baseline.json"


def save_baseline(key_map: Dict[str, List[str]], path: str = DEFAULT_BASELINE_FILE) -> None:
    """Persist a mapping of {env_file_path: [keys]} to disk as JSON."""
    serialisable = {k: sorted(v) for k, v in key_map.items()}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(serialisable, fh, indent=2)
        fh.write("\n")


def load_baseline(path: str = DEFAULT_BASELINE_FILE) -> Dict[str, List[str]]:
    """Load a previously saved baseline from disk.

    Returns an empty dict if the file does not exist.
    """
    baseline_path = Path(path)
    if not baseline_path.exists():
        return {}
    with open(baseline_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {k: list(v) for k, v in data.items()}


def diff_against_baseline(
    current: Dict[str, List[str]],
    baseline: Dict[str, List[str]],
) -> Dict[str, Dict[str, List[str]]]:
    """Compare current key map against baseline.

    Returns a dict keyed by file path with sub-keys:
      'added'   – keys present now but not in baseline
      'removed' – keys in baseline but no longer present
      'new_file'– file not tracked in baseline at all
    """
    result: Dict[str, Dict[str, List[str]]] = {}

    for file_path, keys in current.items():
        current_set = set(keys)
        if file_path not in baseline:
            result[file_path] = {"new_file": list(sorted(current_set)), "added": [], "removed": []}
            continue
        baseline_set = set(baseline[file_path])
        added = sorted(current_set - baseline_set)
        removed = sorted(baseline_set - current_set)
        if added or removed:
            result[file_path] = {"new_file": [], "added": added, "removed": removed}

    return result
