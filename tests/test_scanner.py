"""Tests for the dotenv_audit.scanner module."""

import pytest
from pathlib import Path

from dotenv_audit.scanner import is_env_file, scan_directory


# ---------------------------------------------------------------------------
# is_env_file
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    ".env",
    ".env.local",
    ".env.production",
    ".env.example",
    ".env.sample",
    ".env.test",
    ".env.2024",
    ".env.bak",
])
def test_is_env_file_matches_env_patterns(name):
    assert is_env_file(name) is True


@pytest.mark.parametrize("name", [
    "config.py",
    "settings.json",
    "environment.txt",
    ".envrc",          # direnv file — not a dotenv file
    "myapp.env",       # doesn't start with '.env'
])
def test_is_env_file_rejects_non_env_files(name):
    assert is_env_file(name) is False


# ---------------------------------------------------------------------------
# scan_directory
# ---------------------------------------------------------------------------

def test_scan_directory_finds_env_files(tmp_path):
    (tmp_path / ".env").write_text("SECRET=abc")
    (tmp_path / ".env.local").write_text("SECRET=local")
    (tmp_path / "app.py").write_text("print('hello')")

    found = list(scan_directory(tmp_path))
    names = {f.name for f in found}

    assert ".env" in names
    assert ".env.local" in names
    assert "app.py" not in names


def test_scan_directory_recurses_into_subdirs(tmp_path):
    subdir = tmp_path / "backend"
    subdir.mkdir()
    (subdir / ".env.production").write_text("DB=prod")

    found = list(scan_directory(tmp_path))
    assert any(f.name == ".env.production" for f in found)


def test_scan_directory_ignores_node_modules(tmp_path):
    nm = tmp_path / "node_modules" / "some-pkg"
    nm.mkdir(parents=True)
    (nm / ".env").write_text("IGNORED=true")

    found = list(scan_directory(tmp_path))
    assert not any("node_modules" in str(f) for f in found)


def test_scan_directory_raises_for_missing_path(tmp_path):
    with pytest.raises(NotADirectoryError):
        list(scan_directory(tmp_path / "nonexistent"))


def test_scan_directory_returns_absolute_paths(tmp_path):
    (tmp_path / ".env").write_text("X=1")
    found = list(scan_directory(tmp_path))
    assert all(f.is_absolute() for f in found)
