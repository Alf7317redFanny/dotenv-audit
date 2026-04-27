"""Tests for dotenv_audit.reporter module."""

import pytest

from dotenv_audit.reporter import report_secrets, report_comparison, full_report
from dotenv_audit.comparator import ComparisonResult
from dotenv_audit.parser import ParsedEnvFile, EnvEntry


def _entry(key, value, line=1, reason=None):
    e = EnvEntry(key=key, value=value, line_number=line, raw_line=f"{key}={value}")
    e.secret_reason = reason
    return e


def _parsed(path, entries):
    return ParsedEnvFile(path=path, entries=entries)


def test_report_secrets_no_flags(monkeypatch):
    monkeypatch.setattr(
        "dotenv_audit.parser.ParsedEnvFile.flagged_entries", lambda self: []
    )
    pf = _parsed(".env", [])
    out = report_secrets(pf, use_color=False)
    assert "No exposed secrets" in out
    assert ".env" in out


def test_report_secrets_with_flags(monkeypatch):
    entry = _entry("API_KEY", "ghp_abc123", line=3, reason="GitHub PAT pattern")
    monkeypatch.setattr(
        "dotenv_audit.parser.ParsedEnvFile.flagged_entries", lambda self: [entry]
    )
    pf = _parsed(".env", [entry])
    out = report_secrets(pf, use_color=False)
    assert "API_KEY" in out
    assert "LINE 3" in out
    assert "GitHub PAT pattern" in out


def test_report_comparison_no_issues():
    result = ComparisonResult(
        reference_path=".env",
        compared_path=".env.prod",
    )
    out = report_comparison(result, use_color=False)
    assert "Keys match" in out


def test_report_comparison_with_missing_and_extra():
    result = ComparisonResult(
        reference_path=".env",
        compared_path=".env.staging",
        missing_in_compared=["SECRET_KEY"],
        extra_in_compared=["STAGING_ONLY"],
    )
    out = report_comparison(result, use_color=False)
    assert "MISSING" in out
    assert "SECRET_KEY" in out
    assert "EXTRA" in out
    assert "STAGING_ONLY" in out


def test_full_report_sections(monkeypatch):
    monkeypatch.setattr(
        "dotenv_audit.parser.ParsedEnvFile.flagged_entries", lambda self: []
    )
    pf = _parsed(".env", [])
    cmp = ComparisonResult(".env", ".env.prod", missing_in_compared=["DB_URL"])
    out = full_report([pf], [cmp], use_color=False)
    assert "Secret Scan" in out
    assert "Key Comparison" in out
    assert "DB_URL" in out


def test_full_report_no_comparisons(monkeypatch):
    monkeypatch.setattr(
        "dotenv_audit.parser.ParsedEnvFile.flagged_entries", lambda self: []
    )
    pf = _parsed(".env", [])
    out = full_report([pf], [], use_color=False)
    assert "Key Comparison" not in out
    assert "Secret Scan" in out
