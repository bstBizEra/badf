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
WP_LINE = re.compile(r"^Work-Package:\s*(?:BADF-WP-|WP-2026-)([0-9]{4})\s*$", re.M)


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
    wp = f"WP-2026-{m.group(1)}"
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

        for cmd in (("init", "-q"), ("remote", "add", "origin", str(repo))):
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

        # No material code without a Work Package: the WP the message names must
        # have a record in the composed tree. Whether the ledger then reports it
        # LANDED_UNRECONCILED (the usual case) or finds it already reconciled (a
        # follow-up under a closed WP) is informational -- the first version keyed
        # on the LANDED_UNRECONCILED line and broke the moment a record was
        # reconciled, a third fixture-vs-ledger dependence in one session.
        if not (work / "work" / wp / "work-package.json").is_file():
            return fail(f"no work package record for {wp} in the composed tree; the message names a work package the candidate does not carry")
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
    args = ap.parse_args()
    try:
        return compose(args)
    except Exception as exc:  # noqa: BLE001 -- the contract is: never a traceback
        print(f"BADF COMPOSE FAIL: internal error ({type(exc).__name__}): {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
