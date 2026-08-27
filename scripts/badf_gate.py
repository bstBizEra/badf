#!/usr/bin/env python3
"""Fail-closed structural validator for BADF repository and gate dossiers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "AGENTS.md",
    "docs/00-operating-model.md",
    "docs/01-lifecycle-gates.md",
    "docs/02-engineering-loop.md",
    "docs/03-authority-and-agent-councils.md",
    "docs/04-memory-and-context.md",
    "docs/05-evidence-and-provenance.md",
    "docs/06-sessions-handoffs-recovery.md",
    "docs/07-skills-governance.md",
    "docs/08-mcp-and-tools.md",
    "docs/09-security-supply-chain.md",
    "docs/10-quality-testing.md",
    "docs/11-release-production.md",
    "docs/12-operations-learning.md",
    "docs/13-artifact-model.md",
    "badf/lifecycle.json",
    "badf/authority-matrix.json",
    "badf/tool-registry.json",
    "badf/mcp-registry.json",
    "badf/skill-registry.json",
    "schemas/evidence.schema.json",
    "schemas/gate-dossier.schema.json",
    "schemas/work-package.schema.json",
    "schemas/memory.schema.json",
    "schemas/session.schema.json",
    "skills/badf-delivery/SKILL.md",
]

DOSSIER_FIELDS = {
    "schema_version", "id", "work_package_id", "gate", "policy_epoch",
    "source_revision", "target", "change_class", "evidence", "approvals",
    "exceptions", "risks", "disposition", "created_at",
}
EVIDENCE_FIELDS = {
    "schema_version", "id", "work_package_id", "gate", "claim",
    "evidence_type", "producer", "source_revision", "target", "toolchain",
    "operation", "started_at", "completed_at", "outcome", "artifact", "digest",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def require_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - set(value))
    if missing:
        raise ValidationError(f"{label} missing fields: {', '.join(missing)}")


def parse_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} is not ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label} must include timezone")
    return parsed.astimezone(timezone.utc)


def safe_repo_path(value: str, label: str) -> Path:
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise ValidationError(f"{label} escapes repository root") from exc
    if not candidate.is_file():
        raise ValidationError(f"{label} does not exist: {value}")
    return candidate


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def validate_repo() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise ValidationError("required files missing: " + ", ".join(missing))

    for path in sorted((ROOT / "badf").glob("*.json")) + sorted((ROOT / "schemas").glob("*.json")):
        load_json(path)

    lifecycle = load_json(ROOT / "badf/lifecycle.json")
    gates = lifecycle.get("gates")
    if not isinstance(gates, list):
        raise ValidationError("lifecycle.gates must be an array")
    actual_ids = [gate.get("id") for gate in gates if isinstance(gate, dict)]
    expected_ids = [f"G{i:02d}" for i in range(15)]
    if actual_ids != expected_ids:
        raise ValidationError(f"gates must be ordered exactly {expected_ids}")
    for gate in gates:
        require_fields(gate, {"id", "name", "owner_role", "required_evidence", "exit_criteria"}, f"gate {gate.get('id')}")
        evidence = gate["required_evidence"]
        if not isinstance(evidence, list) or not evidence or len(evidence) != len(set(evidence)):
            raise ValidationError(f"gate {gate['id']} has invalid required_evidence")
        if not gate["exit_criteria"]:
            raise ValidationError(f"gate {gate['id']} has no exit criteria")

    authority = load_json(ROOT / "badf/authority-matrix.json")
    if set(authority.get("change_classes", {})) != {"C0", "C1", "C2", "C3"}:
        raise ValidationError("authority matrix must define C0 through C3")
    if not authority.get("reserved_actions"):
        raise ValidationError("authority matrix must reserve high-impact actions")

    skill = (ROOT / "skills/badf-delivery/SKILL.md").read_text(encoding="utf-8")
    if not re.match(r"^---\nname: badf-delivery\ndescription: .+\n---\n", skill):
        raise ValidationError("badf-delivery SKILL.md frontmatter is invalid")


def validate_evidence(path: Path, dossier: dict[str, Any], expected_type: str) -> None:
    evidence = load_json(path)
    require_fields(evidence, EVIDENCE_FIELDS, f"evidence {path}")
    if evidence["schema_version"] != "1.0.0":
        raise ValidationError(f"evidence {path} has unsupported schema_version")
    if evidence["work_package_id"] != dossier["work_package_id"] or evidence["gate"] != dossier["gate"]:
        raise ValidationError(f"evidence {path} is not bound to dossier work package and gate")
    if evidence["source_revision"] != dossier["source_revision"] or evidence["target"] != dossier["target"]:
        raise ValidationError(f"evidence {path} source or target drift")
    if evidence["evidence_type"] != expected_type:
        raise ValidationError(f"evidence {path} type does not match index")
    if evidence["outcome"] != "PASS":
        raise ValidationError(f"evidence {path} outcome is not PASS")
    if not isinstance(evidence["producer"], dict) or not {"id", "type"} <= set(evidence["producer"]):
        raise ValidationError(f"evidence {path} producer is incomplete")
    if not isinstance(evidence["toolchain"], dict) or not {"name", "version"} <= set(evidence["toolchain"]):
        raise ValidationError(f"evidence {path} toolchain is incomplete")
    started = parse_time(evidence["started_at"], f"evidence {path} started_at")
    completed = parse_time(evidence["completed_at"], f"evidence {path} completed_at")
    if completed < started:
        raise ValidationError(f"evidence {path} completed before it started")
    artifact = safe_repo_path(evidence["artifact"], f"evidence {path} artifact")
    if evidence["digest"] != sha256(artifact):
        raise ValidationError(f"evidence {path} artifact digest mismatch")


def validate_dossier(dossier_path: Path) -> None:
    validate_repo()
    dossier = load_json(dossier_path.resolve())
    require_fields(dossier, DOSSIER_FIELDS, "dossier")
    if dossier["schema_version"] != "1.0.0":
        raise ValidationError("unsupported dossier schema_version")
    if not re.fullmatch(r"DOS-[A-Za-z0-9._-]+", str(dossier["id"])):
        raise ValidationError("invalid dossier id")
    if not re.fullmatch(r"WP-[A-Za-z0-9._-]+", str(dossier["work_package_id"])):
        raise ValidationError("invalid work_package_id")
    if dossier["change_class"] not in {"C0", "C1", "C2", "C3"}:
        raise ValidationError("invalid change_class")
    if dossier["disposition"] not in {"PASS", "PASS_WITH_CONDITIONS", "FAIL", "BLOCKED", "HUMAN_REQUIRED"}:
        raise ValidationError("invalid disposition")
    parse_time(dossier["created_at"], "dossier.created_at")

    lifecycle = load_json(ROOT / "badf/lifecycle.json")
    if dossier["policy_epoch"] != lifecycle["policy_epoch"]:
        raise ValidationError("dossier policy epoch is stale")
    gate = next((item for item in lifecycle["gates"] if item["id"] == dossier["gate"]), None)
    if gate is None:
        raise ValidationError("unknown gate")
    if not isinstance(dossier["evidence"], list):
        raise ValidationError("dossier evidence must be an array")

    indexed: dict[str, str] = {}
    for item in dossier["evidence"]:
        if not isinstance(item, dict) or not {"type", "path"} <= set(item):
            raise ValidationError("evidence index items require type and path")
        if item["type"] in indexed:
            raise ValidationError(f"duplicate evidence type: {item['type']}")
        indexed[item["type"]] = item["path"]

    if dossier["disposition"] in {"PASS", "PASS_WITH_CONDITIONS"}:
        missing = sorted(set(gate["required_evidence"]) - set(indexed))
        if missing:
            raise ValidationError("passing dossier missing evidence: " + ", ".join(missing))
        if dossier["disposition"] == "PASS_WITH_CONDITIONS" and not dossier["exceptions"] and not dossier.get("conditions"):
            raise ValidationError("conditional pass requires conditions or exceptions")

    for evidence_type, path_value in indexed.items():
        validate_evidence(safe_repo_path(path_value, "evidence path"), dossier, evidence_type)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("repo", help="validate repository governance structure")
    dossier_parser = subparsers.add_parser("dossier", help="validate a gate dossier and its evidence")
    dossier_parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        validate_repo() if args.command == "repo" else validate_dossier(args.path)
    except ValidationError as exc:
        print(f"BADF GATE FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"BADF GATE PASS: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
