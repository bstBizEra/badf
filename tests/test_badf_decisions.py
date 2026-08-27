"""Decision records: an ack must name a decision that EXISTS and PERMITS.

Before this, BADF_AUTHORITY_DOWNGRADE_ACK was checked against a regex.
BADF-DEC-9999 matched and named nothing. Every test here presents an ack
the framework declares insufficient and asserts refusal; the positive
control proves a real, permitting, correctly-bound decision is admitted.
Written to FAIL against the regex version first.
"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import scripts.badf_gate as gate

DEC_DIR = gate.ROOT / gate.DECISIONS_DIR
DOWNGRADE = ["C3 lost required role(s): x"]


def matrix_digest_at_baseline():
    base = gate.resolve_authority_baseline()
    raw = subprocess.run(["git", "show", f"{base}:{gate.MATRIX}"], cwd=gate.ROOT, capture_output=True).stdout
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def decision(**over):
    d = {"schema_version": "1.0.0", "decision_id": "BADF-DEC-0900", "title": "test",
         "status": "DECIDED", "decided_at": "2026-08-27T00:00:00Z",
         "decision_authority": {"role": "human_sponsor", "principal": "operator"},
         "work_package_id": "BADF-WP-0900", "change_class": "C3", "ballot": "AGREE",
         "authorizes": {"summary": "s", "scope": [], "excluded": []},
         "authority_downgrade": {"permits_downgrade": True, "note": "t"},
         "binding": {"authority_matrix_digest": matrix_digest_at_baseline()}}
    d.update(over)
    return d


class DecisionAckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = []
        os.environ.pop(gate.DOWNGRADE_ACK, None)

    def tearDown(self):
        for p in self.tmp:
            Path(p).unlink(missing_ok=True)
        os.environ.pop(gate.DOWNGRADE_ACK, None)

    def write(self, d):
        p = DEC_DIR / f"{d['decision_id']}.json"
        p.write_text(json.dumps(d)); self.tmp.append(p); return p

    def deny(self, pattern, ack):
        os.environ[gate.DOWNGRADE_ACK] = ack
        with self.assertRaisesRegex(gate.ValidationError, pattern):
            gate._admit_downgrade(DOWNGRADE)

    # --- the F-8 residue ----------------------------------------------
    def test_well_formed_id_that_names_no_file_is_refused(self):
        self.deny("does not exist", "BADF-DEC-9999")

    def test_malformed_id_is_refused(self):
        self.deny("not a decision id", "BADF-DEC-TEST")

    # --- the decision must actually PERMIT ------------------------------
    def test_decision_that_does_not_permit_downgrade_is_refused(self):
        self.write(decision(authority_downgrade={"permits_downgrade": False, "note": "n"}))
        self.deny("does not permit an authority downgrade", "BADF-DEC-0900")

    def test_dec_0001_a_strengthening_decision_cannot_admit_a_downgrade(self):
        """The real DEC-0001 STRENGTHENED authority. Citing it for a downgrade is refused."""
        self.deny("does not permit an authority downgrade", "BADF-DEC-0001")

    def test_proposed_decision_is_refused(self):
        self.write(decision(status="PROPOSED"))
        self.deny("PROPOSED, not DECIDED", "BADF-DEC-0900")

    def test_revoked_decision_is_refused(self):
        self.write(decision(status="REVOKED"))
        self.deny("REVOKED, not DECIDED", "BADF-DEC-0900")

    # --- the decision must be BOUND to the policy being changed ----------
    def test_decision_bound_to_a_different_matrix_is_refused(self):
        self.write(decision(binding={"authority_matrix_digest": "sha256:" + "0" * 64}))
        self.deny("bound to authority matrix", "BADF-DEC-0900")

    def test_decision_with_no_binding_is_refused(self):
        self.write(decision(binding={}))
        self.deny("bound to authority matrix", "BADF-DEC-0900")

    # --- shape: deny-unless-established ---------------------------------
    def test_decision_missing_fields_is_refused(self):
        d = decision(); del d["decision_authority"]
        self.write(d)
        self.deny("missing fields: decision_authority", "BADF-DEC-0900")

    def test_decision_file_with_mismatched_id_is_refused(self):
        p = DEC_DIR / "BADF-DEC-0901.json"
        p.write_text(json.dumps(decision(decision_id="BADF-DEC-0902"))); self.tmp.append(p)
        self.deny("carries id", "BADF-DEC-0901")

    def test_decision_with_invalid_status_is_refused(self):
        self.write(decision(status="YES"))
        self.deny("invalid status", "BADF-DEC-0900")

    # --- positive control -----------------------------------------------
    def test_real_permitting_bound_decision_is_admitted(self):
        self.write(decision())
        os.environ[gate.DOWNGRADE_ACK] = "BADF-DEC-0900"
        gate._admit_downgrade(DOWNGRADE)

    # --- the shipped records are themselves valid ------------------------
    def test_shipped_decisions_load_and_are_decided(self):
        for did in ("BADF-DEC-0001", "BADF-DEC-0002"):
            with self.subTest(decision=did):
                d = gate.load_decision(did)
                self.assertEqual(d["status"], "DECIDED")
                self.assertEqual(d["ballot"], "AGREE")

    def test_dec_0001_binding_matches_the_matrix_it_was_taken_against(self):
        """DEC-0001 changed the GUARD not the policy; its bound digest must equal
        the matrix at its enacting commit AND at that commit's parent."""
        d = gate.load_decision("BADF-DEC-0001")
        for ref in (d["binding"]["enacting_commit"], d["binding"]["enacting_commit"] + "^"):
            raw = subprocess.run(["git", "show", f"{ref}:{gate.MATRIX}"], cwd=gate.ROOT, capture_output=True)
            self.assertEqual(raw.returncode, 0, f"cannot read matrix at {ref}")
            self.assertEqual(d["binding"]["authority_matrix_digest"],
                             "sha256:" + hashlib.sha256(raw.stdout).hexdigest())

    # --- forged decisions are drift ---------------------------------------
    def test_unsigned_new_decision_file_is_integrity_drift(self):
        self.write(decision(decision_id="BADF-DEC-0950"))
        with self.assertRaisesRegex(gate.ValidationError, "absent from lockfile"):
            gate.verify_integrity()


if __name__ == "__main__":
    unittest.main()
