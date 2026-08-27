"""Mandate section 7: BADF decides whether council invocation is warranted.

Measured before this existed: the gate rendered WP-2026-0010 APPROVED and
said nothing about challenge. The decision not to convene a council was made
in a chat transcript. Four of the mandate's eight triggers (novelty,
architectural significance, blast radius, uncertainty-as-a-value) have NO
carrier on any BADF object; a classifier claiming to weigh them would be
inferring, which section 21 forbids. So this classifier reads ONLY fields
that exist -- change_class, risks[], rollback.reversible,
data_classification, gate -- and names which triggers fired.

Tier A: the disposition is ADVISORY. It grants no authority and changes who
may approve nothing. The only enforcement is a fact-check: a dossier that
claims a pass while CHALLENGE_REQUIRED must carry a council record, or it is
held. Written to FAIL before the classifier existed.
"""
import json
import unittest

import scripts.badf_gate as gate

WP = gate.ROOT / "work/WP-2026-0010"


def wp(**over):
    w = {"change_class": "C1", "data_classification": "internal",
         "rollback": {"reversible": True, "method": "revert"}}
    w.update(over); return w


def dossier(**over):
    d = {"change_class": "C1", "gate": "G07", "risks": [], "conditions": [], "council": None}
    d.update(over); return d


class CouncilDispositionTests(unittest.TestCase):
    # --- reads only what exists; names its triggers ------------------------
    def test_low_risk_reversible_internal_change_needs_no_council(self):
        r = gate.compute_council_disposition(dossier(), wp())
        self.assertEqual(r["disposition"], "CHALLENGE_NOT_REQUIRED")
        self.assertEqual(r["triggers"], [])

    def test_c3_change_requires_challenge(self):
        r = gate.compute_council_disposition(dossier(change_class="C3"), wp(change_class="C3"))
        self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
        self.assertIn("change_class:C3", r["triggers"])

    def test_irreversible_change_requires_challenge(self):
        r = gate.compute_council_disposition(dossier(), wp(rollback={"reversible": False, "method": "none"}))
        self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
        self.assertIn("irreversible", r["triggers"])

    def test_restricted_data_requires_challenge(self):
        r = gate.compute_council_disposition(dossier(), wp(data_classification="restricted"))
        self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
        self.assertIn("data_classification:restricted", r["triggers"])

    def test_production_gates_require_challenge(self):
        for g in ("G10", "G11", "G12"):
            with self.subTest(gate=g):
                r = gate.compute_council_disposition(dossier(gate=g), wp())
                self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
                self.assertIn(f"gate:{g}", r["triggers"])

    def test_declared_critical_risk_requires_challenge(self):
        r = gate.compute_council_disposition(
            dossier(risks=[{"id": "R-1", "severity": "Critical", "statement": "x"}]), wp())
        self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
        self.assertIn("risk:Critical", r["triggers"])

    def test_c2_alone_is_optional_not_required(self):
        r = gate.compute_council_disposition(dossier(change_class="C2"), wp(change_class="C2"))
        self.assertEqual(r["disposition"], "CHALLENGE_OPTIONAL")

    # --- deny-unless-established: the classifier never infers -------------
    def test_missing_rollback_is_treated_as_irreversible(self):
        r = gate.compute_council_disposition(dossier(), wp(rollback=None))
        self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
        self.assertIn("irreversible", r["triggers"])

    def test_untyped_risk_is_refused_not_ignored(self):
        with self.assertRaisesRegex(gate.ValidationError, "risks\\[0\\]"):
            gate.compute_council_disposition(dossier(risks=["something bad"]), wp())

    # --- the ONLY enforcement: a claimed pass at CHALLENGE_REQUIRED must carry a council record
    def test_pass_at_challenge_required_without_council_record_is_held(self):
        d = dossier(change_class="C3", disposition="PASS")
        with self.assertRaisesRegex(gate.ValidationError, "CHALLENGE_REQUIRED.*no council record"):
            gate.verify_council(d, wp(change_class="C3"))

    def test_pass_at_challenge_required_with_council_record_passes(self):
        d = dossier(change_class="C3", disposition="PASS",
                    council={"convened_at": "2026-08-27T00:00:00Z", "verdict": "APPROVE",
                             "ballots": [{"by": "a", "principal_type": "agent", "verdict": "APPROVE", "sealed": True},
                                         {"by": "b", "principal_type": "agent", "verdict": "APPROVE", "sealed": True}]})
        gate.verify_council(d, wp(change_class="C3"))

    def test_council_record_does_not_substitute_for_authority(self):
        """Council consensus != authority. A council REJECT does not refuse the
        dossier by itself (it is evidence); a council APPROVE does not satisfy
        an approval quorum. The classifier writes a disposition; it never
        touches approvals."""
        d = dossier(change_class="C3", disposition="PASS",
                    council={"convened_at": "2026-08-27T00:00:00Z", "verdict": "REJECT",
                             "ballots": [{"by": "a", "principal_type": "agent", "verdict": "REJECT", "sealed": True}]})
        r = gate.verify_council(d, wp(change_class="C3"))
        self.assertEqual(r["council_verdict"], "REJECT")
        self.assertEqual(r["disposition"], "CHALLENGE_REQUIRED")
        self.assertNotIn("approvals", r)

    def test_same_principal_cannot_cast_two_ballots(self):
        """docs/03: the same person or model run cannot count twice toward
        quorum. Canonicalization applies -- 'Alice' and 'alice ' are one
        principal. Found by mutation: this check had no test."""
        d = dossier(change_class="C3", disposition="PASS",
                    council={"convened_at": "2026-08-27T00:00:00Z", "verdict": "APPROVE",
                             "ballots": [{"by": "alice", "principal_type": "agent", "verdict": "APPROVE", "sealed": True},
                                         {"by": "Alice ", "principal_type": "agent", "verdict": "APPROVE", "sealed": True}]})
        with self.assertRaisesRegex(gate.ValidationError, "cast more than one ballot"):
            gate.verify_council(d, wp(change_class="C3"))

    def test_unsealed_first_round_ballot_is_refused(self):
        d = dossier(change_class="C3", disposition="PASS",
                    council={"convened_at": "2026-08-27T00:00:00Z", "verdict": "APPROVE",
                             "ballots": [{"by": "a", "principal_type": "agent", "verdict": "APPROVE", "sealed": False}]})
        with self.assertRaisesRegex(gate.ValidationError, "sealed"):
            gate.verify_council(d, wp(change_class="C3"))

    # --- the disposition is WRITTEN to the dossier as an output -----------
    def test_wp_0010_dossier_carries_the_computed_disposition(self):
        d = json.loads((WP / "gate-dossier.G07.json").read_text())
        self.assertIn("council_disposition", d)
        self.assertEqual(d["council_disposition"]["disposition"], "CHALLENGE_NOT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
