"""Tests for dotenv_audit.parser."""

from pathlib import Path

import pytest

from dotenv_audit.parser import EnvEntry, ParsedEnvFile, parse_env_file, _looks_like_secret


# ---------------------------------------------------------------------------
# _looks_like_secret
# ---------------------------------------------------------------------------

def test_looks_like_secret_returns_none_for_empty():
    assert _looks_like_secret("") is None


def test_looks_like_secret_returns_none_for_placeholder():
    assert _looks_like_secret("your_secret_here") is None
    assert _looks_like_secret("<CHANGE_ME>") is None
    assert _looks_like_secret("changeme") is None


def test_looks_like_secret_flags_hex_token():
    reason = _looks_like_secret("a3f1c2d4e5b6a7f8c9d0e1f2a3b4c5d6")
    assert reason is not None


def test_looks_like_secret_flags_aws_key():
    reason = _looks_like_secret("AKIAIOSFODNN7EXAMPLE")
    assert reason is not None


def test_looks_like_secret_flags_github_pat():
    reason = _looks_like_secret("ghp_" + "A" * 36)
    assert reason is not None


def test_looks_like_secret_flags_openai_key():
    reason = _looks_like_secret("sk-" + "x" * 25)
    assert reason is not None


# ---------------------------------------------------------------------------
# parse_env_file
# ---------------------------------------------------------------------------

SAMPLE_ENV = """
# This is a comment
DB_HOST=localhost
DB_PASSWORD=a3f1c2d4e5b6a7f8c9d0e1f2a3b4c5d6
API_KEY=your_api_key_here
EMPTY_VAR=
SECRET_TOKEN=ghp_{'A' * 36}
"""


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# comment\n"
        "DB_HOST=localhost\n"
        "DB_PASSWORD=a3f1c2d4e5b6a7f8c9d0e1f2a3b4c5d6\n"
        "API_KEY=your_api_key_here\n"
        "EMPTY_VAR=\n"
    )
    return p


def test_parse_returns_parsed_env_file(env_file: Path):
    result = parse_env_file(env_file)
    assert isinstance(result, ParsedEnvFile)
    assert result.path == env_file


def test_parse_extracts_keys(env_file: Path):
    result = parse_env_file(env_file)
    assert "DB_HOST" in result.keys
    assert "DB_PASSWORD" in result.keys
    assert "API_KEY" in result.keys


def test_parse_flags_suspicious_value(env_file: Path):
    result = parse_env_file(env_file)
    flagged_keys = {e.key for e in result.flagged_entries}
    assert "DB_PASSWORD" in flagged_keys


def test_parse_does_not_flag_placeholder(env_file: Path):
    result = parse_env_file(env_file)
    flagged_keys = {e.key for e in result.flagged_entries}
    assert "API_KEY" not in flagged_keys


def test_parse_handles_comments(env_file: Path):
    result = parse_env_file(env_file)
    comments = [e for e in result.entries if e.is_comment]
    assert len(comments) == 1


def test_parse_raises_on_missing_file(tmp_path: Path):
    with pytest.raises(ValueError, match="Cannot read"):
        parse_env_file(tmp_path / "nonexistent.env")
