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
    "badf/decisions/*.json",
    "badf/demands/*.json",
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
LEDGER_OUTCOMES = {"PREPARED", "COMMITTED", "REJECTED", "OUTCOME_UNKNOWN", "PROVEN_ABSENT",
                   "COMPENSATED", "MANUAL_REMEDIATION", "SKIPPED_ALREADY_COMMITTED", "OBSERVED"}
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



# ---- work ledger: landing is derived from git, claims are corroborated (BADF-WP-0019, #26) ----
WP_LINE = re.compile(r"^Work-Package:\s*(?:BADF-WP-|WP-2026-)([0-9]{4})\s*$", re.M)
WP_ID_FORMS = re.compile(r"^(?:BADF-WP-|WP-2026-)([0-9]{4})$")


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
            out.setdefault(f"WP-2026-{m.group(1)}", []).append(sha.strip())
    return out


def self_work_packages() -> list[tuple[Path, dict[str, Any]]]:
    me = self_repository()
    found = []
    for path in sorted((ROOT / "work").glob("WP-2026-*/work-package.json")):
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


def reconcile_work_package(wp_arg: str) -> str:
    m = WP_ID_FORMS.match(wp_arg.strip())
    if not m:
        raise ValidationError(f"{wp_arg!r} is not a work package id (WP-2026-NNNN or BADF-WP-NNNN)")
    wp = f"WP-2026-{m.group(1)}"
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
    target["landed_as"] = sha
    rec["external_target"] = target
    rec["status"] = "CLOSED"
    rec.pop("landing_not_on_ledger", None)
    path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    write_lockfile()
    also = f" (also carried by {', '.join(s[:7] for s in landed[:-1])})" if len(landed) > 1 else ""
    return f"BADF RECONCILE: {wp} CLOSED, landed_as {sha[:7]}{also}; lockfile re-signed -- ship it in the next work package's PR"


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
    verify_work_ledger()

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


EVIDENCE_RULES = {"prd": check_prd, "acceptance-criteria": check_acceptance_criteria, "product-approval": check_product_approval}


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
        span = f"{base}..{revision}" if base else f"{revision}^..{revision}"
        actual = _foreign_git(repo_root, "diff", span)
        if actual.returncode != 0:
            raise ValidationError(f"cannot compute the actual diff for {span} in {repo_name}")
        if actual.stdout != recorded:
            raise ValidationError(
                f"source-change artifact does not match what {revision[:12]} actually changed in {repo_name} "
                f"(recorded {len(recorded)} bytes, actual {len(actual.stdout)} bytes)")


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
    return events


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
    m = re.fullmatch(r"work/(WP-2026-[0-9]{4})/gate-dossier\.(G(?:0[0-9]|1[0-4]))\.json", dossier_rel.replace("\\", "/"))
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
    for d in (ROOT / "work").glob("WP-2026-*"):
        try:
            nums.append(int(d.name.split("-")[-1]))
        except ValueError:
            pass
    return f"WP-2026-{(max(nums) + 1 if nums else 1):04d}"


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
    existing = [d for d in (ROOT / "work").glob("WP-2026-*/work-package.json")
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
    append_event(wp_dir, "init", "COMMITTED", "badf-init", "controller", effect_id="intake",
                 output_digest=sha256(wp_dir / "work-package.json"),
                 note=f"intake of {proj['repository']} at {head[:12]} ({classification}); instance {receipt_rel}; "
                      f"{len(discovered)} facts discovered; {len(JUDGMENT_FIELDS)} judgment fields DECLARED_MISSING; dossier HUMAN_REQUIRED")
    write_lockfile()
    written = ", ".join(rel for rel, _ in contents) + f", {receipt_rel}"
    return (f"BADF INIT: {wp_id} created at G00, disposition HUMAN_REQUIRED; instance written to {root}: {written}"
            + ("; AGENTS.md preserved (merge plan required)" if agents_exists else ""))


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
        return rendered
    for evidence_type, path_value in indexed.items():
        validate_evidence(safe_repo_path(path_value, "evidence path"), dossier, evidence_type)
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("repo", help="validate repository governance structure")
    lock_parser = subparsers.add_parser("lock", help="re-sign badf/lockfile.json from current content")
    lock_parser.add_argument("--instance", type=Path, default=None, help="re-sign a project instance's badf/lockfile.json instead")
    inst_parser = subparsers.add_parser("instance", help="validate a project instance at <path>; writes nothing")
    inst_parser.add_argument("path", type=Path)
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
