"""Tests for dotenv_audit.grouper."""

from __future__ import annotations

from dotenv_audit.grouper import EnvGroup, group_env_files, infer_label
from dotenv_audit.parser import EnvEntry, ParsedEnvFile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parsed(path: str, keys: list[str] | None = None) -> ParsedEnvFile:
    entries = [EnvEntry(key=k, raw_value="val", comment=None) for k in (keys or [])]
    return ParsedEnvFile(path=path, entries=entries)


# ---------------------------------------------------------------------------
# infer_label
# ---------------------------------------------------------------------------

def test_infer_label_default():
    assert infer_label("/project/.env") == "default"


def test_infer_label_development():
    assert infer_label(".env.dev") == "development"
    assert infer_label(".env.development") == "development"


def test_infer_label_production():
    assert infer_label(".env.prod") == "production"
    assert infer_label(".env.production") == "production"


def test_infer_label_staging():
    assert infer_label(".env.staging") == "staging"
    assert infer_label(".env.stag") == "staging"


def test_infer_label_test():
    assert infer_label(".env.test") == "test"
    assert infer_label(".env.testing") == "test"


def test_infer_label_local():
    assert infer_label(".env.local") == "local"


def test_infer_label_example():
    assert infer_label(".env.example") == "example"


def test_infer_label_unknown():
    assert infer_label("some_random_config.txt") == "unknown"


def test_infer_label_case_insensitive():
    assert infer_label(".ENV.PROD") == "production"


# ---------------------------------------------------------------------------
# EnvGroup helpers
# ---------------------------------------------------------------------------

def test_env_group_all_keys_union():
    g = EnvGroup(label="test", files=[
        _parsed("a", ["KEY_A", "SHARED"]),
        _parsed("b", ["KEY_B", "SHARED"]),
    ])
    assert g.all_keys() == ["KEY_A", "KEY_B", "SHARED"]


def test_env_group_all_keys_empty():
    g = EnvGroup(label="default", files=[])
    assert g.all_keys() == []


def test_env_group_files_missing_key():
    g = EnvGroup(label="default", files=[
        _parsed("has.env", ["DB_URL", "SECRET"]),
        _parsed("missing.env", ["DB_URL"]),
    ])
    assert g.files_missing_key("SECRET") == ["missing.env"]
    assert g.files_missing_key("DB_URL") == []


# ---------------------------------------------------------------------------
# group_env_files
# ---------------------------------------------------------------------------

def test_group_env_files_empty():
    assert group_env_files([]) == {}


def test_group_env_files_single_file():
    pf = _parsed(".env", ["KEY"])
    groups = group_env_files([pf])
    assert "default" in groups
    assert groups["default"].files == [pf]


def test_group_env_files_multiple_labels():
    files = [
        _parsed(".env", ["A"]),
        _parsed(".env.prod", ["A", "B"]),
        _parsed(".env.dev", ["A"]),
    ]
    groups = group_env_files(files)
    assert set(groups.keys()) == {"default", "production", "development"}


def test_group_env_files_same_label_merged():
    files = [
        _parsed("services/api/.env", ["PORT"]),
        _parsed("services/db/.env", ["DB_URL"]),
    ]
    groups = group_env_files(files)
    assert len(groups["default"].files) == 2


def test_group_env_files_preserves_insertion_order():
    files = [
        _parsed(".env.prod"),
        _parsed(".env.dev"),
        _parsed(".env.test"),
    ]
    groups = group_env_files(files)
    assert list(groups.keys()) == ["production", "development", "test"]
