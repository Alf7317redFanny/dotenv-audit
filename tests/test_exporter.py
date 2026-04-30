"""Tests for dotenv_audit.exporter."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dotenv_audit.exporter import AuditExport, build_export, to_json, to_csv
from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.comparator import ComparisonResult


def _entry(key: str, value: str, reason: str | None = None) -> EnvEntry:
    return EnvEntry(key=key, value=value, flag_reason=reason)


def _parsed(path: str, entries) -> ParsedEnvFile:
    pf = MagicMock(spec=ParsedEnvFile)
    pf.path = Path(path)
    pf.flagged_entries.return_value = [e for e in entries if e.flag_reason]
    return pf


def _result(base: str, other: str, missing=(), extra=(), mismatch=()) -> ComparisonResult:
    return ComparisonResult(
        base_path=Path(base),
        other_path=Path(other),
        missing_keys=list(missing),
        extra_keys=list(extra),
        mismatched_keys=list(mismatch),
    )


def test_build_export_empty():
    export = build_export([], [])
    assert export.secrets == []
    assert export.comparisons == []


def test_build_export_secrets():
    entries = [
        _entry("API_KEY", "abc123", reason="hex token"),
        _entry("DEBUG", "true"),
    ]
    pf = _parsed(".env", entries)
    export = build_export([pf], [])
    assert len(export.secrets) == 1
    assert export.secrets[0]["key"] == "API_KEY"
    assert export.secrets[0]["reason"] == "hex token"
    assert export.secrets[0]["file"] == ".env"


def test_build_export_comparisons():
    cr = _result(".env", ".env.prod", missing=["DB_URL"], extra=["OLD_KEY"], mismatch=["PORT"])
    export = build_export([], [cr])
    issues = {r["issue"]: r["key"] for r in export.comparisons}
    assert issues["missing"] == "DB_URL"
    assert issues["extra"] == "OLD_KEY"
    assert issues["mismatch"] == "PORT"


def test_to_json_valid():
    export = AuditExport(secrets=[{"file": ".env", "key": "X", "reason": "y"}], comparisons=[])
    result = to_json(export)
    parsed = json.loads(result)
    assert parsed["secrets"][0]["key"] == "X"


def test_to_json_empty_export():
    """to_json should still produce valid JSON with both keys present when export is empty."""
    export = AuditExport(secrets=[], comparisons=[])
    result = to_json(export)
    parsed = json.loads(result)
    assert "secrets" in parsed
    assert "comparisons" in parsed
    assert parsed["secrets"] == []
    assert parsed["comparisons"] == []


def test_to_csv_headers():
    export = AuditExport(secrets=[], comparisons=[])
    csv_str = to_csv(export)
    assert "type" in csv_str
    assert "key" in csv_str


def test_to_csv_rows():
    export = AuditExport(
        secrets=[{"file": ".env", "key": "TOKEN", "reason": "hex"}],
        comparisons=[{"base": ".env", "other": ".env.prod", "issue": "missing", "key": "DB"}],
    )
    csv_str = to_csv(export)
    assert "secret" in csv_str
    assert "TOKEN" in csv_str
    assert "comparison" in csv_str
    assert "DB" in csv_str
