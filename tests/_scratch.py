"""One way to build a scratch clone of BADF that works on ANY checkout.

`git clone <checkout>` copies the checkout's LOCAL branches as origin/*. On a
pull_request runner the checkout is a detached merge ref with no local main,
so the clone has no origin/main, and the monotonic baseline resolver refuses
everything before the code under test runs. This was fixed once in WP-0004
(CommittedDowngradeTests) and reintroduced in WP-0010 by a second clone
helper written from scratch. There is now exactly one.

Seeds the clone from the SHA of origin/<default> as the source checkout knows
it: init, fetch that one commit, pin refs/remotes/origin/<default> to it, and
check it out as a local branch. Nothing depends on the source having a local
branch by any name.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import scripts.badf_gate as gate


def seed_clone(dest: Path, *, carry_working_state: bool = False) -> str:
    base = subprocess.run(["git", "-C", str(gate.ROOT), "rev-parse", f"origin/{gate.DEFAULT_BRANCH}"],
                          capture_output=True, text=True, check=True).stdout.strip()
    dest.mkdir(parents=True)
    g = ["git", "-C", str(dest)]
    subprocess.run([*g, "init", "-q"], check=True)
    subprocess.run([*g, "remote", "add", "origin", str(gate.ROOT)], check=True)
    subprocess.run([*g, "fetch", "-q", "--tags", "origin", base], check=True)
    subprocess.run([*g, "update-ref", f"refs/remotes/origin/{gate.DEFAULT_BRANCH}", base], check=True)
    subprocess.run([*g, "checkout", "-q", "-B", gate.DEFAULT_BRANCH, base], check=True)
    subprocess.run([*g, "config", "user.email", "t@t"], check=True)
    subprocess.run([*g, "config", "user.name", "t"], check=True)
    if carry_working_state:
        # The clone must see the same working state as ROOT: the gate under test,
        # the registries and decisions, and any work packages -- including files
        # not yet committed on the source branch.
        for rel in ("scripts/badf_gate.py", gate.REPOSITORIES, gate.DECISIONS_DIR, gate.DEMANDS_DIR, "work", "examples", "templates"):
            src = gate.ROOT / rel; dst = dest / rel
            if src.is_dir():
                shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
            elif src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
    return base
