"""Tests for dotenv_audit.annotator."""
import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.annotator import (
    AnnotatedEntry,
    AnnotatedEnvFile,
    annotate_env_file,
)


def _entry(key: str, value: str, comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _parsed(entries, path=".env") -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


# --- AnnotatedEntry ---

def test_annotated_entry_no_notes_renders_plain():
    e = _entry("PORT", "8080")
    ae = AnnotatedEntry(entry=e, notes=[])
    assert str(ae) == "PORT=8080"


def test_annotated_entry_single_note_renders_comment():
    e = _entry("SECRET", "abc123")
    ae = AnnotatedEntry(entry=e, notes=["possible secret (hex token)"])
    assert "# AUDIT:" in str(ae)
    assert "possible secret" in str(ae)


def test_annotated_entry_multiple_notes_joined():
    e = _entry("KEY", "val")
    ae = AnnotatedEntry(entry=e, notes=["note one", "note two"])
    result = str(ae)
    assert "note one" in result
    assert "note two" in result
    assert "; " in result


# --- AnnotatedEnvFile ---

def test_annotated_env_file_lines_returns_all_entries():
    entries = [
        AnnotatedEntry(entry=_entry("A", "1"), notes=[]),
        AnnotatedEntry(entry=_entry("B", "2"), notes=["flag"]),
    ]
    aef = AnnotatedEnvFile(source=".env", entries=entries)
    lines = aef.lines()
    assert len(lines) == 2


def test_annotated_env_file_annotated_count_zero():
    entries = [AnnotatedEntry(entry=_entry("A", "1"), notes=[])]
    aef = AnnotatedEnvFile(source=".env", entries=entries)
    assert aef.annotated_count() == 0


def test_annotated_env_file_annotated_count_nonzero():
    entries = [
        AnnotatedEntry(entry=_entry("A", "1"), notes=[]),
        AnnotatedEntry(entry=_entry("B", "2"), notes=["secret"]),
    ]
    aef = AnnotatedEnvFile(source=".env", entries=entries)
    assert aef.annotated_count() == 1


def test_summary_no_annotations():
    entries = [AnnotatedEntry(entry=_entry("A", "1"), notes=[])]
    aef = AnnotatedEnvFile(source=".env", entries=entries)
    assert "none annotated" in aef.summary()


def test_summary_with_annotations():
    entries = [
        AnnotatedEntry(entry=_entry("A", "1"), notes=["x"]),
    ]
    aef = AnnotatedEnvFile(source=".env", entries=entries)
    assert "1 annotated" in aef.summary()


# --- annotate_env_file ---

def test_annotate_clean_file_no_notes():
    parsed = _parsed([_entry("PORT", "8080"), _entry("DEBUG", "true")])
    result = annotate_env_file(parsed)
    assert result.annotated_count() == 0


def test_annotate_flags_hex_secret():
    # 32-char hex string should be flagged as a secret
    secret_val = "a1b2c3d4" * 4
    parsed = _parsed([_entry("TOKEN", secret_val)])
    result = annotate_env_file(parsed)
    assert result.annotated_count() == 1
    assert any("secret" in n for n in result.entries[0].notes)


def test_annotate_returns_correct_source():
    parsed = _parsed([], path="config/.env.production")
    result = annotate_env_file(parsed)
    assert result.source == "config/.env.production"


def test_annotate_preserves_entry_order():
    entries = [_entry("Z", "1"), _entry("A", "2"), _entry("M", "3")]
    parsed = _parsed(entries)
    result = annotate_env_file(parsed)
    keys = [ae.entry.key for ae in result.entries]
    assert keys == ["Z", "A", "M"]
