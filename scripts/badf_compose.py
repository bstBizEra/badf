#!/usr/bin/env python3
"""badf_compose -- verify the tree that WOULD land, not the branch.

PR #30 (a77c042) was green on every step and its squash 30186c5 turned main
red: a pull-request runner's origin/main is the PRE-merge ledger, and the
merge itself changed what the tests read. This script composes base +
candidate exactly as the squash merge will -- with the candidate's message,
so the ledger sees the landing -- points origin/main at the result, and runs
`badf_gate.py repo` and the suite THERE.

Rules it holds itself to:
  - clone by SHA (a detached runner checkout has no local branches to copy);
  - refuse a message without a Work-Package line: the composed ledger would
    not see the landing, and a green run would prove nothing;
  - nest ONE level: the composed suite runs this script's own tests (depth 1),
    each composing with a restricted pattern at depth 2, where they skip.
    Refusing to nest at all (WP-0024) left the gate blind to exactly its own
    tests -- and those broke on main at 0b88c74 (#40);
  - print any restriction of the suite; never a silent cap;
  - write nothing to the source repository; work in a scratch directory.

Exit 0: BADF COMPOSE PASS. Exit 1: FAIL with the reason. Exit 2: internal.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BRANCH = "main"
FULL_PATTERN = "test_*.py"
# The Work-Package line and the machine-id namespace are defined once, in
# badf_gate.py (BADF-WP-0070 / GIT-B); this script must not repeat the literal.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from badf_gate import WP_LINE, WP_NAMESPACE, ValidationError, content_tree, load_composition_record  # noqa: E402
# content_tree and load_composition_record live in badf_gate.py (GIT-F moved them there:
# reconcile needs the same, object-store-only computation); this script only imports them.

# ---- badf-git GIT-E: the composition claim (BADF-WP-0076) ----------------------------
# A committed record of what integration is expected to produce. Its binding is the
# CONTENT TREE -- the composed tree with work/<WP>/ and badf/lockfile.json removed --
# so the record (and the self-dossier and lockfile that follow it) can live inside the
# PR they verify without moving the identity they bind. Compose recomputes it on the
# composed tree and refuses a stale base or a changed content tree. No record is
# backward compatible: requiring one is a later policy decision.
RECORD_REL = "evidence/G07/composition-record.json"


def _self_name(repo: Path) -> str | None:
    reg = repo / "badf/repositories.json"
    if not reg.is_file():
        return None
    try:
        for name, spec in (json.loads(reg.read_text(encoding="utf-8")).get("repositories") or {}).items():
            if isinstance(spec, dict) and spec.get("resolution") == "SELF":
                return name
    except ValueError:
        return None
    return None


def composition_record(*, repo: Path, candidate: str, wp: str, base: str, cand: str,
                       tree: str, ctree: str, tests: str) -> dict:
    from datetime import datetime, timezone
    name = sh(["git", "rev-parse", "--symbolic-full-name", candidate], repo).stdout.strip()
    epoch = None
    life = repo / "badf/lifecycle.json"
    if life.is_file():
        try:
            epoch = json.loads(life.read_text(encoding="utf-8")).get("policy_epoch")
        except ValueError:
            epoch = None
    return {
        "record": "git-composition",
        "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": _self_name(repo),
        "work_package_id": wp,
        "target_ref": f"refs/heads/{DEFAULT_BRANCH}",
        "target_base_sha": base,
        "source_ref": name if name.startswith("refs/") else None,
        "source_head_sha": cand,
        "merge_base_sha": sh(["git", "merge-base", base, cand], repo).stdout.strip() or None,
        "merge_method": "squash",
        "expected_result_tree": tree,
        "expected_content_tree": ctree,
        "policy_epoch": epoch,
        "test_set_epoch": None,
        "suite_pattern": tests,
        "non_coverage": ["test_set_epoch: BADF defines no test-set/toolchain epoch; not recorded rather than invented",
                         "source_head_sha and expected_result_tree are informational: committing this record moves both; "
                         "the binding is expected_content_tree (work/<WP>/ and the lockfile excluded)"],
    }


def verify_composition_record(rec: dict, *, wp: str, base: str, ctree: str) -> list[str]:
    problems = []
    if rec.get("work_package_id") != wp:
        problems.append(f"the record binds {rec.get('work_package_id')!r}, not {wp}")
    if rec.get("target_ref") != f"refs/heads/{DEFAULT_BRANCH}":
        problems.append(f"foreign target_ref {rec.get('target_ref')!r}; the protected target is refs/heads/{DEFAULT_BRANCH}")
    if rec.get("merge_method") != "squash":
        problems.append(f"merge_method {rec.get('merge_method')!r}; the protected method is squash")
    if rec.get("target_base_sha") != base:
        problems.append(f"composition record is stale: recorded for base {str(rec.get('target_base_sha'))[:7]}, composing onto "
                        f"{base[:7]} -- recompute with --record")
    elif rec.get("expected_content_tree") != ctree:
        problems.append(f"composition record does not match the composed content (recorded content tree "
                        f"{str(rec.get('expected_content_tree'))[:7]}, actual {ctree[:7]}) -- the content changed after the claim; "
                        f"recompute with --record")
    return problems


def sh(cmd: list[str], cwd: Path, env: dict | None = None, input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env, input=input)


def fail(reason: str) -> int:
    print(f"BADF COMPOSE FAIL: {reason}")
    return 1


def compose(args: argparse.Namespace) -> int:
    depth = int(os.environ.get("BADF_COMPOSE_DEPTH", "0") or 0)
    if depth >= 2:
        return fail(f"refusing to nest beyond depth 2 (BADF_COMPOSE_DEPTH={depth}); the composed world is verified one level deep")
    message = Path(args.message_file).read_text(encoding="utf-8")
    m = WP_LINE.search(message)
    if not m:
        return fail("candidate message carries no Work-Package line; the composed ledger would not see this landing")
    wp = f"{WP_NAMESPACE}{m.group(1)}"
    repo = Path(args.repo).resolve()

    def rev(ref: str) -> str | None:
        r = sh(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], repo)
        return r.stdout.strip() if r.returncode == 0 else None

    base, cand = rev(args.base), rev(args.candidate)
    if base is None:
        return fail(f"base {args.base!r} is not reachable in {repo}")
    if cand is None:
        return fail(f"candidate {args.candidate!r} is not reachable in {repo}")

    scratch = Path(tempfile.mkdtemp(prefix="badf-compose-"))
    work = scratch / "composed"
    try:
        work.mkdir()

        def g(*a: str, input: str | None = None) -> subprocess.CompletedProcess:
            return sh(["git", "-C", str(work), *a], work, input=input)

        # The scratch needs an identity for EVERY git operation, not only the squash commit:
        # a non-fast-forward `merge --squash` (base moved AND candidate ahead -- the divergent
        # case GIT-E's tests compose, which a PR head never is) prepares a merge commit and
        # dies with `fatal: empty ident name` on a runner that has no git identity (WP-0076).
        for cmd in (("init", "-q"), ("remote", "add", "origin", str(repo)),
                    ("config", "user.email", "badf-compose@local"), ("config", "user.name", "badf-compose")):
            r = g(*cmd)
            if r.returncode:
                return fail(f"git {' '.join(cmd)} failed: {r.stderr.strip()}")
        # --tags: the example dossier's source_revision is a TAG; a by-SHA fetch
        # without tags composed a tree the dossier tests could not validate --
        # this gate's first real run on its own branch (WP-0024) caught it.
        r = g("fetch", "-q", "--tags", "origin", base, cand)
        if r.returncode:
            return fail(f"base/candidate are not reachable by SHA from {repo}: {r.stderr.strip()}")
        g("update-ref", f"refs/remotes/origin/{DEFAULT_BRANCH}", base)
        r = g("checkout", "-q", "-B", DEFAULT_BRANCH, base)
        if r.returncode:
            return fail(f"checkout of base failed: {r.stderr.strip()}")
        r = g("merge", "--squash", "-q", cand)
        if r.returncode:
            g("merge", "--abort")
            last = ((r.stdout + r.stderr).strip().splitlines() or ["(no output)"])[-1]
            return fail(f"candidate {cand[:7]} does not compose onto base {base[:7]}: {last}")
        r = g("-c", "user.email=badf-compose@local", "-c", "user.name=badf-compose", "commit", "-q", "-F", "-", input=message)
        if r.returncode:
            last = ((r.stdout + r.stderr).strip().splitlines() or ["(no output)"])[-1]
            return fail(f"composing the squash commit failed (does the candidate change anything?): {last}")
        composed = g("rev-parse", "HEAD").stdout.strip()
        tree = g("rev-parse", "HEAD^{tree}").stdout.strip()
        g("update-ref", f"refs/remotes/origin/{DEFAULT_BRANCH}", composed)
        print(f"BADF COMPOSE: base {base[:7]} + candidate {cand[:7]} -> composed {composed[:7]} (tree {tree[:7]})")

        env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        env["BADF_COMPOSE_DEPTH"] = str(depth + 1)
        # The repository contract is judged on the UNTOUCHED composed tree, before any
        # CI-shape mutation: --ci-shape re-signs the scratch lockfile, and the first
        # version ran `repo` after that re-sign, so a candidate carrying integrity
        # drift passed under --ci-shape and failed under host shape (WP-0029).
        # No material code without a Work Package: the WP the message names must
        # have a record in the composed tree. Whether the ledger then reports it
        # LANDED_UNRECONCILED (the usual case) or finds it already reconciled (a
        # follow-up under a closed WP) is informational -- the first version keyed
        # on the LANDED_UNRECONCILED line and broke the moment a record was
        # reconciled, a third fixture-vs-ledger dependence in one session.
        if not (work / "work" / wp / "work-package.json").is_file():
            return fail(f"no work package record for {wp} in the composed tree; the message names a work package the candidate does not carry")
        # GIT-E (BADF-WP-0076): the composition claim. Compute the content tree of the
        # composed commit; write the record when asked; verify a committed record on the
        # tree that would land -- a stale base or a changed content tree is a refusal.
        ctree = content_tree(work, wp, "HEAD")
        if args.record:
            record = composition_record(repo=repo, candidate=args.candidate, wp=wp, base=base, cand=cand,
                                        tree=tree, ctree=ctree, tests=args.tests)
            args.record.parent.mkdir(parents=True, exist_ok=True)
            args.record.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            print(f"  record: written to {args.record} (content tree {ctree[:7]}, base {base[:7]})")
        rec_path = work / "work" / wp / RECORD_REL
        if rec_path.is_file():
            try:
                committed = load_composition_record(rec_path)
            except ValidationError as exc:
                return fail(f"composition record: {exc}")
            problems = verify_composition_record(committed, wp=wp, base=base, ctree=ctree)
            if problems:
                return fail("composition record: " + "; ".join(problems))
            print(f"  composition: CURRENT (content tree {ctree[:7]}, recorded for base {base[:7]})")
        else:
            print("  composition: no record (pre-GIT-E work package; requiring one is a later decision)")
        landed_body = g("log", "-1", "--format=%B", f"origin/{DEFAULT_BRANCH}").stdout
        if not WP_LINE.search(landed_body) or f"{m.group(1)}" not in (WP_LINE.search(landed_body).group(1)):
            return fail("the composed commit on origin/main does not carry the candidate's Work-Package line")
        r = sh([sys.executable, "scripts/badf_gate.py", "repo"], work, env=env)
        if r.returncode != 0:
            last = ((r.stdout + r.stderr).strip().splitlines() or ["(no output)"])[-1]
            print(f"  repo: FAIL -- {last}")
            return fail("the composed tree fails the repository contract")
        debt = any(f"{wp} LANDED_UNRECONCILED" in line for line in r.stdout.splitlines())
        print(f"  repo: PASS -- {wp} " + ("LANDED_UNRECONCILED on the composed ledger (reconciled by the next work package)"
                                         if debt else "record present and already reconciled (a follow-up under a closed work package)"))

        # If the work package ships its own G07 gate dossier, validate it on the
        # tree that would land: BADF's own work is governed like any project's
        # (BADF-WP-0033). exit 0 = APPROVED, 3 = HELD (a HUMAN_REQUIRED request);
        # 1/2 = a defective dossier and the merge is unsafe.
        self_dossier = work / "work" / wp / "gate-dossier.G07.json"
        if self_dossier.is_file():
            rd = sh([sys.executable, "scripts/badf_gate.py", "dossier", f"work/{wp}/gate-dossier.G07.json"], work, env=env)
            last = ((rd.stdout + rd.stderr).strip().splitlines() or ["(no output)"])[-1]
            if rd.returncode not in (0, 3):
                print(f"  self-dossier: FAIL -- {last}")
                return fail(f"{wp}'s own G07 dossier does not validate on the composed tree")
            print(f"  self-dossier: {'APPROVED' if rd.returncode == 0 else 'HELD (HUMAN_REQUIRED)'} -- {last}")

        shape = "host"
        if args.ci_shape:
            shape = "CI"
            env["BADF_PROPTECH_PATH"] = str(scratch / "no-proptech")
            reg = work / "badf/repositories.json"
            if reg.is_file():
                doc = json.loads(reg.read_text(encoding="utf-8"))
                for spec in (doc.get("repositories") or {}).values():
                    if isinstance(spec, dict) and spec.get("resolution") == "LOCAL_MIRROR":
                        spec["local_path"] = str(scratch / "no-mirror")
                reg.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
                r = sh([sys.executable, "scripts/badf_gate.py", "lock"], work, env=env)
                if r.returncode:
                    return fail(f"re-signing the CI-shape scratch failed: {r.stderr.strip()}")
        print(f"  shape: {shape}")
        print(f"  suite pattern: {args.tests}" + ("" if args.tests == FULL_PATTERN else "   (RESTRICTED -- not the full suite)"))

        r = sh([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", args.tests, "-q"], work, env=env)
        text = r.stdout + r.stderr
        ran = re.search(r"^Ran \d+ tests?[^\n]*", text, re.M)
        summary = re.search(r"^(OK\b[^\n]*|FAILED[^\n]*)$", text, re.M)
        if r.returncode != 0 or summary is None or not summary.group(1).startswith("OK"):
            print(f"  suite: FAILED ({ran.group(0) if ran else 'no test count'}; {summary.group(1) if summary else 'no summary'})")
            for line in text.splitlines():
                if line.startswith(("FAIL:", "ERROR:")):
                    print("    " + line[:160])
            return fail("the composed suite is red")
        print(f"  suite: {summary.group(1)} ({ran.group(0) if ran else '?'})")
        print("BADF COMPOSE PASS")
        return 0
    finally:
        if args.keep:
            print(f"  kept: {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, default=ROOT, help="source repository (default: this framework)")
    ap.add_argument("--base", default=f"origin/{DEFAULT_BRANCH}", help="the ledger the candidate would land on")
    ap.add_argument("--candidate", default="HEAD", help="the commit that would be squash-merged")
    ap.add_argument("--message-file", required=True, type=Path, help="the squash message (the PR body); must carry a Work-Package line")
    ap.add_argument("--tests", default=FULL_PATTERN, help="unittest discovery pattern (a restriction is printed)")
    ap.add_argument("--ci-shape", action="store_true", help="no PropTech clone, no local mirror -- as on the runner")
    ap.add_argument("--keep", action="store_true", help="keep the scratch directory")
    ap.add_argument("--record", type=Path, help="write the git-composition record (the content-tree-bound composition claim) "
                    "to this path; commit it as work/<WP>/evidence/G07/composition-record.json and compose again to verify it")
    args = ap.parse_args()
    try:
        return compose(args)
    except Exception as exc:  # noqa: BLE001 -- the contract is: never a traceback
        print(f"BADF COMPOSE FAIL: internal error ({type(exc).__name__}): {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
