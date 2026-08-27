"""WP-2026-0010 through G08: the first BADF gate whose evidence includes a
JUDGMENT (independent review) and a declared NON-APPLICABILITY (contract test
of prose). Both exposed gaps:

  - validate_evidence required outcome == PASS for every type. A contract
    test that honestly does not apply could only be recorded by lying. G08's
    own exit criterion says "non-coverage declared"; nothing on a dossier
    could declare it.
  - the independent review returned APPROVE_WITH_CONDITIONS with three
    conditions. Those must become carried conditions with owners and scopes,
    and the two-plane verdict must decide whether they block G08 itself.

Written to fail before the gate accepted NOT_APPLICABLE or read non_coverage.
"""
import json
import unittest

import scripts.badf_gate as gate
from tests.test_badf_foreign_work import MIRROR_PRESENT, MIRROR_REASON

WP = gate.ROOT / "work/WP-2026-0010"
DOSSIER = WP / "gate-dossier.G08.json"


class G08DossierTests(unittest.TestCase):
    def test_g08_dossier_exists_and_carries_all_four_evidence_types(self):
        d = json.loads(DOSSIER.read_text())
        self.assertEqual(d["gate"], "G08")
        self.assertEqual({e["type"] for e in d["evidence"]},
                         {"independent-review", "integration-test", "contract-test", "composed-tree-test"})

    def test_contract_test_is_recorded_as_not_applicable_not_pass(self):
        ev = json.loads((WP / "evidence/G08/contract-test.json").read_text())
        self.assertEqual(ev["outcome"], "NOT_APPLICABLE")

    def test_dossier_declares_non_coverage_for_the_not_applicable_type(self):
        d = json.loads(DOSSIER.read_text())
        self.assertIn("non_coverage", d)
        self.assertIn("contract-test", [n["evidence_type"] for n in d["non_coverage"]])

    def test_not_applicable_without_declared_non_coverage_is_refused(self):
        """Deny-unless-established: NOT_APPLICABLE is admitted only when the
        dossier explicitly declares non-coverage for that type with a reason."""
        d = json.loads(DOSSIER.read_text())
        d["non_coverage"] = []
        ev = {"type": "contract-test", "path": "work/WP-2026-0010/evidence/G08/contract-test.json"}
        with self.assertRaisesRegex(gate.ValidationError, "NOT_APPLICABLE.*non_coverage"):
            gate.check_non_coverage(d, ev["type"], "NOT_APPLICABLE")

    def test_the_three_review_conditions_are_carried_conditions(self):
        d = json.loads(DOSSIER.read_text())
        self.assertEqual(d["disposition"], "PASS_WITH_CONDITIONS")
        ids = {c["condition_id"] for c in d["conditions"]}
        self.assertEqual(ids, {"C-1", "C-2", "C-3"})
        for c in d["conditions"]:
            self.assertEqual(c["status"], "OPEN")
            self.assertIn(c["owner"], {"engineering_owner"})
            self.assertNotEqual(c["closure_authority"], "engineering_owner",
                                "the party that must do the work may not certify it done")

    def test_review_conditions_do_not_block_g08_itself(self):
        """C1-C3 are fixes to the change and to sibling docs; they block the
        MERGE (G09+), not the verification gate that found them."""
        d = json.loads(DOSSIER.read_text())
        self.assertEqual(gate.compute_obligation_posture(d), "OPEN_NON_BLOCKING")

    @unittest.skipUnless(MIRROR_PRESENT, MIRROR_REASON)
    def test_g08_validates_end_to_end_as_approved_with_conditions(self):
        """End-to-end resolves secb_pf through its LOCAL_MIRROR. On a CI
        runner the mirror does not exist and the gate says UNRESOLVABLE_HERE
        -- a fact about the host, by design. The seven tests above are pure
        file reads and run everywhere; this one runs where the mirror is.
        Went red on CI run 33080946366 for exactly this reason."""
        out = gate.validate_dossier(DOSSIER)
        self.assertEqual(out, "APPROVED_WITH_CONDITIONS")

    def test_council_disposition_is_recorded_and_the_review_is_the_council(self):
        """G08's independent-review IS the challenge. The classifier says
        NOT_REQUIRED (C1, reversible, internal, G08) -- and that is correct:
        the review happened because G08 demands it, not because risk did."""
        d = json.loads(DOSSIER.read_text())
        self.assertEqual(d["council_disposition"]["disposition"], "CHALLENGE_NOT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
