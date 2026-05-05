"""Tag .env entries with semantic labels based on key patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from dotenv_audit.parser import EnvEntry, ParsedEnvFile

# Pattern groups: (tag, substrings that trigger the tag)
_TAG_RULES: List[tuple[str, List[str]]] = [
    ("database", ["DB_", "DATABASE_", "POSTGRES", "MYSQL", "MONGO", "REDIS", "SQLITE"]),
    ("auth", ["SECRET", "TOKEN", "JWT", "API_KEY", "AUTH", "PASSWORD", "PASSWD", "PASS_"]),
    ("aws", ["AWS_", "S3_", "ECR_", "ECS_", "LAMBDA_"]),
    ("email", ["SMTP", "MAIL_", "EMAIL", "SENDGRID", "MAILGUN"]),
    ("url", ["URL", "HOST", "PORT", "ENDPOINT", "BASE_URI", "DOMAIN"]),
    ("feature", ["FEATURE_", "FLAG_", "ENABLE_", "DISABLE_"]),
    ("logging", ["LOG_", "LOGGING", "SENTRY", "DATADOG", "NEWRELIC"]),
]


def tag_entry(entry: EnvEntry) -> List[str]:
    """Return a list of semantic tags for a single entry."""
    key_upper = entry.key.upper()
    tags: List[str] = []
    for tag, patterns in _TAG_RULES:
        if any(p in key_upper for p in patterns):
            tags.append(tag)
    return tags


@dataclass
class TaggedEntry:
    entry: EnvEntry
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "untagged"
        return f"{self.entry.key} [{tag_str}]"


@dataclass
class TaggedEnvFile:
    source: str
    entries: List[TaggedEntry] = field(default_factory=list)

    def by_tag(self, tag: str) -> List[TaggedEntry]:
        """Return all entries that carry the given tag."""
        return [e for e in self.entries if tag in e.tags]

    def all_tags(self) -> List[str]:
        """Sorted unique set of tags present in this file."""
        seen: set[str] = set()
        for e in self.entries:
            seen.update(e.tags)
        return sorted(seen)

    def summary(self) -> str:
        lines = [f"{self.source}: {len(self.entries)} entries"]
        for tag in self.all_tags():
            count = len(self.by_tag(tag))
            lines.append(f"  {tag}: {count}")
        untagged = [e for e in self.entries if not e.tags]
        if untagged:
            lines.append(f"  untagged: {len(untagged)}")
        return "\n".join(lines)


def tag_env_file(parsed: ParsedEnvFile) -> TaggedEnvFile:
    """Produce a TaggedEnvFile from a ParsedEnvFile."""
    entries = [TaggedEntry(entry=e, tags=tag_entry(e)) for e in parsed.entries]
    return TaggedEnvFile(source=parsed.path, entries=entries)
