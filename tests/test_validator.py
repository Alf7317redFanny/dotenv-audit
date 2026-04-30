"""Tests for dotenv_audit.validator."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.validator import (
    ValidationIssue,
    ValidationResult,
    _check_type,
    validate_env_file,
)


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, raw_value=value, value=value, line_number=1)


def _parsed(*entries: EnvEntry, path: str = ".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=list(entries))


# --- ValidationIssue ---

def test_validation_issue_str():
    issue = ValidationIssue(key="PORT", message="expected int, got 'abc'")
    assert str(issue) == "PORT: expected int, got 'abc'"


# --- ValidationResult ---

def test_validation_result_no_issues():
    result = ValidationResult(path=".env")
    assert not result.has_issues
    assert result.summary == ".env: OK"


def test_validation_result_summary_lists_issues():
    result = ValidationResult(
        path=".env",
        issues=[ValidationIssue("PORT", "expected int, got 'abc'")],
    )
    assert result.has_issues
    assert "1 validation issue" in result.summary
    assert "PORT" in result.summary


# --- _check_type ---

def test_check_type_int_valid():
    assert _check_type("PORT", "8080", "int") is None


def test_check_type_int_invalid():
    issue = _check_type("PORT", "abc", "int")
    assert issue is not None
    assert "int" in issue.message


def test_check_type_bool_valid():
    for val in ("true", "false", "1", "0", "yes", "no"):
        assert _check_type("FLAG", val, "bool") is None


def test_check_type_bool_invalid():
    issue = _check_type("FLAG", "maybe", "bool")
    assert issue is not None


def test_check_type_url_valid():
    assert _check_type("API", "https://example.com", "url") is None


def test_check_type_url_invalid():
    issue = _check_type("API", "ftp://example.com", "url")
    assert issue is not None


def test_check_type_email_valid():
    assert _check_type("ADMIN", "admin@example.com", "email") is None


def test_check_type_email_invalid():
    issue = _check_type("ADMIN", "not-an-email", "email")
    assert issue is not None


def test_check_type_str_always_passes():
    assert _check_type("NAME", "anything goes", "str") is None


# --- validate_env_file ---

def test_validate_clean_file():
    parsed = _parsed(_entry("PORT", "8080"), _entry("DEBUG", "true"))
    schema = {"PORT": "int", "DEBUG": "bool"}
    result = validate_env_file(parsed, schema)
    assert not result.has_issues


def test_validate_missing_required_key():
    parsed = _parsed(_entry("PORT", "8080"))
    schema = {"PORT": "int", "SECRET": "str"}
    result = validate_env_file(parsed, schema, require_all=True)
    keys = [i.key for i in result.issues]
    assert "SECRET" in keys


def test_validate_require_all_false_skips_missing():
    parsed = _parsed(_entry("PORT", "8080"))
    schema = {"PORT": "int", "SECRET": "str"}
    result = validate_env_file(parsed, schema, require_all=False)
    assert not result.has_issues


def test_validate_unknown_schema_type():
    parsed = _parsed(_entry("FOO", "bar"))
    result = validate_env_file(parsed, {"FOO": "uuid"}, require_all=False)
    assert result.has_issues
    assert "unknown schema type" in result.issues[0].message


def test_validate_wrong_type_flagged():
    parsed = _parsed(_entry("PORT", "not-a-number"))
    result = validate_env_file(parsed, {"PORT": "int"}, require_all=False)
    assert result.has_issues
