"""Tests for dotenv_audit.linter."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.linter import LintIssue, LintResult, lint_env_file


def _make_entry(key: str, value: str, line: int = 1) -> EnvEntry:
    return EnvEntry(key=key, value=value, line_number=line, raw=f"{key}={value}")


def _make_parsed(entries, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


def _issue_messages(result: LintResult) -> list[str]:
    """Return all issue messages from a LintResult for easy assertion."""
    return [i.message for i in result.issues]


# --- LintResult helpers ---

def test_lint_result_no_issues():
    r = LintResult(path=".env")
    assert not r.has_issues
    assert r.summary == ".env: OK"


def test_lint_result_summary_lists_issues():
    r = LintResult(path=".env", issues=[LintIssue(1, "foo", "bad")])
    assert r.has_issues
    assert "1 issue" in r.summary
    assert "bad" in r.summary


# --- lint_env_file: clean file ---

def test_lint_clean_file_no_issues():
    parsed = _make_parsed([
        _make_entry("DATABASE_URL", "postgres://localhost/db", 1),
        _make_entry("SECRET_KEY", "abc123", 2),
    ])
    result = lint_env_file(parsed)
    assert not result.has_issues


# --- lint_env_file: lowercase key ---

def test_lint_flags_lowercase_key():
    parsed = _make_parsed([_make_entry("database_url", "value", 1)])
    result = lint_env_file(parsed)
    assert result.has_issues
    assert any("UPPER_SNAKE_CASE" in m for m in _issue_messages(result))


def test_lint_flags_mixed_case_key():
    parsed = _make_parsed([_make_entry("MyKey", "value", 1)])
    result = lint_env_file(parsed)
    assert any("UPPER_SNAKE_CASE" in m for m in _issue_messages(result))


# --- lint_env_file: empty value ---

def test_lint_flags_empty_value():
    parsed = _make_parsed([_make_entry("SECRET_KEY", "", 1)])
    result = lint_env_file(parsed)
    assert any("empty" in m for m in _issue_messages(result))


# --- lint_env_file: space in key ---

def test_lint_flags_space_in_key():
    parsed = _make_parsed([_make_entry("MY KEY", "value", 1)])
    result = lint_env_file(parsed)
    assert any("spaces" in m for m in _issue_messages(result))


# --- lint_env_file: duplicate key ---

def test_lint_flags_duplicate_key():
    parsed = _make_parsed([
        _make_entry("API_KEY", "aaa", 1),
        _make_entry("API_KEY", "bbb", 3),
    ])
    result = lint_env_file(parsed)
    dup_issues = [i for i in result.issues if "duplicate" in i.message]
    assert len(dup_issues) == 1
    assert dup_issues[0].line_number == 3


# --- lint_env_file: multiple issues on one entry ---

def test_lint_multiple_issues_same_entry():
    # lowercase + empty
    parsed = _make_parsed([_make_entry("my_secret", "", 2)])
    result = lint_env_file(parsed)
    assert len(result.issues) >= 2
