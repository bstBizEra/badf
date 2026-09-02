#!/usr/bin/env python3
"""Fail-closed structural validator for BADF repository and gate dossiers."""

from __future__ import annotations

import argparse
import unicodedata
import os
import subprocess
import hashlib
import json
import re
import sys
import tempfile
import fnmatch
import platform
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
    "docs/governance/DECISION_GOVERNANCE_BOARD_AUTHORITY.md",
    "badf/lifecycle.json",
    "badf/authority-matrix.json",
    "badf/seats.json",
    "badf/decision-policy.json",
    "badf/risk-appetite.json",
    "badf/council-registry.json",
    "badf/tool-registry.json",
    "badf/mcp-registry.json",
    "badf/skill-registry.json",
    "schemas/evidence.schema.json",
    "schemas/gate-dossier.schema.json",
    "schemas/work-package.schema.json",
    "schemas/memory.schema.json",
    "schemas/session.schema.json",
    "schemas/decision-policy.schema.json",
    "schemas/risk-appetite.schema.json",
    "schemas/council-registry.schema.json",
    "schemas/ballot.schema.json",
    "schemas/decision-dossier.schema.json",
    "schemas/calibration-ledger.schema.json",
    "skills/badf-delivery/SKILL.md",
]

INTEGRITY_PATHS = [
    # QA finding F-1: the gate was not in its own lockfile. Any control could
    # be deleted from this file with the lockfile byte-identical to main.
    # Hashing the gate, the workflow and the tests does not make them
    # un-editable -- it makes every edit carry a visible re-sign in the same
    # diff, so the reviewer's eye is drawn to exactly the files that decide.
    "scripts/*.py",
    ".github/workflows/badf-gates.yml",
    "AGENTS.md",
    # The analysis of f337d9f found the lockfile protected the ENFORCER and
    # not the POLICY: all 16 docs, all 7 test files, the skill source and the
    # templates were unlocked. A change to the document defining what a
    # council may do was invisible to every control. Directories are locked
    # by glob; the lockfile lists every matched file explicitly so an added
    # or removed file is drift too.
    "docs/**/*.md",
    "tests/*.py",
    "skills/**/*",
    "templates/*",
    # #43: what CI applies is locked -- the example dossier is validated on every
    # run and the drift walker reads example files as shipped instances.
    "examples/**/*",
    "badf/authority-matrix.json",
    "badf/lifecycle.json",
    "badf/mcp-registry.json",
    "badf/skill-registry.json",
    "badf/tool-registry.json",
    "badf/decision-policy.json",
    "badf/risk-appetite.json",
    "badf/council-registry.json",
    "badf/decisions/*.json",
    "badf/demands/*.json",
    "badf/releases/*.json",
    "badf/repositories.json",
    # Foreign work packages: the evidence ARTIFACTS are digest-bound already,
    # but the dossier and evidence .json files were not -- a re-pointed digest
    # plus a re-pointed artifact is a consistent forgery the gate cannot see.
    # Every new work package re-signs the lockfile: that is the reviewable act.
    "work/**/*.json",
    "work/**/*.jsonl",
    "work/**/*.diff",
    "work/**/*.txt",
    "schemas/*.json",
]
LOCKFILE = "badf/lockfile.json"


DOSSIER_FIELDS = {
    "schema_version", "id", "work_package_id", "gate", "policy_epoch",
    "source_revision", "target", "change_class", "evidence", "approvals",
    "exceptions", "risks", "disposition", "created_at", "author", "author_type",
}
APPROVAL_FIELDS = {
    "role", "decision", "by", "principal_type", "revision", "policy_epoch", "approved_at",
}
PRINCIPAL_TYPES = {"human", "agent", "service", "controller"}
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


INVISIBLE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}
CLASS_RANK = {"C0": 0, "C1": 1, "C2": 2, "C3": 3}
DECISION_ID = re.compile(r"^BADF-DEC-[0-9]{4,}$")
DECISIONS_DIR = "badf/decisions"
REPOSITORIES = "badf/repositories.json"
DEMANDS_DIR = "badf/demands"
DEMAND_ID = re.compile(r"^BADF-DEM-[0-9]{4,}$")
DEMAND_FIELDS = {"schema_version", "demand_id", "kind", "source", "title", "problem", "recorded_at", "provenance", "status"}
DEMAND_KINDS = {"issue", "token", "decision", "discovery"}
DEMAND_PROVENANCE = {"EXPORTED_FROM_SOURCE", "RECONSTRUCTED", "DISCOVERED"}
LEDGER_NAME = "run-ledger.jsonl"
GENESIS_HASH = "sha256:" + "0" * 64
LEDGER_FIELDS = {"event_id", "workflow_id", "sequence", "step", "outcome", "actor", "recorded_at",
                 "previous_event_hash", "event_hash"}
LEDGER_OUTCOMES = {"PREPARED", "AUTHORITY_CHECKED", "COMMITTED", "REJECTED", "OUTCOME_UNKNOWN",
                   "PROVEN_ABSENT", "COMPENSATED", "MANUAL_REMEDIATION",
                   "SKIPPED_ALREADY_COMMITTED", "OBSERVED"}
# AET-I05's second phase had no vocabulary: nothing recorded that the AUTHORITY CHECK
# ran, and REJECTED is ambiguous about which phase rejected on whose authority. A phase
# that leaves no trace cannot be shown to have happened (#294). Mandatory from the WP
# that ships it; earlier runs are grandfathered; sentinels exempt -- the surface/seat
# ratchet shape reused, not a new mechanism.
AUTHORITY_RATCHET_THRESHOLD = 132
# The outcomes that assert THE EFFECT HAPPENED. Narrower than TERMINAL_OUTCOMES on
# purpose (#294): terminal means "this attempt concluded", established means "the world
# changed". PROVEN_ABSENT and REJECTED are terminal and NOT established -- the protocol
# already lets a proven-absent effect be prepared again, which is correct, because
# proving absence is proof it is safe to retry. Conflating the two would have forbidden
# a retry the ledger's own tests require.
EFFECT_ESTABLISHED = {"COMMITTED", "SKIPPED_ALREADY_COMMITTED"}
# What may follow an established effect: you may record undoing it or escalating it.
# You may never record preparing or committing it again -- that is the double execution
# AET-I05 exists to prevent -- nor asserting it never happened.
AFTER_ESTABLISHED_ALLOWED = {"COMPENSATED", "MANUAL_REMEDIATION"}
COUNCIL_DISPOSITIONS = {"CHALLENGE_REQUIRED", "CHALLENGE_OPTIONAL", "CHALLENGE_NOT_REQUIRED"}
COUNCIL_VERDICTS = {"APPROVE", "APPROVE_WITH_CONDITIONS", "REJECT", "ABSTAIN", "INSUFFICIENT_EVIDENCE"}
RISK_SEVERITIES = {"Critical", "Major", "Minor"}
PRODUCTION_GATES = {"G10", "G11", "G12"}
TERMINAL_OUTCOMES = {"COMMITTED", "REJECTED", "PROVEN_ABSENT", "COMPENSATED", "MANUAL_REMEDIATION",
                     "SKIPPED_ALREADY_COMMITTED", "OBSERVED"}
DECISION_FIELDS = {
    "schema_version", "decision_id", "title", "status", "decided_at",
    "decision_authority", "work_package_id", "change_class", "ballot",
    "authorizes", "authority_downgrade", "binding",
}
DECISION_STATUSES = {"PROPOSED", "DECIDED", "SUPERSEDED", "REVOKED"}


def expect_str(value: Any, label: str) -> str:
    """Refuse a non-string where a string is required, as a controlled refusal.

    QA found 32 inputs that exited via traceback rather than BADF GATE FAIL:
    a list where a string was expected hits `in <set>` and raises TypeError; a
    null hits `.replace` and raises AttributeError. A traceback is not a
    refusal -- it leaks internals and is not the contract main() promises.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a string, got {type(value).__name__}")
    return value


def canonical_principal(value: Any, label: str) -> str:
    """One identity for one person, however they typed it.

    QA finding F-2: principals were compared with raw `==`, so `mallory`,
    `mallory `, `Mallory`, `mallory<ZWSP>` and `mallory<TAB>` were four
    distinct approvers -- and the author approved their own C3 change under
    all four. Canonical form is NFKC + casefold + strip. Invisible and
    control characters (Unicode Cc/Cf/Zl/Zp, and any Zs but plain space)
    survive NFKC, so they are REFUSED rather than stripped: an identifier
    carrying a zero-width space is not a typo, it is an attempt.

    Not handled: cross-script homoglyphs (Cyrillic `а` for Latin `a`). A
    confusables table is out of scope here; mixed-script identifiers are
    refused as the cheap approximation, and the residue is stated.
    """
    text = expect_str(value, label)
    norm = unicodedata.normalize("NFKC", text).casefold().strip()
    if not norm:
        raise ValidationError(f"{label} principal is empty")
    for ch in norm:
        cat = unicodedata.category(ch)
        if cat in INVISIBLE_CATEGORIES or (cat == "Zs" and ch != " "):
            raise ValidationError(
                f"{label} contains an invisible or control character (U+{ord(ch):04X}); refused")
    scripts = {"latin" if "LATIN" in unicodedata.name(ch, "") else "other"
               for ch in norm if ch.isalpha()}
    if len(scripts) > 1:
        raise ValidationError(f"{label} mixes scripts; refused as a possible homoglyph")
    return norm


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """QA finding F-9: json.loads keeps the LAST duplicate key, so a dossier
    whose first `disposition` reads FAIL and last reads PASS is evaluated as
    PASS while a reviewer reading top-down sees FAIL. Refuse duplicates."""
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


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
    expect_str(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} is not ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label} must include timezone")
    return parsed.astimezone(timezone.utc)


def safe_repo_path(value: str, label: str) -> Path:
    expect_str(value, label)
    try:
        candidate = (ROOT / value).resolve()
    except (OSError, ValueError) as exc:
        raise ValidationError(f"{label} is not a usable path: {exc.__class__.__name__}") from exc
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


def compute_integrity(root: Path = None, patterns: list[str] = None) -> dict[str, str]:
    """sha256 of every governance-critical file, by root-relative path.

    Entries may be globs. A glob that matches nothing is REFUSED, not skipped:
    a pattern that silently matches zero files is a hole shaped exactly like
    the directory it was meant to cover. One implementation serves the
    framework (ROOT, INTEGRITY_PATHS) and every project instance
    (BADF-WP-0022): a second lockfile format would drift from the first.
    """
    root = ROOT if root is None else root
    patterns = INTEGRITY_PATHS if patterns is None else patterns
    digests: dict[str, str] = {}
    for entry in patterns:
        if any(ch in entry for ch in "*?["):
            matches = sorted(q for q in root.glob(entry) if q.is_file())
            if not matches:
                raise ValidationError(f"integrity glob matches no files: {entry}")
            for path in matches:
                digests[path.relative_to(root).as_posix()] = sha256(path)
        else:
            path = root / entry
            if not path.is_file():
                raise ValidationError(f"integrity path missing: {entry}")
            digests[entry] = sha256(path)
    return digests


def verify_lock(root: Path, patterns: list[str], what: str, resign_hint: str) -> None:
    lock_path = root / LOCKFILE
    if not lock_path.is_file():
        raise ValidationError(f"{LOCKFILE} is absent -- integrity cannot be established. "
                              f"Generate it deliberately with: {resign_hint}")
    lock = load_json(lock_path)
    recorded = lock.get("digests")
    if not isinstance(recorded, dict):
        raise ValidationError(f"{LOCKFILE} has no digests object")
    actual = compute_integrity(root, patterns)
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
            f"{what} integrity drift -- " + "; ".join(detail)
            + f". If the change is intended, re-sign with `{resign_hint}` in the same change, "
              "so the edit is visible in the diff and reviewable.")


def write_lock(root: Path, patterns: list[str]) -> int:
    digests = compute_integrity(root, patterns)
    (root / LOCKFILE).write_text(
        json.dumps({"schema_version": "1.0.0", "digests": digests}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return len(digests)


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
    verify_lock(ROOT, INTEGRITY_PATHS, "governance", "python3 scripts/badf_gate.py lock")



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


def _git_bytes(*args: str) -> bytes | None:
    """Like _git but returns raw stdout bytes -- for digests, where _git's strip
    would drop the trailing newline and corrupt every comparison."""
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout
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
        # QA finding F-3: an explicit baseline was accepted for ANY commit,
        # including the attacker's own weak parent (HEAD~1) or a tag on a side
        # branch. The baseline must be a policy that actually reached the
        # default branch: require it to be an ancestor of origin/<default>.
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", base, f"origin/{DEFAULT_BRANCH}"],
                             cwd=ROOT, capture_output=True)
        if anc.returncode != 0:
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
    if out is None:
        return None
    try:
        parsed = json.loads(out, object_pairs_hook=_no_duplicate_keys)
    except ValueError:
        raise ValidationError(f"the baseline {MATRIX} at {base[:12]} is not valid JSON; refusing")
    if not isinstance(parsed, dict):
        raise ValidationError(f"the baseline {MATRIX} at {base[:12]} is not an object; refusing")
    return parsed


def authority_downgrades(baseline: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Every way `current` is weaker than `baseline`. ONE definition of
    "downgrade": the framework's monotonic guard (matrix vs its authorized
    baseline) and the instance charter check (charter vs the framework floor
    at the pinned revision) both call this."""
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

    # BADF-DEC-0003: human_reserved_roles is a constraint. Losing one is a
    # downgrade of exactly the kind losing a required_role is.
    lost_reserved = set(baseline.get("human_reserved_roles") or []) - set(current.get("human_reserved_roles") or [])
    if lost_reserved:
        downgrades.append("human_reserved_roles lost: " + ", ".join(sorted(lost_reserved)))

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

    return downgrades


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

    downgrades = authority_downgrades(baseline, current)
    if not downgrades:
        return
    _admit_downgrade(downgrades)


def load_decision(decision_id: str) -> dict[str, Any]:
    """The decision record a given id names, or a refusal.

    F-8 residue: the ack was validated against a REGEX. BADF-DEC-9999
    matched and named nothing. A decision the framework acts on must be a
    file in the tree -- lockfile-covered, so it cannot be forged without a
    visible re-sign -- with a status, an authority, a scope and a binding.
    BADF's own two decisions had less provenance than its evidence until
    this existed.
    """
    if not DECISION_ID.match(decision_id):
        raise ValidationError(f"{decision_id!r} is not a decision id (expected BADF-DEC-nnnn)")
    path = ROOT / DECISIONS_DIR / f"{decision_id}.json"
    if not path.is_file():
        raise ValidationError(f"decision {decision_id} does not exist at {DECISIONS_DIR}/{decision_id}.json")
    record = load_json(path)
    require_fields(record, DECISION_FIELDS, f"decision {decision_id}")
    if record["decision_id"] != decision_id:
        raise ValidationError(f"decision file {path.name} carries id {record['decision_id']!r}")
    status = expect_str(record["status"], f"decision {decision_id} status")
    if status not in DECISION_STATUSES:
        raise ValidationError(f"decision {decision_id} has invalid status {status!r}")
    parse_time(record["decided_at"], f"decision {decision_id}.decided_at")
    return record


def _admit_downgrade(downgrades: list[str]) -> None:
    """QA finding F-8: any non-blank ack admitted a downgrade -- "0", "false",
    10,000 characters, and ANSI escapes that erased their own log line. The
    ack must look like a decision id and is echoed ASCII-safe."""
    ack = os.environ.get(DOWNGRADE_ACK, "").strip()
    if ack:
        decision = load_decision(ack)
        if decision["status"] != "DECIDED":
            raise ValidationError(
                f"decision {ack} is {decision['status']}, not DECIDED; it cannot admit a downgrade")
        grant = decision.get("authority_downgrade") or {}
        if grant.get("permits_downgrade") is not True:
            raise ValidationError(
                f"decision {ack} does not permit an authority downgrade "
                f"(authority_downgrade.permits_downgrade is not true); refusing")
        # The decision must name the baseline it was taken against. A decision
        # that authorized SOME downgrade does not authorize THIS one unless the
        # policy it looked at is the policy being changed.
        bound = (decision.get("binding") or {}).get("authority_matrix_digest")
        baseline = resolve_authority_baseline()
        actual = None
        if baseline:
            # Raw bytes, not _git()'s stripped text: the artifact binds to the
            # file exactly as sha256() hashes evidence, trailing newline and
            # all. The first version stripped and could never match a real
            # decision -- caught by the test that checks DEC-0001's own binding.
            raw = subprocess.run(["git", "show", f"{baseline}:{MATRIX}"], cwd=ROOT, capture_output=True)
            if raw.returncode == 0:
                actual = "sha256:" + hashlib.sha256(raw.stdout).hexdigest()
        if not bound or not actual or bound != actual:
            raise ValidationError(
                f"decision {ack} is bound to authority matrix {str(bound)[:23]}..., but the baseline "
                f"being changed is {str(actual)[:23]}...; a decision authorizes a downgrade from ONE "
                f"specific policy, not from whatever is current. Take a new decision.")
        print("authority downgrade admitted under decision " + ascii(ack)
              + " (" + ascii(decision["title"])[:60] + "): " + "; ".join(downgrades))
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
    n = write_lock(ROOT, INTEGRITY_PATHS)
    print(f"re-signed {LOCKFILE} over {n} governance paths")



# ---- badf-git GIT-E/GIT-F: the content tree and the composition record (BADF-WP-0076/0079) ----
COMPOSITION_REQUIRED = ("schema_version", "observed_at", "repository", "work_package_id", "target_ref", "target_base_sha",
                        "source_ref", "merge_base_sha", "merge_method", "expected_result_tree", "expected_content_tree",
                        "policy_epoch", "test_set_epoch", "suite_pattern", "non_coverage")


def content_tree(checkout: Path, wp: str, rev: str = "HEAD") -> str:
    """The tree of <rev> with work/<wp>/ and badf/lockfile.json removed -- the binding of a
    composition record (BADF-WP-0076). Computed from the OBJECT STORE ALONE on a temporary
    index: `read-tree <rev>`, `update-index --force-remove` of the excluded paths,
    `write-tree`. GIT-E's first version used `git rm --cached`, which refuses a path whose
    worktree file differs from the index -- never inside compose's fresh scratch, always
    possible elsewhere -- and the helper silently returned the FULL tree (BADF-WP-0079).
    The checkout's own index and worktree are never touched."""
    with tempfile.TemporaryDirectory(prefix="badf-ctree-") as d:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(d) / "index")}

        def run(*a: str) -> subprocess.CompletedProcess:
            return subprocess.run(["git", "-C", str(checkout), *a], capture_output=True, text=True, env=env)

        r = run("read-tree", rev)
        if r.returncode:
            raise ValidationError(f"cannot read the tree of {rev} in {checkout}: {r.stderr.strip()}")
        listed = run("ls-files", "--", f"work/{wp}", "badf/lockfile.json").stdout.split()
        if listed:
            r = run("update-index", "--force-remove", "--", *listed)
            if r.returncode:
                raise ValidationError(f"cannot exclude work/{wp}/ and the lockfile from {rev}: {r.stderr.strip()}")
        r = run("write-tree")
        if r.returncode:
            raise ValidationError(f"cannot write the content tree of {rev} in {checkout}: {r.stderr.strip()}")
        return r.stdout.strip()


def parse_composition_record(text: str, label: str) -> dict[str, Any]:
    """A git-composition record as `badf_compose.py --record` wrote it. Refuses anything
    that is not a complete record: a verdict must never be computed against a file that
    merely looks like one, and reconcile must never downgrade a broken record to 'none'."""
    try:
        rec = json.loads(text)
    except ValueError:
        raise ValidationError(f"{label} is not a git-composition record (not JSON)")
    if not isinstance(rec, dict) or rec.get("record") != "git-composition":
        raise ValidationError(f"{label} is not a git-composition record (no `record: git-composition`)")
    missing = [k for k in COMPOSITION_REQUIRED if k not in rec]
    if missing:
        raise ValidationError(f"{label} is not a complete git-composition record; missing {missing}")
    return rec


def load_composition_record(path: Path) -> dict[str, Any]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read the composition record {path}: {exc}")
    return parse_composition_record(text, str(path))


# ---- work ledger: landing is derived from git, claims are corroborated (BADF-WP-0019, #26) ----
# One identity, three faces, one binding (BADF-WP-0070 / badf-git GIT-B): the
# machine id is WP_NAMESPACE + NNNN. WP-2026- is the ledger's genesis namespace,
# a fixed constant -- NOT a calendar field; NNNN continues monotonically and never
# rolls over. Defined ONCE here; badf_compose.py and check_pr_traceability.py
# import it, so the three regexes that used to repeat the literal cannot drift.
# WP_DISPLAY is the human label permitted in PR titles / squash subjects only.
# The ledger keeps reading historical display-form trailers (history is never
# rewritten, GIT-I06); only new PRs must bind the canonical form.
WP_NAMESPACE = "WP-2026-"
WP_DISPLAY = "BADF-WP-"
WP_LINE = re.compile(rf"^Work-Package:\s*(?:{re.escape(WP_DISPLAY)}|{re.escape(WP_NAMESPACE)})([0-9]{{4}})\s*$", re.M)
WP_ID_FORMS = re.compile(rf"^(?:{re.escape(WP_DISPLAY)}|{re.escape(WP_NAMESPACE)})([0-9]{{4}})$")


def self_repository() -> str:
    reg = load_json(ROOT / REPOSITORIES)
    for name, spec in (reg.get("repositories") or {}).items():
        if isinstance(spec, dict) and spec.get("resolution") == "SELF":
            return name
    raise ValidationError(f"{REPOSITORIES} declares no SELF repository; the ledger cannot be established")


def ledger_landings() -> dict[str, list[str]]:
    """WP id -> commits on the first-parent history of origin/<default> whose
    body carries that WP's Work-Package line, newest first. A record cannot
    know its own squash SHA before it lands, so landing is never read from
    the record: it is read from the ledger and the record is held to it."""
    ref = f"origin/{DEFAULT_BRANCH}"
    if _git("rev-parse", "--verify", f"{ref}^{{commit}}") is None:
        raise ValidationError(f"ledger cannot be established: {ref} is unreachable")
    raw = _git("log", "--first-parent", "--format=%H%x00%B%x1e", ref)
    if raw is None:
        raise ValidationError(f"ledger cannot be established: git log {ref} failed")
    out: dict[str, list[str]] = {}
    for rec in raw.split("\x1e"):
        if "\x00" not in rec:
            continue
        sha, body = rec.split("\x00", 1)
        for m in WP_LINE.finditer(body):
            out.setdefault(f"{WP_NAMESPACE}{m.group(1)}", []).append(sha.strip())
    return out


def self_work_packages() -> list[tuple[Path, dict[str, Any]]]:
    me = self_repository()
    found = []
    for path in sorted((ROOT / "work").glob(f"{WP_NAMESPACE}*/work-package.json")):
        rec = load_json(path)
        if isinstance(rec, dict) and rec.get("repository") == me:
            found.append((path, rec))
    return found


def verify_work_ledger() -> list[str]:
    """Corroborate every landing claim; name silence; refuse a new record
    while landed ones are unreconciled. Returns the LANDED_UNRECONCILED ids."""
    ref = f"origin/{DEFAULT_BRANCH}"
    landings = ledger_landings()
    first_parent = set((_git("rev-list", "--first-parent", ref) or "").split())
    ledger_tree = set((_git("ls-tree", "-r", "--name-only", ref, "--", "work/") or "").splitlines())
    unreconciled: list[tuple[str, str]] = []
    new: list[str] = []
    for path, rec in self_work_packages():
        wp = rec.get("id") or path.parent.name
        status = rec.get("status")
        target = rec.get("external_target") if isinstance(rec.get("external_target"), dict) else {}
        claimed = target.get("landed_as")
        reason = rec.get("landing_not_on_ledger")
        landed = landings.get(wp, [])
        if claimed:
            full = _git("rev-parse", "--verify", f"{claimed}^{{commit}}")
            if full is None:
                raise ValidationError(f"{wp} claims landed_as {claimed}, which is not a commit in this repository")
            if full not in first_parent:
                raise ValidationError(f"{wp} claims landed_as {full[:7]}, which is not on the ledger (first-parent history of {ref})")
            if full not in landed:
                raise ValidationError(f"{wp} claims landed_as {full[:7]}, but that commit does not carry its Work-Package line")
            if status != "CLOSED":
                raise ValidationError(f"{wp} claims landed_as {full[:7]} so its status must be CLOSED, not {status!r}")
            if reason:
                raise ValidationError(f"{wp} states landing_not_on_ledger while claiming landed_as {full[:7]}: contradictory")
        elif status == "CLOSED":
            if landed:
                what = "landing_not_on_ledger is a false statement" if reason else "reconcile it"
                raise ValidationError(f"{wp} is CLOSED with no landed_as, but the ledger shows it landed as {landed[-1][:7]}; {what}")
            if not isinstance(reason, str) or not reason.strip():
                raise ValidationError(f"{wp} is CLOSED with no corroborated landing; state landing_not_on_ledger: <reason>")
        else:
            if reason:
                raise ValidationError(f"{wp} states landing_not_on_ledger but is {status!r}, not CLOSED")
            if landed:
                unreconciled.append((wp, landed[-1]))
        if path.relative_to(ROOT).as_posix() not in ledger_tree:
            new.append(wp)
    if new and unreconciled:
        debt = ", ".join(f"{wp} (landed as {sha[:7]})" for wp, sha in unreconciled)
        raise ValidationError(f"reconcile landed work packages before opening a new one: {debt}; new: {', '.join(new)}")
    for wp, sha in unreconciled:
        print(f"BADF LEDGER: {wp} LANDED_UNRECONCILED (landed as {sha[:7]}; run: badf_gate.py reconcile {wp})")
    return [wp for wp, _ in unreconciled]


# ---- GOV-0108 (#246, WP-2026-0126): the enforcement-input ratchet ----
SURFACE_RATCHET_THRESHOLD = 126
SURFACE_RATCHET_SENTINELS = frozenset({997, 998, 999, 9999})


def _surface_ratchet_applies(wp_id: str) -> bool:
    """expected_surfaces.files is mandatory from WP-2026-0126 forward -- the record
    that shipped the ratchet is the first one it binds. Earlier records are
    grandfathered (counted at the point of judgment, never edited); the sentinel ids
    (#199 / GOV-0085 synthetic fixtures) are exempt by declaration, not by silence."""
    m = WP_ID_FORMS.match(str(wp_id))
    if not m:
        return False
    n = int(m.group(1))
    return n >= SURFACE_RATCHET_THRESHOLD and n not in SURFACE_RATCHET_SENTINELS


def _unmatchable_declared(wp_id: str, patterns: list[str]) -> list[str]:
    """Patterns that can NEVER match a governed diff: the record's own work/ dir and
    the lockfile are excluded from that diff by construction, so declaring either is
    noise wearing C7 authority (the VAL-B near-miss, #232 thread)."""
    bad = []
    for pat in patterns:
        p = str(pat)
        if p == "badf/lockfile.json" or p == f"work/{wp_id}" or p.startswith(f"work/{wp_id}/"):
            bad.append(p)
    return bad


def verify_surface_ratchet() -> None:
    """GOV-0108: a control whose input is optional is a control that is off by
    default, and nothing says so. This says so -- coverage is counted out loud on
    every run, records at or above the threshold are refused without a declaration,
    and a declaration that can never match is refused outright. Over-reach and
    over-declaration remain DISTINCT judgments at the assembly/binding sites (#257);
    this counter never blends them into one number."""
    declared = grandfathered = ratcheted = 0
    for path, rec in self_work_packages():
        wp = rec.get("id") or path.parent.name
        files = [str(x) for x in ((rec.get("expected_surfaces") or {}).get("files") or [])]
        under = _surface_ratchet_applies(wp)
        if under:
            ratcheted += 1
        if files:
            declared += 1
            if under:
                bad = _unmatchable_declared(wp, files)
                if bad:
                    raise ValidationError(f"{wp}: expected_surfaces.files declares {bad}, which can never match a governed diff (the record's own work/ dir and the lockfile are excluded from it by construction) -- an unmatchable pattern is C7 authority attached to nothing (GOV-0108)")
        elif under:
            raise ValidationError(f"{wp}: no expected_surfaces.files declared -- mandatory at and above the threshold WP-2026-0126; C3 containment and the C7 delegation ceiling cannot read an absent input (GOV-0108)")
        else:
            grandfathered += 1
    total = declared + grandfathered
    print(f"BADF SURFACE RATCHET: declared {declared}/{total}; grandfathered undeclared {grandfathered} (threshold WP-2026-0126; sentinels exempt; {ratcheted} record(s) under the ratchet); over-reach and over-declaration judged separately at assembly/binding (GOV-0108)")


# ---- AET-B-1 (#287, WP-2026-0130): the seat roster ----
SEAT_RATCHET_THRESHOLD = 130
_SEAT_FORBIDDEN_PERMISSION_KEYS = ("allowed_paths", "allowed_tools", "actions", "permissions", "prohibited")
_SEAT_FORBIDDEN_TIME_KEYS = ("expires", "expiry", "until", "valid_until", "window", "time_window")


def _authority_ratchet_applies(wp_id: str) -> bool:
    """The authority-check witness is mandatory from WP-2026-0132 forward (the WP that
    shipped it); earlier ledgers are grandfathered, sentinels exempt (same shape and
    same reasons as the surface and seat ratchets)."""
    m = WP_ID_FORMS.match(str(wp_id))
    if not m:
        return False
    n = int(m.group(1))
    return n >= AUTHORITY_RATCHET_THRESHOLD and n not in SURFACE_RATCHET_SENTINELS


def _seat_ratchet_applies(wp_id: str) -> bool:
    """The delegation seat field is mandatory from WP-2026-0130 forward (the WP that
    shipped the roster); earlier delegations are grandfathered and counted; sentinel
    ids stay exempt by declaration (same shape as the surface ratchet, same reasons)."""
    m = WP_ID_FORMS.match(str(wp_id))
    if not m:
        return False
    n = int(m.group(1))
    return n >= SEAT_RATCHET_THRESHOLD and n not in SURFACE_RATCHET_SENTINELS


def _seat_entries() -> list[dict[str, Any]]:
    """The single authoritative loader and validator of roster CONTENT (#290, sixth
    reseal): every refusal a seat's content can earn lives HERE, so both consumers --
    verify_seat_roster's walk and _rostered_seats()/_check_delegations -- inherit all
    of it. Consumer-side validation is how the id asymmetry, the shape divergence
    (sweep crashed, loader skipped), and the invisible-to-assembly authority guards
    each happened; this closes the CLASS at one site instead of patching instances.
    The schema's declarations remain backstop where the walker enforces them and
    decorative where it does not (#265); this loader is the sole code-side enforcer
    (#264 pattern, stated). Runs before any check_schema call, so doctrine-declared
    shapes get doctrine-declared messages; schema stays backstop."""
    data = load_json(ROOT / "badf/seats.json")
    entries = data.get("seats") or []
    if not entries:
        # A loop finding nothing passes like one finding everything (REV, vacuity).
        raise ValidationError("badf/seats.json declares no seats: an empty roster reports clean over its own absence -- refused (AET-B-1 / #287, enumeration-vacuity)")
    seen: set[str] = set()
    for s in entries:
        if not isinstance(s, dict):
            # Governed refusal, never a skip and never a crash: the loader skipping
            # while the sweep crashed was the delegation-fork divergence at the roster.
            raise ValidationError(f"a seat entry is not a mapping: {s!r} (#290 REV, roster shape)")
        sid = str(s.get("id") or "")
        if not sid.strip() or sid != sid.strip():
            raise ValidationError(f"seat id {sid!r} is empty, whitespace-only, or padded: it names nothing a delegation could safely bind to (QA Finding 1, #290 / #293 degenerate-content)")
        if sid in seen:
            raise ValidationError(f"seat id {sid!r} appears more than once: a set would collapse the duplicate silently on a roster whose subject is identity (QA Finding 2, #290)")
        seen.add(sid)
        for k in _SEAT_FORBIDDEN_PERMISSION_KEYS:
            if k in s:
                raise ValidationError(f"seat {sid!r} carries permission-shaped key {k!r}: the roster holding permissions forks badf/authority-matrix.json -- AUTHORITY_CONFLICT (AET-B-1 / #287)")
        for k in _SEAT_FORBIDDEN_TIME_KEYS:
            if k in s:
                raise ValidationError(f"seat {sid!r} carries time-shaped key {k!r}: the time window is a doctrine-declared component of authority whose home is undecided (#261 round, docs/03) -- AUTHORITY_CONFLICT (AET-B-1 / #287)")
        for field in ("role", "status", "description"):
            if not str(s.get(field) or "").strip():
                raise ValidationError(f"seat {sid!r} has blank {field}: degenerate content on the identity surface (#290 sixth reseal / #293)")
        refs = s.get("charter_refs") or []
        # Non-emptiness of the CONTENTS, not the container: [""] is truthy (#293,
        # REV's third-appearance finding -- truthiness on the list, verbatim).
        if not refs or not all(str(r).strip() for r in refs):
            raise ValidationError(f"seat {sid!r} has empty charter_refs or a blank entry: provenance-free identity is the degenerate-content shape (QA Finding 2 + REV cc3ca64, #290)")
    return entries


def _rostered_seats() -> set[str]:
    """Thin projection of the validated roster; all refusals live in _seat_entries()."""
    return {str(s["id"]) for s in _seat_entries()}


def _declared_seat(d: dict[str, Any]) -> str | None:
    """QA Finding 1 (#290): a blank or whitespace-only `seat` names nothing -- it passed
    the mandatory-seat ratchet (only None read as absent) and resolved against an
    empty-id seat. Normalized to absent HERE, once, called from BOTH sites
    (_check_delegations and verify_seat_roster), so the twins cannot fork on it."""
    seat = d.get("seat")
    if seat is None:
        return None
    s = str(seat).strip()
    return s or None


def verify_seat_roster() -> None:
    """AET-B-1: the roster holds identity and NOTHING else. Both doctrine-declared
    shapes that must never land in it are refused by name -- permissions fork
    badf/authority-matrix.json, and time windows pre-empt the #261-round decision
    docs/03 requires. Delegation seat coverage is counted at the point of judgment."""
    entries = _seat_entries()   # every content refusal lives in the loader (sixth reseal)
    held = vacant = 0
    for s in entries:
        if s.get("status") == "VACANT":
            vacant += 1
        else:
            held += 1
    # Schema stays backstop for what the loader does not name (e.g. an arbitrary
    # undeclared key): additionalProperties is walker-enforced (#265, measured). The
    # loader has already run, so doctrine shapes got doctrine messages first.
    check_schema("seats", load_json(ROOT / "badf/seats.json"))
    seats = {str(s["id"]) for s in entries}
    with_seat = without = 0
    for path in sorted((ROOT / "work").glob(f"{WP_NAMESPACE}*/build/session.json")):
        wp = path.parent.parent.name
        for d in (load_json(path) or {}).get("delegations") or []:
            if not isinstance(d, dict):
                # Consistent with the assembly-side raise: assembly does not stand on
                # every landing path (session.json can change post-assembly), so the
                # sweep must refuse what assembly would refuse (#290 review, REV).
                raise ValidationError(f"{wp}: a delegation is not a mapping (C7)")
            seat = _declared_seat(d)
            if seat is None:
                without += 1
                if _seat_ratchet_applies(wp):
                    raise ValidationError(f"{wp}: delegation {d.get('task')!r} names no seat -- mandatory at and above the threshold {WP_NAMESPACE}0130 (AET-B-1 / #287)")
            else:
                with_seat += 1
                if seat not in seats:
                    raise ValidationError(f"{wp}: delegation {d.get('task')!r} declares seat {seat!r}, which is not in badf/seats.json (declaration-consistency; identity verification lands with #261)")
    print(f"BADF SEAT ROSTER: {held} held, {vacant} VACANT; delegations naming a seat {with_seat}, grandfathered without {without} (threshold {WP_NAMESPACE}0130; sentinels exempt) -- declaration-consistency only until #261 gives seats a structural referent (AET-B-1)")


def reconcile_work_package(wp_arg: str) -> str:
    m = WP_ID_FORMS.match(wp_arg.strip())
    if not m:
        raise ValidationError(f"{wp_arg!r} is not a work package id ({WP_NAMESPACE}NNNN or {WP_DISPLAY}NNNN)")
    wp = f"{WP_NAMESPACE}{m.group(1)}"
    path = ROOT / "work" / wp / "work-package.json"
    if not path.is_file():
        raise ValidationError(f"{wp} has no record at work/{wp}/work-package.json")
    rec = load_json(path)
    me = self_repository()
    if rec.get("repository") != me:
        raise ValidationError(f"{wp} targets {rec.get('repository')!r}: not this repository's ledger ({me}); reconcile it where it landed")
    target = dict(rec.get("external_target") or {})
    if target.get("landed_as"):
        raise ValidationError(f"{wp} already claims landed_as {target['landed_as']}; nothing to reconcile")
    landed = ledger_landings().get(wp, [])
    if not landed:
        raise ValidationError(f"{wp} has not landed on origin/{DEFAULT_BRANCH}: no first-parent commit carries its Work-Package line")
    sha = landed[-1]   # the first landing; later ones are named, not chosen
    # GIT-F (BADF-WP-0079): MERGED != VERIFIED. The composition record is read from the
    # LANDED commit's tree, never from the checkout, and the landed content tree is
    # computed from the object store alone; a mismatch is the one window the
    # expected-head merge guard cannot close -- main moved between the last CI run and
    # the merge -- and it is a refusal, not a note. No record stays honest and visible.
    record_text = _git("show", f"{sha}:work/{wp}/evidence/G07/composition-record.json")
    if record_text is not None:
        record = parse_composition_record(record_text, f"{sha[:12]}:work/{wp}/evidence/G07/composition-record.json")
        landed_tree = content_tree(ROOT, wp, sha)
        expected = record.get("expected_content_tree")
        if landed_tree != expected:
            raise ValidationError(
                f"BLOCKED: the landed content of {wp} ({sha[:12]}, content tree {landed_tree[:12]}) is not the composition "
                f"that was verified (recorded {str(expected)[:12]}) -- main moved between verification and merge; "
                f"open recovery as a forward change, never rewrite {DEFAULT_BRANCH}")
        target["landed_content_tree"] = landed_tree
        target["composition_verified"] = True
    else:
        target["composition_verified"] = False
    target["landed_as"] = sha
    rec["external_target"] = target
    rec["status"] = "CLOSED"
    rec.pop("landing_not_on_ledger", None)
    path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    write_lockfile()
    also = f" (also carried by {', '.join(s[:7] for s in landed[:-1])})" if len(landed) > 1 else ""
    verified = ("composition_verified: true (landed content tree matches the record)" if target["composition_verified"]
                else "composition_verified: false (no composition record on the landed tree)")
    return (f"BADF RECONCILE: {wp} CLOSED, landed_as {sha[:7]}{also}; {verified}; lockfile re-signed -- "
            f"ship it in the next work package's PR")


DIGEST_FORM = re.compile(r"^sha256:[0-9a-f]{64}$")


DEMAND_TERMINAL = {"RESOLVED", "REJECTED"}
LEARNING_FORM = re.compile(r"^(NONE_DECLARED|docs/learnings/[a-z0-9-]+\.md)$")


def verify_demand_learnings() -> None:
    """Every resolved Issue becomes potential institutional learning
    (GITHUB_CONTROL_PLANE.md). A demand that reached a terminal status
    (RESOLVED or REJECTED) must carry a `learning`: a docs/learnings/<slug>.md
    path that exists, or the literal NONE_DECLARED. Silence is not 'nothing
    learned' -- it is drift (BADF-WP-0035, #29)."""
    for path in sorted((ROOT / DEMANDS_DIR).glob("*.json")):
        rec = load_json(path)
        did = rec.get("demand_id", path.name)
        learning = rec.get("learning")
        if learning is not None and not (isinstance(learning, str) and LEARNING_FORM.match(learning)):
            raise ValidationError(f"demand {did} learning {learning!r} is malformed (expected NONE_DECLARED or docs/learnings/<slug>.md)")
        if rec.get("status") in DEMAND_TERMINAL:
            if not isinstance(learning, str) or not LEARNING_FORM.match(learning):
                raise ValidationError(f"demand {did} is {rec.get('status')} but declares no learning; a concluded demand states docs/learnings/<slug>.md or NONE_DECLARED")
            if learning != "NONE_DECLARED" and not (ROOT / learning).is_file():
                raise ValidationError(f"demand {did} learning file {learning} does not exist")


def verify_registry_digests() -> None:
    """Every skill-registry entry's digest is the sha256 of the source it
    names (BADF-WP-0032, #52). docs/07 makes ACTIVE mean a pinned digest; the
    field carried GENERATED_AT_RELEASE from the start and nothing compared
    it. A placeholder, a malformed value, a stale digest or a missing source
    is refused, naming the entry."""
    registry = load_json(ROOT / "badf/skill-registry.json")
    for entry in registry.get("skills") or []:
        name = entry.get("name", "?")
        source = entry.get("source")
        digest = entry.get("digest")
        if not isinstance(source, str) or not (ROOT / source).is_file():
            raise ValidationError(f"skill registry entry {name}: source {source!r} does not exist")
        if not isinstance(digest, str) or not DIGEST_FORM.match(digest):
            raise ValidationError(f"skill registry entry {name}: digest {digest!r} is not a sha256 pin (a placeholder is not a pin)")
        actual = sha256(ROOT / source)
        if digest != actual:
            raise ValidationError(f"skill registry entry {name}: digest does not match {source} ({digest[:19]}... vs {actual[:19]}...); re-pin the entry with the edit")


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
    verify_registry_digests()
    verify_release_refs()
    verify_demand_learnings()
    verify_monotonic_authority()
    verify_work_ledger()
    verify_surface_ratchet()
    verify_seat_roster()

def check_non_coverage(dossier: dict[str, Any], evidence_type: str, outcome: str) -> None:
    """G08 exit criterion: 'non-coverage declared'. Before WP-0014 nothing on a
    dossier could declare it, and validate_evidence required PASS for every
    type -- so a contract test that honestly did not apply could only be
    recorded by lying. NOT_APPLICABLE is admitted ONLY when the dossier's
    non_coverage[] names that evidence type with a reason and an owner who
    stands behind the declaration. Absence of a declaration is not
    non-coverage; it is a missing test.
    """
    declared = dossier.get("non_coverage") or []
    if not isinstance(declared, list):
        raise ValidationError("dossier.non_coverage must be an array")
    for i, n in enumerate(declared):
        if not isinstance(n, dict) or not {"evidence_type", "reason", "declared_by"} <= set(n):
            raise ValidationError(f"non_coverage[{i}] must carry evidence_type, reason, declared_by")
    if not any(n["evidence_type"] == evidence_type for n in declared):
        raise ValidationError(
            f"evidence type {evidence_type!r} is {outcome} but the dossier's non_coverage does not declare it; "
            f"an undeclared non-applicability is a missing test, not a non-coverage")



# ---- G01 evidence contract: per-type rules the gate enforces by OPENING the artifact (BADF-WP-0030, #51) ----
PLACEHOLDER = re.compile(r"__[A-Z_]+__|\bTBD\b|\bTODO\b|\{\{[^}]*\}\}")


def _strings(obj: Any, where: str = ""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, f"{where}.{k}" if where else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{where}[{i}]")
    elif isinstance(obj, str):
        yield where, obj


def _no_placeholders(doc: Any, label: str) -> None:
    for where, text in _strings(doc):
        if PLACEHOLDER.search(text):
            raise ValidationError(f"{label}: unresolved placeholder at {where}: {text[:60]!r}")


def _sibling_artifact(dossier: dict[str, Any], evidence_type: str, label: str) -> tuple[Path, dict[str, Any]]:
    """The artifact of another evidence type in the SAME dossier, by the
    dossier's own index -- never by guessing a path."""
    for item in dossier.get("evidence") or []:
        if isinstance(item, dict) and item.get("type") == evidence_type:
            rec = load_json(safe_repo_path(item["path"], f"{evidence_type} evidence path"))
            art = safe_repo_path(rec["artifact"], f"{evidence_type} artifact")
            return art, load_json(art)
    raise ValidationError(f"{label} requires a {evidence_type} evidence in the same dossier")


def check_prd(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("prd", doc)
    _no_placeholders(doc, "prd")
    inside, outside = set(doc["scope"]["in_scope"]), set(doc["scope"]["out_of_scope"])
    both = sorted(inside & outside)
    if both:
        raise ValidationError(f"prd: same item in both in_scope and out_of_scope: {', '.join(both)}")
    metrics = {m["id"] for m in doc["success_metrics"]}
    for objective in doc["objectives"]:
        unknown = sorted(set(objective.get("metric_refs") or []) - metrics)
        if unknown:
            raise ValidationError(f"prd: objective {objective['id']} references unknown metric(s): {', '.join(unknown)}")


def check_acceptance_criteria(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("acceptance-criteria", doc)
    _no_placeholders(doc, "acceptance-criteria")
    if not doc["criteria"]:
        raise ValidationError("acceptance-criteria: no criteria; an empty list is not acceptance")
    ids = [c["id"] for c in doc["criteria"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"acceptance-criteria: duplicate criterion id(s): {', '.join(dupes)}")
    _, prd = _sibling_artifact(dossier, "prd", "acceptance-criteria")
    if doc["prd_id"] != prd["id"]:
        raise ValidationError(f"acceptance-criteria: prd_id {doc['prd_id']!r} is not the dossier's PRD {prd['id']!r}")
    objectives = {o["id"] for o in prd["objectives"]}
    for c in doc["criteria"]:
        unknown = sorted(set(c.get("objective_refs") or []) - objectives)
        if unknown:
            raise ValidationError(f"acceptance-criteria: criterion {c['id']} references unknown objective(s): {', '.join(unknown)}")


def check_product_approval(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("product-approval", doc)
    _no_placeholders(doc, "product-approval")
    producer = evidence["producer"]
    if producer.get("type") != "human":
        raise ValidationError("product-approval must be produced by a human product_owner; a non-human producer cannot approve a product")
    if producer.get("id") != doc["approved_by"]["principal"]:
        raise ValidationError(f"product-approval producer {producer.get('id')!r} is not approved_by.principal {doc['approved_by']['principal']!r}")
    prd_path, prd = _sibling_artifact(dossier, "prd", "product-approval")
    if doc["prd_id"] != prd["id"]:
        raise ValidationError(f"product-approval: prd_id {doc['prd_id']!r} is not the dossier's PRD {prd['id']!r}")
    if doc["approved_by"]["principal"] == prd["author"]["principal"]:
        raise ValidationError(f"product-approval: the PRD author {prd['author']['principal']!r} cannot approve their own PRD")
    if doc["prd_digest"] != sha256(prd_path):
        raise ValidationError("product-approval: prd_digest does not match the prd artifact in this dossier (the PRD changed after approval, or the approval is for other bytes)")


# ---- G02 evidence contract: requirement decomposition, NFRs, the RTM, definition of ready (BADF-WP-0041, #70) ----
def check_requirements(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("requirements", doc)
    _no_placeholders(doc, "requirements")
    reqs = doc["requirements"]
    if not reqs:
        raise ValidationError("requirements: no requirements; an empty list does not decompose a product")
    ids = [r["id"] for r in reqs]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"requirements: duplicate requirement id(s): {', '.join(dupes)}")
    _, rtm = _sibling_artifact(dossier, "traceability", "requirements")
    objectives = set(rtm.get("objectives") or [])
    for r in reqs:
        refs = r.get("objective_refs") or []
        if not refs:
            raise ValidationError(f"requirements: {r['id']} decomposes no objective; a requirement must trace to at least one PRD objective")
        unknown = sorted(set(refs) - objectives)
        if unknown:
            raise ValidationError(f"requirements: {r['id']} references objective(s) absent from the RTM's objective universe: {', '.join(unknown)}")


def check_nfr(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("nfr", doc)
    _no_placeholders(doc, "nfr")
    nfrs = doc["nfrs"]
    if not nfrs:
        raise ValidationError("nfr: no NFRs; 'NFRs quantified' cannot be established from an empty list")
    ids = [n["id"] for n in nfrs]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"nfr: duplicate NFR id(s): {', '.join(dupes)}")
    for n in nfrs:
        value = n["target"]["value"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"nfr: {n['id']} is not quantified; target value {value!r} is not a number")


def check_traceability(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("traceability", doc)
    _no_placeholders(doc, "traceability")
    objectives = set(doc["objectives"])
    criteria = set(doc["acceptance_criteria"])
    if not objectives or not criteria:
        raise ValidationError("traceability: an RTM must declare at least one objective and one acceptance criterion")
    _, req_art = _sibling_artifact(dossier, "requirements", "traceability")
    req_ids = {r["id"] for r in (req_art.get("requirements") or [])}

    r2o: dict[str, set] = {}
    for row in doc["requirement_to_objective"]:
        req = row["requirement"]
        if req in r2o:
            raise ValidationError(f"traceability: requirement {req} mapped twice in requirement_to_objective")
        r2o[req] = set(row["objectives"])
    c2r: dict[str, set] = {}
    for row in doc["criterion_to_requirement"]:
        crit = row["criterion"]
        if crit in c2r:
            raise ValidationError(f"traceability: criterion {crit} mapped twice in criterion_to_requirement")
        c2r[crit] = set(row["requirements"])

    # requirement -> objective: no dangling map entry; every requirement mapped to >=1 declared objective
    dangling_req = sorted(set(r2o) - req_ids)
    if dangling_req:
        raise ValidationError(f"traceability: requirement_to_objective names requirement(s) absent from the requirements artifact: {', '.join(dangling_req)}")
    for req in sorted(req_ids):
        objs = r2o.get(req)
        if not objs:
            raise ValidationError(f"traceability: orphan requirement {req}: not mapped to any objective")
        unknown = sorted(objs - objectives)
        if unknown:
            raise ValidationError(f"traceability: requirement {req} maps to undeclared objective(s): {', '.join(unknown)}")

    # criterion -> requirement: every declared criterion covered by >=1 existing requirement; no dangling map entry
    for crit in sorted(criteria):
        mapped = c2r.get(crit)
        if not mapped:
            raise ValidationError(f"traceability: uncovered acceptance criterion {crit}: not mapped to any requirement")
        unknown = sorted(mapped - req_ids)
        if unknown:
            raise ValidationError(f"traceability: criterion {crit} maps to unknown requirement(s): {', '.join(unknown)}")
    dangling_crit = sorted(set(c2r) - criteria)
    if dangling_crit:
        raise ValidationError(f"traceability: criterion_to_requirement names criterion(s) not declared in acceptance_criteria: {', '.join(dangling_crit)}")


def check_definition_of_ready(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("definition-of-ready", doc)
    _no_placeholders(doc, "definition-of-ready")
    if evidence["producer"].get("type") != "human":
        raise ValidationError("definition-of-ready must be produced by a human; readiness is a human judgment, not a generated artifact")
    lifecycle = load_json(ROOT / "badf/lifecycle.json")
    g02 = next((g for g in lifecycle["gates"] if g["id"] == "G02"), None)
    if g02 is None:
        raise ValidationError("definition-of-ready: lifecycle.json declares no G02")
    required = list(g02["exit_criteria"])
    checked = {item["criterion"]: item["met"] for item in doc["checklist"]}
    missing = [c for c in required if c not in checked]
    if missing:
        raise ValidationError(f"definition-of-ready: missing G02 exit-criterion checklist item(s): {'; '.join(missing)}")
    unmet = [c for c in required if checked.get(c) is not True]
    if unmet:
        raise ValidationError(f"definition-of-ready: G02 exit criterion not met: {'; '.join(unmet)}")


# ---- G03 evidence contract: UX and service design -- journeys, blueprint, accessibility, validation (BADF-WP-0042, #72) ----
def check_journeys(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("journeys", doc)
    _no_placeholders(doc, "journeys")
    journeys = doc["journeys"]
    if not journeys:
        raise ValidationError("journeys: no journeys; an empty list designs no path")
    ids = [j["id"] for j in journeys]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"journeys: duplicate journey id(s): {', '.join(dupes)}")
    for j in journeys:
        if not j.get("steps"):
            raise ValidationError(f"journeys: {j['id']} has no steps")
    kinds = {j["path_type"] for j in journeys}
    missing = {"happy", "unhappy"} - kinds
    if missing:
        raise ValidationError(f"journeys: no {', '.join(sorted(missing))} path designed; both a happy and an unhappy path are required")


def check_service_blueprint(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("service-blueprint", doc)
    _no_placeholders(doc, "service-blueprint")
    lanes = doc["lanes"]
    if not lanes:
        raise ValidationError("service-blueprint: no lanes")
    _, jr = _sibling_artifact(dossier, "journeys", "service-blueprint")
    journey_ids = {j["id"] for j in (jr.get("journeys") or [])}
    covered: dict[str, Any] = {}
    for lane in lanes:
        jid = lane["journey"]
        if jid in covered:
            raise ValidationError(f"service-blueprint: journey {jid} has more than one lane")
        covered[jid] = lane
        if not lane.get("support_actions"):
            raise ValidationError(f"service-blueprint: lane for {jid} defines no support actions; support operations must be defined")
    dangling = sorted(set(covered) - journey_ids)
    if dangling:
        raise ValidationError(f"service-blueprint: lane(s) for journey(s) absent from the journeys artifact: {', '.join(dangling)}")
    uncovered = sorted(journey_ids - set(covered))
    if uncovered:
        raise ValidationError(f"service-blueprint: uncovered journey(s) with no lane: {', '.join(uncovered)}")


def check_accessibility(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("accessibility", doc)
    _no_placeholders(doc, "accessibility")
    if not (doc.get("standard") or "").strip():
        raise ValidationError("accessibility: no standard declared")
    criteria = doc["criteria"]
    if not criteria:
        raise ValidationError("accessibility: no criteria; accessibility is not addressed by an empty list")
    ids = [c["id"] for c in criteria]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"accessibility: duplicate criterion id(s): {', '.join(dupes)}")
    for c in criteria:
        if c["status"] == "not_applicable" and not (c.get("rationale") or "").strip():
            raise ValidationError(f"accessibility: {c['id']} is not_applicable without a rationale")


def check_user_validation(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("user-validation", doc)
    _no_placeholders(doc, "user-validation")
    if evidence["producer"].get("type") != "human":
        raise ValidationError("user-validation must be produced by a human; validation with users is a human activity")
    participants = doc["participants"]
    if isinstance(participants, bool) or not isinstance(participants, (int, float)) or participants < 1:
        raise ValidationError(f"user-validation: participants must be a positive number; got {participants!r}; a design is not validated with zero users")
    findings = doc["findings"]
    if not findings:
        raise ValidationError("user-validation: no findings recorded")
    ids = [f["id"] for f in findings]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"user-validation: duplicate finding id(s): {', '.join(dupes)}")
    for f in findings:
        if f["severity"] in {"major", "critical"} and not (f.get("resolution") or "").strip():
            raise ValidationError(f"user-validation: {f['id']} is {f['severity']} but carries no resolution; an unresolved major finding means the design is not validated")


# ---- G04 evidence contract: architecture DESIGN semantics on the frozen badf-architecture contract (BADF-WP-0044, #76) ----
def _unique_ids(items: list, key: str, label: str) -> set:
    ids = [it[key] for it in items]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValidationError(f"{label}: duplicate id(s): {', '.join(dupes)}")
    return set(ids)


def check_architecture(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("architecture", doc)
    _no_placeholders(doc, "architecture")
    boundary_ids = _unique_ids(doc["boundaries"], "id", "architecture boundaries")
    element_ids = _unique_ids(doc["elements"], "id", "architecture elements")
    element_boundary = {e["id"]: e["boundary"] for e in doc["elements"]}
    for e in doc["elements"]:
        if e["boundary"] not in boundary_ids:
            raise ValidationError(f"architecture: element {e['id']} is outside every declared boundary ({e['boundary']} is not a declared boundary)")
    interface_ids = set()
    for i in doc.get("interfaces") or []:
        interface_ids.add(i["id"])
        if i["provider"] not in element_ids:
            raise ValidationError(f"architecture: interface {i['id']} is provided by unknown element {i['provider']}")
    for idx, r in enumerate(doc["relationships"]):
        where = f"relationship[{idx}] {r['from']}->{r['to']}"
        if not (r.get("intent") or "").strip():
            raise ValidationError(f"architecture: {where} has no intent; a bare A->B is not an architecture relationship")
        if r["from"] not in element_ids or r["to"] not in element_ids:
            raise ValidationError(f"architecture: {where} references an unknown element")
        if element_boundary[r["from"]] != element_boundary[r["to"]]:
            via = r.get("via_interface")
            if not via or via not in interface_ids:
                raise ValidationError(f"architecture: {where} crosses a boundary but not through a declared interface")
    trust_ids = {t["id"] for t in (doc.get("trust_boundaries") or [])}  # noqa: F841 (declared universe; reserved for ASSURE)
    for df in doc.get("data_flows") or []:
        if df["source"] not in element_ids or df["destination"] not in element_ids:
            raise ValidationError(f"architecture: data flow {df['id']} references an unknown element")
        if df["trust_boundary_crossing"] and not (df.get("data_classification") or "").strip():
            raise ValidationError(f"architecture: data flow {df['id']} crosses a trust boundary with no data classification")
    fit_ids = set()
    for f in doc["fitness_obligations"]:
        fit_ids.add(f["id"])
        if not (f.get("property") or "").strip() or not (f.get("scope") or "").strip():
            raise ValidationError(f"architecture: fitness obligation {f['id']} has no measurable property or no scope")
    for a in doc["nfr_allocations"]:
        disp = a["disposition"]
        if disp == "ALLOCATED":
            if a.get("element") not in element_ids or not (a.get("mechanism") or "").strip() or a.get("fitness_obligation") not in fit_ids:
                raise ValidationError(f"architecture: NFR allocation for {a['nfr']} is ALLOCATED but has no valid element, mechanism, and fitness obligation")
        elif not (a.get("reason") or "").strip():
            raise ValidationError(f"architecture: NFR allocation for {a['nfr']} is {disp} but carries no reason")
    for v in doc.get("c4_views") or []:
        unknown = sorted(set(v["elements"]) - element_ids)
        if unknown:
            raise ValidationError(f"architecture: C4 {v['level']} view names element(s) absent from the baseline: {', '.join(unknown)}")


def check_adr(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("adr", doc)
    _no_placeholders(doc, "adr")
    records = doc["records"]
    if not records:
        raise ValidationError("adr: no records")
    _unique_ids(records, "id", "adr")
    _, arch = _sibling_artifact(dossier, "architecture", "adr")
    element_ids = {e["id"] for e in (arch.get("elements") or [])}
    req_universe = set(arch.get("upstream_requirements") or [])
    nfr_universe = {a["nfr"] for a in (arch.get("nfr_allocations") or [])}
    for adr in records:
        if not (adr.get("affected_elements") or []):
            raise ValidationError(f"adr: {adr['id']} affects no architecture element")
        if not (adr.get("decision_drivers") or []):
            raise ValidationError(f"adr: {adr['id']} has no decision driver")
        unknown_el = sorted(set(adr["affected_elements"]) - element_ids)
        if unknown_el:
            raise ValidationError(f"adr: {adr['id']} affects element(s) absent from the baseline: {', '.join(unknown_el)}")
        unknown_req = sorted(set(adr.get("requirement_refs") or []) - req_universe)
        if unknown_req:
            raise ValidationError(f"adr: {adr['id']} references unknown requirement(s): {', '.join(unknown_req)}")
        unknown_nfr = sorted(set(adr.get("nfr_refs") or []) - nfr_universe)
        if unknown_nfr:
            raise ValidationError(f"adr: {adr['id']} references NFR(s) absent from the baseline: {', '.join(unknown_nfr)}")


def check_data_model(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("data-model", doc)
    _no_placeholders(doc, "data-model")
    entities = doc["entities"]
    if not entities:
        raise ValidationError("data-model: no entities")
    _unique_ids(entities, "id", "data-model")
    _, arch = _sibling_artifact(dossier, "architecture", "data-model")
    boundary_ids = {b["id"] for b in (arch.get("boundaries") or [])}
    for ent in entities:
        if ent["owner_boundary"] not in boundary_ids:
            raise ValidationError(f"data-model: entity {ent['id']} owner boundary {ent['owner_boundary']} is not a declared architecture boundary")


def check_api_contract(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("api-contract", doc)
    _no_placeholders(doc, "api-contract")
    apis = doc["apis"]
    if not apis:
        raise ValidationError("api-contract: no apis")
    _unique_ids(apis, "id", "api-contract")
    _, arch = _sibling_artifact(dossier, "architecture", "api-contract")
    interface_ids = {i["id"] for i in (arch.get("interfaces") or [])}
    for api in apis:
        if api["interface"] not in interface_ids:
            raise ValidationError(f"api-contract: {api['id']} declares interface {api['interface']} absent from the architecture baseline")


def check_operability_design(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("operability-design", doc)
    _no_placeholders(doc, "operability-design")
    failure_modes = doc["failure_modes"]
    if not failure_modes:
        raise ValidationError("operability-design: no failure modes; architecture that explains only the happy path is incomplete")
    if not (doc.get("observability") or []):
        raise ValidationError("operability-design: no observability seams declared")
    _unique_ids(failure_modes, "id", "operability-design")
    _, arch = _sibling_artifact(dossier, "architecture", "operability-design")
    element_ids = {e["id"] for e in (arch.get("elements") or [])}
    for fm in failure_modes:
        if not (fm.get("recovery") or "").strip():
            raise ValidationError(f"operability-design: failure mode {fm['id']} declares no recovery")
        if fm["element"] not in element_ids:
            raise ValidationError(f"operability-design: failure mode {fm['id']} names element {fm['element']} absent from the baseline")


# ---- G05 evidence contract: security, privacy and AI safety (BADF-WP-0060, #109-successor) ----
def check_threat_model(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("threat-model", doc)
    _no_placeholders(doc, "threat-model")
    threats = doc["threats"]
    if not threats:
        raise ValidationError("threat-model: no threats; a threat model of nothing controls nothing")
    _unique_ids(threats, "id", "threat-model")
    for t in threats:
        if not (t.get("mitigation") or "").strip():
            raise ValidationError(f"threat-model: threat {t['id']} has no mitigation; threats and abuse cases must be controlled")


def check_privacy_assessment(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("privacy-assessment", doc)
    _no_placeholders(doc, "privacy-assessment")
    cats = doc["data_categories"]
    if not cats:
        raise ValidationError("privacy-assessment: no data categories")
    _unique_ids(cats, "id", "privacy-assessment")
    for c in cats:
        if not (c.get("lawful_basis") or "").strip() or not (c.get("handling") or "").strip():
            raise ValidationError(f"privacy-assessment: data category {c['id']} has no lawful basis or handling; privacy obligations must be addressed")


def check_supply_chain_plan(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("supply-chain-plan", doc)
    _no_placeholders(doc, "supply-chain-plan")
    if not doc["secret_controls"]:
        raise ValidationError("supply-chain-plan: no secret controls declared; dependency and secret controls must be planned")
    _unique_ids(doc["dependencies"], "id", "supply-chain-plan")
    for d in doc["dependencies"]:
        if not (d.get("control") or "").strip():
            raise ValidationError(f"supply-chain-plan: dependency {d['id']} has no control; each dependency must be controlled")


def check_security_approval(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("security-approval", doc)
    _no_placeholders(doc, "security-approval")
    producer = evidence["producer"]
    if producer.get("type") != "human":
        raise ValidationError("security-approval must be produced by a human security_authority; a non-human producer cannot own residual risk")
    if producer.get("id") != doc["approved_by"]["principal"]:
        raise ValidationError(f"security-approval producer {producer.get('id')!r} is not approved_by.principal {doc['approved_by']['principal']!r}")
    if not (doc.get("residual_risk_owner") or "").strip():
        raise ValidationError("security-approval: no residual_risk_owner; residual risk must be owned")
    tm_path, tm = _sibling_artifact(dossier, "threat-model", "security-approval")
    if doc["threat_model_digest"] != sha256(tm_path):
        raise ValidationError("security-approval: threat_model_digest does not match the threat-model artifact in this dossier (the threat model changed after approval, or the approval is for other bytes)")


# ---- G06 evidence contract: implementation planning -- work breakdown, test plan, release plan, rollback plan (BADF-WP-0067, #125) ----
def check_work_breakdown(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("work-breakdown", doc)
    _no_placeholders(doc, "work-breakdown")
    tasks = doc["tasks"]
    if not tasks:
        raise ValidationError("work-breakdown: no tasks; an empty breakdown bounds no work (G06: work packages bounded)")
    _unique_ids(tasks, "id", "work-breakdown")
    ids = {t["id"] for t in tasks}
    for t in tasks:
        if not (t.get("description") or "").strip():
            raise ValidationError(f"work-breakdown: task {t['id']} has no description; a bounded task states what it delivers")
        for dep in t.get("depends_on") or []:
            if dep not in ids:
                raise ValidationError(f"work-breakdown: task {t['id']} depends on {dep} which the breakdown does not carry; the composition order must resolve")
    # composition order is real only if a build order exists -- the dependency graph is acyclic.
    graph = {t["id"]: list(t.get("depends_on") or []) for t in tasks}
    color = {i: 0 for i in graph}  # 0=unvisited 1=on-stack 2=done

    def acyclic(n: str) -> bool:
        color[n] = 1
        for m in graph[n]:
            if color[m] == 1 or (color[m] == 0 and not acyclic(m)):
                return False
        color[n] = 2
        return True
    for i in graph:
        if color[i] == 0 and not acyclic(i):
            raise ValidationError("work-breakdown: the task dependency graph has a cycle; no composition order can be defined (G06: composition order defined)")

    # ---- WP-IMP-C: the deterministic planning controls the schema walker cannot do (#171). Each fires
    # only when its optional field is present, so a minimal id/description/depends_on task is unaffected.
    matrix = (load_json(ROOT / "badf/authority-matrix.json").get("change_classes") or {})
    for t in tasks:
        tid = t["id"]
        # IMP-C1 (IMP-I07): authority is derived from change_class and cannot be reduced below the matrix.
        if "change_class" in t and "authority_requirement" in t:
            need = set((matrix.get(t["change_class"]) or {}).get("required_roles") or [])
            have = set((t["authority_requirement"] or {}).get("required_roles") or [])
            missing = need - have
            if missing:
                raise ValidationError(f"work-breakdown: task {tid} is {t['change_class']} but its authority_requirement omits {sorted(missing)}; the plan cannot reduce the authority the change class requires (IMP-C1 / IMP-I07)")
        # IMP-C2 (IMP-I09): every acceptance claim has a verification obligation.
        if t.get("acceptance"):
            claimed = {(o or {}).get("claim") for o in (t.get("test_obligations") or [])}
            for ac in t["acceptance"]:
                if ac not in claimed:
                    raise ValidationError(f"work-breakdown: task {tid} acceptance {ac!r} has no test_obligation claiming it; every acceptance claim carries a verification obligation (IMP-C2 / IMP-I09)")
        # IMP-C3 (IMP-I11): a declared execution budget is bounded -- max_attempts a positive integer
        # (a code control: the schema walker does not type-check non-object types, #171).
        if "execution_budget" in t:
            ma = (t["execution_budget"] or {}).get("max_attempts")
            if not isinstance(ma, int) or isinstance(ma, bool) or ma < 1:
                raise ValidationError(f"work-breakdown: task {tid} execution_budget.max_attempts must be a positive integer (got {ma!r}); autonomous execution is bounded (IMP-C3 / IMP-I11)")
        # IMP-C4 (IMP-I12): a declared stop contract names at least one condition.
        if "stop_conditions" in t and not (t.get("stop_conditions") or []):
            raise ValidationError(f"work-breakdown: task {tid} declares stop_conditions but names none; an empty stop contract stops nothing (IMP-C4 / IMP-I12)")
        # IMP-C5 (IMP-I06): composition_after resolves to real tasks (landing order, separate from blocking).
        for dep in t.get("composition_after") or []:
            if dep not in ids:
                raise ValidationError(f"work-breakdown: task {tid} composition_after {dep} which the breakdown does not carry; the landing order must resolve (IMP-C5 / IMP-I06)")
    # IMP-C5 (cont.): the composition-order graph is itself acyclic (landing order must be buildable).
    cgraph = {t["id"]: list(t.get("composition_after") or []) for t in tasks}
    ccolor = {i: 0 for i in cgraph}

    def cacyclic(n: str) -> bool:
        ccolor[n] = 1
        for m in cgraph[n]:
            if ccolor[m] == 1 or (ccolor[m] == 0 and not cacyclic(m)):
                return False
        ccolor[n] = 2
        return True
    for i in cgraph:
        if ccolor[i] == 0 and not cacyclic(i):
            raise ValidationError("work-breakdown: the composition_after graph has a cycle; no landing order can be defined (IMP-C5 / IMP-I06)")


def check_test_plan(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("test-plan", doc)
    _no_placeholders(doc, "test-plan")
    planned = doc["planned_tests"]
    if not planned:
        raise ValidationError("test-plan: no planned tests; 'tests first' cannot be established from an empty plan")
    _unique_ids(planned, "id", "test-plan")
    for pt in planned:
        if not (pt.get("verifies") or "").strip():
            raise ValidationError(f"test-plan: planned test {pt['id']} names nothing it verifies; a planned test targets a requirement or task")


def check_release_plan(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("release-plan", doc)
    _no_placeholders(doc, "release-plan")
    if not [e for e in doc["environments"] if (e or "").strip()]:
        raise ValidationError("release-plan: no environments; environments and resources must be ready (G06)")
    steps = doc["steps"]
    if not steps:
        raise ValidationError("release-plan: no steps; a release with no steps is not a plan")
    _unique_ids(steps, "id", "release-plan")
    for s in steps:
        if not (s.get("description") or "").strip():
            raise ValidationError(f"release-plan: step {s['id']} has no description; each release step states what it does")


def check_rollback_plan(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    doc = load_json(artifact)
    check_schema("rollback-plan", doc)
    _no_placeholders(doc, "rollback-plan")
    if not (doc.get("method") or "").strip():
        raise ValidationError("rollback-plan: no method; rollback must be executable, not aspirational (G06: rollback executable)")
    steps = doc["steps"]
    if not steps:
        raise ValidationError("rollback-plan: no steps; an executable rollback has concrete steps")
    _unique_ids(steps, "id", "rollback-plan")
    for s in steps:
        if not (s.get("description") or "").strip():
            raise ValidationError(f"rollback-plan: step {s['id']} has no description; each rollback step states what it does")
    if not [c for c in doc["stop_conditions"] if (c or "").strip()]:
        raise ValidationError("rollback-plan: no stop_conditions; a rollback plan states when to stop (G06: stop conditions executable)")



# ---- badf-build BLD-B (BADF-WP-0098, #191): typed G07 evidence bindings ----
# The self-dossier is the canonical producer of G07 evidence for BADF's own work (BLD-I18);
# these helpers make its four objects EXACT (BLD-I16) and judgeable (BLD-I04/I07/I09).

def _surface_match(path: str, pattern: str) -> bool:
    """Does a changed path fall inside one declared expected-surface pattern?
    `dir/**` is a prefix; other globs are fnmatch (where `*` may cross `/`)."""
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return path == pattern or fnmatch.fnmatchcase(path, pattern.replace("**", "*"))


def _parse_unittest_log(text: str) -> tuple[str, int, int]:
    """(result, tests_run, failures) from a unittest transcript: `Ran N tests` and OK/FAILED."""
    m = re.search(r"^Ran (\d+) tests?", text, re.M)
    ran = int(m.group(1)) if m else 0
    fm = re.search(r"^FAILED \((.*)\)", text, re.M)
    if fm:
        counts = [int(x) for x in re.findall(r"=(\d+)", fm.group(1))]
        return "FAIL", ran, (sum(counts) if counts else 1)
    if re.search(r"^OK", text, re.M):
        return "PASS", ran, 0
    return "NOT_RUN", ran, 0


def _diff_paths(text: str) -> list[str]:
    return sorted({m.group(1) for m in re.finditer(r"^diff --git a/(\S+) b/", text, re.M)})



# ---- badf-build BLD-C (BADF-WP-0099, #194): deterministic G07 controls ----
# Each control fires only on the field that declares it (undeclared -> BLD-B behaviour), is typed
# in code (never walker-trusted), and refuses with the invariant it enforces. No second gate.

DELEGATION_PROHIBITED = ("push", "merge", "release", "credential-use")


def _wp_record(wp_id: str) -> dict[str, Any] | None:
    path = ROOT / "work" / wp_id / "work-package.json"
    return load_json(path) if path.is_file() else None


def _require_authorized_demand(wp: dict[str, Any], wp_id: str) -> None:
    """C1 (BLD-I03): authority before mutation -- the work package's demand must exist, be
    AUTHORIZED, and be authorized by a human. Absent is not validated."""
    demand = str(wp.get("demand") or "")
    path = ROOT / "badf" / "demands" / f"{demand}.json"
    if not demand or not path.is_file():
        raise ValidationError(f"{wp_id}: demand {demand or '(none)'} has no record at badf/demands/; authority cannot be validated before mutation (BLD-I03 / C1)")
    rec = load_json(path)
    if rec.get("status") != "AUTHORIZED":
        raise ValidationError(f"{wp_id}: demand {demand} is {rec.get('status')!r}, not AUTHORIZED (BLD-I03 / C1)")
    who = rec.get("authorized_by") or {}
    if not isinstance(who, dict) or who.get("principal_type") != "human":
        raise ValidationError(f"{wp_id}: demand {demand} is authorized by principal_type {who.get('principal_type') if isinstance(who, dict) else who!r}; a human must authorize (BLD-I03 / C1)")


def _build_events(wp_dir: Path) -> list[dict[str, Any]]:
    path = wp_dir / BUILD_LEDGER
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _check_build_budget_and_stop(wp_dir: Path, wp: dict[str, Any], wp_id: str) -> None:
    """C6 (BLD-I11..I13): the ledger is read for REFUSAL only, never to grant. RETRY events may
    not exceed execution_budget.max_attempts; a recorded STOP dominates."""
    events = _build_events(wp_dir)
    stops = [e for e in events if e.get("step") == "STOP"]
    if stops:
        s = stops[-1]
        raise ValidationError(f"{wp_id}: the build ledger records STOP ({s.get('outcome')}: {s.get('note', '')}); a stopped build hands off BLOCKED -- it is not packaged or passed (BLD-I13 / C6)")
    budget = wp.get("execution_budget")
    if isinstance(budget, dict) and isinstance(budget.get("max_attempts"), int) and not isinstance(budget.get("max_attempts"), bool):
        retries = sum(1 for e in events if e.get("step") == "RETRY")
        if retries > budget["max_attempts"]:
            raise ValidationError(f"{wp_id}: {retries} RETRY events exceed execution_budget.max_attempts {budget['max_attempts']}; exhaustion yields BLOCKED, never an autonomous extension (BLD-I12 / C6)")


def _check_delegations(wp_dir: Path, wp: dict[str, Any], wp_id: str) -> None:
    """C7 (BLD-I10): every delegation in build/session.json is a strict subset of the work
    package -- paths inside the declared surface, the prohibited set intact, no integration tools."""
    path = wp_dir / "build" / "session.json"
    if not path.is_file():
        return
    delegations = (load_json(path) or {}).get("delegations") or []
    if not delegations:
        return
    surface = [str(x) for x in ((wp.get("expected_surfaces") or {}).get("files") or [])]
    for d in delegations:
        if not isinstance(d, dict):
            raise ValidationError(f"{wp_id}: a delegation is not a mapping (C7)")
        name = str(d.get("task") or "?")
        _seat = _declared_seat(d)
        if _seat is None and _seat_ratchet_applies(wp_id):
            raise ValidationError(f"{wp_id}: delegation {name} names no seat -- mandatory at and above the threshold {WP_NAMESPACE}0130 (AET-B-1 / #287)")
        if _seat is not None and _seat not in _rostered_seats():
            raise ValidationError(f"{wp_id}: delegation {name} declares seat {_seat!r}, which is not in badf/seats.json (declaration-consistency; identity verification lands with #261)")
        if not surface:
            raise ValidationError(f"{wp_id}: delegation {name} declared but the work package declares no expected_surfaces; a subset of nothing cannot be granted (BLD-I10 / C7)")
        for ap in d.get("allowed_paths") or []:
            probe = ap[:-3] + "/__probe__" if str(ap).endswith("/**") else str(ap)
            if not any(_surface_match(probe, pat) for pat in surface):
                raise ValidationError(f"{wp_id}: delegation {name} allows path {ap!r} outside the work package's expected_surfaces {surface} (BLD-I10 / C7)")
        missing = sorted(set(DELEGATION_PROHIBITED) - set(d.get("prohibited") or []))
        if missing:
            raise ValidationError(f"{wp_id}: delegation {name} leaves {missing} out of its prohibited set; the prohibited set {list(DELEGATION_PROHIBITED)} stays intact -- delegation can only narrow authority (BLD-I10 / C7)")
        bad_tools = sorted(set(d.get("allowed_tools") or []) & set(DELEGATION_PROHIBITED + ("git-push", "gh", "deploy")))
        if bad_tools:
            raise ValidationError(f"{wp_id}: delegation {name} grants integration tools {bad_tools} (BLD-I10 / BLD-I17 / C7)")


def check_g07_binding(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    """EVIDENCE_RULES entry for the four G07 types: a typed `binding`, when present, must
    conform to schemas/<type>.schema.json AND agree with the artifact it binds -- the gate
    opens the artifact; a binding is not evidence of itself. Generic objects (no binding)
    stay admissible: the typed form is additive (BLD-B)."""
    if "binding" not in evidence:
        return
    kind = evidence["evidence_type"]
    check_schema(kind, evidence)
    b = evidence["binding"]
    label = f"evidence {evidence.get('id', kind)}"
    wp_id = str(evidence.get("work_package_id") or "")
    wp = _wp_record(wp_id) if wp_id else None
    wp_dir = ROOT / "work" / wp_id
    if kind == "source-change":
        paths = _diff_paths(artifact.read_text(encoding="utf-8", errors="replace"))
        if sorted(b["changed_paths"]) != paths:
            raise ValidationError(f"{label}: binding.changed_paths {sorted(b['changed_paths'])} do not equal the paths in the diff artifact {paths}")
        if b["change_digest"] != evidence["digest"]:
            raise ValidationError(f"{label}: binding.change_digest does not equal the artifact digest")
        if wp is not None:
            # C2 (BLD-I02): the exact baseline -- the binding's base is the work package's base, and
            # the content tree agrees with the composition claim when one exists.
            base_rev = str(((wp.get("external_target") or {}).get("base_revision")) or "")
            resolved = _git("rev-parse", base_rev) if base_rev else None
            if resolved and b["base_sha"] != resolved:
                raise ValidationError(f"{label}: binding.base_sha {b['base_sha'][:12]} does not equal the work package's base_revision {resolved[:12]} (BLD-I02 / C2)")
            record = wp_dir / "evidence" / "G07" / "composition-record.json"
            if record.is_file():
                rec = load_json(record)
                if rec.get("expected_content_tree") and b["content_tree"] != rec["expected_content_tree"]:
                    raise ValidationError(f"{label}: binding.content_tree {b['content_tree'][:12]} does not equal the composition record's expected_content_tree {str(rec['expected_content_tree'])[:12]} (BLD-I02 / C2)")
                if rec.get("target_base_sha") and b["base_sha"] != rec["target_base_sha"]:
                    raise ValidationError(f"{label}: binding.base_sha does not equal the composition record's target_base_sha (BLD-I02 / C2)")
            # C3 (BLD-I04): a PASS with paths outside the declared surface is refused unless a
            # discovery allowance covers each of them; a request keeps its C-2 condition instead.
            if dossier.get("disposition") == "PASS" and b.get("unexpected_paths"):
                allowance = [str(x) for x in ((wp.get("expected_surfaces") or {}).get("discovery_allowance") or [])]
                uncovered = [x for x in b["unexpected_paths"] if not any(_surface_match(x, a) for a in allowance)]
                if uncovered:
                    raise ValidationError(f"{label}: PASS claimed with changed paths outside expected_surfaces and no discovery_allowance covering {uncovered}; unexpected scope is refused or re-authorized, never absorbed (BLD-I04 / C3)")
            # C3 mirror (BLD-I04 / GOV-0102): containment is two-sided -- a PASS may not carry a
            # declared files pattern that matched no changed path. files is must-touch (it is also
            # the C7 delegation ceiling, BLD-I10); discovery_allowance is may-touch and exempt by
            # construction. Recomputed from the record and the equality-bound changed_paths, never
            # trusted from storage -- there is nothing for a forged binding to omit.
            if dossier.get("disposition") == "PASS":
                files_pats = [str(x) for x in ((wp.get("expected_surfaces") or {}).get("files") or [])]
                unmatched = [p for p in files_pats if not any(_surface_match(n, p) for n in (b.get("changed_paths") or []))]
                if unmatched:
                    raise ValidationError(f"{label}: PASS claimed with declared expected_surfaces matching no changed path: {unmatched}; an over-broad declaration widens the C7 delegation ceiling and is pruned or exercised, never carried (BLD-I04 / C3 / GOV-0102)")
    elif kind == "unit-test":
        if b["result"] != "NOT_RUN":
            result, ran, failures = _parse_unittest_log(artifact.read_text(encoding="utf-8", errors="replace"))
            if (result, ran, failures) != (b["result"], b["tests_run"], b["failures"]):
                raise ValidationError(f"{label}: binding ({b['result']}, {b['tests_run']}, {b['failures']}) does not equal the log ({result}, {ran}, {failures})")
        if wp is not None:
            # C4 (BLD-I07/I08): declared unit obligations require observed red, or an explicit exception.
            if any(isinstance(o, dict) and o.get("level") == "unit" for o in (wp.get("test_obligations") or [])):
                tdd = b.get("tdd")
                excepted = isinstance(tdd, dict) and tdd.get("applies") is False and str(tdd.get("reason") or "").strip()
                if not excepted and not all((o.get("red") or {}).get("observed") for o in b.get("obligations") or []):
                    raise ValidationError(f"{label}: the work package declares unit test obligations but the binding carries no observed red phase and no tdd exception with a reason (BLD-I07 / BLD-I08 / C4)")
        # C5 (BLD-I09): a PASS on a passing dossier needs the fresh composed-tree run -- the composition record.
        if dossier.get("disposition") == "PASS" and b["result"] == "PASS" and not (wp_dir / "evidence" / "G07" / "composition-record.json").is_file():
            raise ValidationError(f"{label}: unit-test PASS claimed on a passing dossier without a composition record for {wp_id}; the composed-tree run is the fresh verification (BLD-I09 / C5)")
    elif kind == "build":
        m = re.search(r"-> exit (\d+)", artifact.read_text(encoding="utf-8", errors="replace"))
        if not m:
            raise ValidationError(f"{label}: the build artifact carries no `-> exit N` line, so binding.exit_code {b['exit_code']} cannot be verified against it (BLD-I16: build evidence is exact, never best-effort)")
        if int(m.group(1)) != b["exit_code"]:
            raise ValidationError(f"{label}: binding.exit_code {b['exit_code']} does not equal the recorded exit {m.group(1)}")


EVIDENCE_RULES = {"prd": check_prd, "acceptance-criteria": check_acceptance_criteria, "product-approval": check_product_approval,
                  "requirements": check_requirements, "nfr": check_nfr, "traceability": check_traceability,
                  "definition-of-ready": check_definition_of_ready,
                  "journeys": check_journeys, "service-blueprint": check_service_blueprint,
                  "accessibility": check_accessibility, "user-validation": check_user_validation,
                  "architecture": check_architecture, "adr": check_adr, "data-model": check_data_model,
                  "api-contract": check_api_contract, "operability-design": check_operability_design,
                  "threat-model": check_threat_model, "privacy-assessment": check_privacy_assessment,
                  "supply-chain-plan": check_supply_chain_plan, "security-approval": check_security_approval,
                  "work-breakdown": check_work_breakdown, "test-plan": check_test_plan,
                  "release-plan": check_release_plan, "rollback-plan": check_rollback_plan}

EVIDENCE_RULES.update({t: check_g07_binding for t in ("source-change", "build", "unit-test", "documentation")})


CONTRACT_RESULT_OUTCOME = {"CONFORMANT": "PASS", "NONCONFORMANT": "FAIL", "INDETERMINATE": "BLOCKED", "NOT_APPLICABLE": "NOT_APPLICABLE"}
BLOCKING_SEVERITIES = {"MAJOR", "CRITICAL"}


def check_g08_binding(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    """EVIDENCE_RULES entry for the four G08 types (badf-engineering-verification VER-B): a typed
    `binding`, when present, must conform to schemas/<type>.schema.json AND agree with the artifact
    the gate opens. Generic objects (no binding) stay admissible -- the typed form is additive, so
    WP-2026-0010's historical G08 dossier is untouched. The Reviewer plane: a review is findings +
    non-coverage + completion, never a bare PASS (VER-I10/I11), and its verdict cannot contradict
    its own findings. The Verifier plane: an observation is produced by a runtime, never by an
    agent (VER-I08); a contract result serialises onto the evidence outcome and INDETERMINATE is
    never a pass (VER-I14); a composed observation binds a CURRENT, reproduced composition
    (VER-I01/I15); counts and exit codes are read from the artifact, not from the binding."""
    if "binding" not in evidence:
        return
    kind = evidence["evidence_type"]
    check_schema(kind, evidence)
    b = evidence["binding"]
    label = f"evidence {evidence.get('id', kind)}"
    if kind == "independent-review":
        if not b["findings"] and not b["non_coverage"] and not b["completion"].get("comprehensive_coverage_permitted_by"):
            raise ValidationError(f"{label}: a review with no findings and no non_coverage claims comprehensive coverage without naming the contract that permits it (VER-I10 / VER-I11: no findings is not correctness)")
        open_blocking = [f["finding_id"] for f in b["findings"] if f["status"] == "OPEN" and f["severity"] in BLOCKING_SEVERITIES]
        if b["verdict"] == "APPROVE" and open_blocking:
            raise ValidationError(f"{label}: verdict APPROVE contradicts OPEN blocking finding(s) {', '.join(open_blocking)}; a verdict cannot contradict its own findings")
        return
    if evidence["producer"]["type"] == "agent":
        raise ValidationError(f"{label}: a typed {kind} observation carries producer.type 'agent'; a claimed result is not an observation (VER-I08)")
    text = artifact.read_text(encoding="utf-8", errors="replace")
    if kind == "contract-test":
        want = CONTRACT_RESULT_OUTCOME[b["result"]]
        if evidence["outcome"] != want:
            raise ValidationError(f"{label}: contract result {b['result']} serialises as outcome {want}, not {evidence['outcome']} (VER-I14: INDETERMINATE is never a pass)")
        return
    if kind == "integration-test":
        ex = b["execution"]
        if re.search(r"^Ran \d+ tests?", text, re.M):
            result, ran, failures = _parse_unittest_log(text)
            if (ran, failures) != (ex["tests"]["total"], ex["tests"]["failed"]) or (evidence["outcome"] == "PASS" and result != "PASS"):
                raise ValidationError(f"{label}: binding tests ({ex['tests']['total']} run, {ex['tests']['failed']} failed) do not equal the log (Ran {ran}, {failures} failed, {result})")
            return
        m = re.search(r"(?:^|\s)exit=(\d+)|-> exit (\d+)", text)
        if not m:
            raise ValidationError(f"{label}: the artifact carries neither a `Ran N tests` transcript nor an `exit=N` line, so binding.execution.exit_code {ex['exit_code']} cannot be verified against it (VER-I09: provenance is read from the artifact)")
        got = int(m.group(1) or m.group(2))
        if got != ex["exit_code"]:
            raise ValidationError(f"{label}: binding.execution.exit_code {ex['exit_code']} does not equal the recorded exit {got}")
        return
    if kind == "composed-tree-test":
        c = b["composition"]
        if b["staleness"] != "CURRENT":
            raise ValidationError(f"{label}: staleness {b['staleness']}; a composed observation binds a CURRENT composition or it is stale evidence (VER-I01)")
        if c["equal"] is not True or c["recorded_expected_content_tree"] != c["recomputed_content_tree"]:
            raise ValidationError(f"{label}: composition.equal must be true with recorded == recomputed content tree ({c['recorded_expected_content_tree'][:12]} vs {c['recomputed_content_tree'][:12]}); a composition that did not reproduce is not verified (VER-I15)")
        tree = c["recomputed_content_tree"]
        if tree not in text and tree[:7] not in text:
            raise ValidationError(f"{label}: the recomputed content tree {tree[:12]} does not appear in the artifact; a binding is not evidence of itself")


EVIDENCE_RULES.update({t: check_g08_binding for t in ("independent-review", "integration-test", "contract-test", "composed-tree-test")})


G09_TYPES = ("quality-validation", "security-validation", "performance-test", "resilience-test")


def check_g09_binding(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    """EVIDENCE_RULES entry for the four G09 types (badf-release-validation WP-VAL-B): a typed
    `binding`, when present, must conform to schemas/<type>.schema.json AND honor the VAL
    invariants that are checkable on a single evidence object. Generic objects (no binding)
    stay admissible -- the typed form is additive, exactly as VER-B's G08 rung.

    The walker enforces required/enum/pattern/additionalProperties/type only, so every
    non-emptiness, ordering and cross-field constraint below is a named code control:

      V1  candidate agreement       -- binding.candidate.source_revision == evidence.source_revision
                                       (VAL-I01: one immutable candidate; a binding naming a different
                                       revision than its own envelope is mixed-candidate evidence)
      V2  observation provenance    -- producer.type != 'agent' for a typed observation (VAL-I04/I05)
      V3  oracle outside the agent  -- oracle.evaluated_by.type != 'agent' (VAL-I04: an agent may
                                       attempt a journey; it may not adjudicate its own success)
      V4  runtime approved          -- outcome PASS requires runtime.approved true (VAL-I04:
                                       no validation credit without an APPROVED observed execution)
      V5  non-coverage mandatory    -- binding.non_coverage non-empty (VAL-I15; minItems is inert)
      V6  deviation declared        -- environment NON_PRODUCTION requires non-empty
                                       material_deviations (VAL-I08)
      V7  flake policy              -- failed_observations_retained must be true (VAL-I16:
                                       rerun-until-green cannot erase a failed observation)
      V8  blockers preserved        -- outcome PASS cannot coexist with an OPEN finding of
                                       blocking severity (VAL-I14), any class
      per-class:
      V9  security obligations      -- security_obligations non-empty (an empty obligation set
                                       is a routing decision, not a validation) and residual_risk
                                       acceptance is structurally NOT_ACCEPTED/REFERRED (VAL-I09;
                                       the enum bakes it, mirroring SEC-I12)
      V10 measurement != PASS       -- performance: measurements non-empty; every slo.bound_at
                                       precedes runtime.started_at (VAL-I06/I10: a threshold bound
                                       after the run began was fitted to the result)
      V11 recovery observed         -- resilience: steady_state.observed_before true; abort_conditions
                                       non-empty and each executable; outcome PASS requires
                                       recovery.observed true, non-empty integrity_checks, none FAIL
                                       (VAL-I11/I12: survival during injection is not recovery)
      V12 quality oracle named      -- quality: quality_dimensions non-empty; a dimension with
                                       result PASS names its oracle_locator (VAL-I04 applied to the
                                       class where 'it looked successful' is the failure mode)

    Class substitution (VAL-I13) at the dossier level and cross-class candidate identity are
    WP-VAL-C's dossier controls; here each binding is internally sound. additionalProperties:false
    on every binding already refuses one class's payload in another's slot structurally."""
    if "binding" not in evidence:
        return
    kind = evidence["evidence_type"]
    check_schema(kind, evidence)
    b = evidence["binding"]
    label = f"evidence {evidence.get('id', kind)}"
    # validate_evidence dispatches EVIDENCE_RULES only on outcome PASS, so `passing` is
    # redundant against today's caller. It is kept deliberately: the controls that gate on it
    # (V4, V8, V11-recovery) are the ones whose refusal is only correct for a PASS claim, and
    # an honestly-recorded failure must not be refused if a future caller routes one here.
    # Defensive, not vestigial -- removing it would make the rule caller-dependent.
    passing = evidence["outcome"] == "PASS"

    if b["candidate"]["source_revision"] != evidence["source_revision"]:  # V1
        raise ValidationError(f"{label}: binding.candidate.source_revision {b['candidate']['source_revision']!r} does not equal the evidence source_revision {evidence['source_revision']!r}; mixed-candidate evidence is refused (VAL-I01)")
    if evidence["producer"]["type"] == "agent":  # V2
        raise ValidationError(f"{label}: a typed {kind} observation carries producer.type 'agent'; a claimed result is not an observation (VAL-I04/VAL-I05)")
    if b["oracle"]["evaluated_by"]["type"] == "agent":  # V3
        raise ValidationError(f"{label}: the oracle is evaluated by an agent; the oracle sits outside the agent under validation (VAL-I04)")
    if not b["oracle"]["locator"].strip():  # V3b -- schema minLength is inert in this walker
        raise ValidationError(f"{label}: oracle.locator is empty; an oracle that names nothing cannot be consulted, and an unnameable oracle is not outside the agent (VAL-I04)")
    if passing and b["runtime"]["approved"] is not True:  # V4
        raise ValidationError(f"{label}: outcome PASS on an unapproved runtime; no validation credit without approved observed execution (VAL-I04)")
    if not b["non_coverage"]:  # V5
        raise ValidationError(f"{label}: non_coverage is empty; every validation class names material surfaces it did not establish (VAL-I15)")
    env = b["environment"]
    if env["production_equivalence"] == "NON_PRODUCTION" and not env.get("material_deviations"):  # V6
        raise ValidationError(f"{label}: a NON_PRODUCTION environment declares no material_deviations; staging PASS is not production proven (VAL-I08)")
    if b["flake_policy"]["failed_observations_retained"] is not True:  # V7
        raise ValidationError(f"{label}: flake_policy discards failed observations; rerun-until-green cannot erase a failed validation observation (VAL-I16)")
    open_blocking = [f["finding_id"] for f in b["findings"] if f["status"] == "OPEN" and f["severity"] in ("BLOCKER", "CRITICAL", "MAJOR")]
    if passing and open_blocking:  # V8
        raise ValidationError(f"{label}: outcome PASS coexists with OPEN blocking finding(s) {', '.join(open_blocking)}; normalization cannot erase blocking evidence (VAL-I14)")

    if kind == "security-validation":  # V9
        if not b["security_obligations"]:
            raise ValidationError(f"{label}: security_obligations is empty; an empty obligation set is a routing decision, not a security validation (VAL-I02)")
        # residual_risk acceptance.state is enum-bound to NOT_ACCEPTED/REFERRED_TO_SECURITY_AUTHORITY
        # by the schema (walker enforces enums): VAL-I09 is structural, mirroring SEC-I12.
        return
    if kind == "performance-test":  # V10
        if not b["measurements"]:
            raise ValidationError(f"{label}: measurements is empty; a performance-test with nothing measured cannot render an outcome (VAL-I10)")
        # `format: date-time` is NOT enforced by check_schema, so a validly-typed timestamp
        # in another ISO form ('+00:00' vs 'Z', differing precision) would compare
        # lexicographically and render a silently wrong ordering. parse_time normalises to UTC
        # and refuses malformed input, so the VAL-I06 verdict rests on time, not on spelling.
        started = parse_time(b["runtime"]["started_at"], f"{label}: binding.runtime.started_at")
        for i, m in enumerate(b["measurements"]):
            if parse_time(m["slo"]["bound_at"], f"{label}: measurements[{i}].slo.bound_at") > started:
                raise ValidationError(f"{label}: measurements[{i}].slo.bound_at {m['slo']['bound_at']} is after the run began {started}; thresholds pre-exist outcomes (VAL-I06), a bound fitted to the result is not conformance (VAL-I10)")
        return
    if kind == "resilience-test":  # V11
        if b["steady_state"]["observed_before"] is not True:
            raise ValidationError(f"{label}: steady state was not observed before injection; resilience is hypothesis-driven (VAL-I11)")
        aborts = b["fault"]["abort_conditions"]
        if not aborts:
            raise ValidationError(f"{label}: fault carries no abort_conditions; injection without an executable abort is unbounded blast radius (VAL-I11)")
        dead = [a["condition"] for a in aborts if a["executable"] is not True]
        if dead:
            raise ValidationError(f"{label}: abort condition(s) not executable: {', '.join(dead)}; a non-executable abort is a hope, not a bound (VAL-I11)")
        if passing:
            rec = b["recovery"]
            if rec["observed"] is not True:
                raise ValidationError(f"{label}: outcome PASS without observed recovery; survival during injection is not recovery (VAL-I12)")
            checks = rec["integrity_checks"]
            if not checks:
                raise ValidationError(f"{label}: outcome PASS with no integrity checks; recovery without verified integrity is not established (VAL-I12)")
            failed = [c["check"] for c in checks if c["result"] == "FAIL"]
            if failed:
                raise ValidationError(f"{label}: outcome PASS with failed integrity check(s) {', '.join(failed)} (VAL-I12)")
        return
    if kind == "quality-validation":  # V12
        dims = b["quality_dimensions"]
        if not dims:
            raise ValidationError(f"{label}: quality_dimensions is empty; a quality validation that validated nothing cannot render an outcome (VAL-I02)")
        unoracled = [d["dimension"] for d in dims if d["result"] == "PASS" and not d.get("oracle_locator")]
        if unoracled:
            raise ValidationError(f"{label}: dimension(s) {', '.join(unoracled)} render PASS without an oracle_locator; 'it looked successful' is not an oracle (VAL-I04)")


EVIDENCE_RULES.update({t: check_g09_binding for t in G09_TYPES})


def check_g10_uat_binding(artifact: Path, dossier: dict[str, Any], evidence: dict[str, Any]) -> None:
    """EVIDENCE_RULES entry for the G10 `uat` type (badf-uat WP-UAT-B): a typed `binding`, when
    present, must conform to schemas/uat.schema.json AND honor the UAT invariants that are
    checkable on a single evidence object. Untyped objects stay admissible -- additive, exactly
    as VER-B and VAL-B before it.

    The schema walker enforces required/enum/pattern/additionalProperties/type only, so every
    cross-field and non-emptiness constraint below is a named code control:

      U2  scenario provenance    -- every observation names a scenario that exists in this
                                    binding (UAT-I01: an unanchored observation is not evidence)
      U3  classified failures    -- every FAIL/BLOCKED observation has a defect of its own
                                    (UAT-I11: a failure without a class is noise)
      U4  criticality not hidden -- a critical scenario that is FAIL or NOT_EXECUTED forbids
                                    RECOMMEND_ACCEPT (UAT-I13: an aggregate cannot bury it)
      U5  layer separation       -- an acceptance, when present, binds THIS binding's candidate
                                    digest and carries a human principal (UAT-I15/I16)
      U6  one obs per scenario   -- duplicate observations are ambiguous input, refused rather
                                    than resolved by an invented rule (UAT-I09/I17; BADF-QA #264)

    The recommendation vocabulary IS closed by the schema: check_schema implements `enum`, so
    an acceptance verdict cannot be written into `recommendation` at all.

    `const` IS NOT. check_schema's walker implements required / additionalProperties / type /
    enum / pattern / items and has NO const branch, so every `"const"` in schemas/uat.schema.json
    is decorative -- `principal_type: {"const": "human"}` admits "agent" at the schema layer.
    U5 below is therefore the SOLE enforcer of the human-principal rule. Do not delete it on the
    reasoning that the schema already covers it; that reasoning is correct for the enum four
    lines up and wrong here, and the two sit close enough to be confused. (BADF-QA, #264 review;
    repo-wide as #265.)
    """
    b = evidence.get("binding")
    if not isinstance(b, dict):
        return                                    # untyped stays admissible (additive rung)
    check_schema("uat", evidence)
    label = f"{evidence.get('id', '?')} (uat)"

    # UAT-I05 (exact acceptance basis) needs NO code control: schemas/uat.schema.json makes
    # prd_id, prd_digest and acceptance_criteria_digest REQUIRED inside acceptance_basis, so
    # check_schema above refuses a missing basis before any code here could reach it. A U1 WAS
    # written here, and the mutation battery found it SURVIVES -- unreachable, because the
    # schema raises first and BOTH messages contain "prd_digest", so the test asserting that
    # fragment passed on the wrong raise. A control the schema makes unreachable is not a
    # control; it is the shape of one. Removed rather than kept for symmetry -- #250's class,
    # found by this rung's own battery in this rung's own code.

    known = {s["scenario_id"] for s in b.get("scenarios") or []}
    # U2 -- an observation of a scenario this binding does not carry is unanchored
    orphan = sorted({o["scenario_id"] for o in b.get("observations") or []} - known)
    if orphan:
        raise ValidationError(f"{label}: observation(s) name scenario(s) absent from this binding: {', '.join(orphan)}; an unanchored observation is a test result, not UAT evidence (UAT-I01)")

    # U3 -- every failed or blocked observation carries a classified defect
    classified = {d["scenario_id"] for d in b.get("defects") or []}
    unclassified = sorted({o["scenario_id"] for o in b.get("observations") or []
                           if o["result"] in ("FAIL", "BLOCKED")} - classified)
    if unclassified:
        raise ValidationError(f"{label}: scenario(s) {', '.join(unclassified)} failed or were blocked with no defect class; a failure without a class is noise the disposition cannot act on (UAT-I11)")

    # U6 -- one scenario, one observation. A `uat` evidence object is ONE execution pass over a
    # scenario set; a re-run after a fix is a NEW uat object with its own candidate digest, which
    # is what UAT-I17 already implies. Two observations of one scenario inside one binding is
    # AMBIGUOUS INPUT with no stated resolution -- retry? flake? two adapters? -- and any rule the
    # gate picked (last-wins, worst-wins, newest-wins) would be the gate deciding something the
    # producer never said. Refusing ambiguity beats interpreting it.
    #
    # This also makes `observations` a set BY CONSTRUCTION, so U3 and U4 agree structurally rather
    # than by both happening to be written set-wise. They did not: U4 was a dict comprehension
    # (LAST occurrence wins) while U3 ten lines up was set-based, so the same multiset in a
    # different order produced opposite verdicts -- [FAIL, PASS] admitted under RECOMMEND_ACCEPT,
    # [PASS, FAIL] refused. Found by BADF-QA on #264.
    #
    # And it settles `executed_at`, which QA noted is required and never read: with duplicates
    # refused it is PROVENANCE (when this was observed), never an ordering key. Nothing resolves
    # a conflict, because a conflict cannot be expressed.
    seen: dict[str, int] = {}
    for o in b.get("observations") or []:
        seen[o["scenario_id"]] = seen.get(o["scenario_id"], 0) + 1
    dupes = sorted(s for s, n in seen.items() if n > 1)
    if dupes:
        raise ValidationError(f"{label}: scenario(s) {', '.join(dupes)} carry more than one observation; a uat evidence object is one execution pass and a re-run is a new object, so duplicate observations are ambiguous input rather than a result to be resolved (UAT-I09 / UAT-I17)")

    # U4 -- a critical scenario cannot be buried under an aggregate recommendation.
    # Order-independent by construction now that U6 refuses duplicates.
    if b.get("recommendation") == "RECOMMEND_ACCEPT":
        critical = {s["scenario_id"] for s in b.get("scenarios") or [] if s["criticality"] == "critical"}
        by_scn = {o["scenario_id"]: o["result"] for o in b.get("observations") or []}
        bad = sorted(s for s in critical if by_scn.get(s, "NOT_EXECUTED") in ("FAIL", "BLOCKED", "NOT_EXECUTED"))
        if bad:
            raise ValidationError(f"{label}: RECOMMEND_ACCEPT with critical scenario(s) {', '.join(bad)} not passing; mandatory critical criteria cannot be hidden by an aggregate (UAT-I13)")

    # U5 -- Layer 2 binds Layer 1, and only a human issues it
    acc = b.get("acceptance")
    if isinstance(acc, dict):
        if acc["candidate_digest"] != (b.get("candidate") or {}).get("source_digest"):
            raise ValidationError(f"{label}: acceptance.candidate_digest does not equal the binding's candidate.source_digest; an acceptance bound to a different candidate is void (UAT-I16)")
        # SOLE ENFORCER: the schema's {"const": "human"} is decorative -- check_schema has no
        # const branch (measured: principal_type='agent' is ADMITTED by check_schema alone).
        # Deleting this leaves the appearance of the rule and none of it.
        if (acc.get("accepted_by") or {}).get("principal_type") != "human":
            raise ValidationError(f"{label}: acceptance carries a non-human principal; final product acceptance is a separate authorized human decision, never the producing capability's (UAT-I14 / UAT-I15)")

    # ---- WP-UAT-C: deterministic G10 controls. Lean mode DISABLED -- HARD INVARIANTS. ----
    #
    # U4 (rung B) refuses a critical failure only under RECOMMEND_ACCEPT. I defended that
    # boundary at B on the grounds that "conditions are exactly where a known critical failure
    # gets named" -- BADF-QA's #266 observed that the rationale was right and ENFORCED BY
    # NOTHING: conditions, known_defects_acknowledged and declared_non_coverage_acknowledged are
    # all optional, so a disposition whose NAME asserts conditions exist required none, and
    # UAT-I13's aggregate-burying was reachable one enum value over. C7-C9 enforce the
    # precondition rather than withdraw the judgement.

    def _not_passing_criticals() -> list[str]:
        crit = {s["scenario_id"] for s in b.get("scenarios") or [] if s["criticality"] == "critical"}
        seen = {o["scenario_id"]: o["result"] for o in b.get("observations") or []}
        return sorted(s for s in crit if seen.get(s, "NOT_EXECUTED") != "PASS")

    # C7 -- a critical failure carried under WITH_CONDITIONS must actually be NAMED (UAT-I13).
    # Preserves B's judgement that conditions are the legitimate home for a known failure, and
    # requires that the home be occupied.
    if b.get("recommendation") == "RECOMMEND_ACCEPT_WITH_CONDITIONS":
        named = " ".join(str(x) for x in ((acc or {}).get("conditions") or [])
                         + ((acc or {}).get("known_defects_acknowledged") or [])) if isinstance(acc, dict) else ""
        unnamed = [s for s in _not_passing_criticals() if s not in named]
        if unnamed:
            raise ValidationError(f"{label}: RECOMMEND_ACCEPT_WITH_CONDITIONS with critical scenario(s) {', '.join(unnamed)} not passing and named in no condition or acknowledged defect; conditions are where a known critical failure is named, so an unnamed one is the aggregate UAT-I13 refuses, one enum value over (UAT-I13 / GOV #266)")

    if isinstance(acc, dict):
        # C8 -- a disposition whose NAME asserts conditions exist must carry some.
        if acc["disposition"] == "ACCEPTED_WITH_CONDITIONS" and not (acc.get("conditions") or []):
            raise ValidationError(f"{label}: acceptance disposition ACCEPTED_WITH_CONDITIONS carries no conditions; a disposition whose name asserts conditions exist cannot have none (UAT-I16 / GOV #266)")

        # C9 -- an UNCONDITIONAL human acceptance over an unacknowledged critical failure. A
        # human may accept a known critical failure; acknowledging it is what makes it known.
        if acc["disposition"] == "ACCEPTED":
            ack = " ".join(str(x) for x in (acc.get("known_defects_acknowledged") or [])
                           + (acc.get("conditions") or []))
            unacked = [s for s in _not_passing_criticals() if s not in ack]
            if unacked:
                raise ValidationError(f"{label}: unconditional ACCEPTED over critical scenario(s) {', '.join(unacked)} not passing and not acknowledged; a human may accept a known critical failure, but acknowledging it is what makes it known (UAT-I16 / GOV #266)")

        # C10 -- STALENESS on the scenario set (UAT-I17). The acceptance binds a scenario_set_digest;
        # if it does not equal a digest recomputed over the scenarios actually carried, the
        # acceptance describes a scenario set that is not this one. UAT-I17 says a material change
        # invalidates the acceptance -- this is what makes that mechanical rather than a promise.
        canonical = json.dumps(sorted(s["scenario_id"] for s in b.get("scenarios") or []),
                               separators=(",", ":")).encode("utf-8")
        recomputed = "sha256:" + hashlib.sha256(canonical).hexdigest()
        if acc["scenario_set_digest"] != recomputed:
            raise ValidationError(f"{label}: acceptance.scenario_set_digest does not equal a digest recomputed over the scenarios in this binding; the acceptance describes a different scenario set, so a scenario added or removed after it was issued would carry the acceptance forward silently (UAT-I17)")

    # C11 -- COVERAGE EXACTNESS (UAT-I12). A criterion marked not_covered without a matching
    # non_coverage entry is the defect the matrix exists to prevent, wearing a label: absence
    # from the matrix and an unexplained not_covered are the same silence.
    cov = b.get("coverage") or {}
    # SET, not a joined string. Joining made `ref not in declared_gaps` a SUBSTRING test, so a
    # gap declared for AC-12 reported AC-1 as explained (BADF-QA, PR #274). `item` holds a ref,
    # not prose about one -- membership is the intended semantics and the only exact one.
    declared_gaps = {str(x.get("item", "")) for x in (cov.get("non_coverage") or [])}
    unexplained = sorted(c["acceptance_criterion_ref"] for c in (cov.get("criteria") or [])
                         if c["state"] == "not_covered"
                         and not c.get("reason") and c["acceptance_criterion_ref"] not in declared_gaps)
    if unexplained:
        raise ValidationError(f"{label}: criteri(a) {', '.join(unexplained)} are not_covered with neither a reason nor a declared non_coverage entry; a criterion marked not_covered without one is the same silence as a criterion missing from the matrix (UAT-I12)")


EVIDENCE_RULES["uat"] = check_g10_uat_binding



G08_OBSERVATIONS = ("integration-test", "contract-test", "composed-tree-test")
G08_QUORUM = {"C2": 2, "C3": 3}
G08_REQUIRED_LENSES = {"C2": {"correctness", "quality/test"}, "C3": {"correctness", "quality/test", "data/integration"}}


def _independent_reviewer_deviation_carried(dossier: dict[str, Any]) -> bool:
    """The single-collaborator deviation: an OPEN dossier condition naming the missing independent
    reviewer (the self-dossier's C-1). Carried, never hidden -- and never satisfied by a banner."""
    for c in dossier.get("conditions") or []:
        if isinstance(c, dict) and c.get("status") == "OPEN" and "independent reviewer" in str(c.get("statement", "")).lower():
            return True
    return False


def check_g08_dossier(dossier: dict[str, Any], work_package: dict[str, Any] | None, evidence: dict[str, dict[str, Any]],
                      composition_record: dict[str, Any] | None, record: dict[str, Any] | None) -> None:
    """badf-engineering-verification VER-C: the seven dossier-level G08 controls, as ONE PURE function --
    no reads, no writes, no git; validate_dossier resolves the inputs and stays idempotent. Fires only on
    a G08 dossier claiming PASS / PASS_WITH_CONDITIONS, and each control only on fields that are declared
    (a typed binding, a verification record, a Work Package `verification_obligations`), so every dossier
    on main -- WP-2026-0010's generic G08 dossier included -- stays valid.
      C1 exact target (VER-I01): typed bindings bind the dossier's source_revision and the composition
         record's expected_content_tree / target_base_sha.
      C2 one composed identity (VER-I05): all typed objects bind the same content tree.
      C3 independence and quorum (VER-I04/I19): the author's execution or identity cannot be the reviewer
         unless the deviation is carried as an OPEN condition; C2/C3 change classes need a verification
         record with a quorum of distinct reviewers/runs and the mandatory lenses.
      C4 runtime credit (VER-I08): when the WP declares runtime_required, an untyped observation earns none.
      C5 per-artifact non-coverage (VER-I11): a typed observation declares what it did not observe unless
         the WP permits a comprehensive-coverage claim for that type.
      C6 review blockers resolved (VER-I12): an OPEN MAJOR/CRITICAL finding refuses PASS and must map to a
         condition on PASS_WITH_CONDITIONS; the review's findings are carried or withdrawn by the record.
      C7 composed-result authority (VER-I15): composed-tree-test is never NOT_APPLICABLE."""
    if dossier.get("gate") != "G08" or dossier.get("disposition") not in {"PASS", "PASS_WITH_CONDITIONS"}:
        return
    typed = {t: e for t, e in evidence.items() if isinstance(e, dict) and isinstance(e.get("binding"), dict)}
    change_class = dossier.get("change_class")
    src = str(dossier.get("source_revision", ""))
    # C1 -- exact target
    rec_tree = str((composition_record or {}).get("expected_content_tree") or "")
    rec_base = str((composition_record or {}).get("target_base_sha") or "")
    for t, e in typed.items():
        tb = e["binding"].get("target") or {}
        if str(tb.get("source_revision")) != src:
            raise ValidationError(f"{t}: binding.target.source_revision {str(tb.get('source_revision'))[:12]} does not equal the dossier's source_revision {src[:12]} (VER-I01 / C1)")
        if rec_tree and str(tb.get("expected_content_tree")) != rec_tree:
            raise ValidationError(f"{t}: binding.target.expected_content_tree {str(tb.get('expected_content_tree'))[:12]} does not equal the composition record's expected_content_tree {rec_tree[:12]} (VER-I01 / C1)")
        if rec_base and t == "composed-tree-test" and str((e["binding"].get("composition") or {}).get("target_base_sha")) != rec_base:
            raise ValidationError(f"{t}: binding.composition.target_base_sha does not equal the composition record's target_base_sha {rec_base[:12]} (VER-I01 / C1)")
        if rec_base and t == "independent-review" and str(tb.get("target_base_sha")) != rec_base:
            raise ValidationError(f"{t}: binding.target.target_base_sha does not equal the composition record's target_base_sha {rec_base[:12]} (VER-I01 / C1)")
    # C2 -- one composed identity
    trees = {t: str((e["binding"].get("target") or {}).get("expected_content_tree")) for t, e in typed.items()}
    if len(set(trees.values())) > 1:
        raise ValidationError(f"typed G08 objects do not bind one composed identity: {{{', '.join(f'{k}: {v[:12]}' for k, v in sorted(trees.items()))}}}; a review of one tree and observations of another verify nothing together (VER-I05 / C2)")
    # C3 -- independence and quorum by change class
    rv = typed.get("independent-review")
    if rv is not None:
        b = rv["binding"]; ind = b.get("independence") or {}; who = b.get("reviewer") or {}
        same_run = str(who.get("reviewer_run_id")) == str(ind.get("author_run_id"))
        same_identity = str(who.get("identity", "")).strip().lower() == str(dossier.get("author", "")).strip().lower()
        if (same_run or same_identity) and not _independent_reviewer_deviation_carried(dossier):
            raise ValidationError("independent-review: the reviewer is the author's execution or identity and the dossier carries no OPEN independent-reviewer deviation condition; independence is established or carried, never hidden (VER-I04 / C3)")
    if change_class in G08_QUORUM:
        if record is None:
            raise ValidationError(f"a {change_class} G08 dossier requires a verification record (council review) as the independent-review artifact; none is bound (VER-I19 / C3)")
        ballots = [x for x in (record.get("ballots") or []) if isinstance(x, dict)]
        reviewers = {str(x.get("reviewer")) for x in ballots}; runs = {str(x.get("reviewer_run_id")) for x in ballots}
        need = G08_QUORUM[change_class]
        if min(len(reviewers), len(runs)) < need:
            raise ValidationError(f"{change_class} quorum requires {need} distinct reviewers and runs; the verification record carries {len(reviewers)} reviewer(s) / {len(runs)} run(s) (VER-I19 / C3)")
        missing = sorted(G08_REQUIRED_LENSES[change_class] - {str(x) for x in (record.get("lenses_routed") or [])})
        if missing:
            raise ValidationError(f"{change_class} review must route the mandatory lens(es) {missing} (review-lenses.md / C3)")
    # C4 -- runtime credit when the Work Package demands it
    vo = (work_package or {}).get("verification_obligations") or {}
    if vo.get("runtime_required"):
        for t in G08_OBSERVATIONS:
            e = evidence.get(t)
            if isinstance(e, dict) and e.get("outcome") == "PASS" and "binding" not in e:
                raise ValidationError(f"{t}: the work package declares verification_obligations.runtime_required but the observation carries no typed binding; an untyped {str((e.get('producer') or {}).get('type'))}-produced result earns no runtime credit (VER-I08 / C4)")
    # C5 -- non-coverage per artifact
    permitted = {str(x) for x in (vo.get("comprehensive_coverage_permitted_for") or [])}
    for t in G08_OBSERVATIONS:
        e = typed.get(t)
        if e is not None and not e["binding"].get("non_coverage") and t not in permitted:
            raise ValidationError(f"{t}: typed observation declares no non-coverage and the work package does not permit a comprehensive-coverage claim for it; a run that states nothing unobserved is incomplete (VER-I11 / C5)")
    # C6 -- review blockers resolved
    open_blocking: dict[str, dict[str, Any]] = {}
    review_findings = [f for f in ((rv or {}).get("binding") or {}).get("findings") or [] if isinstance(f, dict)]
    for f in review_findings:
        if f.get("status") == "OPEN" and f.get("severity") in BLOCKING_SEVERITIES:
            open_blocking[str(f.get("finding_id"))] = f
    if record is not None:
        rec_findings = [f for f in (record.get("findings") or []) if isinstance(f, dict)]
        for f in rec_findings:
            if f.get("status") == "OPEN" and f.get("severity") in BLOCKING_SEVERITIES:
                open_blocking[str(f.get("finding_id"))] = f
        carried = {str(f.get("finding_id")) for f in rec_findings} | {str(w.get("finding_id")) for w in ((record.get("synthesis") or {}).get("withdrawn") or []) if isinstance(w, dict)}
        lost = [str(f.get("finding_id")) for f in review_findings if str(f.get("finding_id")) not in carried]
        if lost:
            raise ValidationError(f"review finding(s) {lost} are neither carried nor withdrawn by the verification record; synthesis cannot erase a finding (VER-I12 / C6)")
    if open_blocking:
        if dossier.get("disposition") == "PASS":
            raise ValidationError(f"OPEN blocking finding(s) {sorted(open_blocking)} refuse PASS; review blockers are resolved or carried as conditions, never passed over (VER-I12 / C6)")
        statements = " ".join(str(c.get("statement", "")) for c in (dossier.get("conditions") or []) if isinstance(c, dict))
        unmapped = [fid for fid in sorted(open_blocking) if fid not in statements]
        if unmapped:
            raise ValidationError(f"OPEN blocking finding(s) {unmapped} map to no dossier condition; PASS_WITH_CONDITIONS carries each blocker as a condition naming it (VER-I12 / C6)")
    # C7 -- composed-result authority
    for n in dossier.get("non_coverage") or []:
        if isinstance(n, dict) and n.get("evidence_type") == "composed-tree-test":
            raise ValidationError("composed-tree-test declared as non-coverage (NOT_APPLICABLE); a G08 dossier without a composed observation cannot pass -- source-head success is not composed verification (VER-I15 / C7)")
    ct = evidence.get("composed-tree-test")
    if isinstance(ct, dict) and ct.get("outcome") == "NOT_APPLICABLE":
        raise ValidationError("composed-tree-test outcome NOT_APPLICABLE; the composed observation is never optional at G08 (VER-I15 / C7)")


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
    outcome = expect_str(evidence["outcome"], f"evidence {path} outcome")
    if outcome == "NOT_APPLICABLE":
        check_non_coverage(dossier, expected_type, outcome)
    elif outcome != "PASS":
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
    rule = EVIDENCE_RULES.get(expected_type)
    if rule is not None and outcome == "PASS":
        rule(artifact, dossier, evidence)   # the gate opens the artifact; a name is not evidence


def validate_authority(dossier: dict[str, Any], require_quorum: bool = True) -> None:
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

    author = canonical_principal(dossier.get("author"), "dossier author")
    author_type = expect_str(dossier.get("author_type"), "dossier author_type")
    if author_type not in PRINCIPAL_TYPES:
        raise ValidationError(f"dossier author_type {author_type!r} is not one of {sorted(PRINCIPAL_TYPES)}")
    human_reserved = set(matrix.get("human_reserved_roles") or [])

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
        if not isinstance(role, str) or role not in known_roles:
            raise ValidationError(f"{label} unknown role: {role!r}")
        principal = canonical_principal(item["by"], f"{label} approving")
        ptype = expect_str(item["principal_type"], f"{label} principal_type")
        if ptype not in PRINCIPAL_TYPES:
            raise ValidationError(f"{label} invalid principal_type {ptype!r}; expected one of {sorted(PRINCIPAL_TYPES)}")
        if role in human_reserved and ptype != "human":
            # BADF-DEC-0003 / mandate section 3: Orchestrator != Authority.
            # Before this, the gate knew an approver only as a string. An agent
            # authored a C3 change, four distinct agents approved it including
            # human_sponsor, and the gate rendered APPROVED. The role label is
            # not the principal; the matrix now says which roles a non-human may
            # never hold, and the declared type decides -- deny-unless-established.
            raise ValidationError(
                f"{label} role {role} is human-reserved; a principal of type {ptype!r} "
                f"({principal!r}) may not supply it")
        decision = expect_str(item["decision"], f"{label} decision")
        if decision not in APPROVAL_DECISIONS:
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
        if decision == "REJECTED" and role in required:
            raise ValidationError(
                f"{label}: {principal!r} REJECTED as {role}, a required role -- a rejection from "
                "a required role is a veto, not a vote to be outnumbered")
        if decision == "APPROVED":
            granted.setdefault(principal, set()).add(role)

    for principal, roles in sorted(granted.items()):
        overlap = roles & required
        if len(overlap) > 1:
            raise ValidationError(
                f"principal {principal!r} fills {len(overlap)} required roles "
                f"({', '.join(sorted(overlap))}); required roles must be distinct principals")

    if not require_quorum:
        return
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

    exceptions = dossier.get("exceptions", [])
    if not isinstance(exceptions, list):
        raise ValidationError("dossier exceptions must be an array")
    for index, exc in enumerate(exceptions):
        # QA finding M2: `exceptions` was the unguarded twin of `conditions`.
        # `["waive-mandatory-gate"]` satisfied a conditional pass and rendered
        # unconditional APPROVED. An exception is an object with an owner and
        # an authority, or it is nothing.
        elabel = f"exceptions[{index}]"
        if not isinstance(exc, dict):
            raise ValidationError(f"{elabel} must be an object, not a bare value")
        absent = sorted({"exception_id", "control", "justification", "granted_by", "expires_at"} - set(exc))
        if absent:
            raise ValidationError(f"{elabel} missing required fields: {', '.join(absent)}")
        if exc["granted_by"] not in known_roles:
            raise ValidationError(f"{elabel} granted_by {exc['granted_by']!r} is not a role in the authority matrix")
        parse_time(exc["expires_at"], f"{elabel}.expires_at")
    if disposition == "PASS_WITH_CONDITIONS" and not raw and not exceptions:
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
        expect_str(cond["status"], f"{label} status")
        expect_str(cond["severity"], f"{label} severity")
        expect_str(cond["owner"], f"{label} owner")
        expect_str(cond["closure_authority"], f"{label} closure_authority")
        if cond["status"] not in CONDITION_STATUSES:
            raise ValidationError(f"{label} invalid status {cond['status']!r}")
        if cond["severity"] not in CONDITION_SEVERITIES:
            raise ValidationError(f"{label} invalid severity {cond['severity']!r}")
        if cond["owner"] not in known_roles:
            raise ValidationError(f"{label} owner {cond['owner']!r} is not a role in the authority matrix")
        if cond["closure_authority"] not in known_roles:
            raise ValidationError(
                f"{label} closure_authority {cond['closure_authority']!r} is not a role in the authority matrix")
        if cond["status"] in {"CLOSED", "SUPERSEDED", "WAIVED"}:
            # QA finding F-5: a Critical condition blocking THIS gate could be
            # marked WAIVED with no closer at all, and the dossier rendered
            # APPROVED. Closure is an act by someone; it must name them.
            if cond.get("closed_by") is None:
                raise ValidationError(f"{label} is {cond['status']} but names no closed_by")
            closer = canonical_principal(cond["closed_by"], f"{label} closed_by")
            if author is not None and closer == canonical_principal(author, "dossier author"):
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


def _foreign_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True)


def verify_foreign_revision(dossier: dict[str, Any], indexed: dict[str, str]) -> None:
    """A dossier governs a commit that EXISTS and CHANGED WHAT THE EVIDENCE SAYS.

    WP-2026-0010 -- the first work package BADF governed that was not BADF --
    exposed this: source_revision was only ever compared for EQUALITY across
    dossier, evidence and approvals. A dossier whose three copies all agreed
    on the all-zeros SHA passed. For BADF's own work the SHA was always
    BADF's, so it never mattered. For foreign work it is the whole claim.

    The dossier's `target` is `<repository>:<branch>`. The repository must be
    registered in badf/repositories.json with a local path (no network; the
    gate is deterministic), the path must be a git repository, the revision
    must resolve there, it must descend from the work package's declared
    base_revision, and if a `source-change` evidence artifact is indexed, its
    content must equal `git diff base..revision`. Deny-unless-established.
    """
    target = expect_str(dossier["target"], "dossier.target")
    repo_name, _, _branch = target.partition(":")
    registry = load_json(ROOT / REPOSITORIES)
    entry = (registry.get("repositories") or {}).get(repo_name)
    if not isinstance(entry, dict) or "local_path" not in entry:
        raise ValidationError(f"target repository {repo_name!r} is not a registered repository in {REPOSITORIES}")
    repo_root = (ROOT / entry["local_path"]).resolve() if not Path(entry["local_path"]).is_absolute() else Path(entry["local_path"])
    revision = expect_str(dossier["source_revision"], "dossier.source_revision")
    resolution = entry.get("resolution")
    if resolution not in {"SELF", "LOCAL_MIRROR"}:
        raise ValidationError(f"{repo_name} in {REPOSITORIES} declares no valid resolution (SELF | LOCAL_MIRROR); refusing")

    top = _foreign_git(repo_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        if resolution == "LOCAL_MIRROR" and not repo_root.exists():
            # The registry said this repo lives on a specific host. It is not
            # here. That is a fact about WHERE the gate is running, and it must
            # be reported as such -- not as a refusal of the dossier, which a
            # reader would take as 'the work is bad'. A CI runner hits this for
            # every LOCAL_MIRROR repo, by design: the gate makes no network calls.
            raise ValidationError(
                f"UNRESOLVABLE_HERE: {repo_name} is registered as LOCAL_MIRROR at {repo_root}, which does not "
                f"exist on this host. The dossier is neither approved nor refused here; validate it where the "
                f"mirror exists.")
        raise ValidationError(f"registered local_path {repo_root} for {repo_name} is not a git repository")
    exists = _foreign_git(repo_root, "cat-file", "-e", f"{revision}^{{commit}}")
    if exists.returncode != 0:
        raise ValidationError(f"source_revision {revision[:12]} cannot be resolved: no such commit in {repo_name} at {repo_root}")

    # The work package declares what this revision is built on -- and WHICH
    # repository it belongs to. A second governed project made the id
    # namespace ambiguous: PropTech's own WP-0042 is a syntactically valid
    # BADF work_package_id. If the WP names a repository, it must be the one
    # the dossier targets; a dossier cannot borrow another project's WP.
    wp_path = ROOT / "work" / dossier["work_package_id"] / "work-package.json"
    base = None
    if wp_path.is_file():
        wp_rec = load_json(wp_path)
        wp_repo = wp_rec.get("repository")
        if wp_repo and wp_repo != repo_name:
            raise ValidationError(
                f"work package {dossier['work_package_id']} belongs to {wp_repo}, but this dossier targets "
                f"{repo_name}; a work package is bound to one repository")
        base = ((wp_rec.get("external_target") or {}).get("base_revision"))
    if base:
        base_ok = _foreign_git(repo_root, "cat-file", "-e", f"{base}^{{commit}}")
        if base_ok.returncode != 0:
            raise ValidationError(f"declared base_revision {base[:12]} cannot be resolved in {repo_name}")
        anc = _foreign_git(repo_root, "merge-base", "--is-ancestor", base, revision)
        if anc.returncode != 0:
            raise ValidationError(
                f"source_revision {revision[:12]} is not descended from the declared base_revision {base[:12]} in {repo_name}")

    # The recorded diff must be the diff.
    if "source-change" in indexed:
        ev = load_json(safe_repo_path(indexed["source-change"], "source-change evidence"))
        artifact = safe_repo_path(ev["artifact"], "source-change artifact")
        recorded = artifact.read_bytes()
        if resolution == "SELF":
            # A self-work-package's change is squash-merged; its branch commits
            # do not survive the squash (like landed_as), so the diff is taken
            # against the resolved tip (HEAD) with the work package's own
            # directory and the lockfile excluded -- neither can appear in the
            # diff it records. `base..HEAD` compares the same two trees on the
            # branch, in the composed tree, and on main after the squash.
            if not base:
                raise ValidationError(f"a self-work-package dossier for {repo_name} requires external_target.base_revision")
            wp_dir = dossier["work_package_id"]
            diff_args = ["diff", f"{base}..HEAD", "--", ".", f":(exclude)work/{wp_dir}/", ":(exclude)badf/lockfile.json"]
            span = f"{base}..HEAD (excluding work/{wp_dir}/ and the lockfile)"
        else:
            span = f"{base}..{revision}" if base else f"{revision}^..{revision}"
            diff_args = ["diff", span]
        actual = _foreign_git(repo_root, *diff_args)
        if actual.returncode != 0:
            raise ValidationError(f"cannot compute the actual diff for {span} in {repo_name}")
        if actual.stdout != recorded:
            raise ValidationError(
                f"source-change artifact does not match what {revision[:12]} actually changed in {repo_name} "
                f"({span}: recorded {len(recorded)} bytes, actual {len(actual.stdout)} bytes)")


def _event_hash(event: dict[str, Any]) -> str:
    """Hash of the event with its own event_hash removed; keys sorted so the
    chain is independent of write order."""
    body = {k: v for k, v in event.items() if k != "event_hash"}
    return "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_ledger(wp_dir: Path) -> list[dict[str, Any]]:
    """The run ledger, verified: every event well-formed, sequence strictly
    increasing from 1, hash chain intact. A broken chain is a refusal, not a
    warning -- the ledger's whole value is that it cannot be edited in place.
    Ported from secb_pf DETERMINISTIC_REPLAY_STANDARD step 3.
    """
    path = wp_dir / LEDGER_NAME
    if not path.is_file():
        raise ValidationError(f"no run ledger at {path.relative_to(ROOT)}")
    events: list[dict[str, Any]] = []
    prev = GENESIS_HASH
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            ev = json.loads(line, object_pairs_hook=_no_duplicate_keys)
        except ValueError as exc:
            raise ValidationError(f"ledger line {n} is not valid JSON: {exc}")
        require_fields(ev, LEDGER_FIELDS, f"ledger line {n}")
        if ev["sequence"] != len(events) + 1:
            raise ValidationError(f"ledger line {n}: sequence {ev['sequence']} breaks the run (expected {len(events)+1})")
        if ev["outcome"] not in LEDGER_OUTCOMES:
            raise ValidationError(f"ledger line {n}: invalid outcome {ev['outcome']!r}")
        if ev["previous_event_hash"] != prev:
            raise ValidationError(f"ledger line {n}: hash chain broken (previous_event_hash does not match event {n-1})")
        if ev["event_hash"] != _event_hash(ev):
            raise ValidationError(f"ledger line {n}: event_hash does not match content -- ledger edited in place")
        events.append(ev)
        prev = ev["event_hash"]
    # Inherited from the authoritative site: a ledger written around append_event --
    # edited by hand, restored from a backup, produced by an older writer -- is refused
    # when READ, not only when written.
    _validate_effect_chain(events, f"ledger {path.name}")
    return events


def _validate_effect_chain(events: list[dict[str, Any]], label: str) -> None:
    """AET-I05, enforced (#294, WP-2026-0132): a durable effect that reached a TERMINAL
    outcome cannot receive a further event. Before this, LEDGER_OUTCOMES was a
    membership check at both consumers and never a state machine, so an effect could go
    PREPARED -> COMMITTED -> PREPARED -> COMMITTED and replay_run would report it as one
    clean commit -- a durable external effect executed twice, invisible in the record.

    THIS is the authoritative site. Both consumers call it -- read_ledger over the
    stored chain, append_event over the chain plus its candidate -- so a guard in only
    one of them cannot exist to diverge from the other (the #290 lesson: validation at
    the source, never at the consumer). Scoped per effect_id; events without one are
    the run's own steps, not durable effects, and are untouched.
    """
    last: dict[str, str] = {}
    checked: set[str] = set()
    for ev in events:
        eid = ev.get("effect_id")
        if not eid:
            continue
        prior = last.get(eid)
        if prior in EFFECT_ESTABLISHED and ev["outcome"] not in AFTER_ESTABLISHED_ALLOWED:
            raise ValidationError(
                f"{label}: effect {eid!r} is established as {prior} and now records "
                f"{ev.get('outcome')!r}; the world already changed, so it is neither prepared "
                f"nor committed again and never asserted absent -- only "
                f"{sorted(AFTER_ESTABLISHED_ALLOWED)} may follow (AET-I05 / #294)")
        if (ev["outcome"] == "COMMITTED" and eid not in checked
                and _authority_ratchet_applies(ev.get("workflow_id") or "")):
            raise ValidationError(
                f"{label}: effect {eid!r} records COMMITTED with no AUTHORITY_CHECKED event "
                f"before it; the contract's second phase must leave a trace in the record, "
                f"and a check for another effect does not authorize this one "
                f"(AET-I05 / #294, mandatory from {WP_NAMESPACE}0132)")
        if ev["outcome"] == "AUTHORITY_CHECKED":
            checked.add(eid)
        last[eid] = ev["outcome"]


def replay_run(wp_dir: Path) -> dict[str, Any]:
    """Reconstruct run state from the ledger. PURE: reads only, appends
    nothing, re-executes nothing. Mandate section 6: 'Replay reconstructs
    state; replay must not repeat external side effects.'

    An effect whose LAST recorded outcome is OUTCOME_UNKNOWN is returned as
    unresolved: the protocol says it is never terminal, and resume must
    reconcile it before scheduling anything new.
    """
    events = read_ledger(wp_dir)
    committed: dict[str, str] = {}
    last_by_effect: dict[str, str] = {}
    for ev in events:
        eid = ev.get("effect_id")
        if eid:
            last_by_effect[eid] = ev["outcome"]
            if ev["outcome"] == "COMMITTED" and ev.get("output_digest"):
                committed[eid] = ev["output_digest"]
    unresolved = sorted(e for e, o in last_by_effect.items() if o == "OUTCOME_UNKNOWN")
    return {
        "workflow_id": events[-1]["workflow_id"] if events else None,
        "current_step": events[-1]["step"] if events else None,
        "sequence": len(events),
        "committed_effects": committed,
        "unresolved_effects": unresolved,
        "head_hash": events[-1]["event_hash"] if events else GENESIS_HASH,
    }


def plan_next_effect(wp_dir: Path, effect_id: str) -> str:
    """What resume must do about an effect. Deny-unless-established: an
    effect with a recorded receipt is SKIPPED, an unresolved one must be
    RECONCILED first, anything else may be PREPARED. Never re-executed blind."""
    state = replay_run(wp_dir)
    if effect_id in state["committed_effects"]:
        return "SKIP_ALREADY_COMMITTED"
    if effect_id in state["unresolved_effects"]:
        return "RECONCILE_FIRST"
    return "PREPARE"


def append_event(wp_dir: Path, step: str, outcome: str, actor_id: str, actor_type: str,
                 effect_id: str | None = None, output_digest: str | None = None,
                 note: str | None = None, provenance: str = "RECORDED_AT_EVENT_TIME") -> dict[str, Any]:
    """Append one chained event. Verifies the existing chain first, so an
    append onto a tampered ledger is refused rather than laundered."""
    path = wp_dir / LEDGER_NAME
    events = read_ledger(wp_dir) if path.is_file() else []
    if outcome not in LEDGER_OUTCOMES:
        raise ValidationError(f"invalid outcome {outcome!r}")
    if actor_type not in PRINCIPAL_TYPES:
        raise ValidationError(f"invalid actor type {actor_type!r}")
    seq = len(events) + 1
    ev: dict[str, Any] = {
        "event_id": f"EVT-{wp_dir.name}-{seq:04d}", "workflow_id": wp_dir.name, "sequence": seq,
        "step": step, "outcome": outcome, "actor": {"id": actor_id, "type": actor_type},
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "effect_id": effect_id, "output_digest": output_digest, "provenance": provenance,
        "previous_event_hash": events[-1]["event_hash"] if events else GENESIS_HASH,
    }
    if note:
        ev["note"] = note
    ev["event_hash"] = _event_hash(ev)
    # Same site, same semantic: the candidate is validated against the chain it would
    # extend, before a byte is written.
    _validate_effect_chain(events + [ev], f"appending to {path.name}")
    with path.open("a", encoding="utf-8") as h:
        h.write(json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n")
    return ev


def compute_council_disposition(dossier: dict[str, Any], work_package: dict[str, Any] | None) -> dict[str, Any]:
    """Mandate section 7: is council invocation warranted? Computed, never inferred.

    Of the mandate's eight triggers, four have NO carrier on any BADF object
    (novelty, architectural significance, blast radius, uncertainty-as-a-
    value). Weighing them would be the gate inferring risk -- judgment
    dressed as computation, which section 21 forbids. So this reads ONLY
    fields that exist and names which fired:

      change_class C3                     -> REQUIRED
      declared Critical risk              -> REQUIRED
      irreversible (or rollback absent)   -> REQUIRED   (absence is not reversibility)
      data_classification restricted      -> REQUIRED
      production gate G10-G12             -> REQUIRED
      change_class C2                     -> OPTIONAL
      otherwise                           -> NOT_REQUIRED

    ADVISORY. This writes a disposition; it grants no authority and changes
    who may approve nothing. Council consensus != constitutional authority.
    """
    triggers: list[str] = []
    cc = expect_str(dossier.get("change_class"), "dossier.change_class")
    if cc == "C3":
        triggers.append("change_class:C3")
    for i, r in enumerate(dossier.get("risks") or []):
        if not isinstance(r, dict) or "severity" not in r:
            raise ValidationError(f"risks[{i}] must be an object with a severity; an untyped risk cannot be weighed")
        sev = expect_str(r["severity"], f"risks[{i}].severity")
        if sev not in RISK_SEVERITIES:
            raise ValidationError(f"risks[{i}].severity {sev!r} is not one of {sorted(RISK_SEVERITIES)}")
        if sev == "Critical":
            triggers.append("risk:Critical")
    wp = work_package or {}
    rb = wp.get("rollback")
    if not isinstance(rb, dict) or rb.get("reversible") is not True:
        triggers.append("irreversible")
    if wp.get("data_classification") == "restricted":
        triggers.append("data_classification:restricted")
    g = dossier.get("gate")
    if g in PRODUCTION_GATES:
        triggers.append(f"gate:{g}")
    if triggers:
        disp = "CHALLENGE_REQUIRED"
    elif cc == "C2":
        disp = "CHALLENGE_OPTIONAL"
    else:
        disp = "CHALLENGE_NOT_REQUIRED"
    return {"disposition": disp, "triggers": sorted(set(triggers)),
            "unweighed": ["novelty", "architectural_significance", "blast_radius", "uncertainty"]}


def verify_council(dossier: dict[str, Any], work_package: dict[str, Any] | None) -> dict[str, Any]:
    """The ONLY enforcement: a claimed pass at CHALLENGE_REQUIRED must carry a
    council record, and that record must be well-formed by BADF's own rules
    (docs/03): first-round ballots sealed, each ballot typed and attributable.

    What this does NOT do, deliberately: a council REJECT does not refuse the
    dossier -- it is evidence for the human authority, not a veto. A council
    APPROVE satisfies no approval quorum. Approvals are untouched.
    """
    result = compute_council_disposition(dossier, work_package)
    council = dossier.get("council")
    claims_pass = dossier.get("disposition") in {"PASS", "PASS_WITH_CONDITIONS"}
    if result["disposition"] == "CHALLENGE_REQUIRED" and claims_pass and not council:
        raise ValidationError(
            "council disposition is CHALLENGE_REQUIRED (" + ", ".join(result["triggers"]) +
            ") but the dossier carries no council record; a pass cannot be claimed unchallenged")
    if council is not None:
        if not isinstance(council, dict):
            raise ValidationError("dossier.council must be an object")
        for f in ("convened_at", "verdict", "ballots"):
            if f not in council:
                raise ValidationError(f"council record missing {f}")
        parse_time(council["convened_at"], "council.convened_at")
        v = expect_str(council["verdict"], "council.verdict")
        if v not in COUNCIL_VERDICTS:
            raise ValidationError(f"council.verdict {v!r} is not one of {sorted(COUNCIL_VERDICTS)}")
        ballots = council["ballots"]
        if not isinstance(ballots, list) or not ballots:
            raise ValidationError("council.ballots must be a non-empty array")
        seen: set[str] = set()
        for i, b in enumerate(ballots):
            lbl = f"council.ballots[{i}]"
            if not isinstance(b, dict):
                raise ValidationError(f"{lbl} must be an object")
            for f in ("by", "principal_type", "verdict", "sealed"):
                if f not in b:
                    raise ValidationError(f"{lbl} missing {f}")
            who = canonical_principal(b["by"], lbl)
            if who in seen:
                raise ValidationError(f"{lbl}: {who!r} cast more than one ballot; the same principal cannot count twice")
            seen.add(who)
            if expect_str(b["principal_type"], f"{lbl}.principal_type") not in PRINCIPAL_TYPES:
                raise ValidationError(f"{lbl} invalid principal_type")
            if expect_str(b["verdict"], f"{lbl}.verdict") not in COUNCIL_VERDICTS:
                raise ValidationError(f"{lbl} invalid verdict")
            if b["sealed"] is not True:
                raise ValidationError(f"{lbl} was not sealed before synthesis; first-round ballots must be independent and sealed")
        result["council_verdict"] = v
        result["ballots"] = len(ballots)
    return result


INTENT_REQUIRED = {"name", "intent", "owner", "target", "repository", "local_path", "demand"}
INTENT_OPTIONAL = {"project_id", "type", "maturity"}   # README documents exactly these; a drift test holds both to it
INTENT_TARGETS = {"production", "sandbox"}
JUDGMENT_FIELDS = ["objective", "business_value", "in_scope", "out_of_scope", "acceptance_criteria"]


def load_demand(demand_id: str) -> dict[str, Any]:
    """The demand record a work package cites, or a refusal.

    Issue #22: a work package had no demand link, and the doctrine says no WP
    without one. But the gate makes no network calls and an Issue's existence
    is knowable only via the API -- and PropTech, the intake probe, has zero
    Issues; its demand record is a [WP-NNNN] token. So a demand is a RECORD
    IN THE TREE: the source exported and digest-bound, existence a file
    check, forgery caught by the lockfile. Same pattern as decisions.

    A demand is where authority ENTERS the system. Unless kind is
    'discovery', authorized_by is required and must be a human principal.
    Agents discover; they do not authorize.
    """
    if not isinstance(demand_id, str) or not DEMAND_ID.match(demand_id):
        raise ValidationError(f"{demand_id!r} is not a demand id (expected BADF-DEM-nnnn)")
    path = ROOT / DEMANDS_DIR / f"{demand_id}.json"
    if not path.is_file():
        raise ValidationError(f"demand {demand_id} does not exist at {DEMANDS_DIR}/{demand_id}.json")
    rec = load_json(path)
    require_fields(rec, DEMAND_FIELDS, f"demand {demand_id}")
    if rec["demand_id"] != demand_id:
        raise ValidationError(f"demand file {path.name} carries id {rec['demand_id']!r}")
    if expect_str(rec["kind"], f"demand {demand_id}.kind") not in DEMAND_KINDS:
        raise ValidationError(f"demand {demand_id} kind {rec['kind']!r} is not one of {sorted(DEMAND_KINDS)}")
    if expect_str(rec["provenance"], f"demand {demand_id}.provenance") not in DEMAND_PROVENANCE:
        raise ValidationError(f"demand {demand_id} provenance {rec['provenance']!r} is not one of {sorted(DEMAND_PROVENANCE)}")
    src = rec["source"]
    if not isinstance(src, dict) or "repository" not in src:
        raise ValidationError(f"demand {demand_id} source must carry a repository")
    parse_time(rec["recorded_at"], f"demand {demand_id}.recorded_at")
    if rec["kind"] != "discovery":
        auth = rec.get("authorized_by")
        if not isinstance(auth, dict):
            raise ValidationError(f"demand {demand_id} missing fields: authorized_by")
        if auth.get("principal_type") != "human":
            raise ValidationError(f"demand {demand_id}: authorized_by must be a human principal; a demand is where authority enters")
        canonical_principal(auth.get("principal"), f"demand {demand_id}.authorized_by")
    return rec



# ---- project instance: YAML subset, schema check, classification (BADF-WP-0021, BADF-DEC-0004) ----
_YAML_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
MATURITY = {"EMPTY", "IDEA", "PRD", "DESIGN", "BUILD", "TEST", "RELEASE", "PRODUCTION"}
PROJECT_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,63}$")
GREENFIELD_ALLOWED = {"README.md", "LICENSE", ".gitignore", ".gitattributes"}
INSTANCE_NAMESPACE = ("AGENTS.md", "badf")


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)   # double-quoted; JSON escapes are valid YAML double-quoted escapes
    raise ValidationError(f"YAML subset cannot represent {type(value).__name__}")


def emit_yaml(doc: dict[str, Any], indent: int = 0) -> str:
    """A strict YAML subset the framework can emit AND parse without a
    dependency: block mappings, block sequences of scalars, double-quoted
    strings, ints, booleans, null. Nothing else, so nothing is guessed."""
    if not isinstance(doc, dict) or not doc:
        raise ValidationError("YAML subset: a mapping must be non-empty")
    pad = " " * indent
    lines: list[str] = []
    for key, value in doc.items():
        if not isinstance(key, str) or not _YAML_KEY.match(key):
            raise ValidationError(f"YAML subset: key {key!r} is not a plain identifier")
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.append(emit_yaml(value, indent + 2).rstrip("\n"))
        elif isinstance(value, list):
            if not value or any(isinstance(item, (dict, list)) for item in value):
                raise ValidationError(f"YAML subset: {key} must be a non-empty list of scalars")
            lines.append(f"{pad}{key}:")
            lines.extend(f"{pad}  - {_yaml_scalar(item)}" for item in value)
        else:
            lines.append(f"{pad}{key}: {_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parses exactly what emit_yaml produces. Comments, flow style, anchors,
    tags, multi-documents, tabs, unquoted strings and duplicate keys are
    refused -- a file outside the subset is a refusal, never a guess."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    items: list[tuple[int, str, str | None, str | None]] = []
    for n, line in enumerate(lines, 1):
        if not line.strip():
            raise ValidationError(f"YAML subset: blank line {n}")
        if "\t" in line:
            raise ValidationError(f"YAML subset: tab at line {n}")
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise ValidationError(f"YAML subset: odd indentation at line {n}")
        body = line[indent:]
        if body[0] in "#-&*{[!%|>" and not body.startswith("- "):
            raise ValidationError(f"YAML subset: construct at line {n} is outside the subset")
        if body.startswith("- "):
            items.append((indent, "item", None, body[2:]))
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?$", body)
        if not m:
            raise ValidationError(f"YAML subset: line {n} is not `key: value`, `key:` or `- item`")
        items.append((indent, "key", m.group(1), m.group(2)))

    def scalar(raw: str, n: int) -> Any:
        if raw == "null":
            return None
        if raw == "true":
            return True
        if raw == "false":
            return False
        if re.fullmatch(r"-?[0-9]+", raw):
            return int(raw)
        if len(raw) >= 2 and raw[0] == raw[-1] == '"':
            try:
                return json.loads(raw)
            except ValueError as exc:
                raise ValidationError(f"YAML subset: bad string at item {n}: {exc}")
        raise ValidationError(f"YAML subset: unquoted or unsupported scalar {raw!r}")

    pos = 0

    def mapping(indent: int) -> dict[str, Any]:
        nonlocal pos
        out: dict[str, Any] = {}
        while pos < len(items) and items[pos][0] == indent and items[pos][1] == "key":
            _, _, key, raw = items[pos]; pos += 1
            if key in out:
                raise ValidationError(f"YAML subset: duplicate key {key}")
            if raw is not None:
                out[key] = scalar(raw, pos)
            elif pos < len(items) and items[pos][0] == indent + 2 and items[pos][1] == "key":
                out[key] = mapping(indent + 2)
            elif pos < len(items) and items[pos][0] == indent + 2 and items[pos][1] == "item":
                seq = []
                while pos < len(items) and items[pos][0] == indent + 2 and items[pos][1] == "item":
                    seq.append(scalar(items[pos][3] or "", pos)); pos += 1
                out[key] = seq
            else:
                raise ValidationError(f"YAML subset: key {key} has no value")
        return out

    doc = mapping(0)
    if pos != len(items):
        raise ValidationError(f"YAML subset: unexpected structure at item {pos + 1}")
    if not doc:
        raise ValidationError("YAML subset: empty document")
    return doc


def check_schema(name: str, inst: Any) -> None:
    """Structural conformance to schemas/<name>.schema.json: required keys,
    enum values at any depth, additionalProperties: false, string patterns.
    Deterministic and dependency-free; runs BEFORE anything is written."""
    sch = load_json(ROOT / "schemas" / f"{name}.schema.json")

    def walk(spec: dict[str, Any], val: Any, where: str) -> None:
        label = where or "document"
        if spec.get("type") == "object" or "properties" in spec:
            if not isinstance(val, dict):
                raise ValidationError(f"{name}: {label} must be a mapping")
            props = spec.get("properties", {})
            missing = sorted(set(spec.get("required", [])) - set(val))
            if missing:
                raise ValidationError(f"{name}: {label} missing {', '.join(missing)}")
            if spec.get("additionalProperties", True) is False:
                extra = sorted(set(val) - set(props))
                if extra:
                    raise ValidationError(f"{name}: {label} carries undefined key(s) {', '.join(extra)}")
            for key, sub in props.items():
                if key in val:
                    walk(sub, val[key], f"{where}.{key}" if where else key)
            return
        # scalar/array type conformance: a declared type must match the JSON type
        # (bool is a Python int subclass, so integer/number exclude it explicitly)
        t = spec.get("type")
        if t == "array" and not isinstance(val, list):
            raise ValidationError(f"{name}: {label} must be an array, got {type(val).__name__}")
        if t == "string" and not isinstance(val, str):
            raise ValidationError(f"{name}: {label} must be a string, got {type(val).__name__}")
        if t == "boolean" and not isinstance(val, bool):
            raise ValidationError(f"{name}: {label} must be a boolean, got {type(val).__name__}")
        if t == "integer" and (not isinstance(val, int) or isinstance(val, bool)):
            raise ValidationError(f"{name}: {label} must be an integer, got {type(val).__name__}")
        if t == "number" and (not isinstance(val, (int, float)) or isinstance(val, bool)):
            raise ValidationError(f"{name}: {label} must be a number, got {type(val).__name__}")
        if "enum" in spec and val not in spec["enum"]:
            raise ValidationError(f"{name}: {label}={val!r} is not one of {spec['enum']}")
        if "pattern" in spec and isinstance(val, str) and not re.fullmatch(spec["pattern"], val):
            raise ValidationError(f"{name}: {label}={val!r} does not match {spec['pattern']}")
        if spec.get("type") == "array" and isinstance(val, list) and "items" in spec:
            for i, item in enumerate(val):
                walk(spec["items"], item, f"{where}[{i}]")

    walk(sch, inst, "")


def classify_project(root: Path) -> str:
    tracked = {t for t in _foreign_git(root, "ls-files").stdout.decode().split("\n") if t}
    return "GREENFIELD" if tracked <= GREENFIELD_ALLOWED else "BROWNFIELD"


def derive_project_id(owner: str, name: str) -> str:
    pid = re.sub(r"[^A-Z0-9]+", "-", f"{owner}-{name}".upper()).strip("-")
    if not PROJECT_ID.match(pid):
        raise ValidationError(f"cannot derive a project id from owner {owner!r} and name {name!r}; declare project_id in the intent")
    return pid


def _digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()



# ---- project instance: lockfile, derived state, validation (BADF-WP-0022) ----
INSTANCE_INTEGRITY = ["badf/project.yaml", "badf/state.json", "badf/evidence/**/*.json"]


def instance_root(path: Path) -> Path:
    inst = Path(path).resolve()
    if inst == ROOT.resolve():
        raise ValidationError("the framework itself is not a project instance")
    if not (inst / "badf/project.yaml").is_file():
        raise ValidationError(f"no instance at {inst}: badf/project.yaml is absent")
    top = _foreign_git(inst, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.decode().strip()).resolve() != inst:
        raise ValidationError(f"{inst} is not a git repository root")
    return inst


def instance_patterns(inst: Path) -> list[str]:
    """AGENTS.md is locked only when BADF generated it; a preserved one is the
    project's file. The decision is read from state.json, which is itself locked."""
    patterns = list(INSTANCE_INTEGRITY)
    if any((inst / "badf/authority").glob("*.json")):
        patterns.append("badf/authority/*.json")
    state_path = inst / "badf/state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if isinstance(state, dict) and state.get("entrypoint") == "AGENTS_MD_GENERATED":
            patterns.append("AGENTS.md")
    return patterns


def write_instance_lock(inst: Path) -> int:
    return write_lock(inst, instance_patterns(inst))


GATE_ORDER = [f"G{i:02d}" for i in range(15)]
BOUND_DIR = "badf/evidence/dossiers"
PASSING_VERDICTS = {"APPROVED", "APPROVED_WITH_CONDITIONS"}


def derive_state(project_id: str, framework_revision: str, wp_id: str, target: str,
                 entrypoint: str, baseline_commit: str, receipt_rel: str,
                 charter: str | None = None, gate: str = "G00", lifecycle_state: str = "INITIALIZED") -> dict[str, Any]:
    """The ONLY way a state.json comes to exist. init writes derive_state(...);
    validation recomputes it from the receipt and refuses a stored state that
    differs -- so a hand-typed state, even re-signed, is refused."""
    return {
        "schema_version": "1.0.0", "project_id": project_id, "framework_revision": framework_revision,
        "lifecycle": {"current_gate": gate, "state": lifecycle_state, "target": target.upper()},
        "active_work_package": wp_id, "active_session": None,
        "authority": {"status": "RESOLVED", "charter": charter} if charter else {"status": "UNRESOLVED"},
        "entrypoint": entrypoint,
        "readiness": {"product": "NOT_STARTED", "architecture": "NOT_STARTED", "engineering": "NOT_STARTED",
                      "security": "NOT_STARTED", "release": "NOT_STARTED", "production": "NOT_READY"},
        "derived_from": {"baseline_commit": baseline_commit, "receipt": receipt_rel},
    }


def _flat(d: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(d, dict):
        out = {}
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
        return out
    return {prefix.rstrip("."): d}


CHARTER = "badf/authority/charter.json"
CHARTER_KEYS = ("change_classes", "human_reserved_roles", "reserved_actions", "rules")


def framework_matrix_at(rev: str) -> tuple[dict[str, Any], str]:
    """The framework's authority matrix at a pinned commit, and the digest of
    that exact blob. The instance's floor is what it pinned, not what HEAD says."""
    raw = _git_bytes("show", f"{rev}:{MATRIX}")
    if raw is None:
        raise ValidationError(f"framework matrix at {rev[:7]} cannot be read from this framework")
    try:
        matrix = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except ValueError as exc:
        raise ValidationError(f"framework matrix at {rev[:7]} is not valid JSON: {exc}")
    return matrix, _digest_bytes(raw)


def validate_charter(inst: Path, project: dict[str, Any], framework_revision: str) -> tuple[str | None, list[str]]:
    """(charter path or None, notes). A charter may only ADD to the floor.
    There is deliberately no acknowledgement path here: an instance cannot
    ack itself below the framework (BADF-DEC-0006)."""
    path = inst / CHARTER
    policy = project["authority"].get("policy")
    if not path.is_file():
        if policy is not None:
            raise ValidationError(f"project.yaml names authority policy {policy!r} but no charter exists")
        return None, []
    charter = load_json(path)
    check_schema("charter", charter)
    if policy != CHARTER:
        raise ValidationError(f"documents disagree on authority policy: project.yaml says {policy!r}, charter exists at {CHARTER}")
    if charter["framework_revision"] != framework_revision:
        raise ValidationError(f"charter pins framework {charter['framework_revision'][:7]} but the instance pins {framework_revision[:7]}")
    if charter["framework_repository"] != self_repository():
        raise ValidationError(f"charter names framework {charter['framework_repository']!r}; this is {self_repository()!r}")
    floor, digest = framework_matrix_at(framework_revision)
    if charter["framework_matrix_digest"] != digest:
        raise ValidationError(f"charter is bound to a different framework matrix ({charter['framework_matrix_digest'][:19]}...) "
                              f"than the one at the pinned revision ({digest[:19]}...)")
    floor_classes, charter_classes = set(floor.get("change_classes", {})), set(charter.get("change_classes", {}))
    if charter_classes - floor_classes:   # an extra class is not a downgrade, so the comparison below cannot see it
        raise ValidationError("charter declares unknown change class(es): " + ", ".join(sorted(charter_classes - floor_classes)))
    # a MISSING class is a downgrade ("change class X removed") and is refused by authority_downgrades below
    downgrades = authority_downgrades(floor, charter)
    if downgrades:
        raise ValidationError("charter lowers the framework floor -- " + "; ".join(downgrades)
                              + ". An instance may add constraints, never remove them; there is no acknowledgement path for instances.")
    notes = []
    current = sha256(ROOT / MATRIX)
    if current != digest:
        notes.append(f"BADF INSTANCE NOTE: framework authority matrix has moved since the pin "
                     f"(pinned {digest[7:14]}, current {current[7:14]}); re-pin to adopt it")
    return CHARTER, notes


def write_charter(path: Path) -> str:
    """`badf_gate.py charter <path>`: the default charter -- floor = ceiling --
    and the re-derived state. Refuses unless the instance validates first."""
    inst = instance_root(path)
    validate_instance(inst)   # deny unless established: a drifted or inconsistent instance gets no charter
    if (inst / CHARTER).exists():
        raise ValidationError(f"{inst} already has a charter at {CHARTER}; narrow it by editing and re-signing, never by regenerating")
    project = parse_yaml_subset((inst / "badf/project.yaml").read_text(encoding="utf-8"))
    state = load_json(inst / "badf/state.json")
    rev = state["framework_revision"]
    floor, digest = framework_matrix_at(rev)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    charter = {"schema_version": "1.0.0", "framework_repository": self_repository(), "framework_revision": rev,
               "framework_matrix_digest": digest, **{k: json.loads(json.dumps(floor.get(k, []))) for k in CHARTER_KEYS},
               "generated_by": "badf-charter", "generated_at": now}
    check_schema("charter", charter)
    new_state = derive_state(state["project_id"], rev, state["active_work_package"], project["delivery"]["target"],
                             state["entrypoint"], state["derived_from"]["baseline_commit"], state["derived_from"]["receipt"],
                             charter=CHARTER)
    check_schema("state", new_state)
    project["authority"]["policy"] = CHARTER
    check_schema("project", project)
    yaml_text = emit_yaml(project)
    if parse_yaml_subset(yaml_text) != project:
        raise ValidationError("project.yaml does not round-trip through the YAML subset; refusing to write it")
    (inst / "badf/authority").mkdir(exist_ok=True)
    (inst / CHARTER).write_text(json.dumps(charter, indent=2) + "\n", encoding="utf-8")
    (inst / "badf/state.json").write_text(json.dumps(new_state, indent=2) + "\n", encoding="utf-8")
    (inst / "badf/project.yaml").write_text(yaml_text, encoding="utf-8")
    write_instance_lock(inst)
    return (f"BADF CHARTER: {state['project_id']} bound to framework matrix {digest[7:14]} at {rev[:7]}; "
            f"authority RESOLVED (floor = ceiling; narrow by adding, never by removing)")


def bound_dossiers(inst: Path) -> list[tuple[str, Path]]:
    """(gate, path) for every file under badf/evidence/dossiers/, in gate order.
    Anything that is not G0N.json is refused: the directory holds bound
    dossiers and nothing else."""
    found = []
    for path in sorted((inst / BOUND_DIR).glob("*")):
        if not path.is_file() or path.stem not in GATE_ORDER or path.suffix != ".json":
            raise ValidationError(f"{BOUND_DIR}/{path.name} is not a bound gate dossier (expected G0N.json)")
        found.append((path.stem, path))
    return sorted(found, key=lambda t: GATE_ORDER.index(t[0]))


def validate_chain(inst: Path, wp_id: str) -> tuple[str, str]:
    """The instance's lifecycle, DERIVED from its bound dossiers (BADF-DEC-0007):
    each bound copy must equal its framework original, the original must
    still render APPROVED, and gates must be contiguous from G00. Returns
    (current_gate, state); (G00, INITIALIZED) when nothing is bound."""
    chain = bound_dossiers(inst)
    if not chain:
        return "G00", "INITIALIZED"
    expected = GATE_ORDER[:len(chain)]
    got = [g for g, _ in chain]
    if got != expected:
        missing = sorted(set(expected) - set(got)) or [expected[0]]
        raise ValidationError(f"bound dossiers are not contiguous from G00: have {', '.join(got)}; missing {', '.join(missing)}")
    for g, path in chain:
        original = ROOT / "work" / wp_id / f"gate-dossier.{g}.json"
        if not original.is_file() or original.read_bytes() != path.read_bytes():
            raise ValidationError(f"bound dossier {g} differs from the framework original work/{wp_id}/gate-dossier.{g}.json (or the original is gone)")
        try:
            rendered = validate_dossier(original)
        except ValidationError as exc:
            raise ValidationError(f"bound dossier {g} no longer validates at the framework ({exc}); the instance cannot stay at {g}")
        if rendered not in PASSING_VERDICTS:
            raise ValidationError(f"bound dossier {g} no longer renders APPROVED at the framework (renders {rendered}); the instance cannot stay at {g}")
    return chain[-1][0], "APPROVED"


def advance_instance(path: Path, dossier_rel: str) -> str:
    """`badf_gate.py advance <instance> work/<WP>/gate-dossier.<gate>.json`:
    bind what humans approved for the instance's NEXT gate; never approve."""
    inst = instance_root(path)
    validate_instance(inst)   # deny unless established
    state = load_json(inst / "badf/state.json")
    wp_id = state["active_work_package"]
    m = re.fullmatch(rf"work/({re.escape(WP_NAMESPACE)}[0-9]{{4}})/gate-dossier\.(G(?:0[0-9]|1[0-4]))\.json", dossier_rel.replace("\\", "/"))
    if not m:
        raise ValidationError(f"dossier must be the framework's work/<WP>/gate-dossier.<gate>.json, got {dossier_rel!r}")
    if m.group(1) != wp_id:
        raise ValidationError(f"dossier belongs to work package {m.group(1)}; this instance's work package is {wp_id}")
    gate_id = m.group(2)
    original = ROOT / dossier_rel
    if not original.is_file():
        raise ValidationError(f"{dossier_rel} does not exist in the framework")
    doc = load_json(original)
    if doc.get("work_package_id") != wp_id:
        raise ValidationError(f"dossier names work package {doc.get('work_package_id')!r}, not {wp_id}")
    if doc.get("gate") != gate_id:
        raise ValidationError(f"dossier says gate {doc.get('gate')!r} but is filed as {gate_id}")
    chain = bound_dossiers(inst)
    next_gate = GATE_ORDER[len(chain)]
    if (inst / BOUND_DIR / f"{gate_id}.json").exists():
        raise ValidationError(f"{gate_id} is already bound in this instance; a gate is passed once")
    if gate_id != next_gate:
        raise ValidationError(f"the instance's next gate is {next_gate}, not {gate_id}")
    rendered = validate_dossier(original)
    if rendered not in PASSING_VERDICTS:
        raise ValidationError(f"{dossier_rel} does not render APPROVED (renders {rendered}); advance binds approvals, it does not grant them")
    project = parse_yaml_subset((inst / "badf/project.yaml").read_text(encoding="utf-8"))
    new_state = derive_state(state["project_id"], state["framework_revision"], wp_id, project["delivery"]["target"],
                             state["entrypoint"], state["derived_from"]["baseline_commit"], state["derived_from"]["receipt"],
                             charter=(state["authority"].get("charter") if state["authority"]["status"] == "RESOLVED" else None),
                             gate=gate_id, lifecycle_state="APPROVED")
    check_schema("state", new_state)
    (inst / BOUND_DIR).mkdir(parents=True, exist_ok=True)
    (inst / BOUND_DIR / f"{gate_id}.json").write_bytes(original.read_bytes())
    (inst / "badf/state.json").write_text(json.dumps(new_state, indent=2) + "\n", encoding="utf-8")
    write_instance_lock(inst)
    return (f"BADF ADVANCE: {state['project_id']} bound {dossier_rel} ({rendered}); lifecycle {gate_id} / APPROVED; "
            f"next gate {GATE_ORDER[len(chain) + 1] if len(chain) + 1 < len(GATE_ORDER) else 'none'}")


def validate_instance(path: Path) -> list[str]:
    """`badf_gate.py instance <path>`: writes nothing; refuses unless every
    claim in the instance is corroborated by another document, by git, or by
    the framework. Returns the lines to print (notes, then the PASS line)."""
    inst = instance_root(path)
    verify_lock(inst, instance_patterns(inst), "instance",
                f"python3 scripts/badf_gate.py lock --instance {inst}")
    project = parse_yaml_subset((inst / "badf/project.yaml").read_text(encoding="utf-8"))
    check_schema("project", project)
    state = load_json(inst / "badf/state.json")
    check_schema("state", state)
    receipts = sorted((inst / "badf/evidence/receipts").glob("init-*.json"))
    if len(receipts) != 1:
        raise ValidationError(f"expected exactly one init receipt, found {len(receipts)}")
    receipt = load_json(receipts[0])
    check_schema("init-receipt", receipt)
    receipt_rel = receipts[0].relative_to(inst).as_posix()

    def agree(label: str, *values: Any) -> Any:
        if any(v != values[0] for v in values[1:]):
            raise ValidationError(f"documents disagree on {label}: {' vs '.join(repr(v) for v in values)}")
        return values[0]

    project_id = agree("project id", project["project"]["id"], state["project_id"], receipt["project_id"])
    framework_revision = agree("framework_revision", project["badf"]["framework_revision"],
                               state["framework_revision"], receipt["framework_revision"])
    wp_id = agree("work package", project["delivery"]["work_package"], receipt["work_package"])
    agree("repository", project["project"]["repository"], receipt["repository"])
    agree("classification", project["project"]["classification"], receipt["classification"])
    agree("framework_repository", project["badf"]["framework_repository"], receipt["framework_repository"], self_repository())
    agree("receipt", state["derived_from"]["receipt"], receipt_rel)
    baseline = agree("baseline commit", state["derived_from"]["baseline_commit"], receipt["baseline_commit"])

    if _foreign_git(inst, "cat-file", "-e", f"{baseline}^{{commit}}").returncode != 0:
        raise ValidationError(f"baseline commit {baseline[:7]} is unknown to the instance")
    if _foreign_git(inst, "merge-base", "--is-ancestor", baseline, "HEAD").returncode != 0:
        raise ValidationError(f"baseline commit {baseline[:7]} is not an ancestor of the instance's HEAD")
    if _git("cat-file", "-e", f"{framework_revision}^{{commit}}") is None:
        raise ValidationError(f"framework_revision {framework_revision[:7]} is unknown to this framework")

    charter_rel, charter_notes = validate_charter(inst, project, framework_revision)
    current_gate, lifecycle_state = validate_chain(inst, wp_id)
    expected = derive_state(project_id, framework_revision, wp_id, project["delivery"]["target"],
                            state["entrypoint"], baseline, receipt_rel, charter=charter_rel,
                            gate=current_gate, lifecycle_state=lifecycle_state)
    if state != expected:
        have, want = _flat(state), _flat(expected)
        diffs = sorted(k for k in set(have) | set(want) if have.get(k) != want.get(k))
        raise ValidationError("state.json disagrees with the derived state on " + ", ".join(diffs)
                              + "; a state that the receipt, the charter and the chain of bound dossiers cannot corroborate is refused")

    notes: list[str] = list(charter_notes)
    agents = inst / "AGENTS.md"
    if state["entrypoint"] == "EXISTING_AGENTS_MD_PRESERVED":
        recorded = next((p["digest"] for p in receipt["preserved"] if p["path"] == "AGENTS.md"), None)
        if recorded is None:
            raise ValidationError("state says AGENTS.md was preserved but the receipt records no preserved AGENTS.md")
        if not agents.is_file():
            notes.append("BADF INSTANCE NOTE: AGENTS.md removed since baseline (project-owned; merge plan required)")
        elif sha256(agents) != recorded:
            notes.append("BADF INSTANCE NOTE: AGENTS.md changed since baseline (project-owned; merge plan required)")
    elif not agents.is_file():
        raise ValidationError("state says BADF generated AGENTS.md but it is absent")
    notes.append(f"BADF INSTANCE PASS: {project_id} ({receipt['repository']}) at "
                 f"{state['lifecycle']['current_gate']} / {state['lifecycle']['state']}; "
                 f"authority {state['authority']['status']}; framework {framework_revision[:7]}; "
                 f"baseline {baseline[:7]}; work package {wp_id}")
    return notes


def load_intent(path: Path) -> dict[str, Any]:
    """The four-line intent (plus where the project lives). JSON is accepted
    as YAML's strict subset -- no new dependency. A document that is not a
    single mapping with a `project` key is refused."""
    if not path.is_file():
        raise ValidationError(f"intent file not found: {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except ValueError as exc:
        raise ValidationError(f"intent must be a JSON/YAML mapping: {exc}")
    proj = doc.get("project") if isinstance(doc, dict) else None
    if not isinstance(proj, dict):
        raise ValidationError("intent must carry a top-level `project` mapping")
    missing = sorted(INTENT_REQUIRED - set(proj))
    if missing:
        raise ValidationError(f"intent.project missing required field(s): {', '.join(missing)}")
    unknown = sorted(set(proj) - INTENT_REQUIRED - INTENT_OPTIONAL)
    if unknown:
        # a typo of an optional key would otherwise be ignored and its value
        # invented as DECLARED_MISSING -- refused, never silently dropped
        raise ValidationError(f"intent.project has unknown field(s): {', '.join(unknown)}; "
                              f"known: {', '.join(sorted(INTENT_REQUIRED | INTENT_OPTIONAL))}")
    for k in INTENT_REQUIRED:
        expect_str(proj[k], f"intent.project.{k}")
        if not proj[k].strip():
            raise ValidationError(f"intent.project.{k} is empty")
    if proj["target"] not in INTENT_TARGETS:
        raise ValidationError(f"intent.project.target {proj['target']!r} is not one of {sorted(INTENT_TARGETS)}")
    return proj


def discover_project(root: Path) -> list[dict[str, str]]:
    """What the target project STATES about itself. init reads; it never
    invents. Each finding is attributed to the file it came from."""
    found: list[dict[str, str]] = []
    agents = root / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text(encoding="utf-8", errors="replace")
        first = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#")), "")
        found.append({"kind": "mandate", "source": "AGENTS.md", "value": first[:200]})
        for l in text.splitlines():
            if l.startswith("## ") and "Mission" in l:
                found.append({"kind": "mission_heading", "source": "AGENTS.md", "value": l.strip("# ").strip()})
                break
    readme = root / "README.md"
    if readme.is_file():
        for l in readme.read_text(encoding="utf-8", errors="replace").splitlines():
            if "Boundary" in l and "binding" in l.lower():
                found.append({"kind": "binding_boundary", "source": "README.md", "value": l.strip("> ").strip()[:200]})
                break
    for cand in root.glob(".github/scripts/*admission*"):
        found.append({"kind": "existing_wp_admission", "source": str(cand.relative_to(root)),
                      "value": "the project already enforces its own work-package reference on commits; BADF ids must not collide"})
    ci = root / ".github/workflows/ci.yml"
    if ci.is_file():
        found.append({"kind": "existing_ci", "source": ".github/workflows/ci.yml", "value": "present"})
    return found


def next_wp_id() -> str:
    nums = []
    for d in (ROOT / "work").glob(f"{WP_NAMESPACE}*"):
        try:
            nums.append(int(d.name.split("-")[-1]))
        except ValueError:
            pass
    return f"{WP_NAMESPACE}{(max(nums) + 1 if nums else 1):04d}"


def init_project(intent_path: Path) -> str:
    """`badf init <intent>`: intake of a project into BADF at G00, and the
    project's own control plane (BADF-DEC-0004):

      DISCOVER  what the project states about itself
      CLASSIFY  GREENFIELD | BROWNFIELD; type / maturity from the intent or DECLARED_MISSING
      BASELINE  target HEAD; the tree must be CLEAN; digest of an existing AGENTS.md
      GENERATE  <project>/AGENTS.md (only if absent) · badf/project.yaml · badf/state.json
      VALIDATE  every document against its schema BEFORE the first byte is written
      REGISTER  the receipt in the project, bound by digest into BADF's G00 evidence;
                the work package, dossier (HUMAN_REQUIRED), registry entry, ledger event

    The write is BOUNDED to <project>/AGENTS.md-if-absent and <project>/badf/.
    Judgment fields stay DECLARED_MISSING; the dossier renders HELD until a
    human supplies them and signs the declarations. An instance is a request
    for authority, not a grant of it.
    """
    proj = load_intent(intent_path)
    dem = load_demand(proj["demand"])
    if dem["source"]["repository"] != proj["repository"]:
        raise ValidationError(
            f"demand {proj['demand']} belongs to {dem['source']['repository']}, but the intent targets "
            f"{proj['repository']}; a demand authorizes work on ONE repository")
    root = Path(proj["local_path"]).resolve()
    if root == ROOT.resolve():
        raise ValidationError("intent.project.local_path is the BADF framework itself; the framework is not a project instance")
    top = _foreign_git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise ValidationError(f"intent.project.local_path {root} is not a git repository")
    if Path(top.stdout.decode().strip()).resolve() != root:
        raise ValidationError(f"intent.project.local_path {root} is not the repository root")
    # The most specific fact refuses first: an existing instance, a duplicate
    # registry entry or a duplicate work package are stronger facts than the
    # dirty tree they may have caused. Nothing is written before any of these.
    if (root / "badf").exists():
        raise ValidationError(f"{root} already has a badf/ control plane; init refuses to overwrite an instance")
    registry_path = ROOT / REPOSITORIES
    registry = load_json(registry_path)
    repos = registry.setdefault("repositories", {})
    if proj["repository"] in repos:
        raise ValidationError(f"{proj['repository']} is already registered; init refuses to overwrite a registry entry")
    existing = [d for d in (ROOT / "work").glob(f"{WP_NAMESPACE}*/work-package.json")
                if load_json(d).get("repository") == proj["repository"]]
    if existing:
        raise ValidationError(f"{proj['repository']} already has work package {existing[0].parent.name}; init refuses to duplicate")
    dirty = _foreign_git(root, "status", "--porcelain").stdout.decode()
    if dirty.strip():
        raise ValidationError(f"target working tree is not clean ({len(dirty.splitlines())} change(s)); "
                              "a baseline requires a clean tree -- commit or stash first")
    head = _foreign_git(root, "rev-parse", "HEAD").stdout.decode().strip()
    remote = _foreign_git(root, "remote", "get-url", "origin")
    remote_url = remote.stdout.decode().strip() if remote.returncode == 0 else None
    framework_revision = _git("rev-parse", "HEAD")
    if not framework_revision or not re.fullmatch(r"[0-9a-f]{40}", framework_revision):
        raise ValidationError("framework revision cannot be established; an instance must pin the framework commit")
    framework_repository = self_repository()

    # DISCOVER / CLASSIFY -- read, never invent
    discovered = discover_project(root)
    classification = classify_project(root)
    ptype = proj.get("type") or "DECLARED_MISSING"
    maturity = proj.get("maturity") or "DECLARED_MISSING"
    if maturity != "DECLARED_MISSING" and maturity not in MATURITY:
        raise ValidationError(f"intent.project.maturity {maturity!r} is not one of {sorted(MATURITY)}")
    project_id = proj.get("project_id") or derive_project_id(proj["owner"], proj["name"])
    if not PROJECT_ID.match(str(project_id)):
        raise ValidationError(f"intent.project.project_id {project_id!r} must match {PROJECT_ID.pattern}")

    # BASELINE
    wp_id = next_wp_id()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stamp = now.replace("-", "").replace(":", "")
    agents_path = root / "AGENTS.md"
    agents_exists = agents_path.is_file()
    agents_digest = _digest_bytes(agents_path.read_bytes()) if agents_exists else None
    receipt_rel = f"badf/evidence/receipts/init-{stamp}.json"

    project_doc: dict[str, Any] = {
        "badf": {"schema_version": "1.0.0", "framework_repository": framework_repository, "framework_revision": framework_revision},
        "project": {"id": project_id, "name": proj["name"], "repository": proj["repository"],
                    "classification": classification, "type": ptype, "maturity": maturity},
        "ownership": {"organization": proj["owner"], "product_owner": None, "service_owner": None},
        "mission": {"intent": proj["intent"]},
        "delivery": {"target": proj["target"], "lifecycle": "G00-G14", "work_package": wp_id},
        "authority": {"mode": "bounded-autonomous", "fail_closed": True, "policy": None},
        "evidence": {"root": "badf/evidence", "receipts": "badf/evidence/receipts"},
        "state": {"file": "badf/state.json"},
    }
    state_doc = derive_state(project_id, framework_revision, wp_id, proj["target"],
                             "EXISTING_AGENTS_MD_PRESERVED" if agents_exists else "AGENTS_MD_GENERATED",
                             head, receipt_rel)
    template_path = ROOT / "templates/AGENTS.instance.md"
    if not template_path.is_file():
        raise ValidationError("templates/AGENTS.instance.md is missing from the framework; refusing to invent an entrypoint")
    template = template_path.read_text(encoding="utf-8")
    agents_text = template
    for key, value in {"PROJECT_NAME": proj["name"], "FRAMEWORK_REPOSITORY": framework_repository,
                       "FRAMEWORK_REVISION": framework_revision, "WORK_PACKAGE": wp_id, "RECEIPT": receipt_rel}.items():
        agents_text = agents_text.replace("{{" + key + "}}", value)
    if "{{" in agents_text:
        raise ValidationError("templates/AGENTS.instance.md carries a placeholder init does not fill")
    contents: list[tuple[str, bytes]] = []
    if not agents_exists:
        contents.append(("AGENTS.md", agents_text.encode("utf-8")))
    contents.append(("badf/project.yaml", emit_yaml(project_doc).encode("utf-8")))
    contents.append(("badf/state.json", (json.dumps(state_doc, indent=2) + "\n").encode("utf-8")))
    receipt: dict[str, Any] = {
        "schema_version": "1.0.0", "operation": "badf.init", "project_id": project_id, "repository": proj["repository"],
        "baseline_commit": head, "baseline_tree": "CLEAN",
        "framework_repository": framework_repository, "framework_revision": framework_revision,
        "classification": classification, "maturity": maturity,
        "generated": [{"path": rel, "digest": _digest_bytes(data)} for rel, data in contents],
        "preserved": [{"path": "AGENTS.md", "digest": agents_digest}] if agents_exists else [],
        "conflicts": [{"path": "AGENTS.md", "disposition": "PRESERVED_MERGE_PLAN_REQUIRED"}] if agents_exists else [],
        "validation": "PASS", "recorded_at": now, "work_package": wp_id,
    }
    # VALIDATE -- all four documents, before the first byte is written
    check_schema("project", project_doc)
    check_schema("state", state_doc)
    check_schema("init-receipt", receipt)
    if parse_yaml_subset(emit_yaml(project_doc)) != project_doc:
        raise ValidationError("project.yaml does not round-trip through the YAML subset; refusing to write it")
    receipt_bytes = (json.dumps(receipt, indent=2) + "\n").encode("utf-8")

    # GENERATE -- the bounded write
    (root / "badf/evidence/receipts").mkdir(parents=True)
    for rel, data in contents:
        (root / rel).write_bytes(data)
    (root / receipt_rel).write_bytes(receipt_bytes)
    write_instance_lock(root)   # the signature over the governed files; not a generated claim

    # REGISTER -- BADF's side
    wp_dir = ROOT / "work" / wp_id
    wp_dir.mkdir(parents=True)
    wp: dict[str, Any] = {
        "$schema": "../../schemas/work-package.schema.json", "schema_version": "1.0.0",
        "id": wp_id, "title": f"{proj['name']}: {proj['intent']}", "owner": proj["owner"],
        "repository": proj["repository"], "demand": proj["demand"],
        "objective": "DECLARED_MISSING", "business_value": "DECLARED_MISSING",
        "in_scope": "DECLARED_MISSING", "out_of_scope": "DECLARED_MISSING", "acceptance_criteria": "DECLARED_MISSING",
        "declared_missing": list(JUDGMENT_FIELDS),
        "target_gate": "G00",
        "change_class": "C3",
        "change_class_rationale": "a new product targeting " + proj["target"] + " is high blast radius under the matrix's own C3 definition; lowering it is a human judgment, recorded in a dossier",
        "data_classification": "restricted",
        "data_classification_rationale": "deny-unless-established: the most restrictive class until the owner declares otherwise",
        "permissions": [f"read: {proj['repository']}",
                        f"write: {proj['repository']} bounded to AGENTS.md-if-absent and badf/ (BADF-DEC-0004); nothing else"],
        "tests": ["DECLARED_MISSING"], "evidence": ["authority", "scope", "risk-classification", "init-receipt"],
        "rollback": {"reversible": True, "method": "a project at G00 has started nothing; withdrawing the work package and removing the instance namespace is the rollback"},
        "status": "DRAFT",
        "discovered": discovered,
        "instance": {"project_id": project_id, "classification": classification, "entrypoint": state_doc["entrypoint"],
                     "receipt": receipt_rel, "framework_revision": framework_revision},
        "external_target": {"repository": proj["repository"], "branch": "main", "base_revision": head,
                            "remote_url": remote_url, "remote_verified": remote_url is not None},
        "intent": {k: proj[k] for k in ("name", "intent", "owner", "target")},
        "initialized_at": now,
    }
    (wp_dir / "work-package.json").write_text(json.dumps(wp, indent=2) + "\n", encoding="utf-8")
    ev_dir = wp_dir / "evidence/G00"; ev_dir.mkdir(parents=True)
    decls = {
        "authority": f"PREPARED, UNSIGNED. {proj['owner']} must authorize {proj['name']} for BADF governance at G00. An agent prepared this declaration; only a human signature makes it evidence.",
        "scope": f"PREPARED, UNSIGNED. Intent as given: {proj['intent']}. in_scope / out_of_scope are DECLARED_MISSING and must be supplied by the owner.",
        "risk-classification": f"PREPARED, UNSIGNED. Derived C3 (new {proj['target']} product) and data_classification restricted, both deny-unless-established; the owner may lower either in a dossier, never here.",
    }
    index = []
    for t, text in decls.items():
        art = ev_dir / f"{t}.txt"; art.write_text(text + "\n", encoding="utf-8")
        e = {"schema_version": "1.0.0", "id": f"EVD-{wp_id}-G00-{t}", "work_package_id": wp_id, "gate": "G00",
             "claim": text.split(". ", 1)[1][:160], "evidence_type": t,
             "producer": {"id": "badf-init", "type": "controller"},
             "source_revision": head, "target": f"{proj['repository']}:main",
             "toolchain": {"name": "badf-init", "version": "1"}, "operation": "prepare declaration",
             "started_at": now, "completed_at": now, "outcome": "NOT_RUN",
             "artifact": f"work/{wp_id}/evidence/G00/{art.name}", "digest": sha256(art)}
        (ev_dir / f"{t}.json").write_text(json.dumps(e, indent=2) + "\n", encoding="utf-8")
        index.append({"type": t, "path": f"work/{wp_id}/evidence/G00/{t}.json"})
    # the receipt, byte-identical, bound as G00 evidence: the first link of the chain
    art = ev_dir / "init-receipt.receipt.json"; art.write_bytes(receipt_bytes)
    e = {"schema_version": "1.0.0", "id": f"EVD-{wp_id}-G00-init-receipt", "work_package_id": wp_id, "gate": "G00",
         "claim": f"init wrote a bounded instance into {proj['repository']} at {head[:12]}: {len(contents)} generated, "
                  f"{1 if agents_exists else 0} preserved; the receipt is the same bytes as {receipt_rel} in the project",
         "evidence_type": "init-receipt", "producer": {"id": "badf-init", "type": "controller"},
         "source_revision": head, "target": f"{proj['repository']}:main",
         "toolchain": {"name": "badf-init", "version": "2"}, "operation": "initialise instance",
         "started_at": now, "completed_at": now, "outcome": "PASS",
         "artifact": f"work/{wp_id}/evidence/G00/{art.name}", "digest": sha256(art)}
    (ev_dir / "init-receipt.json").write_text(json.dumps(e, indent=2) + "\n", encoding="utf-8")
    index.append({"type": "init-receipt", "path": f"work/{wp_id}/evidence/G00/init-receipt.json"})
    dossier = {
        "schema_version": "1.0.0", "id": f"DOS-{wp_id}-G00-v1", "work_package_id": wp_id, "gate": "G00",
        "policy_epoch": load_json(ROOT / "badf/lifecycle.json")["policy_epoch"],
        "source_revision": head, "target": f"{proj['repository']}:main", "change_class": "C3",
        "author": "badf-init", "author_type": "controller",
        "evidence": index, "approvals": [], "conditions": [], "non_coverage": [], "exceptions": [],
        "risks": [], "council": None,
        "disposition": "HUMAN_REQUIRED", "created_at": now,
        "held_because": f"demand {proj['demand']} ({dem['kind']}); 5 judgment fields DECLARED_MISSING; 3 G00 declarations PREPARED but UNSIGNED; C3 requires "
                        + ", ".join(load_json(ROOT / MATRIX)["change_classes"]["C3"]["required_roles"]) + " approvals"
                        + ("; existing AGENTS.md preserved -- merge plan required" if agents_exists else ""),
    }
    (wp_dir / "gate-dossier.G00.json").write_text(json.dumps(dossier, indent=2) + "\n", encoding="utf-8")
    repos[proj["repository"]] = {"local_path": str(root), "default_branch": "main", "resolution": "LOCAL_MIRROR",
                                 "remote_url": remote_url, "remote_verified": remote_url is not None,
                                 "registered_by": "badf-init", "registered_at": now, "work_package": wp_id,
                                 "instance": {"entrypoint": state_doc["entrypoint"], "receipt": receipt_rel}}
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    # The contract's second phase, recorded rather than assumed (#294): init's authority
    # to write this intake is the operator's invocation, and until now that basis left no
    # trace in the ledger at all. The witness names what the authority actually WAS -- it
    # does not assert a check that never happened, and it grants nothing: the dossier this
    # run produces stays HELD / HUMAN_REQUIRED.
    append_event(wp_dir, "init", "AUTHORITY_CHECKED", "badf-init", "controller", effect_id="intake",
                 note="authority for this intake is the operator invocation of `badf init`; "
                      "no gate authority is claimed and the G00 dossier remains HUMAN_REQUIRED")
    append_event(wp_dir, "init", "COMMITTED", "badf-init", "controller", effect_id="intake",
                 output_digest=sha256(wp_dir / "work-package.json"),
                 note=f"intake of {proj['repository']} at {head[:12]} ({classification}); instance {receipt_rel}; "
                      f"{len(discovered)} facts discovered; {len(JUDGMENT_FIELDS)} judgment fields DECLARED_MISSING; dossier HUMAN_REQUIRED")
    write_lockfile()
    written = ", ".join(rel for rel, _ in contents) + f", {receipt_rel}"
    return (f"BADF INIT: {wp_id} created at G00, disposition HUMAN_REQUIRED; instance written to {root}: {written}"
            + ("; AGENTS.md preserved (merge plan required)" if agents_exists else ""))


SELF_G07_EVIDENCE = ("source-change", "build", "unit-test", "documentation")


def _diff_bytes(*args: str) -> bytes:
    r = _foreign_git(ROOT, "diff", *args)
    if r.returncode != 0:
        raise ValidationError(f"git diff {' '.join(args)} failed: {r.stderr.decode(errors='replace')[:200]}")
    return r.stdout



# ---- badf-build BLD-B: the build ledger (recovery and evidence, never authority) ----
BUILD_LEDGER = "build/progress.jsonl"


def _event_hash(event: dict[str, Any]) -> str:
    body = {k: v for k, v in event.items() if k != "event_hash"}
    return "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def append_build_event(wp_id: str, step: str, outcome: str, note: str) -> dict[str, Any]:
    """Append one hash-chained run-ledger event to work/<WP>/build/progress.jsonl.
    Nothing reads the ledger for a verdict; it exists so a resumed or compacted
    session cannot redispatch finished work and so the build's transitions are evidence."""
    path = ROOT / "work" / wp_id / BUILD_LEDGER
    path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash, seq = GENESIS_HASH, 1
    if path.is_file():
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if lines:
            last = json.loads(lines[-1]); prev_hash = last["event_hash"]; seq = int(last["sequence"]) + 1
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    event = {"event_id": f"EVT-{wp_id}-{seq:04d}", "workflow_id": wp_id, "sequence": seq, "step": step, "outcome": outcome,
             "actor": {"id": "badf-self-dossier", "type": "controller"}, "recorded_at": now, "note": note,
             "previous_event_hash": prev_hash}
    event["event_hash"] = _event_hash(event)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def verify_build_ledger(wp_id: str) -> str:
    """`badf_gate.py build-ledger <WP>`: read-only chain verification of the build ledger.
    Exit 0 when every event's hash recomputes and links to its predecessor; 1 otherwise.
    The dossier verdict never consults this."""
    m = WP_ID_FORMS.match(wp_id.strip())
    if not m:
        raise ValidationError(f"{wp_id!r} is not a work package id")
    wp_id = f"{WP_NAMESPACE}{m.group(1)}"
    path = ROOT / "work" / wp_id / BUILD_LEDGER
    if not path.is_file():
        raise ValidationError(f"{wp_id} has no build ledger at work/{wp_id}/{BUILD_LEDGER}")
    prev, count = GENESIS_HASH, 0
    for n, line in enumerate((l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()), 1):
        event = json.loads(line)
        for k in ("event_id", "workflow_id", "sequence", "step", "outcome", "actor", "recorded_at", "previous_event_hash", "event_hash"):
            if k not in event:
                raise ValidationError(f"build ledger chain broken at line {n}: missing {k}")
        if event["workflow_id"] != wp_id or int(event["sequence"]) != n:
            raise ValidationError(f"build ledger chain broken at line {n}: sequence/workflow mismatch")
        if event["previous_event_hash"] != prev:
            raise ValidationError(f"build ledger chain broken at line {n}: previous_event_hash does not link")
        if event["event_hash"] != _event_hash(event):
            raise ValidationError(f"build ledger chain broken at line {n}: event_hash does not recompute (tampered)")
        prev = event["event_hash"]; count = n
    return f"BADF BUILD-LEDGER PASS: {wp_id} {count} events, chain intact (recovery/evidence only; no verdict is derived from it)"


def self_dossier(wp_id: str) -> str:
    """`badf_gate.py self-dossier <WP>`: assemble a G07 gate dossier for one of
    BADF's OWN work packages, from measured evidence, as a HUMAN_REQUIRED
    request. It binds; it never approves. Run it AFTER the deliverables are
    committed and BEFORE committing the dossier: the source-change diff is
    taken against HEAD, excluding the work package's own directory and the
    lockfile, so committing this dossier does not change it."""
    m = WP_ID_FORMS.match(wp_id.strip())
    if not m:
        raise ValidationError(f"{wp_id!r} is not a work package id")
    wp_id = f"{WP_NAMESPACE}{m.group(1)}"
    wp_dir = ROOT / "work" / wp_id
    wp_path = wp_dir / "work-package.json"
    if not wp_path.is_file():
        raise ValidationError(f"{wp_id} has no record at work/{wp_id}/work-package.json")
    wp = load_json(wp_path)
    if wp.get("repository") != self_repository():
        raise ValidationError(f"{wp_id} targets {wp.get('repository')!r}; self-dossier is for this repository's own work only")
    base = ((wp.get("external_target") or {}).get("base_revision"))
    if not base:
        raise ValidationError(f"{wp_id} has no external_target.base_revision to diff against")
    _require_authorized_demand(wp, wp_id)                       # C1: no request without validated authority
    # GOV-0108: the ratchet bites at assembly too -- the same refusal at the moment
    # planning would otherwise skate past it, reported where controls report.
    if _surface_ratchet_applies(wp_id):
        _files = [str(x) for x in ((wp.get("expected_surfaces") or {}).get("files") or [])]
        if not _files:
            raise ValidationError(f"{wp_id}: no expected_surfaces.files declared -- mandatory at and above the threshold WP-2026-0126 (GOV-0108); declare the surface before assembling")
        _bad = _unmatchable_declared(wp_id, _files)
        if _bad:
            raise ValidationError(f"{wp_id}: expected_surfaces.files declares {_bad}, which can never match the governed diff (GOV-0108)")
    _check_build_budget_and_stop(wp_dir, wp, wp_id)             # C6: a stopped or exhausted build is not packaged
    _check_delegations(wp_dir, wp, wp_id)                       # C7: delegations must be subsets before anything is bound
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    ev_dir = wp_dir / "evidence/G07"
    ev_dir.mkdir(parents=True, exist_ok=True)
    exclude = ["--", ".", f":(exclude)work/{wp_id}/", ":(exclude)badf/lockfile.json"]
    change = _diff_bytes(f"{base}..HEAD", *exclude)
    if not change:
        raise ValidationError(f"{wp_id}: no change between {base[:12]} and HEAD (outside its own directory); nothing to govern -- commit the deliverables first")
    docs = _diff_bytes(f"{base}..HEAD", "--", "docs/", "README.md", "AGENTS.md")
    py = subprocess.run([sys.executable, "-m", "py_compile", "scripts/badf_gate.py", "scripts/badf_compose.py"],
                        cwd=ROOT, capture_output=True, text=True)
    build_txt = f"python -m py_compile scripts/badf_gate.py scripts/badf_compose.py -> exit {py.returncode}\n{py.stderr}"
    # ---- BLD-B typed bindings (BADF-WP-0098): exactness lives here, not in source_revision ----
    base_full = _git("rev-parse", base) or base
    head_full = _git("rev-parse", "HEAD") or "HEAD"
    names = sorted((_git("diff", "--name-only", f"{base}..HEAD", *exclude) or "").split())
    ctree = content_tree(ROOT, wp_id, "HEAD")
    surfaces = wp.get("expected_surfaces") or {}
    patterns = [str(x) for x in (surfaces.get("files") or [])]
    declared = bool(patterns)
    allowance = [str(x) for x in (surfaces.get("discovery_allowance") or [])]
    # #272 unification (GOV-0119): may-touch means ONE thing at both sites. A path
    # covered by discovery_allowance is never `unexpected` here, exactly as the
    # binding-side C3 exempts it; binding keeps its own filter because bindings
    # written before this unification still carry allowance-covered paths.
    unexpected = [n for n in names if declared
                  and not any(_surface_match(n, pat) for pat in patterns)
                  and not any(_surface_match(n, a) for a in allowance)]
    # GOV-0102 (#232): the mirror direction -- a declared files pattern that matched no changed
    # path. files is must-touch (it is also the C7 delegation ceiling, BLD-I10); a pattern that
    # is supposed to match nothing belongs in discovery_allowance, which never widens C7.
    unmatched_declared = [pat for pat in patterns if not any(_surface_match(n, pat) for n in names)]
    build_cmd = f"{sys.executable} -m py_compile scripts/badf_gate.py scripts/badf_compose.py"
    build_binding = {"command": build_cmd, "cwd": ".", "environment": {"python": platform.python_version(), "platform": platform.platform()},
                     "exit_code": py.returncode, "artifacts": [{"ref": r, "digest": sha256(ROOT / r)} for r in ("scripts/badf_gate.py", "scripts/badf_compose.py")],
                     "non_coverage": []}
    modules = [str(x).split()[0] for x in (wp.get("tests") or []) if str(x).strip()]
    log_path = ev_dir / "unit-test.log"; ff_path = ev_dir / "failing-first.txt"
    fresh_run = "scripts/badf_compose.py (the composed-tree gate) re-runs the suite on the tree that would land; CI is the fresh, authoritative run (BLD-I09)"
    if log_path.is_file():
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        ut_result, ut_ran, ut_failures = _parse_unittest_log(log_text)
        if ut_result == "FAIL":
            raise ValidationError(f"{wp_id}: the author's unit-test log {log_path.name} reports FAILED ({ut_failures}); fix the tests before assembling -- a request must not bind a failing run (BLD-I09)")
        if ut_result == "NOT_RUN":
            raise ValidationError(f"{wp_id}: {log_path.name} carries no `Ran N tests` / OK transcript; bind a real unittest log")
        first = log_text.strip().splitlines()[0] if log_text.strip() else ""
        ut_command = first if first.startswith(("python", "uv ")) else f"{sys.executable} -m unittest " + " ".join(modules)
        ut_outcome, ut_artifact_data, ut_artifact_name = "PASS", None, "unit-test.log"
    else:
        ut_result, ut_ran, ut_failures, ut_command = "NOT_RUN", 0, 0, "deferred-to-compose"
        ut_outcome, ut_artifact_name = "NOT_RUN", "unit-test.txt"
        ut_artifact_data = (b"Unit tests are executed by the composed-tree gate (scripts/badf_compose.py) on the tree that would land. "
                            b"This dossier is a REQUEST; its test evidence is the PR's BADF COMPOSE PASS transcript, not a run by this tool.\n")
    red_obs = ff_path.is_file()
    obligations = [{"id": f"TEST-{i + 1:03d}", "seam": {"type": "module", "ref": m},
                    "red": ({"observed": True, "ref": f"work/{wp_id}/evidence/G07/failing-first.txt", "digest": sha256(ff_path)} if red_obs else {"observed": False}),
                    "green": ({"observed": True, "ref": f"work/{wp_id}/evidence/G07/unit-test.log", "digest": sha256(log_path)} if log_path.is_file() else {"observed": False})}
                   for i, m in enumerate(modules)]
    unit_binding = {"obligations": obligations, "command": ut_command, "result": ut_result, "tests_run": ut_ran, "failures": ut_failures,
                    "coverage_scope": modules, "fresh_run": fresh_run}
    # C4 (BLD-I07/I08): declared unit obligations need an observed red, or an explicit exception with a reason.
    if any(isinstance(o, dict) and o.get("level") == "unit" for o in (wp.get("test_obligations") or [])) and not red_obs:
        reason = str(((wp.get("tdd_exception") or {}).get("reason")) or "").strip() if isinstance(wp.get("tdd_exception"), dict) else ""
        if not reason:
            raise ValidationError(f"{wp_id}: the work package declares unit test obligations but no failing-first (red) observation is bound and no tdd_exception.reason is declared; TDD is required at a durable seam or its absence is explicit, never silent (BLD-I07 / BLD-I08 / C4)")
        unit_binding["tdd"] = {"applies": False, "reason": reason}
    doc_changed = [n for n in names if n.startswith("docs/") or n in ("README.md", "AGENTS.md")]
    contract_changed = any(n.startswith("schemas/") or n in ("badf/lifecycle.json", "badf/skill-registry.json") for n in names)
    behavior_changed = any(n.startswith("scripts/") for n in names)
    doc_binding = {"changed": doc_changed, "contract_changed": contract_changed, "behavior_changed": behavior_changed,
                   "required_updates": (["docs/ (behavior changed under scripts/ with no documentation change)"] if behavior_changed and not doc_changed else []),
                   "not_updated_with_reason": str(wp.get("documentation_note") or ("no documentation changed in this work package" if not doc_changed else "documentation changed with the work package"))}
    source_binding_partial = {"base_sha": base_full, "head_sha": head_full, "content_tree": ctree, "changed_paths": names,
                              "expected_surfaces": {"declared": declared, "files": patterns}, "unexpected_paths": unexpected}
    build_dir = wp_dir / "build"; build_dir.mkdir(parents=True, exist_ok=True)
    session = {"work_package_id": wp_id, "producer": "badf-self-dossier", "started_at": now, "base_sha": base_full, "head_sha": head_full, "content_tree": ctree}
    if (build_dir / "session.json").is_file():
        prior = load_json(build_dir / "session.json") or {}
        if prior.get("delegations"):
            session["delegations"] = prior["delegations"]   # declared delegations survive re-assembly (C7 judged them)
    (build_dir / "session.json").write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    append_build_event(wp_id, "START", "OK", "self-dossier assembly started")
    append_build_event(wp_id, "BASELINE", "OK", f"base {base_full[:12]} head {head_full[:12]} content tree {ctree[:12]}")

    artifacts = {
        "source-change": (change, "git diff", "PASS", f"the change {wp_id} makes to this repository, outside its own directory and the lockfile", "source-change.diff", None),
        "build": (build_txt.encode(), "py_compile", "PASS" if py.returncode == 0 else "FAIL", "the modules compile", "build.txt", build_binding),
        "unit-test": (ut_artifact_data, ut_command if ut_result != "NOT_RUN" else "deferred-to-compose", ut_outcome,
                      ("the author's unit-test run, bound; the composed-tree gate is the fresh run" if ut_result != "NOT_RUN" else "unit tests run in the composed-tree gate, not here"),
                      ut_artifact_name, unit_binding),
        "documentation": (docs if docs else b"", "git diff", "PASS" if docs else "NOT_APPLICABLE", "the documentation this change carries", "documentation.diff", doc_binding),
    }
    index, non_coverage = [], []
    for t in SELF_G07_EVIDENCE:
        data, op, outcome, claim, art_name, binding = artifacts[t]
        art = ev_dir / art_name
        if data is not None:
            art.write_bytes(data)
        rel_art = f"work/{wp_id}/evidence/G07/{art.name}"
        rec = {"schema_version": "1.0.0", "id": f"EVD-{wp_id}-G07-{t}", "work_package_id": wp_id, "gate": "G07",
               "claim": claim, "evidence_type": t, "producer": {"id": "badf-self-dossier", "type": "controller"},
               "source_revision": "HEAD", "target": f"{self_repository()}:main",
               "toolchain": {"name": op if len(op) < 40 else "unittest", "version": "1"}, "operation": op,
               "started_at": now, "completed_at": now, "outcome": outcome,
               "artifact": rel_art, "digest": sha256(art)}
        if t == "source-change":
            binding = dict(source_binding_partial, change_digest=rec["digest"])
        rec["binding"] = binding
        check_schema(t, rec)   # production-time conformance: the producer refuses to write a malformed binding
        (ev_dir / f"{t}.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        index.append({"type": t, "path": f"work/{wp_id}/evidence/G07/{t}.json"})
        if outcome == "NOT_APPLICABLE":
            non_coverage.append({"evidence_type": t, "reason": "no documentation changed in this work package", "declared_by": "badf-self-dossier"})
    if not declared:
        non_coverage.append({"evidence_type": "source-change", "reason": "expected_surfaces not declared on the work package; surface containment is not measurable (BLD-I04)", "declared_by": "badf-self-dossier"})
    append_build_event(wp_id, "VERIFY", "OK" if ut_result == "PASS" else ut_result, f"unit-test {ut_result}: ran {ut_ran}, failures {ut_failures}; build exit {py.returncode}")
    record = ev_dir / "composition-record.json"
    if record.is_file():
        # GIT-E (BADF-WP-0076): the composition claim written by `badf_compose.py --record`
        # is indexed as `composition` evidence when present. Its binding is the content
        # tree (work/<WP>/ and the lockfile excluded), so indexing it here does not move it;
        # compose verifies it on the tree that would land.
        rec = {"schema_version": "1.0.0", "id": f"EVD-{wp_id}-G07-composition", "work_package_id": wp_id, "gate": "G07",
               "claim": f"the composition claim of {wp_id}: the expected content tree bound to its target base "
                        f"(recomputed and compared by scripts/badf_compose.py on the composed tree)",
               "evidence_type": "composition", "producer": {"id": "badf-self-dossier", "type": "controller"},
               "source_revision": "HEAD", "target": f"{self_repository()}:main",
               "toolchain": {"name": "badf_compose.py --record", "version": "1"}, "operation": "badf_compose.py --record",
               "started_at": now, "completed_at": now, "outcome": "PASS",
               "artifact": f"work/{wp_id}/evidence/G07/composition-record.json", "digest": sha256(record)}
        (ev_dir / "composition.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        index.append({"type": "composition", "path": f"work/{wp_id}/evidence/G07/composition.json"})
    condition = {"condition_id": "C-1",
                 "statement": "An independent reviewer distinct from the author has not recorded an approval; BADF runs under a single collaborator (recorded, not hidden -- see GITHUB_CONTROL_PLANE.md).",
                 "status": "OPEN", "severity": "Major", "blocking_scope": "G09",
                 "owner": "engineering_owner",
                 "closure_predicate": "a distinct human independent_reviewer records an approval, or the deviation is accepted in a decision record",
                 "closure_authority": "quality_authority"}
    conditions = [condition]
    held_extra = ""
    if unexpected:
        conditions.append({"condition_id": "C-2",
                           "statement": f"BLD-I04 scope containment: {len(unexpected)} changed path(s) fall outside the declared expected_surfaces: {', '.join(unexpected)}",
                           "status": "OPEN", "severity": "Major", "blocking_scope": "G07", "owner": "engineering_owner",
                           "closure_predicate": "planning amends expected_surfaces to admit the paths, or the change is reverted to the declared surface",
                           "closure_authority": "quality_authority"})
        held_extra = f" Unexpected paths outside expected_surfaces: {', '.join(unexpected)} (BLD-I04) -- refused or re-authorized, never absorbed."
    if unmatched_declared:
        conditions.append({"condition_id": f"C-{len(conditions) + 1}",
                           "statement": f"GOV-0102 two-sided scope containment: {len(unmatched_declared)} declared expected_surfaces pattern(s) match no changed path: {', '.join(unmatched_declared)}; an unexercised declaration widens the C7 delegation ceiling (BLD-I04 / C3)",
                           "status": "OPEN", "severity": "Major", "blocking_scope": "G07", "owner": "engineering_owner",
                           "closure_predicate": "planning prunes the pattern or moves it to discovery_allowance, or the change grows to touch it",
                           "closure_authority": "quality_authority"})
        held_extra += f" Declared surfaces matching no changed path: {', '.join(unmatched_declared)} (BLD-I04 / GOV-0102) -- pruned or exercised, never carried."
    dossier = {
        "schema_version": "1.0.0", "id": f"DOS-{wp_id}-G07-v1", "work_package_id": wp_id, "gate": "G07",
        "policy_epoch": load_json(ROOT / "badf/lifecycle.json")["policy_epoch"],
        "source_revision": "HEAD", "target": f"{self_repository()}:main",
        "change_class": expect_str(wp.get("change_class"), f"{wp_id}.change_class"),
        "author": "badf-self-dossier", "author_type": "controller",
        "evidence": index, "approvals": [], "conditions": conditions, "non_coverage": non_coverage,
        "exceptions": [], "risks": [], "council": None,
        "disposition": "HUMAN_REQUIRED", "created_at": now,
        "held_because": f"BADF's own work package {wp_id} at G07: evidence prepared and digest-bound; the independent-reviewer "
                        f"condition C-1 is open under a single collaborator; a human merges. The tool binds evidence, it does not approve." + held_extra,
    }
    (wp_dir / "gate-dossier.G07.json").write_text(json.dumps(dossier, indent=2) + "\n", encoding="utf-8")
    append_build_event(wp_id, "HANDOFF", "OK", "G07 dossier assembled, disposition HUMAN_REQUIRED")
    write_lockfile()
    return (f"BADF SELF-DOSSIER: {wp_id} G07 assembled, disposition HUMAN_REQUIRED; "
            f"source-change {len(change)} bytes bound to {base[:7]}..HEAD; a human merges. "
            f"Validate: python3 scripts/badf_gate.py dossier work/{wp_id}/gate-dossier.G07.json (exit 3 = HELD).")



# ---- research record checks: record / source / claim (BADF-WP-0036, #29 research track, RSR-002) ----
def derive_confidence(basis: dict[str, Any]) -> str:
    """Confidence is computed from the basis, never self-reported (the mandate
    forbids 'agent confidence' in evidence semantics). A pure function of
    independent_primary_sources, reproducible and contradictions -- the table
    in skills/badf-research/references/evidence-contract.md."""
    ips = basis["independent_primary_sources"]; repro = basis["reproducible"]; contra = basis["contradictions"]
    if ips == 0:
        return "VERY_LOW"
    if ips == 1:
        return "MODERATE" if repro else "LOW"
    if not repro:
        return "MODERATE"
    return "HIGH" if contra > 0 else "VERY_HIGH"


def compute_research_evidence_digest(rec: dict[str, Any]) -> str:
    """The digest of a record's MATERIAL evidence -- its sources, claims,
    contradictions and experiments. Interpretation (findings, recommendation,
    disposition, and a claim's semantic_support -- fact-checking's reading of
    the evidence under RSR-I06) is deliberately excluded: the digest changes
    when the evidence changes, not when its reading does (RSR-002 control 17).
    Canonical JSON so the same evidence always yields the same digest."""
    material = {k: rec[k] for k in ("sources", "contradictions", "experiments")}
    # semantic_support is fact-checking's reading of a claim (RSR-I06), not the
    # evidence itself; support_assessments (a top-level key) is likewise a reading
    # and is already outside the material set. Excluding both keeps recording an
    # assessment from invalidating the evidence digest, like findings/disposition.
    material["claims"] = [{k: v for k, v in c.items() if k != "semantic_support"} for c in rec["claims"]]
    blob = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def validate_research_record(path: Path) -> str:
    """`badf_gate.py research <path>`: the deterministic record/source/claim
    controls of the frozen research contract (RSR-002). Schema conformance,
    referential integrity, derived confidence, and the invariants that a
    VERIFIED claim rests on an independent primary source and an OBSERVED
    claim on a primary source. Research output never grants implementation
    authority. Later work packages add the challenge, state-transition and
    traceability controls."""
    rec = load_json(path)
    # check_schema enforces implementation_authority == false (RSR-I01) via the
    # schema's enum [false]; a separate check here would be dead code (a mutant
    # proved the schema catches it first).
    check_schema("research-record", rec)
    # 19: the scope contract is bounded and machine-readable (WP-0045). The root
    # skill instructs resolving stop conditions; the record must carry non-empty
    # stop_conditions (no unbounded research), assumptions distinct from evidence,
    # and the decision it serves. These are framing, not evidence -- they are
    # excluded from the evidence_digest, so control 17 is unaffected.
    if not [s for s in rec["stop_conditions"] if s.strip()]:
        raise ValidationError("research record declares no bounded stop_conditions; a material research run states when it stops (control 19)")
    for a in rec["assumptions"]:
        if not a.strip():
            raise ValidationError("research record has an empty assumption; an assumption is a non-empty statement kept distinct from evidence (control 19)")
    if not rec["decision_context"]["decision_question"].strip():
        raise ValidationError("research record decision_context.decision_question is empty; research must name the decision it serves (control 19)")
    # 20: framing precedes evidence (problem-framing). A record in a pre-evidence
    # state carries no claims, sources, or findings -- framing sharpens the
    # question; it does not research or answer it.
    if rec["state"] in {"PROPOSED", "FRAMED", "BASELINED"}:
        premature = [n for n in ("claims", "sources", "findings") if rec[n]]
        if premature:
            raise ValidationError(f"research record is in pre-evidence state {rec['state']} but carries {', '.join(premature)}; framing precedes evidence collection (control 20)")
    # 3: repository research (R02/R03) baselines to a commit that RESOLVES in its
    # repository -- an investigation cannot be anchored to a commit that does not
    # exist. Mirrors verify_foreign_revision's resolution and UNRESOLVABLE_HERE.
    if rec["type"] in {"R02", "R03"}:
        repo_name = rec["baseline"]["repository"]
        revision = rec["baseline"]["revision"]
        registry = load_json(ROOT / REPOSITORIES)
        entry = (registry.get("repositories") or {}).get(repo_name)
        if not isinstance(entry, dict) or "local_path" not in entry:
            raise ValidationError(f"repository research baselines to {repo_name}, which is not registered in {REPOSITORIES} (control 3)")
        repo_root = (ROOT / entry["local_path"]).resolve() if not Path(entry["local_path"]).is_absolute() else Path(entry["local_path"])
        top = _foreign_git(repo_root, "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            if entry.get("resolution") == "LOCAL_MIRROR" and not repo_root.exists():
                raise ValidationError(f"UNRESOLVABLE_HERE: {repo_name} is a LOCAL_MIRROR at {repo_root}, absent on this host; validate this record where the mirror exists")
            raise ValidationError(f"registered path {repo_root} for {repo_name} is not a git repository")
        if _foreign_git(repo_root, "cat-file", "-e", f"{revision}^{{commit}}").returncode != 0:
            raise ValidationError(f"baseline revision {revision[:12]} does not resolve in {repo_name}; repository research must baseline to a real commit (control 3)")
    source_ids = [src["id"] for src in rec["sources"]]
    if len(source_ids) != len(set(source_ids)):
        raise ValidationError("research record has duplicate source ids")
    sources = {src["id"]: src for src in rec["sources"]}
    claim_ids = set()
    for c in rec["claims"]:
        cid = c["id"]
        if cid in claim_ids:
            raise ValidationError(f"research record has duplicate claim id {cid}")
        claim_ids.add(cid)
        for ref in c["supporting_sources"] + c["contradicting_sources"]:
            if ref not in sources:
                raise ValidationError(f"claim {cid} references source {ref} that the record does not carry")
        want = derive_confidence(c["confidence"]["basis"])
        if c["confidence"]["level"] != want:
            raise ValidationError(f"claim {cid} confidence {c['confidence']['level']} is not the derived level {want}; confidence is computed from its basis, not asserted")
        supporting_primary = any(sources[r]["source_type"] == "PRIMARY" for r in c["supporting_sources"])
        if c["status"] == "VERIFIED":
            if c["confidence"]["basis"]["independent_primary_sources"] < 1 or not supporting_primary:
                raise ValidationError(f"claim {cid} is VERIFIED but rests on no independent primary source (RSR-I02)")
        if c["classification"] == "OBSERVED" and not supporting_primary:
            raise ValidationError(f"claim {cid} is OBSERVED but cites no primary source; an observation is of the thing itself, not a report of it (RSR-I03)")
        # 21: a claim's status is consistent with its evidence (fact-checking). NO
        # EVIDENCE != FALSE; and a dispute is support and contradiction coexisting.
        # (Whether a source's CONTENT entails the claim is not machine-checkable
        # here -- the source carries no content locator -- and is tracked separately.)
        if c["status"] == "FALSIFIED" and not c["contradicting_sources"]:
            raise ValidationError(f"claim {cid} is FALSIFIED but cites no contradicting source; no evidence is not falsification (control 21)")
        if c["status"] == "DISPUTED" and not (c["supporting_sources"] and c["contradicting_sources"]):
            raise ValidationError(f"claim {cid} is DISPUTED but does not carry both supporting and contradicting evidence; a dispute is support and contradiction coexisting (control 21)")
        # 6: a changed source digest makes dependent claims stale. deep-research
        # re-resolves a source and sets its freshness (CURRENT when an immutable
        # revision resolves or the digest is unchanged; STALE when the bytes
        # changed; UNKNOWN when it could not be resolved). A claim may not rest on
        # a STALE or UNKNOWN source -- source unavailable/changed fails closed.
        for ref in c["supporting_sources"] + c["contradicting_sources"]:
            if sources[ref]["freshness"] != "CURRENT":
                raise ValidationError(f"claim {cid} rests on source {ref} whose freshness is {sources[ref]['freshness']}; a stale or unresolvable source cannot support a claim (control 6)")
        # 27: a VERIFIED claim must not silently represent a source as supporting
        # it (RSR-I06; SOURCE_EXISTS != SOURCE_SUPPORTS_CLAIM). The gate never
        # proves entailment -- it requires the record to be honest about whether
        # semantic support was assessed. A VERIFIED claim on cited support either
        # carries a fact-checking receipt (with a locator) for each supporting
        # source, or explicitly declares semantic-support NON_COVERAGE. Silence is
        # refused. (The receipts themselves are checked for well-formedness and
        # substantiation below, once every claim and source is known.)
        if c["status"] == "VERIFIED" and c["supporting_sources"]:
            mode = c.get("semantic_support")
            if mode is None:
                raise ValidationError(f"claim {cid} is VERIFIED on cited support but declares no semantic_support; a VERIFIED binding carries a fact-checking receipt or declares NON_COVERAGE -- semantic support is never represented in silence (RSR-I06, control 27)")
            if mode == "ASSESSED":
                receipted = {a["source_ref"] for a in rec.get("support_assessments", []) if a["claim_ref"] == cid}
                for ref in c["supporting_sources"]:
                    if ref not in receipted:
                        raise ValidationError(f"claim {cid} declares semantic_support ASSESSED but carries no support-assessment receipt for supporting source {ref}; an assessed binding is receipted per source (RSR-I06, control 27)")
    # 27 (receipts): every support-assessment resolves to a carried claim and
    # source, carries a non-empty locator, and -- where it names a source cited as
    # support for a VERIFIED claim -- its own assessment substantiates that support.
    # A receipt the record's own reading does not substantiate cannot back a
    # VERIFIED binding (RSR-I06). The gate checks the assessment happened under
    # contract; it never asserts the source entails the claim.
    claims_by_id = {c["id"]: c for c in rec["claims"]}
    substantiating = {"SUPPORTS", "PARTIALLY_SUPPORTS"}
    for i, a in enumerate(rec.get("support_assessments", [])):
        if a["claim_ref"] not in claims_by_id:
            raise ValidationError(f"support_assessments[{i}] names claim {a['claim_ref']} the record does not carry (RSR-I06, control 27)")
        if a["source_ref"] not in sources:
            raise ValidationError(f"support_assessments[{i}] names source {a['source_ref']} the record does not carry (RSR-I06, control 27)")
        if not a["locator"]["value"].strip():
            raise ValidationError(f"support_assessments[{i}] carries an empty locator; a receipt names where in the source it looked (RSR-I06, control 27)")
        claim = claims_by_id[a["claim_ref"]]
        substantiates = a["relation"] in substantiating and a["assessment"] in ("SUBSTANTIATED", "PARTIALLY_SUBSTANTIATED")
        if claim["status"] == "VERIFIED" and a["source_ref"] in claim["supporting_sources"] and not substantiates:
            raise ValidationError(f"support_assessments[{i}]: source {a['source_ref']} is cited as support for VERIFIED claim {a['claim_ref']}, but its receipt records {a['relation']}/{a['assessment']}; a source the record's own assessment does not substantiate cannot back a VERIFIED binding (RSR-I06, control 27)")
    for f in rec["findings"]:
        # 22: a finding is grounded in the claims it synthesises (evidence-synthesis).
        # A synthesis conclusion rests on adjudicated claims, not free assertion.
        if not f["claim_refs"]:
            raise ValidationError(f"finding {f['id']} rests on no claim; a finding is synthesis of adjudicated evidence, not a free assertion (control 22)")
        missing = sorted(set(f["claim_refs"]) - claim_ids)
        if missing:
            raise ValidationError(f"finding {f['id']} references claim(s) the record does not carry: {', '.join(missing)}")

    # 23: a TECHNICAL_SOLUTION run yields candidate approaches, each grounded in
    # the record's evidence (technical-research). An R04 record carries at least
    # one alternative, and every alternative's evidence_refs resolves to a claim,
    # finding or source the record holds -- an option is proposed on the strength
    # of gathered evidence, not asserted.
    if rec["type"] == "R04" and not rec["alternatives"]:
        raise ValidationError("technical-solution research (R04) carries no alternatives; it must yield at least one candidate approach (control 23)")
    # An evidence_ref that is shaped like a record id (C-/F-/S-nnn) must resolve to
    # a claim, finding or source the record holds; free-form external references are
    # left as-is. This catches a dangling in-record citation without forbidding an
    # external pointer or a rationale string.
    grounded = claim_ids | {f["id"] for f in rec["findings"]} | set(sources)
    for alt in rec["alternatives"]:
        for ref in alt.get("evidence_refs") or []:
            if re.fullmatch(r"[CFS]-[0-9]{3,}", ref) and ref not in grounded:
                raise ValidationError(f"alternative {alt['id']} cites in-record evidence {ref} that is absent; an id-shaped evidence_ref must resolve to a claim, finding or source it holds (control 23)")
    # 24: a comparison needs at least two options to weigh (comparative-evaluation).
    # A COMPARATIVE (R07) run of one alternative is not a comparison.
    if rec["type"] == "R07" and len(rec["alternatives"]) < 2:
        raise ValidationError("comparative research (R07) carries fewer than two alternatives; a comparison needs at least two options to weigh (control 24)")
    # 28: an empirical run measures something (experimental-research). An R08
    # (EMPIRICAL_EXPERIMENT) record carries at least one experiment, and every
    # experiment -- in any record -- tests a hypothesis the record actually holds.
    # A run that measured nothing, or an experiment on a hypothesis the record
    # never stated, is not an experiment. Mirror of controls 23/24: type-specific
    # structure, grounded in the record. The experiment mechanism itself (method,
    # result, and reproduction under the composed-tree gate) is the evidence; the
    # gate checks the experiment is real and bound, not that the result is true.
    if rec["type"] == "R08" and not rec["experiments"]:
        raise ValidationError("empirical-experiment research (R08) carries no experiment; a controlled measurement that ran nothing measures nothing (control 28)")
    hypothesis_ids = {h["id"] for h in rec["hypotheses"]}
    for e in rec["experiments"]:
        if e["hypothesis_ref"] not in hypothesis_ids:
            raise ValidationError(f"experiment {e['id']} tests hypothesis {e['hypothesis_ref']} the record does not hold; an experiment is bound to a stated hypothesis, not a dangling reference (control 28)")

    # ---- challenge / independence controls (RSR-003, BADF-WP-0037) ----
    # 10: source count is not source independence -- the basis cannot claim more
    # independent primary sources than the claim actually cites.
    for c in rec["claims"]:
        cited_primary = len({r for r in c["supporting_sources"] if sources[r]["source_type"] == "PRIMARY"})
        if c["confidence"]["basis"]["independent_primary_sources"] > cited_primary:
            raise ValidationError(f"claim {c['id']}: basis claims {c['confidence']['basis']['independent_primary_sources']} independent primary sources but cites {cited_primary}; source count is not independence")
    # challenge is REQUIRED (computed, not asserted) at depth D4/D5 or type R06.
    required = rec["challenge"]["required"]
    must_challenge = rec["depth"] in {"D4", "D5"} or rec["type"] == "R06"
    if must_challenge and not required:
        raise ValidationError(f"{rec['type']}/{rec['depth']} requires independent challenge, but challenge.required is false; the requirement is computed, not asserted")
    council = rec["challenge"]["council"]
    if council is not None:
        if not isinstance(council, dict) or not isinstance(council.get("ballots"), list) or not council["ballots"]:
            raise ValidationError("challenge council must be an object with a non-empty ballots array")
        researcher = rec["researcher"]["principal"]
        reviewers = []
        for i, ballot in enumerate(council["ballots"]):
            if not isinstance(ballot, dict) or not {"reviewer", "principal_type", "verdict", "non_coverage"} <= set(ballot):
                raise ValidationError(f"council ballot[{i}] must carry reviewer, principal_type, verdict, non_coverage")
            if ballot["verdict"] not in {"CONFIRMED", "REFUTED", "INCONCLUSIVE"}:
                raise ValidationError(f"council ballot[{i}] verdict {ballot['verdict']!r} is not one of CONFIRMED, REFUTED, INCONCLUSIVE")
            if not isinstance(ballot["non_coverage"], list):
                raise ValidationError(f"council ballot[{i}] must declare non_coverage as a list (a reviewer states what they did not cover)")
            if ballot["reviewer"] == researcher:
                raise ValidationError(f"council ballot[{i}]: the researcher {researcher!r} cannot ballot on their own research (RSR-I05)")
            reviewers.append(ballot["reviewer"])
        if len(reviewers) != len(set(reviewers)):
            raise ValidationError("council has a duplicate reviewer identity; one identity cannot increase quorum")
    if required:
        if not isinstance(council, dict):
            raise ValidationError("challenge is required but no council record is present")
        distinct = {b["reviewer"] for b in council["ballots"]}
        if len(distinct) < 2:
            raise ValidationError(f"a required independent challenge needs at least two distinct reviewers; found {len(distinct)}")

    # ---- conclusion integrity + traceability (RSR-004, BADF-WP-0038) ----
    disposition = rec["disposition"]["state"]
    state = rec["state"]
    # 25: an independent refutation cannot be erased by declaring sufficiency
    # (adversarial-research). If the challenge council carries a REFUTED ballot,
    # the research is not RESEARCH_SUFFICIENT -- a critical contradiction is not
    # overridden by a majority or by the disposition; it reconciles to a
    # non-sufficient state (CONTRADICTORY_EVIDENCE, MORE_RESEARCH_REQUIRED, ...).
    if council is not None and disposition == "RESEARCH_SUFFICIENT":
        if any(b["verdict"] == "REFUTED" for b in council["ballots"]):
            raise ValidationError("the challenge council carries a REFUTED ballot but the disposition is RESEARCH_SUFFICIENT; an independent refutation cannot be erased by declaring sufficiency (control 25)")
    # 16: a disposition other than the in-flight RESEARCH_BLOCKED means the record
    # concluded, which is the RECONCILED state -- an invalid state fails closed.
    if disposition != "RESEARCH_BLOCKED" and state != "RECONCILED":
        raise ValidationError(f"disposition {disposition} means the research concluded, but state is {state}, not RECONCILED; a state that the content does not support is refused")
    if state == "CHALLENGED" and not isinstance(council, dict):
        raise ValidationError("state is CHALLENGED but no council record is present")
    # 8: contradictory evidence is preserved -- a contradictions[] entry references
    # real claims, and a claim that cites contradicting sources is recorded there,
    # not buried in the claim (RSR-I04).
    contradicted = set()
    for x in rec["contradictions"]:
        bad = sorted(set(x["claim_refs"]) - claim_ids)
        if bad:
            raise ValidationError(f"contradiction {x['id']} references claim(s) the record does not carry: {', '.join(bad)}")
        contradicted.update(x["claim_refs"])
    for c in rec["claims"]:
        if c["contradicting_sources"] and c["id"] not in contradicted:
            raise ValidationError(f"claim {c['id']} cites contradicting sources but no contradictions[] entry records it; contradictory evidence is preserved, not buried")
    # 15: only RESEARCH_SUFFICIENT makes a work package eligible downstream; a
    # not-sufficient disposition cannot have spawned an implementation work package.
    down = rec["downstream"]
    if disposition != "RESEARCH_SUFFICIENT" and down["work_package_id"] is not None:
        raise ValidationError(f"disposition {disposition} names downstream work package {down['work_package_id']}, but only RESEARCH_SUFFICIENT makes a work package eligible")
    # 26: sufficiency means the evidence was synthesised (research-reconciliation).
    # A RESEARCH_SUFFICIENT record carries at least one finding -- research declared
    # sufficient on the strength of nothing synthesised is incoherent.
    if disposition == "RESEARCH_SUFFICIENT" and not rec["findings"]:
        raise ValidationError("disposition is RESEARCH_SUFFICIENT but the record carries no findings; sufficiency means the evidence was synthesised into at least one finding (control 26)")
    # 18: the chain Issue -> demand -> research -> decision -> work package can be
    # reconstructed. The demand resolves; a named decision resolves; a named work
    # package has a record; and a named decision governs the named work package.
    # 17: the evidence_digest is computed from the material evidence, not
    # asserted; a claim or source edited without re-digesting is stale.
    want_digest = compute_research_evidence_digest(rec)
    if rec["evidence_digest"] != want_digest:
        raise ValidationError(f"evidence_digest {rec['evidence_digest']} is not the digest of this record's sources/claims/contradictions/experiments ({want_digest[:19]}...); it is computed, not asserted -- re-digest when the evidence changes")
    load_demand(rec["demand"])
    if down["decision_id"] is not None:
        dec = load_decision(down["decision_id"])
        if down["work_package_id"] is not None:
            dec_wp = re.search(r"([0-9]{4})$", str(dec.get("work_package_id") or ""))
            this_wp = re.search(r"([0-9]{4})$", down["work_package_id"])
            if not dec_wp or not this_wp or dec_wp.group(1) != this_wp.group(1):
                raise ValidationError(f"decision {down['decision_id']} governs {dec.get('work_package_id')!r}, not {down['work_package_id']}; the Research -> Decision -> Work Package chain does not reconstruct")
    if down["work_package_id"] is not None:
        wp_path = ROOT / "work" / down["work_package_id"] / "work-package.json"
        if not wp_path.is_file():
            raise ValidationError(f"downstream work package {down['work_package_id']} has no record; the chain cannot be reconstructed")

    return f"BADF RESEARCH PASS: {rec['id']} ({rec['type']}/{rec['depth']}) -- {len(rec['claims'])} claims, disposition {rec['disposition']['state']}; grants no implementation authority"


def validate_architecture_assurance(path: Path) -> str:
    """`badf_gate.py assure <path>`: the ASSURE controls (13-18) of the frozen
    badf-architecture contract (WP-ARCH-C). Read-only: an assurance record binds
    to one baseline and one observed revision, never infers compliance, never
    self-authorises drift, declares its non-coverage, and grants no authority."""
    rec = load_json(path)
    check_schema("architecture-assurance", rec)
    base_rev = (rec["baseline"]["revision"] or "").strip()
    obs_rev = (rec["observed"]["revision"] or "").strip()
    conclusion = rec["conclusion"]
    # 13: an ASSURE run binds one baseline revision and one observed revision;
    # assessment against an unpinned, moving state is invalid (ARCH-I09).
    if not base_rev or not obs_rev:
        raise ValidationError("architecture assurance has no bound baseline or observed revision; assessment against an unpinned state is invalid (control 13)")
    # 14: NO BASELINE != COMPLIANT -- a compliance verdict rests on a bound
    # baseline digest; missing architecture documentation yields observations,
    # never compliance (ARCH-I07).
    if conclusion == "COMPLIANT" and not rec["baseline"]["digest"]:
        raise ValidationError("architecture assurance concludes COMPLIANT with no baseline digest; missing architecture yields observations, never compliance (control 14)")
    # 15: an INDETERMINATE ADR-compliance result cannot serialise as a COMPLIANT pass.
    if conclusion == "COMPLIANT" and any(a["result"] == "INDETERMINATE" for a in rec["adr_compliance"]):
        raise ValidationError("architecture assurance concludes COMPLIANT while an ADR compliance result is INDETERMINATE; INDETERMINATE never converts to PASS (control 15)")
    # 16: the read-only run identifies drift; it cannot classify drift as approved
    # evolution -- only independent authority may (ARCH-I08).
    for d in rec["drift"]:
        if d["classification"] == "APPROVED_EVOLUTION_NOT_BASELINED":
            raise ValidationError(f"drift {d['id']} classifies itself as approved evolution, but an ASSURE run identifies drift, it does not authorise it (control 16)")
    # 17: an ASSURE run declares what it did not inspect.
    if not rec["non_coverage"]:
        raise ValidationError("architecture assurance declares no non-coverage; a run that states nothing uninspected is incomplete (control 17)")
    # 18: single baseline -- every finding is assessed against the one bound
    # baseline revision; a stale baseline cannot silently pass (ARCH-I01).
    for f in rec["findings"]:
        if f["baseline_ref"] != base_rev:
            raise ValidationError(f"finding {f['finding_id']} baseline_ref {f['baseline_ref']!r} is not the record's single bound baseline {base_rev!r}; one assurance, one baseline (control 18)")
    return f"BADF ASSURE PASS: {rec['id']} -- baseline {base_rev[:12]} vs observed {obs_rev[:12]}; conclusion {conclusion}; grants no implementation authority"


def validate_verification_record(path: Path) -> str:
    """`badf_gate.py verify <path>`: the structural controls of a G08 verification record
    (badf-engineering-verification VER-B). One record in the canonical gate -- not a second
    validator (VER-I20) and not a lifecycle result. Every ballot cites the council's sealed input
    digest (VER-I05); no reviewer identity or run counts twice (VER-I19); the author's run cannot
    ballot (VER-I04); every balloted finding is carried or withdrawn with a reason -- synthesis
    cannot erase (VER-I12); every finding names a persisted ballot (VER-I06); matrix refs resolve;
    a VERIFIED row carries no OPEN blocking finding and needs a composed-tree observation
    (VER-I15); non-coverage is declared (VER-I11); the record grants no authority (VER-I18)."""
    rec = load_json(path)
    check_schema("verification-record", rec)
    _no_placeholders(rec, "verification-record")
    sealed = rec["target"]["sealed_input_digest"]
    ind = rec["independence"]
    if ind["sealed_input_digest"] != sealed:
        raise ValidationError("independence.sealed_input_digest differs from the target's sealed input digest (VER-I05)")
    ballots = rec["ballots"]
    if not ballots:
        raise ValidationError("verification record carries no ballot; nothing was reviewed (VER-I04)")
    ballot_ids, reviewers, runs = [], [], []
    for b in ballots:
        if b["sealed_input_digest"] != sealed:
            raise ValidationError(f"ballot {b['ballot_id']} cites a sealed input digest that is not the council's; a ballot on other inputs is not this review (VER-I05)")
        if b["reviewer_run_id"] == ind["author_run_id"]:
            raise ValidationError(f"ballot {b['ballot_id']}: reviewer run {b['reviewer_run_id']!r} is the author run; the build execution cannot review its own candidate (VER-I04)")
        ballot_ids.append(b["ballot_id"]); reviewers.append(b["reviewer"]); runs.append(b["reviewer_run_id"])
    if len(set(ballot_ids)) != len(ballot_ids):
        raise ValidationError("verification record carries a duplicate ballot_id")
    if len(set(reviewers)) != len(reviewers) or len(set(runs)) != len(runs):
        raise ValidationError("council has a duplicate reviewer identity or run; one execution cannot increase quorum (VER-I19)")
    findings = {f["finding_id"]: f for f in rec["findings"]}
    if len(findings) != len(rec["findings"]):
        raise ValidationError("verification record carries a duplicate finding_id")
    withdrawn = {w["finding_id"] for w in rec["synthesis"]["withdrawn"]}
    for b in ballots:
        for fid in b["finding_ids"]:
            if fid not in findings and fid not in withdrawn:
                raise ValidationError(f"ballot {b['ballot_id']} reported {fid} but the record neither carries it nor withdraws it with a reason; synthesis cannot erase a finding (VER-I12)")
    for d in rec["synthesis"]["downgraded"]:
        if d["finding_id"] not in findings:
            raise ValidationError(f"synthesis downgrades {d['finding_id']}, which the record does not carry (VER-I12)")
        # #271: the entry must DESCRIBE the finding it names. Only id-existence was checked,
        # so a downgrade could claim any from/to while the finding carried a third severity --
        # a justification that justifies nothing. The governed path existed and was optional.
        if findings[d["finding_id"]]["severity"] != d["to"]:
            raise ValidationError(f"synthesis downgrades {d['finding_id']} to {d['to']} but the finding carries "
                                  f"severity {findings[d['finding_id']]['severity']}; a downgrade entry that does not "
                                  f"describe its finding justifies nothing (VER-I12)")
    # #271: WITHDRAWN is reachable only through synthesis.withdrawn, which requires a reason and
    # a `by`. Setting the status directly erases the finding with neither -- the unjustified route
    # was free while the justified one was optional, which is what VER-I12 exists to prevent.
    # #271: and the inverse -- an entry whose finding is still carried open is justification
    # without effect. `withdrawn` is the escape hatch for findings NOT carried, so a record
    # that both carries a finding open and claims it withdrawn contradicts itself.
    for w in rec["synthesis"]["withdrawn"]:
        f = findings.get(w["finding_id"])
        if f is not None and f["status"] != "WITHDRAWN":
            raise ValidationError(f"synthesis withdraws {w['finding_id']} but the record still carries it with "
                                  f"status {f['status']}; a finding cannot be both carried and withdrawn (VER-I12)")
    for f in rec["findings"]:
        if f["status"] == "WITHDRAWN" and f["finding_id"] not in withdrawn:
            raise ValidationError(f"finding {f['finding_id']} carries status WITHDRAWN with no synthesis.withdrawn "
                                  f"entry naming a reason and a `by`; a finding withdrawn by fiat is erased, not "
                                  f"withdrawn (VER-I12)")
    for b in ballots:
        # #211: the ballot layer's own coherence. The matrix layer already refuses a VERIFIED row
        # over an OPEN blocking finding, and check_g08_binding refuses this shape on a review
        # binding -- but the record's ballots were unchecked, so APPROVE could cite an OPEN MAJOR
        # it raised itself. Strict APPROVE only: APPROVE_WITH_CONDITIONS over an open finding is
        # the conditional arc and REJECT over open findings is the rejecting arc; both are honest.
        # status/severity are READ from the record, not recomputed from evidence: the record is
        # the persisted decision and this module has no independent source of truth for it.
        # Deliberate, not an oversight (BADF-QA on #267).
        if b["verdict"] != "APPROVE":
            continue
        # The association is two-sided and the record checks neither direction for
        # reciprocity: a ballot cites via finding_ids, a finding names reporters via
        # reported_by/also_reported_by, and nothing requires them to agree. Walking only
        # finding_ids left the same proposition reachable from the other side -- an APPROVE
        # with finding_ids: [] while the findings side still named it as the reporter of an
        # OPEN MAJOR. Take the union so neither side alone can hide the contradiction.
        associated = set(b["finding_ids"]) | {f["finding_id"] for f in rec["findings"]
                                              if b["ballot_id"] in f["reported_by"] + f["also_reported_by"]}
        cited_open = [fid for fid in associated
                      if fid in findings and findings[fid]["status"] == "OPEN"
                      and findings[fid]["severity"] in BLOCKING_SEVERITIES]
        if cited_open:
            raise ValidationError(f"ballot {b['ballot_id']}: verdict APPROVE contradicts OPEN blocking finding(s) "
                                  f"{', '.join(sorted(cited_open))} associated with it (by its own finding_ids or by the "
                                  f"finding naming it as reporter); a verdict cannot contradict its own findings")
    for f in rec["findings"]:
        if not f["reported_by"]:
            raise ValidationError(f"finding {f['finding_id']} has no reporting ballot; a finding nobody balloted is invented (VER-I06)")
        for bid in f["reported_by"] + f["also_reported_by"]:
            if bid not in ballot_ids:
                raise ValidationError(f"finding {f['finding_id']} cites reporter {bid}, which is not a persisted ballot (VER-I06)")
    evidence_ids = set(rec["evidence_index"])
    for i, row in enumerate(rec["matrix"]):
        for bid in row["review_refs"]:
            if bid not in ballot_ids:
                raise ValidationError(f"matrix[{i}] {row['claim_ref']}: review_ref {bid} does not resolve to a ballot")
        for key in ("integration_refs", "contract_refs", "composed_refs"):
            for eid in row[key]:
                if eid not in evidence_ids:
                    raise ValidationError(f"matrix[{i}] {row['claim_ref']}: {key} {eid} does not resolve to an indexed evidence id")
        if row["result"] == "VERIFIED":
            against = [f["finding_id"] for f in rec["findings"] if f["status"] == "OPEN" and f["severity"] in BLOCKING_SEVERITIES
                       and set(f["reported_by"] + f["also_reported_by"]) & set(row["review_refs"])]
            if against:
                raise ValidationError(f"matrix[{i}] {row['claim_ref']} is VERIFIED while OPEN blocking finding(s) {', '.join(against)} stand against it (MAJOR/CRITICAL)")
            if not row["composed_refs"]:
                raise ValidationError(f"matrix[{i}] {row['claim_ref']} is VERIFIED without a composed-tree observation; source-head success is not composed verification (VER-I15)")
    if not rec["non_coverage"]:
        raise ValidationError("verification record declares no non-coverage; a review that states nothing uninspected is incomplete (VER-I11)")
    open_count = sum(1 for f in rec["findings"] if f["status"] == "OPEN")
    return (f"BADF VERIFY PASS: {rec['id']} -- target {rec['target']['source_revision'][:12]} tree {rec['target']['expected_content_tree'][:12]}; "
            f"{len(ballots)} ballot(s), {len(findings)} finding(s) ({open_count} open), matrix {len(rec['matrix'])} row(s); grants no verification authority")


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
    expect_str(dossier["change_class"], "dossier.change_class")
    expect_str(dossier["disposition"], "dossier.disposition")
    if dossier["change_class"] not in CLASS_RANK:
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
    # QA finding B1 (BLOCKER): change_class was self-asserted and the
    # lifecycle's minimum_change_class was never read. A G09 dossier (floor
    # C2, four roles) declaring C0 passed with ONE reviewer -- no forgery, no
    # re-sign, nothing in the diff for a reviewer to notice. The floor is a
    # floor. Refuse rather than silently promote: the author must reclassify
    # visibly.
    floor = gate.get("minimum_change_class")
    if floor not in CLASS_RANK:
        raise ValidationError(f"gate {gate['id']} declares no valid minimum_change_class; refusing")
    if CLASS_RANK[dossier["change_class"]] < CLASS_RANK[floor]:
        raise ValidationError(
            f"dossier change_class {dossier['change_class']} is below the gate's minimum_change_class "
            f"{floor} for {gate['id']} -- reclassify; the floor is not negotiable per dossier")
    if not isinstance(dossier["evidence"], list):
        raise ValidationError("dossier evidence must be an array")

    indexed: dict[str, str] = {}
    for item in dossier["evidence"]:
        if not isinstance(item, dict) or not {"type", "path"} <= set(item):
            raise ValidationError("evidence index items require type and path")
        expect_str(item["type"], "evidence index type")
        if item["type"] in indexed:
            raise ValidationError(f"duplicate evidence type: {item['type']}")
        indexed[item["type"]] = item["path"]

    # QA finding M1: approvals were not validated at all under FAIL / BLOCKED /
    # HUMAN_REQUIRED, so `approvals: "garbage"` and author self-approval both
    # passed through on a FAIL dossier. The SHAPE of every approval is checked
    # on every disposition; the QUORUM only when the disposition claims a pass.
    validate_authority(dossier, require_quorum=dossier["disposition"] in {"PASS", "PASS_WITH_CONDITIONS"})
    if dossier["disposition"] in {"PASS", "PASS_WITH_CONDITIONS"}:
        missing = sorted(set(gate["required_evidence"]) - set(indexed))
        if missing:
            raise ValidationError("passing dossier missing evidence: " + ", ".join(missing))

    matrix_classes = load_json(ROOT / "badf/authority-matrix.json")["change_classes"]
    known_roles = {role for entry in matrix_classes.values() for role in entry["required_roles"]}
    validate_conditions(dossier, known_roles)
    verify_foreign_revision(dossier, indexed)
    wp_path = ROOT / "work" / dossier["work_package_id"] / "work-package.json"
    work_package = load_json(wp_path) if wp_path.is_file() else None
    council = verify_council(dossier, work_package)
    declared = dossier.get("council_disposition")
    if declared is not None and declared.get("disposition") != council["disposition"]:
        raise ValidationError(
            f"declared council_disposition {declared.get('disposition')!r} contradicts the computed "
            f"{council['disposition']!r}; the disposition is computed, not asserted")
    dossier["council_disposition"] = {"disposition": council["disposition"], "triggers": council["triggers"]}
    rendered = verify_two_plane(dossier)

    _wp = _wp_record(dossier["work_package_id"])
    if _wp is not None:
        _check_delegations(ROOT / "work" / dossier["work_package_id"], _wp, dossier["work_package_id"])   # C7, any disposition
        if dossier["disposition"] in {"PASS", "PASS_WITH_CONDITIONS"}:
            _check_build_budget_and_stop(ROOT / "work" / dossier["work_package_id"], _wp, dossier["work_package_id"])   # C6
    if dossier["disposition"] == "HUMAN_REQUIRED":
        # A HUMAN_REQUIRED dossier is a REQUEST for authority, not a CLAIM of
        # it (badf init produces one). Its evidence is PREPARED and unsigned;
        # validating prepared declarations as if they were proven claims is a
        # category error. So: the evidence index must be well-formed and each
        # file must exist and be digest-bound (a request cannot point at
        # nothing), but outcome is not required to be PASS. The dossier can
        # never render above HELD from here -- render_verdict maps
        # HUMAN_REQUIRED to HUMAN_REQUIRED and main() exits 3. Flipping the
        # disposition to PASS re-enters full evidence validation and the
        # unsigned declarations are refused. A test proves both.
        for evidence_type, path_value in indexed.items():
            ev_path = safe_repo_path(path_value, "evidence path")
            ev = load_json(ev_path)
            require_fields(ev, EVIDENCE_FIELDS, f"evidence {ev_path}")
            if ev["evidence_type"] != evidence_type:
                raise ValidationError(f"evidence {ev_path} type does not match index")
            artifact = safe_repo_path(ev["artifact"], f"evidence {ev_path} artifact")
            if ev["digest"] != sha256(artifact):
                raise ValidationError(f"evidence {ev_path} artifact digest mismatch")
            if "binding" in ev:
                check_schema(ev["evidence_type"], ev)   # BLD-B: a request cannot carry a malformed typed binding
        return rendered
    for evidence_type, path_value in indexed.items():
        validate_evidence(safe_repo_path(path_value, "evidence path"), dossier, evidence_type)
    if dossier["gate"] == "G08" and dossier["disposition"] in {"PASS", "PASS_WITH_CONDITIONS"}:
        # VER-C: resolve the inputs here, judge them in the pure check_g08_dossier (C1..C7).
        objects = {t: load_json(safe_repo_path(p, "evidence path")) for t, p in indexed.items()}
        comp_path = ROOT / "work" / dossier["work_package_id"] / "evidence" / "G07" / "composition-record.json"
        composition_record = load_json(comp_path) if comp_path.is_file() else None
        record = None
        rv = objects.get("independent-review")
        if isinstance(rv, dict) and "binding" in rv:
            art = safe_repo_path(rv["artifact"], "independent-review artifact")
            if art.suffix == ".json":
                validate_verification_record(art)   # the review artifact IS the council record
                record = load_json(art)
        check_g08_dossier(dossier, work_package, objects, composition_record, record)
    return rendered


def validate_solution_composition(path: Path) -> str:
    """`badf_gate.py solution <path>`: the STRUCTURAL controls of a badf-solution-design
    composition matrix (WP-SOL-B). One record in the canonical gate -- not a second
    validator (SOL-I12), and not a lifecycle result. It checks the matrix is internally
    coherent: unique solution ids (SOL-C01), every row bound to a requirement (SOL-C02 /
    SOL-I01), and every row binding at least one specialist artifact (SOL-C03). The
    cross-artifact SEAM checks -- reconciling the matrix against the specialist artifacts
    -- are WP-SOL-C, not here."""
    rec = load_json(path)
    check_schema("solution-composition", rec)
    _no_placeholders(rec, "solution-composition")
    solutions = rec["solutions"]
    if not solutions:
        raise ValidationError("solution-composition: no solutions; an empty matrix composes nothing")
    # SOL-C01: a matrix cannot carry two rows under one solution id.
    _unique_ids(solutions, "solution_id", "solution-composition")
    # SOL-C02 (requirement provenance / SOL-I01, structural) is enforced by the schema --
    # requirement_ref is required and matches ^REQ-nnn; a separate check here would be
    # dead code (the schema refuses a missing or malformed ref first).
    ref_kinds = ("ux_refs", "api_refs", "authorization_refs", "data_refs",
                 "audit_refs", "accessibility_refs", "test_refs")
    for s in solutions:
        # SOL-C03: a requirement composed to nothing satisfies nothing.
        if not any(s.get(k) or [] for k in ref_kinds):
            raise ValidationError(f"solution-composition: {s['solution_id']} (for {s['requirement_ref']}) binds no specialist artifact; a requirement composed to nothing satisfies nothing (SOL-C03)")
        # Matrix-internal seam controls (WP-SOL-C): the composition is coherent across
        # concerns. The FULL seams reconcile against the specialist artifacts (which do
        # not exist yet -- deferred to the adapter WPs); these enforce the co-occurrence
        # the seams require, at the level the matrix alone can decide.
        # SOL-C04 (SOL-I04, API <-> authorization): a protected operation carries its tuple.
        if (s.get("api_refs") or []) and not (s.get("authorization_refs") or []):
            raise ValidationError(f"solution-composition: {s['solution_id']} composes api_refs but no authorization_refs; a protected operation carries an authorization tuple (SOL-C04 / SOL-I04)")
        # SOL-C05 (SOL-I06, authorization <-> audit): a security decision carries its audit.
        if (s.get("authorization_refs") or []) and not (s.get("audit_refs") or []):
            raise ValidationError(f"solution-composition: {s['solution_id']} composes authorization_refs but no audit_refs; a security-sensitive decision defines an audit obligation (SOL-C05 / SOL-I06)")
        # SOL-C06 (SOL-I09, accessibility binds behavior): a UX interaction carries a11y.
        if (s.get("ux_refs") or []) and not (s.get("accessibility_refs") or []):
            raise ValidationError(f"solution-composition: {s['solution_id']} composes ux_refs but no accessibility_refs; accessibility binds interaction states (SOL-C06 / SOL-I09)")
    reqs = {s["requirement_ref"] for s in solutions}
    return f"BADF SOLUTION-COMPOSITION PASS: {len(solutions)} composition(s) over {len(reqs)} requirement(s); structural + matrix-internal seams (SOL-C04/05/06)"


def validate_security_composition(path: Path) -> str:
    """`badf_gate.py security <path>`: the STRUCTURAL controls of a badf-security-design
    composition matrix (WP-SEC-B). One record in the canonical gate -- not a second
    validator (SEC-I15), and not a lifecycle result. It checks the matrix is internally
    coherent: unique threat ids (SEC-C01), every threat resolving to real provenance
    (SEC-C02 / SEC-I02), and every *controlled* threat actually carrying a control
    (SEC-C03 / SEC-I03). The residual_risk enum omits a bare `ACCEPTED` (schema), so the
    skill structurally cannot self-accept residual risk (SEC-I12). The cross-artifact SEAM
    checks -- bidirectional traceability (SEC-I04), exact-baseline binding (SEC-I01) and
    the semantic resolution of every ref against the architecture/solution artifacts -- are
    WP-SEC-C, not here."""
    rec = load_json(path)
    check_schema("security-composition", rec)
    _no_placeholders(rec, "security-composition")
    threats = rec["threats"]
    if not threats:
        raise ValidationError("security-composition: no threats; an empty matrix models nothing")
    # SEC-C01: a matrix cannot carry two rows under one threat id.
    _unique_ids(threats, "security_id", "security-composition")
    provenance_kinds = ("architecture_refs", "solution_refs", "requirement_refs",
                        "trust_boundary_refs", "data_flow_refs")
    for t in threats:
        src = t.get("source") or {}
        # SEC-C02 (SEC-I02): a threat that resolves to nothing is not a threat.
        if not any(src.get(k) or [] for k in provenance_kinds):
            raise ValidationError(f"security-composition: {t['security_id']} binds no provenance source; a material threat resolves to real assets/interfaces/flows/boundaries/requirements (SEC-C02 / SEC-I02)")
        # SEC-C03 (SEC-I03): a threat dispositioned `controlled` must name a control.
        if t["disposition"] == "controlled" and not (t.get("control_refs") or []):
            raise ValidationError(f"security-composition: {t['security_id']} is dispositioned 'controlled' but carries no control_refs; a threat controlled by nothing is not controlled (SEC-C03 / SEC-I03)")
        # ---- WP-SEC-C: matrix-internal cross-artifact seams (the coherence the matrix alone can decide;
        # the full bidirectional/baseline/semantic resolution needs the specialist artifacts -- deferred).
        # SEC-C04 (SEC-I04, downstream traceability): a controlled threat carries a verification obligation.
        if t["disposition"] == "controlled" and not (t.get("verification_refs") or []):
            raise ValidationError(f"security-composition: {t['security_id']} is 'controlled' but carries no verification_refs; a control asserted but never verified is an incomplete chain -- a security conclusion traces downstream to a verification obligation (SEC-C04 / SEC-I04)")
        # SEC-C05 (SEC-I12 / SEC-I03, disposition <-> residual-risk coherence): residual risk cannot be
        # declared pending authority-acceptance unless the threat was actually dispositioned to authority.
        if t.get("residual_risk") == "ACCEPTED-PENDING-AUTHORITY" and t["disposition"] != "pending-authority":
            raise ValidationError(f"security-composition: {t['security_id']} declares residual_risk ACCEPTED-PENDING-AUTHORITY but its disposition is {t['disposition']!r}, not 'pending-authority'; risk cannot be pending authority-acceptance unless the threat was dispositioned to authority (SEC-C05 / SEC-I12)")
    controlled = sum(1 for t in threats if t["disposition"] == "controlled")
    return f"BADF SECURITY-COMPOSITION PASS: {len(threats)} threat(s), {controlled} controlled; structural + matrix-internal seams (SEC-C01..C05)"


# ---- badf-git GIT-C: the read-only baseline inspector (BADF-WP-0069) ----------------
def _git_at(root: Path, *args: str) -> str | None:
    """Like _git, for an arbitrary working tree. Read-only by construction: every
    caller passes an observation command; nothing here writes a ref, the index,
    the worktree, the stash or the reflog, and nothing fetches."""
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_baseline(root: Path) -> dict[str, Any]:
    """`badf_gate.py git-baseline [<path>]`: the GIT_BASELINED record of a working
    tree -- badf-git's BASELINE stage (references/git-cycle.md section 2) measured,
    not typed. GIT-O0 OBSERVE: writes nothing, fetches nothing, moves nothing.

    Repository identity; worktree path / branch or detached / linked; index and
    worktree status as COUNTS ONLY (never a path or a byte of content); the target
    (origin/<default> as known locally) ref + SHA + tree; the source HEAD ref + SHA
    + tree; merge base, ahead/behind, ancestry; remote freshness stated honestly
    (observed without a fetch); the policy epoch. Refuses -- BLOCKED -- outside a
    git working tree, when origin/<default> does not resolve (no fallback to HEAD,
    the monotonic resolver's rule), and on an unborn HEAD. The test-set/toolchain
    epoch the contract mentions does not exist in BADF and is declared as
    non-coverage rather than invented. Deterministic modulo `observed_at`.
    """
    from datetime import datetime, timezone
    root = Path(root).resolve()
    top = _git_at(root, "rev-parse", "--show-toplevel")
    if top is None:
        raise ValidationError(f"BLOCKED: {root} is not inside a git working tree; there is no repository to baseline")
    top_path = Path(top)
    tracking = f"refs/remotes/origin/{DEFAULT_BRANCH}"
    target = _git_at(root, "rev-parse", "--verify", "-q", f"{tracking}^{{commit}}")
    if target is None:
        raise ValidationError(f"BLOCKED: origin/{DEFAULT_BRANCH} ({tracking}) does not resolve in {top}; the target is "
                              "unknown and this inspector never falls back to HEAD and never fetches")
    head = _git_at(root, "rev-parse", "--verify", "-q", "HEAD^{commit}")
    if head is None:
        raise ValidationError(f"BLOCKED: HEAD is unborn in {top} (no commit is checked out); there is no source state to baseline")
    branch = _git_at(root, "symbolic-ref", "-q", "HEAD")
    git_dir = _git_at(root, "rev-parse", "--git-dir") or ".git"
    common_dir = _git_at(root, "rev-parse", "--git-common-dir") or git_dir
    linked = (root / git_dir).resolve() != (root / common_dir).resolve()
    counts = _git_at(root, "rev-list", "--left-right", "--count", f"HEAD...{tracking}") or "0\t0"
    ahead, behind = (int(x) for x in counts.split())
    ancestor = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", "HEAD", target],
                              capture_output=True).returncode == 0
    staged = unstaged = untracked = unmerged = 0
    for line in (_git_at(root, "status", "--porcelain=v2", "--untracked-files=all") or "").splitlines():
        if line.startswith(("1 ", "2 ")):
            xy = line.split(" ", 2)[1]
            staged += xy[0] != "."
            unstaged += xy[1] != "."
        elif line.startswith("u "):
            unmerged += 1
        elif line.startswith("? "):
            untracked += 1
    stash = len([l for l in (_git_at(root, "stash", "list") or "").splitlines() if l.strip()])
    name = None
    reg_path = top_path / REPOSITORIES
    if reg_path.is_file():
        try:
            for n, spec in (load_json(reg_path).get("repositories") or {}).items():
                if isinstance(spec, dict) and spec.get("resolution") == "SELF":
                    name = n
        except ValidationError:
            name = None
    epoch = None
    life = top_path / "badf/lifecycle.json"
    if life.is_file():
        try:
            epoch = load_json(life).get("policy_epoch")
        except ValidationError:
            epoch = None
    return {
        "record": "git-baseline",
        "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disposition": "GIT_BASELINED",
        "repository": {"name": name, "root": top},
        "worktree": {"path": str(root), "linked": linked,
                     "head_kind": "branch" if branch else "detached", "branch": branch},
        "index": {"staged": staged, "unstaged": unstaged, "untracked": untracked, "unmerged": unmerged, "stash": stash},
        "target_ref": f"refs/heads/{DEFAULT_BRANCH}",
        "target_sha": target,
        "target_tree": _git_at(root, "rev-parse", f"{target}^{{tree}}"),
        "source_ref": branch,
        "source_head_sha": head,
        "source_tree": _git_at(root, "rev-parse", "HEAD^{tree}"),
        "merge_base_sha": _git_at(root, "merge-base", "HEAD", target),
        "ahead": ahead,
        "behind": behind,
        "head_is_ancestor_of_target": ancestor,
        "remote_freshness": {"tracking_ref": tracking, "sha": target, "observed_without_fetch": True},
        "policy_epoch": epoch,
        "non_coverage": ["test_set_epoch: BADF defines no test-set/toolchain epoch (git-cycle.md section 2); "
                         "not recorded rather than invented"],
    }


# ---- badf-git GIT-D: staleness against a stored baseline (BADF-WP-0075) --------------
_BASELINE_REQUIRED = ("schema_version", "observed_at", "repository", "source_head_sha", "target_sha",
                      "merge_base_sha", "index", "policy_epoch")


def load_git_baseline_record(path: Path) -> dict[str, Any]:
    """A git-baseline record as `git-baseline` printed it -- tolerating the trailing
    `BADF GATE PASS` line that a stdout redirect captures. Refuses anything that is
    not a complete git-baseline record: a verdict must never be computed against a
    file that merely looks like one."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"BLOCKED: cannot read the baseline record {path}: {exc}")
    lines = text.rstrip("\n").splitlines()
    if lines and lines[-1].startswith("BADF GATE "):
        lines = lines[:-1]
    try:
        rec = json.loads("\n".join(lines))
    except ValueError:
        raise ValidationError(f"BLOCKED: {path} is not a git-baseline record (not JSON)")
    if not isinstance(rec, dict) or rec.get("record") != "git-baseline":
        raise ValidationError(f"BLOCKED: {path} is not a git-baseline record (no `record: git-baseline`)")
    missing = [k for k in _BASELINE_REQUIRED if k not in rec]
    if missing:
        raise ValidationError(f"BLOCKED: {path} is not a complete git-baseline record; missing {missing}")
    if not isinstance(rec.get("repository"), dict) or not rec["repository"].get("root") or not isinstance(rec.get("index"), dict):
        raise ValidationError(f"BLOCKED: {path} is not a complete git-baseline record (repository.root / index)")
    return rec


def git_staleness(record: dict[str, Any], root: Path) -> dict[str, Any]:
    """`badf_gate.py git-staleness <baseline-record.json> [<path>]`: staleness as a
    measured verdict (GIT-I05). Re-observes the tree through git_baseline() and
    compares it with the stored record:

      CURRENT          same source head, target SHA and policy epoch          (exit 0)
      SOURCE_ADVANCED  source moved; the recorded head is an ancestor          (HELD 3)
      STALE_EVIDENCE   the recorded head is NOT an ancestor (a rewrite), or   (HELD 3)
                       the policy epoch changed
      TARGET_MOVED     target moved, source unchanged                          (HELD 3)

    Combined cases report every flag and render the strictest disposition. Index
    and worktree count deltas are informational only: a dirty tree is not a
    rewrite. The rewrite *type* is not deterministically inferable from two SHAs
    and is not guessed. A baseline binds a checkout: a record from another root
    is refused. Read-only, like git_baseline.
    """
    from datetime import datetime, timezone
    now = git_baseline(root)
    if Path(record["repository"]["root"]).resolve() != Path(now["repository"]["root"]).resolve():
        raise ValidationError(f"BLOCKED: the baseline record binds checkout {record['repository']['root']}, not "
                              f"{now['repository']['root']}; a baseline binds a checkout -- take a new one here")
    old_head, new_head = record["source_head_sha"], now["source_head_sha"]
    old_target, new_target = record["target_sha"], now["target_sha"]
    old_mb, new_mb = record.get("merge_base_sha"), now.get("merge_base_sha")
    source_changed = old_head != new_head
    reachable = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{old_head}^{{commit}}"],
                               capture_output=True).returncode == 0
    ancestor = reachable and subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", old_head, new_head],
                                            capture_output=True).returncode == 0
    source_rewritten = source_changed and not ancestor
    target_changed = old_target != new_target
    merge_base_changed = old_mb != new_mb
    epoch_changed = record.get("policy_epoch") != now.get("policy_epoch")
    index_delta = {k: int(now["index"].get(k, 0)) - int(record["index"].get(k, 0))
                   for k in ("staged", "unstaged", "untracked", "unmerged", "stash")}
    if source_rewritten or epoch_changed:
        disposition, invalidated = "STALE_EVIDENCE", ["source-bound evidence", "composition", "review"]
    elif source_changed:
        disposition, invalidated = "SOURCE_ADVANCED", ["composition", "review"]
    elif target_changed:
        disposition, invalidated = "TARGET_MOVED", ["composition"]
    else:
        disposition, invalidated = "CURRENT", []
    return {
        "record": "git-staleness",
        "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disposition": disposition,
        "baseline_observed_at": record["observed_at"],
        "repository": now["repository"],
        "old_source_head": old_head, "new_source_head": new_head,
        "old_target_sha": old_target, "new_target_sha": new_target,
        "old_merge_base": old_mb, "new_merge_base": new_mb,
        "old_policy_epoch": record.get("policy_epoch"), "new_policy_epoch": now.get("policy_epoch"),
        "source_changed": source_changed,
        "source_rewritten": source_rewritten,
        "old_head_still_reachable": reachable,
        "target_changed": target_changed,
        "merge_base_changed": merge_base_changed,
        "epoch_changed": epoch_changed,
        "kind": "history_rewrite" if source_rewritten else None,
        "invalidated": invalidated,
        "index_delta": index_delta,
        "non_coverage": ["rewrite type (amend / rebase / reset / cherry-pick) is not deterministically inferable from two "
                         "revisions and is not guessed", *now.get("non_coverage", [])],
    }


# ---- badf-git GIT-G: recovery inventory and preservation (BADF-WP-0080) ----------------
RECOVERY_LABEL = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def git_recovery(root: Path, *, preserve: str | None = None, wp: str | None = None) -> dict[str, Any]:
    """`badf_gate.py git-recovery [<path>] [--preserve <label> --wp <WP>]`: the recovery
    contract's PRESERVE -> IDENTIFY -> CLASSIFY, measured. Renders the before-state record
    the contract requires -- the git-baseline plus the UNIQUE-STATE inventory (uncommitted
    changes as a count, stash entries, dangling commits = reflog entries of HEAD unreachable
    from any ref, unpushed topic commits, other worktrees of the same repository) -- and
    derives the recovery class (EVIDENCE_ONLY / LOCAL / TOPIC / PROTECTED) and disposition
    (RECOVERABLE / RECOVERY_REQUIRED). Read-only (GIT-O0). With --preserve it establishes
    preservation the only way that cannot lose anything (GIT-O1): refs/recovery/<WP>/<label>
    at HEAD and, for a dirty tree, refs/recovery/<WP>/<label>-worktree at a `git stash
    create` snapshot -- which writes objects and touches neither the worktree, the index nor
    the stash list. It never resets, cleans, checks out, or deletes a ref. Unmerged paths
    make classification impossible and are a refusal, not a guess.
    """
    from datetime import datetime, timezone
    baseline = git_baseline(root)
    root = Path(baseline["worktree"]["path"]); top = Path(baseline["repository"]["root"])
    if baseline["index"]["unmerged"]:
        raise ValidationError(f"BLOCKED: {baseline['index']['unmerged']} unmerged path(s) in {top}; recovery cannot be classified "
                              "until the conflicts are resolved -- resolve or abort the merge/rebase first, never clean around it")
    head = baseline["source_head_sha"]
    reflog = (_git_at(root, "reflog", "show", "--format=%H", "HEAD") or "").split()
    reachable = set((_git_at(root, "rev-list", "--all") or "").split())
    dangling = [sha for sha in dict.fromkeys(reflog) if sha not in reachable]
    unpushed = []
    for line in (_git_at(root, "for-each-ref", "--format=%(refname) %(upstream) %(objectname)", "refs/heads") or "").splitlines():
        parts = line.split(); ref, upstream = parts[0], (parts[1] if len(parts) == 3 else None)
        count = _git_at(root, "rev-list", "--count", f"{upstream}..{ref}") if upstream else _git_at(root, "rev-list", "--count", ref, "--not", "--remotes")
        ahead = int(count) if count and count.isdigit() else 0
        if ahead:
            unpushed.append({"branch": ref, "ahead": ahead, "upstream": upstream})
    others = []
    entry: dict[str, Any] = {}
    for line in (_git_at(root, "worktree", "list", "--porcelain") or "").splitlines() + [""]:
        if not line:
            if entry:
                if Path(entry["path"]).resolve() != top.resolve():
                    others.append({"path": entry["path"], "branch": entry.get("branch"), "head": entry.get("head")})
                entry = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree": entry["path"] = value
        elif key == "HEAD": entry["head"] = value
        elif key == "branch": entry["branch"] = value
        elif key == "detached": entry["branch"] = None
    idx = baseline["index"]
    uncommitted = idx["staged"] + idx["unstaged"] + idx["untracked"]
    unique = {"uncommitted": uncommitted, "stash": idx["stash"], "dangling_commits": dangling,
              "unpushed_commits": unpushed, "other_worktrees": others}
    on_default = baseline["source_ref"] == f"refs/heads/{DEFAULT_BRANCH}"
    if on_default:
        klass = "PROTECTED"
    elif unpushed:
        klass = "TOPIC"
    elif uncommitted or idx["stash"] or dangling:
        klass = "LOCAL"
    else:
        klass = "EVIDENCE_ONLY"
    has_unique = bool(uncommitted or idx["stash"] or dangling or unpushed)
    disposition = "RECOVERY_REQUIRED" if has_unique else "RECOVERABLE"
    paths = {
        "EVIDENCE_ONLY": "nothing unique here: any stale evidence is recomputed (git-staleness, --record), nothing needs preserving",
        "LOCAL": ("PRESERVE first -- `git-recovery --preserve <label> --wp <WP>` creates refs/recovery/<WP>/<label> (HEAD) and a "
                  "-worktree snapshot of uncommitted state; recover any dangling commit from the reflog into a recovery ref "
                  "(refs/recovery/...) and verify it BEFORE any reset --hard or clean; stash entries are not durable handoff"),
        "TOPIC": ("PRESERVE first (refs/recovery/<WP>/<label>); the unpushed commits exist only here -- publish the topic or keep "
                  "a recovery ref before deleting or rewriting the branch; --force-with-lease only after preservation"),
        "PROTECTED": (f"HEAD is the protected branch {DEFAULT_BRANCH}: a landed change is repaired FORWARD with `git revert` under a "
                      f"new work package, composed against current {DEFAULT_BRANCH}; never rewrite {DEFAULT_BRANCH}"),
    }
    preservation = None
    if preserve is not None:
        if not wp or not WP_ID_FORMS.match(wp):
            raise ValidationError("BLOCKED: --preserve requires --wp <work package id> to namespace refs/recovery/<WP>/")
        if not RECOVERY_LABEL.match(preserve):
            raise ValidationError(f"BLOCKED: recovery label {preserve!r} must be lowercase kebab ([a-z0-9][a-z0-9-]*)")
        wp = f"{WP_NAMESPACE}{WP_ID_FORMS.match(wp).group(1)}"
        ref = f"refs/recovery/{wp}/{preserve}"
        if _git_at(root, "rev-parse", "--verify", "-q", ref) is not None:
            raise ValidationError(f"BLOCKED: {ref} already exists; a recovery ref is never overwritten -- choose another label")
        refs = []
        r = subprocess.run(["git", "-C", str(root), "update-ref", ref, head], capture_output=True, text=True)
        if r.returncode:
            raise ValidationError(f"BLOCKED: cannot create {ref}: {r.stderr.strip()}")
        refs.append(ref)
        snapshot = None
        if uncommitted:
            snapshot = _git_at(root, "stash", "create") or None
            if snapshot:
                r = subprocess.run(["git", "-C", str(root), "update-ref", f"{ref}-worktree", snapshot], capture_output=True, text=True)
                if r.returncode:
                    raise ValidationError(f"BLOCKED: cannot create {ref}-worktree: {r.stderr.strip()}")
                refs.append(f"{ref}-worktree")
        preservation = {"refs": refs, "before_head": head, "worktree_snapshot": snapshot}
    return {
        "record": "git-recovery",
        "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseline": baseline,
        "unique_state": unique,
        "recovery_class": klass,
        "disposition": disposition,
        "least_destructive_path": paths[klass],
        "preservation": preservation,
        "non_coverage": ["another actor's reliance on a branch/worktree is reported (other_worktrees), not decided",
                         "remote-topic and release-ref recovery are procedures (git-recovery subskill; GIT-H), not this record",
                         *baseline.get("non_coverage", [])],
    }


# ---- badf-git GIT-H: release refs are checked bindings (BADF-WP-0081) ------------------
RELEASE_VERSION = re.compile(r"^(v[0-9]+\.[0-9]+\.[0-9]+|BADF-BASELINE-[0-9]+\.[0-9]+\.[0-9]+)$")
RELEASE_REQUIRED = ("schema_version", "observed_at", "version", "tag_ref", "source_ref", "source_revision",
                    "source_result_tree", "policy_epoch", "provenance", "release_authority", "disposition", "non_coverage")
RELEASES_DIR = "badf/releases"


def _tag_provenance(root: Path, tag: str) -> dict[str, Any] | None:
    """What the tag object itself says: None when the tag does not exist; annotated
    False for a lightweight tag (no tagger identity at all)."""
    if _git_at(root, "rev-parse", "--verify", "-q", f"refs/tags/{tag}") is None:
        return None
    kind = _git_at(root, "cat-file", "-t", f"refs/tags/{tag}")
    if kind != "tag":
        return {"annotated": False, "signed": False, "tagger": None}
    body = _git_at(root, "cat-file", "tag", f"refs/tags/{tag}") or ""
    tagger = None
    for line in body.splitlines():
        if line.startswith("tagger "):
            parts = line[len("tagger "):].rsplit(" ", 2)   # name <email> <ts> <tz>
            tagger = parts[0] if len(parts) == 3 else line[len("tagger "):]
            break
    return {"annotated": True, "signed": "-----BEGIN" in body, "tagger": tagger}


def _on_first_parent(root: Path, sha: str) -> bool:
    return sha in set((_git_at(root, "rev-list", "--first-parent", f"refs/remotes/origin/{DEFAULT_BRANCH}") or "").split())


def parse_release_record(text: str, label: str) -> dict[str, Any]:
    try:
        rec = json.loads(text)
    except ValueError:
        raise ValidationError(f"{label} is not a git-release record (not JSON)")
    if not isinstance(rec, dict) or rec.get("record") != "git-release":
        raise ValidationError(f"{label} is not a git-release record (no `record: git-release`)")
    missing = [k for k in RELEASE_REQUIRED if k not in rec]
    if missing:
        raise ValidationError(f"{label} is not a complete git-release record; missing {missing}")
    return rec


def git_release_check(root: Path, tag: str) -> dict[str, Any]:
    """`badf_gate.py git-release-check <tag> [<path>]`: a release-class ref is a checked
    binding. Read-only. Refuses (BLOCKED) a missing or lightweight tag, a tag whose commit is
    not on main's first-parent history (release-from-main), a tag with no release record
    (TAG_EXISTS != RELEASE_AUTHORIZED), a record for a different revision (the tag moved --
    an immutability breach), a version that differs from the tag, a result tree that differs,
    or a provenance statement the tag object contradicts."""
    from datetime import datetime, timezone
    baseline = git_baseline(root)
    root = Path(baseline["worktree"]["path"]); top = Path(baseline["repository"]["root"])
    prov = _tag_provenance(root, tag)
    if prov is None:
        raise ValidationError(f"BLOCKED: refs/tags/{tag} does not exist in {top}")
    if not prov["annotated"]:
        raise ValidationError(f"BLOCKED: refs/tags/{tag} is a lightweight tag; a release ref must be annotated (a tagger identity is part of the binding)")
    commit = _git_at(root, "rev-parse", f"refs/tags/{tag}^{{commit}}")
    if not _on_first_parent(root, commit):
        raise ValidationError(f"BLOCKED: refs/tags/{tag} -> {commit[:12]} is not on the first-parent history of origin/{DEFAULT_BRANCH}; release refs are created only from main")
    rec_path = top / RELEASES_DIR / f"{tag}.json"
    if not rec_path.is_file():
        raise ValidationError(f"BLOCKED: refs/tags/{tag} has no release record at {RELEASES_DIR}/{tag}.json -- TAG_EXISTS != RELEASE_AUTHORIZED")
    rec = parse_release_record(rec_path.read_text(encoding="utf-8"), f"{RELEASES_DIR}/{tag}.json")
    if rec["version"] != tag:
        raise ValidationError(f"BLOCKED: {RELEASES_DIR}/{tag}.json records version {rec['version']!r}, not {tag}")
    if rec["source_revision"] != commit:
        raise ValidationError(f"BLOCKED: refs/tags/{tag} has moved: recorded at {str(rec['source_revision'])[:7]}, now at {commit[:7]} -- a published release ref is immutable; "
                              "corrections are a new version or an explicit supersession, never a moved tag")
    tree = _git_at(root, "rev-parse", f"{commit}^{{tree}}")
    if rec["source_result_tree"] != tree:
        raise ValidationError(f"BLOCKED: {RELEASES_DIR}/{tag}.json records result tree {str(rec['source_result_tree'])[:7]}, the tag's commit has {tree[:7]}")
    recorded = rec.get("provenance") or {}
    if recorded.get("annotated") is not True or bool(recorded.get("signed")) != prov["signed"]:
        raise ValidationError(f"BLOCKED: {RELEASES_DIR}/{tag}.json's provenance {recorded} contradicts the tag object "
                              f"(annotated {prov['annotated']}, signed {prov['signed']}); record the limitation, do not rewrite it")
    return {
        "record": "git-release-check", "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disposition": "RELEASE_BOUND", "version": tag, "tag_ref": f"refs/tags/{tag}",
        "source_ref": f"refs/heads/{DEFAULT_BRANCH}", "source_revision": commit, "source_result_tree": tree,
        "provenance": prov, "record_path": f"{RELEASES_DIR}/{tag}.json", "release_authority": rec.get("release_authority"),
        "non_coverage": ["tag signature verification is not performed (recorded as provenance.signed only)",
                         "artifact/SBOM/attestation identity (docs/11 release packet) is not bound here -- G10/G11 evidence"],
    }


def git_release_record(root: Path, version: str) -> dict[str, Any]:
    """`badf_gate.py git-release-record <version> [<path>]`: write badf/releases/<version>.json
    -- the contract's release binding -- as a HUMAN_REQUIRED request. Binds an EXISTING
    tag's commit (recording a historical or freshly created ref) or, when no tag exists yet,
    HEAD (a request for one). Only first-parent commits of origin/<default> qualify
    (release-from-main). Never runs `git tag`; refuses version reuse against a different
    revision and unsupported version forms."""
    from datetime import datetime, timezone
    if not RELEASE_VERSION.match(version):
        raise ValidationError(f"BLOCKED: {version!r} is not a release version; use vX.Y.Z (forward releases) or BADF-BASELINE-X.Y.Z (historical baselines)")
    baseline = git_baseline(root)
    root = Path(baseline["worktree"]["path"]); top = Path(baseline["repository"]["root"])
    prov = _tag_provenance(root, version)
    commit = _git_at(root, "rev-parse", f"refs/tags/{version}^{{commit}}") if prov else baseline["source_head_sha"]
    if not _on_first_parent(root, commit):
        raise ValidationError(f"BLOCKED: {commit[:12]} is not on the first-parent history of origin/{DEFAULT_BRANCH}; release refs are created only from main")
    rec_path = top / RELEASES_DIR / f"{version}.json"
    if rec_path.is_file():
        existing = parse_release_record(rec_path.read_text(encoding="utf-8"), f"{RELEASES_DIR}/{version}.json")
        if existing.get("source_revision") != commit:
            raise ValidationError(f"BLOCKED: version {version} is already recorded for {str(existing.get('source_revision'))[:7]}; a version is never reused for different content -- choose a new version or record a supersession")
    epoch = None
    life = top / "badf/lifecycle.json"
    if life.is_file():
        epoch = load_json(life).get("policy_epoch")
    rec = {
        "record": "git-release", "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": version, "tag_ref": f"refs/tags/{version}", "source_ref": f"refs/heads/{DEFAULT_BRANCH}",
        "source_revision": commit, "source_result_tree": _git_at(root, "rev-parse", f"{commit}^{{tree}}"),
        "policy_epoch": epoch, "provenance": prov,
        "release_authority": "HUMAN_REQUIRED", "disposition": "HUMAN_REQUIRED",
        "non_coverage": ["the tag is created by the release authority (git tag -a / gh release), never by this tool",
                         "artifact/SBOM/attestation identity (docs/11) is G10/G11 evidence, not bound here",
                         *(["provenance limitation: the tag is unsigned; recorded, not rewritten"] if prov and not prov["signed"] else []),
                         *(["no tag exists yet: this record is a request; git-release-check verifies the pair once the tag is created"] if not prov else [])],
    }
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    rec_path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec


def verify_release_refs() -> None:
    """Every recorded release ref that exists locally still points at its recorded
    revision (BADF-WP-0081): a moved release tag is an immutability breach and refuses
    the repository contract. A recorded tag absent locally is tolerated (a shallow clone
    is not a breach)."""
    for path in sorted((ROOT / RELEASES_DIR).glob("*.json")):
        rec = parse_release_record(path.read_text(encoding="utf-8"), path.relative_to(ROOT).as_posix())
        version = rec["version"]
        if path.stem != version:
            raise ValidationError(f"{path.relative_to(ROOT).as_posix()} records version {version!r}; the file must be named {version}.json")
        now = _git("rev-parse", "--verify", "-q", f"refs/tags/{version}^{{commit}}")
        if now is None:
            continue
        if now != rec["source_revision"]:
            raise ValidationError(f"release ref refs/tags/{version} has moved: recorded at {str(rec['source_revision'])[:7]}, now at {now[:7]}; "
                                  "a published release ref is immutable -- restore it, or record a supersession under a new version")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("repo", help="validate repository governance structure")
    lock_parser = subparsers.add_parser("lock", help="re-sign badf/lockfile.json from current content")
    lock_parser.add_argument("--instance", type=Path, default=None, help="re-sign a project instance's badf/lockfile.json instead")
    inst_parser = subparsers.add_parser("instance", help="validate a project instance at <path>; writes nothing")
    inst_parser.add_argument("path", type=Path)
    gb_parser = subparsers.add_parser("git-baseline", help="render the read-only GIT_BASELINED record of <path> (default: this repository); writes nothing, fetches nothing (badf-git GIT-O0)")
    gb_parser.add_argument("path", nargs="?", type=Path, default=ROOT)
    gs_parser = subparsers.add_parser("git-staleness", help="compare a stored git-baseline record with <path> now: CURRENT (0) / SOURCE_ADVANCED, STALE_EVIDENCE, TARGET_MOVED (HELD 3); read-only (badf-git GIT-I05)")
    gs_parser.add_argument("record", type=Path, help="a git-baseline record (stdout of `git-baseline`, PASS line tolerated)")
    gs_parser.add_argument("path", nargs="?", type=Path, default=ROOT)
    gr_parser = subparsers.add_parser("git-recovery", help="inventory unique state and classify the recovery path of <path> (read-only); --preserve <label> --wp <WP> adds refs/recovery/<WP>/ refs and touches nothing else (badf-git GIT-G)")
    gr_parser.add_argument("path", nargs="?", type=Path, default=ROOT)
    gr_parser.add_argument("--preserve", metavar="LABEL", help="create refs/recovery/<WP>/<LABEL> at HEAD (+ -worktree snapshot of a dirty tree)")
    gr_parser.add_argument("--wp", help="work package id that namespaces the recovery refs (required with --preserve)")
    rc_parser = subparsers.add_parser("git-release-check", help="verify a release ref: annotated, on main first-parent, record-bound, unmoved (badf-git GIT-H; read-only)")
    rc_parser.add_argument("tag"); rc_parser.add_argument("path", nargs="?", type=Path, default=ROOT)
    rr_parser = subparsers.add_parser("git-release-record", help="write badf/releases/<version>.json as a HUMAN_REQUIRED release binding; binds an existing tag or HEAD; never creates a tag")
    rr_parser.add_argument("version"); rr_parser.add_argument("path", nargs="?", type=Path, default=ROOT)
    charter_parser = subparsers.add_parser("charter", help="bind an instance to the framework's authority floor at its pinned revision")
    charter_parser.add_argument("path", type=Path)
    adv_parser = subparsers.add_parser("advance", help="bind an APPROVED dossier for the instance's next gate; the gate is derived from the chain")
    adv_parser.add_argument("path", type=Path)
    adv_parser.add_argument("dossier", help="work/<WP>/gate-dossier.<gate>.json in the framework")
    dossier_parser = subparsers.add_parser("dossier", help="validate a gate dossier and its evidence")
    dossier_parser.add_argument("path", type=Path)
    init_parser = subparsers.add_parser("init", help="intake a project from a four-line intent; writes only under BADF's tree")
    init_parser.add_argument("intent", type=Path)
    rec_parser = subparsers.add_parser("reconcile", help="write a landed work package's corroborated landing from the ledger; refuses otherwise")
    rec_parser.add_argument("work_package")
    bl_parser = subparsers.add_parser("build-ledger", help="verify the hash-chained build ledger of one of BADF's own work packages (read-only; exit 0 intact, 1 broken)")
    bl_parser.add_argument("wp_id")

    self_parser = subparsers.add_parser("self-dossier", help="assemble a G07 dossier for one of BADF's own work packages from measured evidence (HUMAN_REQUIRED)")
    self_parser.add_argument("work_package")
    research_parser = subparsers.add_parser("research", help="validate a research record's record/source/claim controls (RSR-002)")
    research_parser.add_argument("path", type=Path)
    assure_parser = subparsers.add_parser("assure", help="validate an architecture-assurance record's ASSURE controls (WP-ARCH-C)")
    assure_parser.add_argument("path", type=Path)
    verify_parser = subparsers.add_parser("verify", help="validate a G08 verification record's structural controls (badf-engineering-verification VER-B); grants no authority")
    verify_parser.add_argument("path", type=Path)
    sol_parser = subparsers.add_parser("solution", help="validate a solution-composition matrix's structural controls (WP-SOL-B)")
    sol_parser.add_argument("path", type=Path)
    sec_parser = subparsers.add_parser("security", help="validate a security-composition matrix's structural controls (WP-SEC-B)")
    sec_parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "repo":
            validate_repo()
        elif args.command == "lock":
            if args.instance is not None:
                inst = instance_root(args.instance)
                print(f"re-signed {inst / LOCKFILE} over {write_instance_lock(inst)} instance paths")
            else:
                write_lockfile()
        elif args.command == "instance":
            for line in validate_instance(args.path):
                print(line)
            return 0
        elif args.command == "git-baseline":
            rec = git_baseline(args.path)
            print(json.dumps(rec, indent=2))
            print(f"BADF GATE PASS: git-baseline -- GIT_BASELINED {rec['source_head_sha'][:7]} on "
                  f"{rec['target_sha'][:7]} (ahead {rec['ahead']}, behind {rec['behind']})")
            return 0
        elif args.command == "git-staleness":
            v = git_staleness(load_git_baseline_record(args.record), args.path)
            print(json.dumps(v, indent=2))
            summary = (f"git-staleness -- {v['disposition']} source {v['old_source_head'][:7]} -> {v['new_source_head'][:7]}, "
                       f"target {v['old_target_sha'][:7]} -> {v['new_target_sha'][:7]}")
            if v["disposition"] == "CURRENT":
                print(f"BADF GATE PASS: {summary}")
                return 0
            print(f"BADF GATE HELD: {summary}; recovery is recomputation, not relabelling")
            return 3
        elif args.command == "git-recovery":
            if args.preserve is not None and not args.wp:
                parser.error("--preserve requires --wp <work package id>")
            rec = git_recovery(args.path, preserve=args.preserve, wp=args.wp)
            print(json.dumps(rec, indent=2))
            u = rec["unique_state"]
            summary = (f"git-recovery -- {rec['recovery_class']} {rec['disposition']}: uncommitted {u['uncommitted']}, "
                       f"stash {u['stash']}, dangling {len(u['dangling_commits'])}, unpushed {len(u['unpushed_commits'])}, "
                       f"other worktrees {len(u['other_worktrees'])}")
            if rec["preservation"]:
                summary += "; preserved " + ", ".join(rec["preservation"]["refs"])
            if rec["disposition"] == "RECOVERABLE":
                print(f"BADF GATE PASS: {summary}")
                return 0
            print(f"BADF GATE HELD: {summary}; preserve before any destructive step")
            return 3
        elif args.command == "git-release-check":
            rec = git_release_check(args.path, args.tag)
            print(json.dumps(rec, indent=2))
            print(f"BADF GATE PASS: git-release-check -- RELEASE_BOUND {rec['version']} -> {rec['source_revision'][:7]} "
                  f"(tree {rec['source_result_tree'][:7]}; annotated, signed={rec['provenance']['signed']})")
            return 0
        elif args.command == "git-release-record":
            rec = git_release_record(args.path, args.version)
            print(json.dumps(rec, indent=2))
            print(f"BADF GATE HELD: git-release-record -- {rec['version']} bound to {rec['source_revision'][:7]} as HUMAN_REQUIRED; "
                  f"the release authority creates the tag, then git-release-check verifies the pair")
            return 3
        elif args.command == "charter":
            print(write_charter(args.path))
            return 0
        elif args.command == "advance":
            print(advance_instance(args.path, args.dossier))
            return 0
        elif args.command == "init":
            print(init_project(args.intent))
            return 0
        elif args.command == "reconcile":
            print(reconcile_work_package(args.work_package))
            return 0
        elif args.command == "self-dossier":
            print(self_dossier(args.work_package))
        elif args.command == "build-ledger":
            print(verify_build_ledger(args.wp_id))

            return 0
        elif args.command == "research":
            print(validate_research_record(args.path))
            return 0
        elif args.command == "assure":
            print(validate_architecture_assurance(args.path))
            return 0
        elif args.command == "verify":
            print(validate_verification_record(args.path))
            return 0
        elif args.command == "solution":
            print(validate_solution_composition(args.path))
            return 0
        elif args.command == "security":
            print(validate_security_composition(args.path))
            return 0
        else:
            args._rendered = validate_dossier(args.path)
    except ValidationError as exc:
        print(f"BADF GATE FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 -- the contract is: never a traceback
        print(f"BADF GATE FAIL: internal error ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 2
    verdict = getattr(args, "_rendered", None)
    # QA finding M1: exit 0 and the PASS banner were printed for REWORK_REQUIRED,
    # BLOCKED and HUMAN_REQUIRED. AGENTS.md makes "returns PASS" a stage-exit
    # trigger, so any exit-code-keyed automation opened the next stage on a
    # FAIL dossier. Exit 0 means APPROVED or APPROVED_WITH_CONDITIONS. Nothing else.
    if verdict and verdict not in {"APPROVED", "APPROVED_WITH_CONDITIONS"}:
        print(f"BADF GATE HELD: {args.command} is well-formed; rendered verdict {verdict}")
        return 3
    print(f"BADF GATE PASS: {args.command}" + (f" -- rendered verdict {verdict}" if verdict else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
