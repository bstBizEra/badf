"""Negative controls for every bypass confirmed by the independent QA pass.

Each test below reproduces a finding that PASSED the gate at 7599c3c. Every
one was reproduced first-hand before this file was written, and this file
was run against the unfixed gate first to prove the tests fail. A test that
cannot fail proves nothing.

Findings and their sources: B1 (code-reviewer), F-1/F-2/F-3/F-5/F-8/A53
(security-auditor), L463/W1/W3/W4/W6 (test-engineer).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.badf_gate as gate

EXAMPLE = gate.ROOT / "examples/gate-dossier.G00.json"
C3_ROLES = ["human_sponsor", "security_authority", "release_authority", "service_owner"]


def load_example():
    return json.loads(EXAMPLE.read_text())


def cli(payload, **env_over):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=str(gate.ROOT / "examples")) as h:
        json.dump(payload, h); p = Path(h.name)
    env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
    env.update(env_over)
    try:
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", str(p)],
                              cwd=str(gate.ROOT), capture_output=True, text=True, env=env)
    finally:
        p.unlink()


def approval(d, role, by):
    a = dict(d["approvals"][0]); a["role"] = role; a["by"] = by; return a


class QAFindingTests(unittest.TestCase):

    # --- B1: change_class is self-asserted; lifecycle floor never read ------
    def test_b1_class_below_gate_floor_is_refused(self):
        d = load_example(); d["gate"] = "G09"; d["change_class"] = "C0"
        r = cli(d)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("below the gate's minimum_change_class", r.stderr)

    # --- F-2: principals compared raw --------------------------------------
    def test_f2_lookalike_principals_do_not_satisfy_distinctness(self):
        d = load_example(); d["change_class"] = "C3"; d["author"] = "mallory"
        names = ["mallory ", "Mallory", "mallory​", "mallory\t"]
        d["approvals"] = [approval(d, r, n) for r, n in zip(C3_ROLES, names)]
        with self.assertRaisesRegex(gate.ValidationError, "invisible|distinct principals|reserved action"):
            gate.validate_authority(d)

    def test_f2_approver_with_trailing_space_is_still_the_author(self):
        """Whitespace must not manufacture a second identity."""
        d = load_example(); d["approvals"][0]["by"] = "example-author "
        with self.assertRaisesRegex(gate.ValidationError, "approve-own-work"):
            gate.validate_authority(d)

    def test_f2_case_variant_of_author_cannot_self_approve(self):
        d = load_example(); d["approvals"][0]["by"] = "Example-Author"
        with self.assertRaisesRegex(gate.ValidationError, "approve-own-work"):
            gate.validate_authority(d)

    def test_f2_invisible_character_in_principal_is_refused(self):
        d = load_example(); d["approvals"][0]["by"] = "someone​else"
        with self.assertRaisesRegex(gate.ValidationError, "invisible"):
            gate.validate_authority(d)

    # --- L463: blank principal counted toward quorum (mutant fail-open) ----
    def test_l463_blank_principal_is_refused(self):
        for by, msg in (("", "principal is empty"), ("   ", "principal is empty"), (None, "must be a string")):
            with self.subTest(by=by):
                d = load_example(); d["approvals"][0]["by"] = by
                with self.assertRaisesRegex(gate.ValidationError, msg):
                    gate.validate_authority(d)

    # --- A53 / M5: REJECTED from a required role is ignored ----------------
    def test_m5_rejected_vote_from_required_role_vetoes(self):
        d = load_example()
        rej = approval(d, "reviewer", "principal-b"); rej["decision"] = "REJECTED"
        d["approvals"].append(rej)
        with self.assertRaisesRegex(gate.ValidationError, "REJECTED"):
            gate.validate_authority(d)

    # --- F-5: CLOSED/WAIVED conditions need no closure authority -----------
    def test_f5_waived_condition_without_closer_is_refused(self):
        d = load_example()
        d["conditions"] = [{"condition_id": "C-1", "statement": "x", "status": "WAIVED", "severity": "Critical",
                            "blocking_scope": "G00", "owner": "reviewer", "closure_predicate": "y",
                            "closure_authority": "security_authority"}]
        with self.assertRaisesRegex(gate.ValidationError, "closed_by"):
            gate.validate_conditions(d, {"reviewer", "security_authority"})

    def test_f5_closed_by_lookalike_of_author_is_refused(self):
        d = load_example()
        d["conditions"] = [{"condition_id": "C-1", "statement": "x", "status": "CLOSED", "severity": "Major",
                            "blocking_scope": "none", "owner": "reviewer", "closure_predicate": "y",
                            "closure_authority": "reviewer", "closed_by": "Example-Author"}]
        with self.assertRaisesRegex(gate.ValidationError, "self-certified"):
            gate.validate_conditions(d, {"reviewer"})

    # --- M2: exceptions unvalidated ----------------------------------------
    def test_m2_bare_string_exception_is_refused(self):
        d = load_example(); d["disposition"] = "PASS_WITH_CONDITIONS"; d["exceptions"] = ["waive-mandatory-gate"]
        r = cli(d)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("exceptions[0] must be an object", r.stderr)

    # --- M1: PASS banner and exit 0 for non-pass verdicts ------------------
    def test_m1_fail_disposition_does_not_exit_zero(self):
        d = load_example(); d["disposition"] = "FAIL"
        r = cli(d)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("BADF GATE PASS", r.stdout)
        self.assertIn("REWORK_REQUIRED", r.stdout + r.stderr)

    def test_m1_malformed_approvals_are_refused_even_on_fail(self):
        d = load_example(); d["disposition"] = "FAIL"; d["approvals"] = "garbage"
        r = cli(d)
        self.assertIn("approvals must be an array", r.stderr)

    # --- M4: uncontrolled crashes ------------------------------------------
    def test_m4_no_traceback_on_any_malformed_field(self):
        cases = {"created_at": None, "change_class": ["C0"], "disposition": ["PASS"]}
        for field, value in cases.items():
            with self.subTest(field=field):
                d = load_example(); d[field] = value
                r = cli(d)
                self.assertNotEqual(r.returncode, 0)
                self.assertNotIn("Traceback", r.stderr, r.stderr)
                self.assertIn("BADF GATE FAIL", r.stderr)

    def test_m4_malformed_approval_fields_do_not_crash(self):
        for field, value in {"decision": ["APPROVED"], "approved_at": None, "approved_at": 5}.items():
            with self.subTest(field=field, value=value):
                d = load_example(); d["approvals"][0][field] = value
                r = cli(d)
                self.assertNotIn("Traceback", r.stderr, r.stderr)

    # --- F-8: downgrade ack unvalidated ------------------------------------
    def test_f8_ack_must_look_like_a_decision_id(self):
        for bad in ("0", "false", "x" * 200, "\x01"):
            with self.subTest(ack=ascii(bad)):
                os.environ[gate.DOWNGRADE_ACK] = bad
                try:
                    with self.assertRaisesRegex(gate.ValidationError, "decision id"):
                        gate._admit_downgrade(["C3 lost required role(s): x"])
                finally:
                    os.environ.pop(gate.DOWNGRADE_ACK, None)

    # --- W1/W3/W4: dossier gate must actually CALL the controls -------------
    def test_w3_w4_cli_holds_conditional_pass_at_its_own_blocked_gate(self):
        d = load_example(); d["disposition"] = "PASS_WITH_CONDITIONS"
        d["conditions"] = [{"condition_id": "C-1", "statement": "x", "status": "OPEN", "severity": "Major",
                            "blocking_scope": d["gate"], "owner": "reviewer", "closure_predicate": "y",
                            "closure_authority": "reviewer"}]
        r = cli(d)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("contradicts computed posture OPEN_BLOCKING", r.stderr)

    def test_w3_cli_refuses_bare_string_condition(self):
        d = load_example(); d["disposition"] = "PASS_WITH_CONDITIONS"; d["conditions"] = ["later"]
        r = cli(d)
        self.assertIn("must be an object", r.stderr)


if __name__ == "__main__":
    unittest.main()
