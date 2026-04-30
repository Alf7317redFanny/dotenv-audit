"""Generate .env.example templates from parsed env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from dotenv_audit.parser import ParsedEnvFile


@dataclass
class TemplateEntry:
    key: str
    comment: str = ""

    def __str__(self) -> str:
        line = f"{self.key}="
        if self.comment:
            return f"# {self.comment}\n{line}"
        return line


@dataclass
class EnvTemplate:
    source_path: str
    entries: List[TemplateEntry] = field(default_factory=list)

    def lines(self) -> List[str]:
        """Return all template lines ready to write to a file."""
        result: List[str] = []
        for entry in self.entries:
            result.append(str(entry))
        return result

    def render(self) -> str:
        """Render the template as a single string."""
        return "\n".join(self.lines())

    @property
    def key_count(self) -> int:
        return len(self.entries)


def build_template(parsed: ParsedEnvFile, annotate_secrets: bool = True) -> EnvTemplate:
    """Build an EnvTemplate from a ParsedEnvFile.

    If *annotate_secrets* is True, entries whose values look like secrets
    get a comment hinting that the value should be kept private.
    """
    entries: List[TemplateEntry] = []
    for env_entry in parsed.entries:
        comment = ""
        if annotate_secrets and env_entry.flag is not None:
            comment = f"secret ({env_entry.flag})"
        entries.append(TemplateEntry(key=env_entry.key, comment=comment))
    return EnvTemplate(source_path=parsed.path, entries=entries)


def build_templates(files: List[ParsedEnvFile], annotate_secrets: bool = True) -> List[EnvTemplate]:
    """Build templates for a list of parsed env files."""
    return [build_template(f, annotate_secrets=annotate_secrets) for f in files]
