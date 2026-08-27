"""Adversarial fixtures for the monotonic-authority guard.

Proven necessary first: with only the integrity lockfile, cutting C3 from
four required roles to one and re-signing the lockfile left the repo gate
and a one-approval C3 dossier both PASSING. These tests mutate the working
matrix into each downgrade shape and assert refusal. The strengthening
controls at the end exist so a guard that refused every change could not
pass.

Each test restores the matrix; a mid-test failure must not leave a weakened
policy on disk.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.badf_gate as gate

MATRIX = gate.ROOT / gate.MATRIX


class MonotonicAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.keep = tempfile.mkdtemp()
        shutil.copy2(MATRIX, Path(self.keep) / "m.json")
        os.environ.pop(gate.DOWNGRADE_ACK, None)

    def tearDown(self):
        shutil.copy2(Path(self.keep) / "m.json", MATRIX)
        shutil.rmtree(self.keep, ignore_errors=True)
        os.environ.pop(gate.DOWNGRADE_ACK, None)

    def edit(self, fn):
        m = json.loads(MATRIX.read_text()); fn(m)
        MATRIX.write_text(json.dumps(m, indent=2))

    def deny(self, pattern):
        with self.assertRaisesRegex(gate.ValidationError, pattern):
            gate.verify_monotonic_authority()

    # --- the proven bypass -------------------------------------------
    def test_c3_cut_from_four_roles_to_one_is_refused(self):
        self.edit(lambda m: m["change_classes"]["C3"].__setitem__("required_roles", ["human_sponsor"]))
        self.deny("C3 lost required role")

    def test_single_role_removed_is_refused(self):
        self.edit(lambda m: m["change_classes"]["C2"]["required_roles"].remove("quality_authority"))
        self.deny("C2 lost required role.*quality_authority")

    def test_change_class_removed_is_refused(self):
        self.edit(lambda m: m["change_classes"].pop("C3"))
        self.deny("change class C3 removed")

    def test_reserved_action_removed_is_refused(self):
        self.edit(lambda m: m["reserved_actions"].remove("approve-own-work"))
        self.deny("reserved action.*approve-own-work")

    def test_rule_minimum_class_lowered_is_refused(self):
        def f(m):
            for r in m["rules"]:
                if r["action"] == "destructive-or-admin": r["minimum_class"] = "C1"
        self.edit(f)
        self.deny("minimum_class lowered C3 -> C1")

    def test_rule_removed_is_refused(self):
        self.edit(lambda m: m.__setitem__("rules", [r for r in m["rules"] if r["action"] != "write-external"]))
        self.deny("rule for action 'write-external' removed")

    def test_rule_minimum_class_made_invalid_is_refused(self):
        def f(m):
            for r in m["rules"]:
                if r["action"] == "production-deploy": r["minimum_class"] = "C9"
        self.edit(f)
        self.deny("became invalid")

    # --- deny-unless-established --------------------------------------
    def test_missing_matrix_is_refused(self):
        MATRIX.unlink()
        self.deny("is missing")

    def test_no_committed_baseline_is_refused_not_skipped(self):
        real = gate.resolve_authority_baseline
        gate.resolve_authority_baseline = lambda: None
        try:
            self.deny("cannot be established")
        finally:
            gate.resolve_authority_baseline = real

    # --- explicit downgrade is admitted only with an attributable ack ----
    def test_downgrade_with_explicit_decision_ack_is_admitted(self):
        self.edit(lambda m: m["change_classes"]["C3"].__setitem__("required_roles", ["human_sponsor"]))
        os.environ[gate.DOWNGRADE_ACK] = "BADF-DEC-0001"
        gate.verify_monotonic_authority()

    def test_malformed_ack_does_not_admit(self):
        """QA finding F-8: '0', 'false', and 200 chars all admitted a downgrade."""
        self.edit(lambda m: m["change_classes"]["C3"].__setitem__("required_roles", ["human_sponsor"]))
        for bad in ("0", "false", "x" * 200, "BADF-DEC-TEST"):
            with self.subTest(ack=bad):
                os.environ[gate.DOWNGRADE_ACK] = bad
                self.deny("not a decision id")

    def test_blank_ack_does_not_admit(self):
        self.edit(lambda m: m["change_classes"]["C3"].__setitem__("required_roles", ["human_sponsor"]))
        os.environ[gate.DOWNGRADE_ACK] = "   "
        self.deny("downgrade refused")

    # --- positive controls: strengthening and no-op must PASS -----------
    def test_unchanged_matrix_passes(self):
        gate.verify_monotonic_authority()

    def test_adding_a_required_role_passes(self):
        self.edit(lambda m: m["change_classes"]["C1"]["required_roles"].append("security_authority"))
        gate.verify_monotonic_authority()

    def test_adding_a_reserved_action_passes(self):
        self.edit(lambda m: m["reserved_actions"].append("rotate-signing-key"))
        gate.verify_monotonic_authority()

    def test_raising_a_rule_minimum_class_passes(self):
        def f(m):
            for r in m["rules"]:
                if r["action"] == "write-repository": r["minimum_class"] = "C2"
        self.edit(f)
        gate.verify_monotonic_authority()

    def test_cli_refuses_a_resigned_downgrade(self):
        """The exact proven bypass, end to end: weaken, re-sign, run the gate."""
        self.edit(lambda m: m["change_classes"]["C3"].__setitem__("required_roles", ["human_sponsor"]))
        lock = gate.ROOT / gate.LOCKFILE
        keep = lock.read_text()
        try:
            gate.write_lockfile()
            r = subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"],
                               cwd=str(gate.ROOT), capture_output=True, text=True,
                               env={k: v for k, v in os.environ.items() if k != gate.DOWNGRADE_ACK})
            self.assertNotEqual(r.returncode, 0, "re-signed downgrade must not pass")
            self.assertIn("authority downgrade refused", r.stdout + r.stderr)
        finally:
            lock.write_text(keep)


if __name__ == "__main__":
    unittest.main()


class CommittedDowngradeTests(unittest.TestCase):
    """The defect the first negative control exposed.

    Every test above weakens the WORKING TREE. In CI the weakening is already
    COMMITTED, HEAD is the weakened commit, and a guard that compares against
    HEAD sees no difference. Run 33044484934 reached 'BADF GATE PASS: repo' on
    a branch that cut C3 from four roles to one; CI went red only because
    unrelated fixtures assumed four roles.

    These tests commit the weakening to a throwaway branch in a scratch clone
    and assert the guard still refuses -- which requires comparing against the
    last AUTHORIZED policy (the merge-base with the default branch), not HEAD.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.clone = Path(self.tmp) / "c"
        # Clone the AUTHORIZED policy -- the real default branch -- not whatever
        # branch the developer happens to be on. A clone whose origin/main is the
        # working branch would carry the candidate change into the baseline and
        # build the exact blind spot this test exists to catch.
        # Seed the scratch repo from the AUTHORIZED baseline commit, not from a
        # branch name. `git clone` of a checkout copies the checkout's LOCAL
        # branches as origin/* and never propagates its remote-tracking refs --
        # so on a pull_request runner (detached HEAD, no local `main`) every
        # clone-by-branch-name fails in setUp, and all four tests here errored
        # on runs 33044484934, 33045361792 and 33045417251 while reading as the
        # deliberate breakage. Resolving the SHA from the checkout's origin/main
        # and fetching that one commit works on push, pull_request and detached
        # checkouts alike.
        base = subprocess.run(["git", "-C", str(gate.ROOT), "rev-parse", f"origin/{gate.DEFAULT_BRANCH}"],
                              capture_output=True, text=True, check=True).stdout.strip()
        self.clone.mkdir()
        subprocess.run(["git", "-C", str(self.clone), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.clone), "remote", "add", "origin", str(gate.ROOT)], check=True)
        subprocess.run(["git", "-C", str(self.clone), "fetch", "-q", "origin", base], check=True)
        subprocess.run(["git", "-C", str(self.clone), "update-ref", f"refs/remotes/origin/{gate.DEFAULT_BRANCH}", base],
                       check=True)
        subprocess.run(["git", "-C", str(self.clone), "checkout", "-q", "-B", gate.DEFAULT_BRANCH, base], check=True)
        subprocess.run(["git", "-C", str(self.clone), "config", "user.email", "t@t"], check=True)
        subprocess.run(["git", "-C", str(self.clone), "config", "user.name", "t"], check=True)
        # The clone must run the guard UNDER TEST, not the baseline's copy of it.
        shutil.copy2(gate.ROOT / "scripts" / "badf_gate.py", self.clone / "scripts" / "badf_gate.py")
        subprocess.run(["git", "-C", str(self.clone), "checkout", "-q", "-b", "weaken"], check=True)
        m = json.loads((self.clone / gate.MATRIX).read_text())
        m["change_classes"]["C3"]["required_roles"] = ["human_sponsor"]
        (self.clone / gate.MATRIX).write_text(json.dumps(m, indent=2))
        env = {k: v for k, v in os.environ.items() if k not in (gate.DOWNGRADE_ACK, gate.BASELINE_ENV)}
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.clone, env=env,
                       capture_output=True, check=True)
        subprocess.run(["git", "-C", str(self.clone), "commit", "-qam", "weaken C3"], check=True)
        self.env = env

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def gate(self, **extra):
        env = dict(self.env); env.update(extra)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"],
                              cwd=self.clone, env=env, capture_output=True, text=True)

    def test_committed_downgrade_is_refused_against_default_branch(self):
        """HEAD is the weakened commit; origin/main is the authorized policy."""
        r = self.gate()
        self.assertNotEqual(r.returncode, 0, "a COMMITTED downgrade passed the gate:\n" + r.stdout + r.stderr)
        self.assertIn("authority downgrade refused", r.stdout + r.stderr)

    def test_explicit_baseline_sha_is_honoured(self):
        base = subprocess.run(["git", "-C", str(self.clone), "rev-parse", "origin/main"],
                              capture_output=True, text=True, check=True).stdout.strip()
        r = self.gate(BADF_AUTHORITY_BASELINE=base)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("authority downgrade refused", r.stdout + r.stderr)

    def test_baseline_equal_to_head_is_refused_as_unestablished(self):
        """Pointing the baseline at the weakened commit itself must not launder it."""
        head = subprocess.run(["git", "-C", str(self.clone), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
        r = self.gate(BADF_AUTHORITY_BASELINE=head)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cannot be established", r.stdout + r.stderr)

    def test_unreachable_default_branch_is_refused_not_skipped(self):
        subprocess.run(["git", "-C", str(self.clone), "remote", "remove", "origin"], check=True)
        r = self.gate()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cannot be established", r.stdout + r.stderr)
