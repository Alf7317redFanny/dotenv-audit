"""Encrypt and decrypt secret values in .env files using Fernet symmetric encryption."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore


def _require_cryptography() -> None:
    if Fernet is None:  # pragma: no cover
        raise RuntimeError(
            "'cryptography' package is required for encryption. "
            "Install it with: pip install cryptography"
        )


def generate_key() -> str:
    """Generate a new Fernet key and return it as a URL-safe base64 string."""
    _require_cryptography()
    return Fernet.generate_key().decode()


@dataclass
class EncryptedEntry:
    original: EnvEntry
    encrypted_value: Optional[str]
    was_encrypted: bool

    def __str__(self) -> str:
        if self.was_encrypted and self.encrypted_value is not None:
            return f"{self.original.key}=ENC[{self.encrypted_value}]"
        return str(self.original)


@dataclass
class EncryptResult:
    file_path: str
    entries: List[EncryptedEntry] = field(default_factory=list)

    @property
    def encrypted_keys(self) -> List[str]:
        return [e.original.key for e in self.entries if e.was_encrypted]

    @property
    def lines(self) -> List[str]:
        return [str(e) for e in self.entries]


def encrypt_env_file(parsed: ParsedEnvFile, key: str) -> EncryptResult:
    """Encrypt all flagged secret values in a ParsedEnvFile."""
    _require_cryptography()
    fernet = Fernet(key.encode() if isinstance(key, str) else key)
    result = EncryptResult(file_path=parsed.path)
    for entry in parsed.entries:
        if entry.flagged_as is not None and entry.value:
            token = fernet.encrypt(entry.value.encode()).decode()
            result.entries.append(EncryptedEntry(entry, token, was_encrypted=True))
        else:
            result.entries.append(EncryptedEntry(entry, None, was_encrypted=False))
    return result


def decrypt_value(encrypted_value: str, key: str) -> Optional[str]:
    """Decrypt a single ENC[...] wrapped value. Returns None on failure."""
    _require_cryptography()
    fernet = Fernet(key.encode() if isinstance(key, str) else key)
    raw = encrypted_value
    if raw.startswith("ENC[") and raw.endswith("]"):
        raw = raw[4:-1]
    try:
        return fernet.decrypt(raw.encode()).decode()
    except (InvalidToken, Exception):
        return None
