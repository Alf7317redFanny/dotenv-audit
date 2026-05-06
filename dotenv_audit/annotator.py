"""Annotate .env entries with inline comments describing detected issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from dotenv_audit.parser import EnvEntry, ParsedEnvFile
from dotenv_audit.linter import lint_env_file, LintIssue


@dataclass
class AnnotatedEntry:
    entry: EnvEntry
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        line = f"{self.entry.key}={self.entry.value}"
        if self.notes:
            joined = "; ".join(self.notes)
            return f"{line}  # AUDIT: {joined}"
        return line


@dataclass
class AnnotatedEnvFile:
    source: str
    entries: List[AnnotatedEntry] = field(default_factory=list)

    def lines(self) -> List[str]:
        return [str(e) for e in self.entries]

    def annotated_count(self) -> int:
        return sum(1 for e in self.entries if e.notes)

    def summary(self) -> str:
        total = len(self.entries)
        flagged = self.annotated_count()
        if flagged == 0:
            return f"{self.source}: {total} entries, none annotated"
        return f"{self.source}: {total} entries, {flagged} annotated"


def _secret_note(entry: EnvEntry) -> Optional[str]:
    from dotenv_audit.parser import _looks_like_secret
    reason = _looks_like_secret(entry.value)
    if reason:
        return f"possible secret ({reason})"
    return None


def _lint_notes(entry: EnvEntry, lint_issues: List[LintIssue]) -> List[str]:
    return [
        f"lint: {issue.message}"
        for issue in lint_issues
        if issue.key == entry.key
    ]


def annotate_env_file(parsed: ParsedEnvFile) -> AnnotatedEnvFile:
    """Produce an AnnotatedEnvFile with inline notes for secrets and lint issues."""
    lint_result = lint_env_file(parsed)
    lint_issues = lint_result.issues

    annotated_entries: List[AnnotatedEntry] = []
    for entry in parsed.entries:
        notes: List[str] = []
        secret_note = _secret_note(entry)
        if secret_note:
            notes.append(secret_note)
        notes.extend(_lint_notes(entry, lint_issues))
        annotated_entries.append(AnnotatedEntry(entry=entry, notes=notes))

    return AnnotatedEnvFile(source=parsed.path, entries=annotated_entries)
