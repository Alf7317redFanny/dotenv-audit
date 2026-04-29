"""Tests for dotenv_audit.watcher."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from dotenv_audit.watcher import WatchState, watch


# ---------------------------------------------------------------------------
# WatchState unit tests
# ---------------------------------------------------------------------------

def test_watch_state_new_file_has_changed(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=value")
    state = WatchState()
    assert state.has_changed(env)  # not yet tracked → counts as changed


def test_watch_state_unchanged_after_update(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=value")
    state = WatchState()
    state.update(env)
    assert not state.has_changed(env)


def test_watch_state_detects_modification(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=value")
    state = WatchState()
    state.update(env)
    # Simulate a later modification by bumping mtime manually.
    new_mtime = env.stat().st_mtime + 5
    import os
    os.utime(env, (new_mtime, new_mtime))
    assert state.has_changed(env)


def test_watch_state_deleted_file_has_changed(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=value")
    state = WatchState()
    state.update(env)
    env.unlink()
    assert state.has_changed(env)


def test_watch_state_remove_clears_entry(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=value")
    state = WatchState()
    state.update(env)
    state.remove(env)
    assert str(env) not in state.snapshots


# ---------------------------------------------------------------------------
# watch() integration tests (using max_iterations to avoid infinite loop)
# ---------------------------------------------------------------------------

def test_watch_calls_callback_on_new_file(tmp_path: Path) -> None:
    """A file created after the watcher starts should trigger the callback."""
    received: list[list[Path]] = []

    def _cb(changed: list[Path]) -> None:
        received.append(changed)

    import threading

    def _create_file() -> None:
        time.sleep(0.05)
        (tmp_path / ".env.new").write_text("SECRET=abc")

    t = threading.Thread(target=_create_file, daemon=True)
    t.start()

    watch(tmp_path, _cb, poll_interval=0.1, max_iterations=3)
    t.join()

    all_changed = [p for batch in received for p in batch]
    assert any(".env.new" in str(p) for p in all_changed)


def test_watch_no_callback_when_nothing_changes(tmp_path: Path) -> None:
    """Callback must NOT fire if no files change."""
    (tmp_path / ".env").write_text("KEY=val")
    received: list[list[Path]] = []
    watch(tmp_path, received.append, poll_interval=0.05, max_iterations=3)
    assert received == []
