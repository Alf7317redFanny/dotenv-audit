"""Tests for dotenv_audit.renamer."""

from pathlib import Path

import pytest

from dotenv_audit.renamer import (
    RenameReport,
    RenameResult,
    _rewrite_lines,
    rename_key_in_directory,
    rename_key_in_file,
)


# ---------------------------------------------------------------------------
# _rewrite_lines
# ---------------------------------------------------------------------------

def test_rewrite_lines_replaces_exact_key():
    lines = ["OLD_KEY=secret\n", "OTHER=value\n"]
    new_lines, renamed = _rewrite_lines(lines, "OLD_KEY", "NEW_KEY")
    assert renamed is True
    assert new_lines[0] == "NEW_KEY=secret\n"
    assert new_lines[1] == "OTHER=value\n"


def test_rewrite_lines_key_not_present():
    lines = ["UNRELATED=foo\n"]
    new_lines, renamed = _rewrite_lines(lines, "MISSING_KEY", "NEW_KEY")
    assert renamed is False
    assert new_lines == lines


def test_rewrite_lines_handles_spaces_around_equals():
    lines = ["OLD_KEY = value\n"]
    new_lines, renamed = _rewrite_lines(lines, "OLD_KEY", "NEW_KEY")
    assert renamed is True
    assert "NEW_KEY" in new_lines[0]


def test_rewrite_lines_does_not_replace_partial_match():
    lines = ["OLD_KEY_EXTRA=value\n"]
    new_lines, renamed = _rewrite_lines(lines, "OLD_KEY", "NEW_KEY")
    assert renamed is False


# ---------------------------------------------------------------------------
# rename_key_in_file
# ---------------------------------------------------------------------------

def test_rename_key_in_file_writes_change(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=abc123\nDEBUG=true\n")
    result = rename_key_in_file(env_file, "SECRET_KEY", "APP_SECRET")
    assert result.renamed is True
    assert "APP_SECRET=abc123" in env_file.read_text()


def test_rename_key_in_file_dry_run_does_not_write(tmp_path):
    env_file = tmp_path / ".env"
    original = "SECRET_KEY=abc123\n"
    env_file.write_text(original)
    result = rename_key_in_file(env_file, "SECRET_KEY", "APP_SECRET", dry_run=True)
    assert result.renamed is True
    assert env_file.read_text() == original  # unchanged on disk


def test_rename_key_in_file_missing_key(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER=value\n")
    result = rename_key_in_file(env_file, "GHOST_KEY", "NEW_KEY")
    assert result.renamed is False


# ---------------------------------------------------------------------------
# RenameResult / RenameReport helpers
# ---------------------------------------------------------------------------

def test_rename_result_str_renamed(tmp_path):
    r = RenameResult(path=tmp_path / ".env", old_key="A", new_key="B", renamed=True)
    assert "renamed" in str(r)


def test_rename_result_str_not_found(tmp_path):
    r = RenameResult(path=tmp_path / ".env", old_key="A", new_key="B", renamed=False)
    assert "not found" in str(r)


def test_rename_report_has_changes_false_when_empty():
    report = RenameReport()
    assert report.has_changes is False


def test_rename_report_summary(tmp_path):
    results = [
        RenameResult(tmp_path / ".env", "A", "B", renamed=True),
        RenameResult(tmp_path / ".env.local", "A", "B", renamed=False),
    ]
    report = RenameReport(results=results)
    assert report.has_changes is True
    assert "1/2" in report.summary


# ---------------------------------------------------------------------------
# rename_key_in_directory
# ---------------------------------------------------------------------------

def test_rename_key_in_directory_renames_across_files(tmp_path):
    (tmp_path / ".env").write_text("OLD=1\n")
    (tmp_path / ".env.production").write_text("OLD=2\n")
    report = rename_key_in_directory(tmp_path, "OLD", "NEW")
    assert report.has_changes is True
    assert all(r.renamed for r in report.results)


def test_rename_key_in_directory_empty_dir(tmp_path):
    report = rename_key_in_directory(tmp_path, "OLD", "NEW")
    assert report.has_changes is False
    assert report.results == []
