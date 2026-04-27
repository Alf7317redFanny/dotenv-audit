"""Format and print audit reports combining parser flags and comparator results."""

from typing import List

from dotenv_audit.comparator import ComparisonResult
from dotenv_audit.parser import ParsedEnvFile


ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def report_secrets(parsed: ParsedEnvFile, use_color: bool = True) -> str:
    """Return a formatted string listing flagged secret entries in a parsed env file."""
    flagged = parsed.flagged_entries()
    lines = [_colorize(f"[{parsed.path}]", ANSI_BOLD, use_color)]
    if not flagged:
        lines.append(_colorize("  No exposed secrets detected.", ANSI_GREEN, use_color))
    else:
        for entry in flagged:
            reason = entry.secret_reason or "unknown"
            lines.append(
                _colorize(f"  LINE {entry.line_number}: {entry.key} — {reason}", ANSI_RED, use_color)
            )
    return "\n".join(lines)


def report_comparison(result: ComparisonResult, use_color: bool = True) -> str:
    """Return a formatted string for a single ComparisonResult."""
    lines = [
        _colorize(
            f"[{result.reference_path}] vs [{result.compared_path}]",
            ANSI_BOLD,
            use_color,
        )
    ]
    if result.missing_in_compared:
        label = _colorize("  MISSING", ANSI_YELLOW, use_color)
        lines.append(f"{label}: {', '.join(result.missing_in_compared)}")
    if result.extra_in_compared:
        label = _colorize("  EXTRA", ANSI_YELLOW, use_color)
        lines.append(f"{label}: {', '.join(result.extra_in_compared)}")
    if not result.has_issues:
        lines.append(_colorize("  Keys match.", ANSI_GREEN, use_color))
    return "\n".join(lines)


def full_report(
    parsed_files: List[ParsedEnvFile],
    comparisons: List[ComparisonResult],
    use_color: bool = True,
) -> str:
    """Produce a full audit report covering secrets and key mismatches."""
    sections = []
    sections.append(_colorize("=== Secret Scan ===", ANSI_BOLD, use_color))
    for pf in parsed_files:
        sections.append(report_secrets(pf, use_color=use_color))

    if comparisons:
        sections.append(_colorize("\n=== Key Comparison ===", ANSI_BOLD, use_color))
        for cmp in comparisons:
            sections.append(report_comparison(cmp, use_color=use_color))

    return "\n".join(sections)
