"""Tests for dotenv_audit.commands.watch_cmd."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dotenv_audit.commands.watch_cmd import cmd_watch, register, _on_change


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"directory": ".", "interval": 0.05, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _write_env(directory: Path, name: str = ".env", content: str = "KEY=val") -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# cmd_watch
# ---------------------------------------------------------------------------

def test_watch_cmd_returns_2_for_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir"
    args = _make_args(directory=str(missing))
    assert cmd_watch(args) == 2


def test_watch_cmd_stops_on_keyboard_interrupt(tmp_path: Path) -> None:
    args = _make_args(directory=str(tmp_path))
    with patch("dotenv_audit.commands.watch_cmd.watch", side_effect=KeyboardInterrupt):
        result = cmd_watch(args)
    assert result == 0


def test_watch_cmd_passes_interval_to_watcher(tmp_path: Path) -> None:
    args = _make_args(directory=str(tmp_path), interval=7.5)
    captured: dict = {}

    def _fake_watch(directory, callback, *, poll_interval):
        captured["interval"] = poll_interval
        raise KeyboardInterrupt

    with patch("dotenv_audit.commands.watch_cmd.watch", side_effect=_fake_watch):
        cmd_watch(args)

    assert captured["interval"] == pytest.approx(7.5)


# ---------------------------------------------------------------------------
# _on_change
# ---------------------------------------------------------------------------

def test_on_change_handles_deleted_file(tmp_path: Path, capsys) -> None:
    missing = tmp_path / ".env.gone"
    # File does not exist — should print deleted notice without crashing.
    _on_change([missing], color=False)
    out = capsys.readouterr().out
    assert "deleted" in out


def test_on_change_reports_secrets_for_existing_file(tmp_path: Path, capsys) -> None:
    env = _write_env(tmp_path, content="TOKEN=abc123def456abc123def456abc123de")
    _on_change([env], color=False)
    out = capsys.readouterr().out
    assert "TOKEN" in out or "token" in out.lower() or env.name in out


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

def test_register_adds_watch_subcommand() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    args = parser.parse_args(["watch", ".", "--interval", "3", "--no-color"])
    assert args.directory == "."
    assert args.interval == pytest.approx(3.0)
    assert args.no_color is True
