"""Adversarial fixtures for the two-plane verdict.

Before this control the disposition was asserted by the author and checked
only for coherence with the conditions' shape. A dossier could assert
PASS_WITH_CONDITIONS while an OPEN Critical condition blocked the very gate
being passed, and the gate said PASS. Every negative test here presents a
disposition that contradicts the computed posture and asserts refusal; the
positive controls prove the rendering matrix on each legitimate row.
"""
import unittest

import scripts.badf_gate as gate


def cond(**over):
    c = {"condition_id": "C-1", "statement": "x", "status": "OPEN", "severity": "Major",
         "blocking_scope": "G12", "owner": "engineering_owner",
         "closure_predicate": "y", "closure_authority": "quality_authority"}
    c.update(over)
    return c


def dossier(gate_id="G09", disposition="PASS_WITH_CONDITIONS", conditions=None, **over):
    d = {"gate": gate_id, "disposition": disposition,
         "conditions": [cond()] if conditions is None else conditions}
    d.update(over)
    return d


class TwoPlaneVerdictTests(unittest.TestCase):
    def deny(self, pattern, **kw):
        with self.assertRaisesRegex(gate.ValidationError, pattern):
            gate.verify_two_plane(dossier(**kw))

    # --- the measured bypass ------------------------------------------
    def test_conditional_pass_at_the_gate_a_condition_blocks_is_refused(self):
        self.deny("contradicts computed posture OPEN_BLOCKING.*C-1 block", gate_id="G12")

    def test_blocking_via_comma_list_is_detected(self):
        self.deny("OPEN_BLOCKING", gate_id="G10", conditions=[cond(blocking_scope="G09, G10, G11")])

    # --- deny-unless-established ---------------------------------------
    def test_unparseable_blocking_scope_is_refused_not_treated_as_none(self):
        self.deny("not parseable", conditions=[cond(blocking_scope="the next stage")])

    def test_unknown_gate_id_in_scope_is_refused(self):
        self.deny("not parseable", conditions=[cond(blocking_scope="G99")])

    def test_empty_blocking_scope_is_refused(self):
        self.deny("not parseable", conditions=[cond(blocking_scope="  ")])

    # --- the verdict is computed, never asserted -------------------------
    def test_declared_verdict_that_disagrees_with_computed_is_refused(self):
        self.deny("contradicts the computed verdict", gate_id="G09",
                  rendered_verdict="APPROVED")           # computed: APPROVED_WITH_CONDITIONS

    def test_declared_approved_on_a_held_dossier_is_refused(self):
        self.deny("contradicts computed posture", gate_id="G12", rendered_verdict="APPROVED")

    def test_bare_pass_with_open_condition_is_refused(self):
        self.deny("PASS contradicts computed posture", disposition="PASS")

    # --- positive controls: every legitimate matrix row ----------------
    def test_clear_renders_approved(self):
        d = dossier(disposition="PASS", conditions=[])
        self.assertEqual(gate.verify_two_plane(d), "APPROVED")
        self.assertEqual(d["obligation_posture"], "CLEAR")

    def test_non_blocking_renders_approved_with_conditions(self):
        d = dossier(gate_id="G09")                      # condition blocks G12, not G09
        self.assertEqual(gate.verify_two_plane(d), "APPROVED_WITH_CONDITIONS")
        self.assertEqual(d["obligation_posture"], "OPEN_NON_BLOCKING")

    def test_scope_none_is_non_blocking(self):
        d = dossier(gate_id="G12", conditions=[cond(blocking_scope="none")])
        self.assertEqual(gate.verify_two_plane(d), "APPROVED_WITH_CONDITIONS")

    def test_closed_condition_does_not_block(self):
        d = dossier(gate_id="G12", disposition="PASS",
                    conditions=[cond(status="CLOSED", closed_by="qa-1")])
        self.assertEqual(gate.verify_two_plane(d), "APPROVED")

    def test_fail_renders_rework_required_regardless_of_posture(self):
        self.assertEqual(gate.verify_two_plane(dossier(gate_id="G12", disposition="FAIL")),
                         "REWORK_REQUIRED")

    def test_human_required_passes_through(self):
        self.assertEqual(gate.verify_two_plane(dossier(disposition="HUMAN_REQUIRED")), "HUMAN_REQUIRED")

    def test_correct_declared_verdict_is_accepted(self):
        d = dossier(gate_id="G09", rendered_verdict="APPROVED_WITH_CONDITIONS")
        self.assertEqual(gate.verify_two_plane(d), "APPROVED_WITH_CONDITIONS")

    def test_absent_declared_verdict_is_filled_in_not_refused(self):
        d = dossier(gate_id="G09")
        self.assertNotIn("rendered_verdict", d)
        gate.verify_two_plane(d)
        self.assertEqual(d["rendered_verdict"], "APPROVED_WITH_CONDITIONS")


if __name__ == "__main__":
    unittest.main()
