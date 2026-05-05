"""Tests for dotenv_audit.encryptor."""

import pytest

pytest.importorskip("cryptography")

from dotenv_audit.encryptor import (
    generate_key,
    encrypt_env_file,
    decrypt_value,
    EncryptedEntry,
    EncryptResult,
)
from dotenv_audit.parser import EnvEntry, ParsedEnvFile


def _entry(key: str, value: str, flagged_as=None) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw_line=f"{key}={value}", flagged_as=flagged_as)


def _parsed(path: str, entries) -> ParsedEnvFile:
    return ParsedEnvFile(path=path, entries=entries)


def test_generate_key_returns_nonempty_string():
    key = generate_key()
    assert isinstance(key, str)
    assert len(key) > 0


def test_generate_key_is_unique():
    assert generate_key() != generate_key()


def test_encrypt_env_file_encrypts_flagged_entries():
    key = generate_key()
    entries = [
        _entry("API_KEY", "abc123def456abc123def456abc123de", flagged_as="hex_token"),
        _entry("APP_NAME", "myapp"),
    ]
    parsed = _parsed(".env", entries)
    result = encrypt_env_file(parsed, key)

    assert isinstance(result, EncryptResult)
    assert result.file_path == ".env"
    assert "API_KEY" in result.encrypted_keys
    assert "APP_NAME" not in result.encrypted_keys


def test_encrypt_env_file_skips_unflagged_entries():
    key = generate_key()
    entries = [_entry("DEBUG", "true"), _entry("PORT", "8080")]
    parsed = _parsed(".env", entries)
    result = encrypt_env_file(parsed, key)

    assert result.encrypted_keys == []
    for enc in result.entries:
        assert not enc.was_encrypted


def test_encrypted_entry_str_wraps_value():
    key = generate_key()
    entries = [_entry("SECRET", "s3cr3tvalue", flagged_as="hex_token")]
    parsed = _parsed(".env", entries)
    result = encrypt_env_file(parsed, key)

    line = str(result.entries[0])
    assert line.startswith("SECRET=ENC[")
    assert line.endswith("]")


def test_unencrypted_entry_str_unchanged():
    key = generate_key()
    entries = [_entry("HOST", "localhost")]
    parsed = _parsed(".env", entries)
    result = encrypt_env_file(parsed, key)

    assert str(result.entries[0]) == "HOST=localhost"


def test_decrypt_value_roundtrip():
    from cryptography.fernet import Fernet
    key = generate_key()
    fernet = Fernet(key.encode())
    original = "supersecretvalue"
    token = fernet.encrypt(original.encode()).decode()
    wrapped = f"ENC[{token}]"

    assert decrypt_value(wrapped, key) == original


def test_decrypt_value_invalid_token_returns_none():
    key = generate_key()
    result = decrypt_value("ENC[notvalidtoken]", key)
    assert result is None


def test_decrypt_value_wrong_key_returns_none():
    key1 = generate_key()
    key2 = generate_key()
    from cryptography.fernet import Fernet
    token = Fernet(key1.encode()).encrypt(b"hello").decode()
    assert decrypt_value(f"ENC[{token}]", key2) is None


def test_result_lines_includes_all_entries():
    key = generate_key()
    entries = [
        _entry("TOKEN", "abc123def456abc123def456abc123de", flagged_as="hex_token"),
        _entry("NAME", "dotenv-audit"),
    ]
    parsed = _parsed(".env", entries)
    result = encrypt_env_file(parsed, key)

    assert len(result.lines) == 2
