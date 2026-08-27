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

INTEGRITY_PATHS = [
    "AGENTS.md",
    "badf/authority-matrix.json",
    "badf/lifecycle.json",
    "badf/mcp-registry.json",
    "badf/skill-registry.json",
    "badf/tool-registry.json",
    "schemas/evidence.schema.json",
    "schemas/gate-dossier.schema.json",
]
LOCKFILE = "badf/lockfile.json"


DOSSIER_FIELDS = {
    "schema_version", "id", "work_package_id", "gate", "policy_epoch",
    "source_revision", "target", "change_class", "evidence", "approvals",
    "exceptions", "risks", "disposition", "created_at", "author",
}
APPROVAL_FIELDS = {
    "role", "decision", "by", "revision", "policy_epoch", "approved_at",
}
APPROVAL_DECISIONS = {"APPROVED", "REJECTED", "ABSTAIN"}
CONDITION_FIELDS = {
    "condition_id", "statement", "status", "severity", "blocking_scope",
    "owner", "closure_predicate", "closure_authority",
}
CONDITION_STATUSES = {"OPEN", "CLOSED", "SUPERSEDED", "WAIVED"}
CONDITION_SEVERITIES = {"Critical", "Major", "Minor"}
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


def compute_integrity() -> dict[str, str]:
    """sha256 of every governance-critical file, by repo-relative path."""
    digests: dict[str, str] = {}
    for rel in INTEGRITY_PATHS:
        path = ROOT / rel
        if not path.is_file():
            raise ValidationError(f"integrity path missing: {rel}")
        digests[rel] = sha256(path)
    return digests


def verify_integrity() -> None:
    """Refuse when a governance-critical file no longer matches the lockfile.

    This exists because policy in this repository was previously decorative:
    flipping `default_policy` from `deny` to `allow` in all three registries
    left `badf_gate.py repo` reporting PASS. Shape was validated; content was
    not.

    What this does and does not buy, stated plainly so the control is not
    read as stronger than it is:

      DOES  make a policy edit impossible to land silently -- the lockfile
            must change in the same diff, which puts it in front of review
            and in front of the authority classifier.
      DOES  detect out-of-band edits to the rule tree between runs.
      NOT   prevent an author who regenerates the lockfile deliberately.
            A lockfile inside the tree it protects can always be re-signed.

    The remedy for that residue is authority, not hashing: `badf/lockfile.json`
    is a governance path, so re-signing it is a reviewable act by someone other
    than the author. Integrity converts a silent change into a visible one; the
    approval control decides whether the visible change is allowed.

    Unlike the upstream pattern this is adapted from, drift is REFUSED and not
    auto-reverted. Reverting a file is a destructive act, and a validator does
    not hold authority to mutate the tree it is judging.
    """
    lock_path = ROOT / LOCKFILE
    if not lock_path.is_file():
        raise ValidationError(
            f"{LOCKFILE} is absent -- integrity cannot be established. "
            f"Generate it deliberately with: python3 scripts/badf_gate.py lock"
        )
    lock = load_json(lock_path)
    recorded = lock.get("digests")
    if not isinstance(recorded, dict):
        raise ValidationError(f"{LOCKFILE} has no digests object")

    actual = compute_integrity()
    drifted = sorted(p for p in actual if recorded.get(p) != actual[p])
    missing = sorted(set(recorded) - set(actual))
    extra = sorted(set(actual) - set(recorded))
    if drifted or missing or extra:
        detail = []
        if drifted:
            detail.append("changed: " + ", ".join(drifted))
        if missing:
            detail.append("in lockfile but not checked: " + ", ".join(missing))
        if extra:
            detail.append("checked but absent from lockfile: " + ", ".join(extra))
        raise ValidationError(
            "governance integrity drift -- " + "; ".join(detail)
            + f". If the change is intended, re-sign with "
              f"`python3 scripts/badf_gate.py lock` in the same change, so the "
              f"edit is visible in the diff and reviewable."
        )


def write_lockfile() -> None:
    """Re-sign the lockfile from current content.

    Deliberate and explicit: re-signing is how an intended policy change is
    admitted, and it must appear in the same diff as the change it admits.
    """
    digests = compute_integrity()
    (ROOT / LOCKFILE).write_text(
        json.dumps({"schema_version": "1.0.0", "digests": digests}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(f"re-signed {LOCKFILE} over {len(digests)} governance paths")


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

    verify_integrity()

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


def validate_authority(dossier: dict[str, Any]) -> None:
    """Enforce AUTHORITY_SATISFIED(change_class).

        required_roles subset of distinct approving roles
    AND author not among approving principals
    AND every approval bound to the dossier's source_revision
    AND every approval carrying the dossier's policy_epoch and not predating it

    Deny-unless-established: a term that is UNKNOWN -- absent, malformed, or
    unparseable -- denies exactly as a term that is FALSE. The matrix is the
    single source of role requirements; this function adds no vocabulary.
    """
    matrix = load_json(ROOT / "badf/authority-matrix.json")
    classes = matrix["change_classes"]
    change_class = dossier["change_class"]
    spec = classes.get(change_class)
    if spec is None:
        raise ValidationError(f"change class absent from authority matrix: {change_class}")
    required = set(spec["required_roles"])
    known_roles = {role for entry in classes.values() for role in entry["required_roles"]}

    author = dossier.get("author")
    if not isinstance(author, str) or not author.strip():
        raise ValidationError("dossier author is required to evaluate authority")

    approvals = dossier["approvals"]
    if not isinstance(approvals, list):
        raise ValidationError("dossier approvals must be an array")

    created_at = parse_time(dossier["created_at"], "dossier.created_at")
    granted: dict[str, set[str]] = {}
    for index, item in enumerate(approvals):
        label = f"approvals[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"{label} must be an object")
        absent = sorted(APPROVAL_FIELDS - set(item))
        if absent:
            raise ValidationError(f"{label} missing required fields: {', '.join(absent)}")
        role = item["role"]
        principal = item["by"]
        if not isinstance(role, str) or role not in known_roles:
            raise ValidationError(f"{label} unknown role: {role!r}")
        if not isinstance(principal, str) or not principal.strip():
            raise ValidationError(f"{label} approving principal is empty")
        if item["decision"] not in APPROVAL_DECISIONS:
            raise ValidationError(f"{label} invalid decision: {item['decision']!r}")
        if item["revision"] != dossier["source_revision"]:
            raise ValidationError(
                f"{label} is bound to revision {item['revision']!r}, "
                f"not {dossier['source_revision']!r}")
        if item["policy_epoch"] != dossier["policy_epoch"]:
            raise ValidationError(f"{label} carries a stale policy epoch: {item['policy_epoch']!r}")
        if parse_time(item["approved_at"], f"{label}.approved_at") < created_at:
            raise ValidationError(f"{label} predates the dossier it approves")
        if principal == author:
            raise ValidationError(
                f"{label} is supplied by the dossier author {principal!r}: "
                "approve-own-work is a reserved action")
        if item["decision"] == "APPROVED":
            granted.setdefault(principal, set()).add(role)

    for principal, roles in sorted(granted.items()):
        overlap = roles & required
        if len(overlap) > 1:
            raise ValidationError(
                f"principal {principal!r} fills {len(overlap)} required roles "
                f"({', '.join(sorted(overlap))}); required roles must be distinct principals")

    satisfied = {role for roles in granted.values() for role in roles}
    unmet = sorted(required - satisfied)
    if unmet:
        raise ValidationError(f"{change_class} requires approvals from: {', '.join(unmet)}")


def validate_conditions(dossier: dict[str, Any], known_roles: set[str]) -> None:
    """A conditional pass must carry conditions that can actually be closed.

    Ported from secb_pf's CONDITION_REGISTER.md, whose rule is: a condition
    changes state only by an explicit disposition event carrying an authority,
    a rationale and evidence -- not being mentioned is not a state. Before
    this function, `PASS_WITH_CONDITIONS` required only that `conditions` be
    non-empty; `["later"]` satisfied it. A condition nobody owns, with no
    closure predicate and no closure authority, is a wish.

    Deny-unless-established. Every condition on a conditional pass must be:
      - an object carrying all CONDITION_FIELDS,
      - OPEN (a CLOSED/SUPERSEDED/WAIVED condition is history, not an obligation),
      - owned by a role the authority matrix knows,
      - closable by an authority the matrix knows, who is not the dossier author,
      - unique by condition_id within the dossier.
    A bare PASS with open conditions attached is refused: either the
    conditions are real, in which case the disposition is conditional, or they
    are not, in which case they must not be recorded as obligations.
    """
    raw = dossier.get("conditions", [])
    if not isinstance(raw, list):
        raise ValidationError("dossier conditions must be an array")
    disposition = dossier["disposition"]
    author = dossier.get("author")

    if disposition == "PASS_WITH_CONDITIONS" and not raw and not dossier["exceptions"]:
        raise ValidationError("conditional pass requires conditions or exceptions")
    if disposition == "PASS" and any(isinstance(c, dict) and c.get("status") == "OPEN" for c in raw):
        raise ValidationError(
            "a bare PASS may not carry OPEN conditions -- use PASS_WITH_CONDITIONS "
            "so the obligation is visible in the disposition")

    seen: set[str] = set()
    open_count = 0
    for index, cond in enumerate(raw):
        label = f"conditions[{index}]"
        if not isinstance(cond, dict):
            raise ValidationError(f"{label} must be an object, not a bare string")
        absent = sorted(CONDITION_FIELDS - set(cond))
        if absent:
            raise ValidationError(f"{label} missing required fields: {', '.join(absent)}")
        cid = cond["condition_id"]
        if not isinstance(cid, str) or not re.fullmatch(r"C-[0-9]+", cid):
            raise ValidationError(f"{label} condition_id must match C-<n>, got {cid!r}")
        if cid in seen:
            raise ValidationError(f"{label} duplicate condition_id {cid}")
        seen.add(cid)
        for field in ("statement", "closure_predicate", "blocking_scope"):
            if not isinstance(cond[field], str) or not cond[field].strip():
                raise ValidationError(f"{label} {field} is empty")
        if cond["status"] not in CONDITION_STATUSES:
            raise ValidationError(f"{label} invalid status {cond['status']!r}")
        if cond["severity"] not in CONDITION_SEVERITIES:
            raise ValidationError(f"{label} invalid severity {cond['severity']!r}")
        if cond["owner"] not in known_roles:
            raise ValidationError(f"{label} owner {cond['owner']!r} is not a role in the authority matrix")
        if cond["closure_authority"] not in known_roles:
            raise ValidationError(
                f"{label} closure_authority {cond['closure_authority']!r} is not a role in the authority matrix")
        if cond.get("closed_by") is not None and cond["closed_by"] == author:
            raise ValidationError(f"{label} closed by the dossier author -- closure is not self-certified")
        if cond["status"] == "OPEN":
            open_count += 1

    if disposition == "PASS_WITH_CONDITIONS" and raw and open_count == 0:
        raise ValidationError(
            "conditional pass carries no OPEN condition -- nothing is actually owed; use PASS")


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
        validate_authority(dossier)
        missing = sorted(set(gate["required_evidence"]) - set(indexed))
        if missing:
            raise ValidationError("passing dossier missing evidence: " + ", ".join(missing))

    matrix_classes = load_json(ROOT / "badf/authority-matrix.json")["change_classes"]
    known_roles = {role for entry in matrix_classes.values() for role in entry["required_roles"]}
    validate_conditions(dossier, known_roles)

    for evidence_type, path_value in indexed.items():
        validate_evidence(safe_repo_path(path_value, "evidence path"), dossier, evidence_type)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("repo", help="validate repository governance structure")
    subparsers.add_parser("lock", help="re-sign badf/lockfile.json from current content")
    dossier_parser = subparsers.add_parser("dossier", help="validate a gate dossier and its evidence")
    dossier_parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "repo":
            validate_repo()
        elif args.command == "lock":
            write_lockfile()
        else:
            validate_dossier(args.path)
    except ValidationError as exc:
        print(f"BADF GATE FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"BADF GATE PASS: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
