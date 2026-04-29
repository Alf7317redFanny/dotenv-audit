"""Tests for dotenv_audit.summarizer."""

from pathlib import Path

import pytest

from dotenv_audit.summarizer import build_summary, AuditSummary


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_build_summary_empty_directory(tmp_path):
    result = build_summary(tmp_path)
    assert isinstance(result, AuditSummary)
    assert result.total_files == 0
    assert result.total_secrets == 0
    assert result.total_lint_issues == 0
    assert result.comparison is None
    assert not result.has_issues


def test_build_summary_single_clean_file(tmp_path):
    _write(tmp_path, ".env", "APP_NAME=myapp\nDEBUG=false\n")
    result = build_summary(tmp_path)
    assert result.total_files == 1
    assert result.total_secrets == 0
    assert result.comparison is None  # need >= 2 files
    assert not result.has_issues


def test_build_summary_detects_secret(tmp_path):
    _write(tmp_path, ".env", "SECRET_KEY=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4\n")
    result = build_summary(tmp_path)
    assert result.total_secrets >= 1
    assert result.has_issues


def test_build_summary_two_files_creates_comparison(tmp_path):
    _write(tmp_path, ".env", "APP=x\nDB_URL=postgres://localhost/dev\n")
    _write(tmp_path, ".env.production", "APP=x\nDB_URL=postgres://prod/db\n")
    result = build_summary(tmp_path)
    assert result.total_files == 2
    assert result.comparison is not None


def test_build_summary_missing_key_has_issues(tmp_path):
    _write(tmp_path, ".env", "APP=x\nEXTRA=only_in_dev\n")
    _write(tmp_path, ".env.production", "APP=x\n")
    result = build_summary(tmp_path)
    assert result.has_issues


def test_summary_string_contains_directory(tmp_path):
    result = build_summary(tmp_path)
    text = result.summary()
    assert str(tmp_path) in text


def test_summary_string_ok_when_no_issues(tmp_path):
    _write(tmp_path, ".env", "PORT=8080\n")
    result = build_summary(tmp_path)
    assert "OK" in result.summary()


def test_summary_string_issues_found_when_secret(tmp_path):
    _write(tmp_path, ".env", "TOKEN=ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456\n")
    result = build_summary(tmp_path)
    assert "ISSUES FOUND" in result.summary()
