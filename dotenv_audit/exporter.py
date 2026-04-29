"""Export audit results to JSON or CSV formats."""
from __future__ import annotations

import csv
import json
import io
from dataclasses import asdict, dataclass
from typing import List

from dotenv_audit.parser import ParsedEnvFile
from dotenv_audit.comparator import ComparisonResult


@dataclass
class AuditExport:
    """Aggregated data ready for serialisation."""
    secrets: List[dict]
    comparisons: List[dict]


def _secrets_rows(parsed_files: List[ParsedEnvFile]) -> List[dict]:
    rows = []
    for pf in parsed_files:
        for entry in pf.flagged_entries():
            rows.append(
                {
                    "file": str(pf.path),
                    "key": entry.key,
                    "reason": entry.flag_reason or "",
                }
            )
    return rows


def _comparison_rows(results: List[ComparisonResult]) -> List[dict]:
    rows = []
    for cr in results:
        for key in cr.missing_keys:
            rows.append({"base": str(cr.base_path), "other": str(cr.other_path), "issue": "missing", "key": key})
        for key in cr.extra_keys:
            rows.append({"base": str(cr.base_path), "other": str(cr.other_path), "issue": "extra", "key": key})
        for key in cr.mismatched_keys:
            rows.append({"base": str(cr.base_path), "other": str(cr.other_path), "issue": "mismatch", "key": key})
    return rows


def build_export(
    parsed_files: List[ParsedEnvFile],
    results: List[ComparisonResult],
) -> AuditExport:
    return AuditExport(
        secrets=_secrets_rows(parsed_files),
        comparisons=_comparison_rows(results),
    )


def to_json(export: AuditExport, indent: int = 2) -> str:
    return json.dumps(asdict(export), indent=indent)


def to_csv(export: AuditExport) -> str:
    """Return a CSV string with a 'type' column distinguishing secrets/comparisons."""
    buf = io.StringIO()
    fieldnames = ["type", "file", "base", "other", "key", "issue", "reason"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in export.secrets:
        writer.writerow({"type": "secret", **row})
    for row in export.comparisons:
        writer.writerow({"type": "comparison", **row})
    return buf.getvalue()
