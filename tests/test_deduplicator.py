"""Tests for dotenv_audit.deduplicator."""
from __future__ import annotations

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.deduplicator import (
    DuplicateReport,
    find_intra_duplicates,
    detect_duplicates,
)


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, raw_line=f"{key}={value}")


def _parsed(path: str, keys: list[str]) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=[_entry(k) for k in keys])


# ---------------------------------------------------------------------------
# DuplicateReport.has_issues / summary
# ---------------------------------------------------------------------------

def test_duplicate_report_no_issues_when_empty():
    report = DuplicateReport()
    assert not report.has_issues


def test_duplicate_report_has_issues_intra():
    report = DuplicateReport(intra_file={".env": ["SECRET"]})
    assert report.has_issues


def test_duplicate_report_has_issues_cross():
    report = DuplicateReport(cross_file={"API_KEY": [".env", ".env.staging"]})
    assert report.has_issues


def test_duplicate_report_summary_no_issues():
    assert DuplicateReport().summary() == "No duplicate keys found."


def test_duplicate_report_summary_intra():
    report = DuplicateReport(intra_file={".env": ["FOO"]})
    assert "[intra]" in report.summary()
    assert "FOO" in report.summary()
    assert ".env" in report.summary()


def test_duplicate_report_summary_cross():
    report = DuplicateReport(cross_file={"DB_URL": [".env", ".env.prod"]})
    text = report.summary()
    assert "[cross]" in text
    assert "DB_URL" in text


# ---------------------------------------------------------------------------
# find_intra_duplicates
# ---------------------------------------------------------------------------

def test_find_intra_no_duplicates():
    pf = _parsed(".env", ["A", "B", "C"])
    assert find_intra_duplicates(pf) == []


def test_find_intra_detects_duplicate():
    pf = ParsedEnvFile(
        path=".env",
        entries=[_entry("KEY"), _entry("OTHER"), _entry("KEY")],
    )
    result = find_intra_duplicates(pf)
    assert "KEY" in result
    assert "OTHER" not in result


def test_find_intra_multiple_duplicates():
    pf = ParsedEnvFile(
        path=".env",
        entries=[_entry("A"), _entry("B"), _entry("A"), _entry("B")],
    )
    result = find_intra_duplicates(pf)
    assert set(result) == {"A", "B"}


# ---------------------------------------------------------------------------
# detect_duplicates
# ---------------------------------------------------------------------------

def test_detect_duplicates_empty_list():
    report = detect_duplicates([])
    assert not report.has_issues


def test_detect_duplicates_no_issues():
    files = [_parsed(".env", ["A", "B"]), _parsed(".env.staging", ["C", "D"])]
    report = detect_duplicates(files)
    assert not report.has_issues


def test_detect_duplicates_cross_file():
    files = [_parsed(".env", ["API_KEY", "SECRET"]), _parsed(".env.prod", ["API_KEY", "DB"])]
    report = detect_duplicates(files)
    assert "API_KEY" in report.cross_file
    assert set(report.cross_file["API_KEY"]) == {".env", ".env.prod"}


def test_detect_duplicates_intra_and_cross():
    pf1 = ParsedEnvFile(
        path=".env",
        entries=[_entry("DUP"), _entry("DUP"), _entry("SHARED")],
    )
    pf2 = _parsed(".env.test", ["SHARED", "UNIQUE"])
    report = detect_duplicates([pf1, pf2])
    assert ".env" in report.intra_file
    assert "DUP" in report.intra_file[".env"]
    assert "SHARED" in report.cross_file
