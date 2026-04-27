"""Compare parsed .env files across environments to find mismatched or missing keys."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class ComparisonResult:
    """Result of comparing two or more env files."""

    reference_path: str
    compared_path: str
    missing_in_compared: List[str] = field(default_factory=list)
    extra_in_compared: List[str] = field(default_factory=list)
    common_keys: List[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.missing_in_compared or self.extra_in_compared)

    def summary(self) -> str:
        lines = [f"Comparing '{self.reference_path}' vs '{self.compared_path}'"]
        if self.missing_in_compared:
            lines.append(f"  Missing keys ({len(self.missing_in_compared)}): {', '.join(sorted(self.missing_in_compared))}")
        if self.extra_in_compared:
            lines.append(f"  Extra keys  ({len(self.extra_in_compared)}): {', '.join(sorted(self.extra_in_compared))}")
        if not self.has_issues:
            lines.append("  No key mismatches found.")
        return "\n".join(lines)


def compare_env_files(reference: ParsedEnvFile, compared: ParsedEnvFile) -> ComparisonResult:
    """Compare two ParsedEnvFile instances and return a ComparisonResult."""
    ref_keys: Set[str] = set(reference.keys())
    cmp_keys: Set[str] = set(compared.keys())

    return ComparisonResult(
        reference_path=reference.path,
        compared_path=compared.path,
        missing_in_compared=sorted(ref_keys - cmp_keys),
        extra_in_compared=sorted(cmp_keys - ref_keys),
        common_keys=sorted(ref_keys & cmp_keys),
    )


def compare_many(
    reference: ParsedEnvFile, others: List[ParsedEnvFile]
) -> List[ComparisonResult]:
    """Compare a reference env file against a list of other env files."""
    return [compare_env_files(reference, other) for other in others]
