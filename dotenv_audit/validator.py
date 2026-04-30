"""Validates .env file entries against a schema of expected keys and types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from dotenv_audit.parser import ParsedEnvFile

# Supported type hints for schema values
_SUPPORTED_TYPES = {"str", "int", "bool", "url", "email"}


@dataclass
class ValidationIssue:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


@dataclass
class ValidationResult:
    path: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def summary(self) -> str:
        if not self.has_issues:
            return f"{self.path}: OK"
        lines = [f"{self.path}: {len(self.issues)} validation issue(s)"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def _check_type(key: str, value: str, expected: str) -> Optional[ValidationIssue]:
    """Return a ValidationIssue if value doesn't match the expected type hint."""
    if expected == "int":
        if not value.lstrip("-").isdigit():
            return ValidationIssue(key, f"expected int, got {value!r}")
    elif expected == "bool":
        if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
            return ValidationIssue(key, f"expected bool, got {value!r}")
    elif expected == "url":
        if not (value.startswith("http://") or value.startswith("https://")):
            return ValidationIssue(key, f"expected URL, got {value!r}")
    elif expected == "email":
        if "@" not in value or "." not in value.split("@")[-1]:
            return ValidationIssue(key, f"expected email, got {value!r}")
    return None


def validate_env_file(
    parsed: ParsedEnvFile,
    schema: Dict[str, str],
    *,
    require_all: bool = True,
) -> ValidationResult:
    """Validate a ParsedEnvFile against a key->type schema.

    Args:
        parsed: The parsed env file to validate.
        schema: Mapping of key name to expected type string.
        require_all: If True, flag keys present in schema but missing from file.
    """
    result = ValidationResult(path=parsed.path)
    present_keys = {e.key: e.value for e in parsed.entries if e.value is not None}

    if require_all:
        for key in schema:
            if key not in present_keys:
                result.issues.append(ValidationIssue(key, "required key is missing"))

    for key, expected_type in schema.items():
        if expected_type not in _SUPPORTED_TYPES:
            result.issues.append(
                ValidationIssue(key, f"unknown schema type {expected_type!r}")
            )
            continue
        if key in present_keys and expected_type != "str":
            issue = _check_type(key, present_keys[key], expected_type)
            if issue:
                result.issues.append(issue)

    return result
