"""File-system watcher that re-runs an audit whenever .env files change."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional


@dataclass
class WatchState:
    """Tracks the last-modified timestamps of watched files."""

    snapshots: Dict[str, float] = field(default_factory=dict)

    def update(self, path: Path) -> None:
        self.snapshots[str(path)] = path.stat().st_mtime

    def has_changed(self, path: Path) -> bool:
        key = str(path)
        try:
            current_mtime = path.stat().st_mtime
        except FileNotFoundError:
            return key in self.snapshots  # file was deleted
        return self.snapshots.get(key) != current_mtime

    def remove(self, path: Path) -> None:
        self.snapshots.pop(str(path), None)


def _collect_env_files(directory: Path) -> list[Path]:
    """Return all .env* files under *directory* (mirrors scanner logic)."""
    from dotenv_audit.scanner import scan_directory

    return scan_directory(directory)


def watch(
    directory: Path,
    callback: Callable[[list[Path]], None],
    *,
    poll_interval: float = 2.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *directory* every *poll_interval* seconds.

    Calls *callback* with the list of changed/new/deleted paths whenever a
    change is detected.  Pass *max_iterations* to stop after N polls (useful
    for testing).
    """
    state = WatchState()
    iterations = 0

    # Seed initial state without triggering the callback.
    for p in _collect_env_files(directory):
        state.update(p)

    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break

        time.sleep(poll_interval)
        iterations += 1

        current_files = set(_collect_env_files(directory))
        known_files = {Path(k) for k in state.snapshots}

        changed: list[Path] = []

        for p in current_files:
            if state.has_changed(p):
                changed.append(p)
                state.update(p)

        deleted = known_files - current_files
        for p in deleted:
            changed.append(p)
            state.remove(p)

        if changed:
            callback(changed)
