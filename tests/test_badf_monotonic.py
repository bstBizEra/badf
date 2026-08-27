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
        real = gate.committed_matrix
        gate.committed_matrix = lambda: None
        try:
            self.deny("cannot be established")
        finally:
            gate.committed_matrix = real

    # --- explicit downgrade is admitted only with an attributable ack ----
    def test_downgrade_with_explicit_decision_ack_is_admitted(self):
        self.edit(lambda m: m["change_classes"]["C3"].__setitem__("required_roles", ["human_sponsor"]))
        os.environ[gate.DOWNGRADE_ACK] = "BADF-DEC-TEST"
        gate.verify_monotonic_authority()

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
