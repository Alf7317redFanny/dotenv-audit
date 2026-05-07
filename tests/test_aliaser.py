"""Tests for dotenv_audit.aliaser."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.aliaser import AliasGroup, AliasReport, detect_aliases


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", lineno=1)


def _parsed(path: str, entries: list) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# AliasReport
# ---------------------------------------------------------------------------

def test_alias_report_no_aliases_when_empty():
    report = AliasReport()
    assert not report.has_aliases


def test_alias_report_has_aliases_when_groups_present():
    group = AliasGroup(value="secret", keys=[("a.env", "KEY_A"), ("b.env", "KEY_B")])
    report = AliasReport(groups=[group])
    assert report.has_aliases


def test_alias_report_summary_no_aliases():
    assert AliasReport().summary == "No aliases detected."


def test_alias_report_summary_lists_groups():
    group = AliasGroup(value="abc123", keys=[("dev.env", "TOKEN"), ("prod.env", "SECRET")])
    report = AliasReport(groups=[group])
    summary = report.summary
    assert "1 alias group" in summary
    assert "abc123" in summary
    assert "TOKEN" in summary
    assert "SECRET" in summary


# ---------------------------------------------------------------------------
# detect_aliases
# ---------------------------------------------------------------------------

def test_detect_aliases_empty_list():
    report = detect_aliases([])
    assert not report.has_aliases


def test_detect_aliases_no_shared_values():
    pf = _parsed("a.env", [_entry("A", "val1"), _entry("B", "val2")])
    report = detect_aliases([pf])
    assert not report.has_aliases


def test_detect_aliases_skips_empty_values():
    pf = _parsed("a.env", [_entry("A", ""), _entry("B", "")])
    report = detect_aliases([pf])
    assert not report.has_aliases


def test_detect_aliases_intra_file_alias():
    pf = _parsed("a.env", [_entry("DB_PASS", "hunter2"), _entry("REDIS_PASS", "hunter2")])
    report = detect_aliases([pf])
    assert report.has_aliases
    assert len(report.groups) == 1
    assert report.groups[0].value == "hunter2"
    keys = [k for _, k in report.groups[0].keys]
    assert "DB_PASS" in keys
    assert "REDIS_PASS" in keys


def test_detect_aliases_cross_file_alias():
    pf1 = _parsed(".env", [_entry("API_KEY", "tok_abc")])
    pf2 = _parsed(".env.prod", [_entry("SERVICE_KEY", "tok_abc")])
    report = detect_aliases([pf1, pf2])
    assert report.has_aliases
    sources = [src for src, _ in report.groups[0].keys]
    assert ".env" in sources
    assert ".env.prod" in sources


def test_detect_aliases_groups_sorted_by_value():
    pf = _parsed(
        "a.env",
        [
            _entry("Z", "zzz"),
            _entry("Z2", "zzz"),
            _entry("A", "aaa"),
            _entry("A2", "aaa"),
        ],
    )
    report = detect_aliases([pf])
    assert report.groups[0].value == "aaa"
    assert report.groups[1].value == "zzz"


def test_detect_aliases_unique_values_not_grouped():
    pf1 = _parsed(".env", [_entry("X", "unique1")])
    pf2 = _parsed(".env.local", [_entry("Y", "unique2")])
    report = detect_aliases([pf1, pf2])
    assert not report.has_aliases
