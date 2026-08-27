#!/usr/bin/env python3
"""Fail-closed structural validator for BADF repository and gate dossiers."""

from __future__ import annotations

import argparse
import os
import subprocess
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
GATE_IDS = {f"G{i:02d}" for i in range(15)}
POSTURES = {"CLEAR", "OPEN_NON_BLOCKING", "OPEN_BLOCKING"}
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


MATRIX = "badf/authority-matrix.json"
DOWNGRADE_ACK = "BADF_AUTHORITY_DOWNGRADE_ACK"


BASELINE_ENV = "BADF_AUTHORITY_BASELINE"
DEFAULT_BRANCH = "main"


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def resolve_authority_baseline() -> str | None:
    """The commit holding the last AUTHORIZED authority policy, or None.

    Never HEAD. The first negative control (run 33044484934) proved why: on a
    pushed branch HEAD *is* the candidate change, so comparing against it
    finds nothing to refuse. The baseline is the last policy that reached the
    default branch:

      1. BADF_AUTHORITY_BASELINE=<sha|ref>, when the caller knows it -- CI
         passes the PR base SHA or the pre-push tip of the default branch;
      2. otherwise merge-base(HEAD, origin/<default>);
      3. otherwise None, and the caller refuses.

    A baseline equal to HEAD is rejected: it would compare the candidate
    against itself and launder any downgrade.
    """
    head = _git("rev-parse", "HEAD")
    explicit = os.environ.get(BASELINE_ENV, "").strip()
    if explicit:
        base = _git("rev-parse", "--verify", f"{explicit}^{{commit}}")
        # An explicit baseline equal to HEAD would compare the candidate against
        # itself and launder any downgrade. Refuse it as unestablished.
        if base is None or head is None or base == head:
            return None
        return base
    # Implicit: the merge-base with the default branch. When HEAD is *on* the
    # default branch (or a branch with no commits past it) the merge-base IS
    # HEAD, and that is the legitimate no-change case -- there is nothing to
    # compare and nothing to refuse.
    base = _git("merge-base", "HEAD", f"origin/{DEFAULT_BRANCH}")
    return base


def committed_matrix() -> dict[str, Any] | None:
    """The authority matrix at the resolved baseline, or None if unestablished."""
    base = resolve_authority_baseline()
    if base is None:
        return None
    out = _git("show", f"{base}:{MATRIX}")
    return None if out is None else json.loads(out)


def verify_monotonic_authority() -> None:
    """Refuse any change to the authority matrix that lowers required authority.

    Enforces the self-development rule's monotonic invariant: BADF may
    strengthen its own controls within delegated authority, but may not
    reduce required authority, independence or fail-closed behaviour without
    an explicit decision.

    Proven necessary before it was written: with the integrity lockfile
    alone, an author could cut C3 from four required roles to one, re-sign
    the lockfile, and both the repo gate and a one-approval C3 dossier
    PASSED. Integrity made the change visible; nothing refused it.

    Compared against the matrix at the last AUTHORIZED baseline (the merge-base
    with the default branch, or an explicit BADF_AUTHORITY_BASELINE -- never
    HEAD), a change is a DOWNGRADE if it:
      - removes a change class;
      - removes any role from a class's required_roles;
      - removes a reserved action;
      - lowers a rule's minimum_class, or removes a rule.
    Additions and strengthenings pass. A downgrade is refused unless the
    environment carries BADF_AUTHORITY_DOWNGRADE_ACK=<decision id> -- an
    explicit, attributable authorization that CI never sets, so a downgrade
    can only ever be admitted deliberately and locally, never by a pipeline
    going green.

    Deny-unless-established: if no baseline can be resolved, or the baseline
    is HEAD itself, monotonicity cannot be established and the check refuses.
    """
    current_path = ROOT / MATRIX
    if not current_path.is_file():
        raise ValidationError(f"{MATRIX} is missing")
    current = load_json(current_path)
    baseline = committed_matrix()
    if baseline is None:
        raise ValidationError(
            f"the last authorized {MATRIX} cannot be established -- no usable "
            f"{BASELINE_ENV}, no reachable origin/{DEFAULT_BRANCH}, or the baseline "
            f"equals HEAD (which would compare the candidate against itself). Refusing.")

    order = ["C0", "C1", "C2", "C3"]
    rank = {c: i for i, c in enumerate(order)}
    downgrades: list[str] = []

    b_classes = baseline.get("change_classes", {})
    c_classes = current.get("change_classes", {})
    for name, spec in b_classes.items():
        if name not in c_classes:
            downgrades.append(f"change class {name} removed")
            continue
        lost = set(spec.get("required_roles", [])) - set(c_classes[name].get("required_roles", []))
        if lost:
            downgrades.append(f"{name} lost required role(s): {', '.join(sorted(lost))}")

    lost_actions = set(baseline.get("reserved_actions", [])) - set(current.get("reserved_actions", []))
    if lost_actions:
        downgrades.append("reserved action(s) removed: " + ", ".join(sorted(lost_actions)))

    b_rules = {r["action"]: r for r in baseline.get("rules", []) if "action" in r}
    c_rules = {r["action"]: r for r in current.get("rules", []) if "action" in r}
    for action, rule in b_rules.items():
        if action not in c_rules:
            downgrades.append(f"rule for action {action!r} removed")
            continue
        was, now = rule.get("minimum_class"), c_rules[action].get("minimum_class")
        if was in rank and now in rank and rank[now] < rank[was]:
            downgrades.append(f"rule {action!r} minimum_class lowered {was} -> {now}")
        elif was in rank and now not in rank:
            downgrades.append(f"rule {action!r} minimum_class became invalid: {now!r}")

    if not downgrades:
        return
    ack = os.environ.get(DOWNGRADE_ACK, "").strip()
    if ack:
        print(f"authority downgrade admitted under explicit decision {ack}: "
              + "; ".join(downgrades))
        return
    raise ValidationError(
        "authority downgrade refused -- " + "; ".join(downgrades)
        + f". Reducing required authority needs an explicit decision: set "
          f"{DOWNGRADE_ACK}=<decision id> for a deliberate, attributable local run. "
          f"No pipeline sets it.")


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
    verify_monotonic_authority()

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


def parse_blocking_scope(value: str, label: str) -> set[str]:
    """`blocking_scope` as a set of gate ids. `none` is the empty set.

    Free text is refused: a scope that cannot be parsed cannot be compared
    to the gate under decision, and an unparseable scope treated as
    non-blocking would be the fail-open. Accepts `none`, one gate id, or a
    comma list of gate ids.
    """
    text = value.strip()
    if text.lower() == "none":
        return set()
    gates = {part.strip() for part in text.split(",") if part.strip()}
    bad = sorted(g for g in gates if g not in GATE_IDS)
    if bad or not gates:
        raise ValidationError(
            f"{label} blocking_scope {value!r} is not parseable -- use 'none', a gate id "
            f"G00..G14, or a comma list of gate ids")
    return gates


def compute_obligation_posture(dossier: dict[str, Any]) -> str:
    """Plane B, computed from the conditions -- never from the disposition.

    Ported from secb_pf TWO_PLANE_DECISION_MODEL.md. The rule there:
    'Posture is computed from the register, never from the verdict's prose.'
    OPEN_UNCONTROLLED is not a return value here because validate_conditions
    already refuses an uncontrolled condition outright -- a decision defect is
    a refusal, not a posture to render.
    """
    gate = dossier["gate"]
    open_conditions = [c for c in dossier.get("conditions", []) if c.get("status") == "OPEN"]
    if not open_conditions:
        return "CLEAR"
    for index, cond in enumerate(open_conditions):
        scope = parse_blocking_scope(str(cond["blocking_scope"]), f"conditions[{index}]")
        if gate in scope:
            return "OPEN_BLOCKING"
    return "OPEN_NON_BLOCKING"


def render_verdict(disposition: str, posture: str) -> str:
    """The rendering matrix. Plane A is the author's baseline disposition;
    Plane B is computed. The rendered verdict is what the gate stands behind.
    """
    if disposition in {"FAIL", "BLOCKED", "HUMAN_REQUIRED"}:
        return {"FAIL": "REWORK_REQUIRED", "BLOCKED": "BLOCKED",
                "HUMAN_REQUIRED": "HUMAN_REQUIRED"}[disposition]
    return {"CLEAR": "APPROVED",
            "OPEN_NON_BLOCKING": "APPROVED_WITH_CONDITIONS",
            "OPEN_BLOCKING": "HELD_FOR_CONDITION_CLOSURE"}[posture]


def verify_two_plane(dossier: dict[str, Any]) -> str:
    """Refuse a disposition that contradicts the computed posture.

    Before this, `disposition` was asserted by the author and checked only
    for coherence with the conditions' *shape*. A dossier could assert
    PASS_WITH_CONDITIONS while carrying an OPEN Critical condition whose
    blocking_scope covered the very gate being passed, and the gate said
    PASS. The author's plane was the only plane.

    Contradictions refused:
      PASS                  with any OPEN condition          (already refused upstream)
      PASS_WITH_CONDITIONS  with posture OPEN_BLOCKING       -> must be HELD
      PASS                  with posture != CLEAR            (defensive; upstream covers)
    A dossier may DECLARE `rendered_verdict`; if it does, it must equal the
    computed one. An absent declaration is filled in, not refused, because
    the rendered verdict is an output of this gate, not an input to it.
    """
    disposition = dossier["disposition"]
    posture = compute_obligation_posture(dossier)
    rendered = render_verdict(disposition, posture)

    if disposition == "PASS_WITH_CONDITIONS" and posture == "OPEN_BLOCKING":
        blocking = [c["condition_id"] for c in dossier.get("conditions", [])
                    if c.get("status") == "OPEN"
                    and dossier["gate"] in parse_blocking_scope(str(c["blocking_scope"]), c["condition_id"])]
        raise ValidationError(
            f"disposition PASS_WITH_CONDITIONS contradicts computed posture OPEN_BLOCKING: "
            f"{', '.join(blocking)} block(s) gate {dossier['gate']}. The rendered verdict is "
            f"HELD_FOR_CONDITION_CLOSURE; a gate cannot be passed while a condition blocks it.")
    if disposition == "PASS" and posture != "CLEAR":
        raise ValidationError(f"disposition PASS contradicts computed posture {posture}")

    declared = dossier.get("rendered_verdict")
    if declared is not None and declared != rendered:
        raise ValidationError(
            f"declared rendered_verdict {declared!r} contradicts the computed verdict {rendered!r} "
            f"(disposition={disposition}, posture={posture}). The verdict is computed, not asserted.")
    dossier["obligation_posture"] = posture
    dossier["rendered_verdict"] = rendered
    return rendered


def validate_dossier(dossier_path: Path) -> str:
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
    rendered = verify_two_plane(dossier)

    for evidence_type, path_value in indexed.items():
        validate_evidence(safe_repo_path(path_value, "evidence path"), dossier, evidence_type)
    return rendered


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
            args._rendered = validate_dossier(args.path)
    except ValidationError as exc:
        print(f"BADF GATE FAIL: {exc}", file=sys.stderr)
        return 1
    verdict = getattr(args, "_rendered", None)
    print(f"BADF GATE PASS: {args.command}" + (f" -- rendered verdict {verdict}" if verdict else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
