"""Adversarial fixtures for carried conditions on a conditional pass.

Before this control, PASS_WITH_CONDITIONS required only that `conditions` be
non-empty -- `["later"]` satisfied it. Every negative test here presents a
condition the framework declares un-closable and asserts refusal. The positive
controls exist so a validator that refused everything could not pass.
"""
import json
import unittest

import scripts.badf_gate as gate

ROLES = {"reviewer", "engineering_owner", "independent_reviewer", "product_owner",
         "quality_authority", "service_owner", "human_sponsor", "security_authority",
         "release_authority"}


def cond(**over):
    c = {"condition_id": "C-1", "statement": "Add the missing negative test",
         "status": "OPEN", "severity": "Major", "blocking_scope": "G09",
         "owner": "engineering_owner", "closure_predicate": "test exists and runs in CI",
         "closure_authority": "quality_authority"}
    c.update(over)
    return c


def dossier(**over):
    d = {"disposition": "PASS_WITH_CONDITIONS", "exceptions": [], "author": "principal-author",
         "conditions": [cond()]}
    d.update(over)
    return d


class CarriedConditionTests(unittest.TestCase):
    def deny(self, pattern, **over):
        with self.assertRaisesRegex(gate.ValidationError, pattern):
            gate.validate_conditions(dossier(**over), ROLES)

    # --- the measured bypass ------------------------------------------
    def test_bare_string_condition_is_refused(self):
        self.deny("must be an object", conditions=["later"])

    def test_empty_conditions_and_exceptions_on_conditional_pass_refused(self):
        self.deny("requires conditions or exceptions", conditions=[])

    # --- deny-unless-established ---------------------------------------
    def test_missing_closure_authority_is_refused(self):
        c = cond(); del c["closure_authority"]
        self.deny("missing required fields: closure_authority", conditions=[c])

    def test_missing_owner_is_refused(self):
        c = cond(); del c["owner"]
        self.deny("missing required fields: owner", conditions=[c])

    def test_empty_closure_predicate_is_refused(self):
        self.deny("closure_predicate is empty", conditions=[cond(closure_predicate="  ")])

    def test_owner_outside_authority_matrix_is_refused(self):
        self.deny("not a role in the authority matrix", conditions=[cond(owner="the-agent")])

    def test_closure_authority_outside_matrix_is_refused(self):
        self.deny("closure_authority 'nobody'", conditions=[cond(closure_authority="nobody")])

    def test_invalid_status_is_refused(self):
        self.deny("invalid status", conditions=[cond(status="DONE")])

    def test_invalid_severity_is_refused(self):
        self.deny("invalid severity", conditions=[cond(severity="Meh")])

    def test_malformed_condition_id_is_refused(self):
        self.deny("must match C-<n>", conditions=[cond(condition_id="COND1")])

    def test_duplicate_condition_id_is_refused(self):
        self.deny("duplicate condition_id C-1", conditions=[cond(), cond()])

    def test_author_cannot_self_certify_closure(self):
        self.deny("closure is not self-certified",
                  conditions=[cond(status="CLOSED", closed_by="principal-author")])

    # --- disposition/condition coherence --------------------------------
    def test_bare_pass_with_open_condition_is_refused(self):
        self.deny("bare PASS may not carry OPEN", disposition="PASS")

    def test_conditional_pass_with_only_closed_conditions_is_refused(self):
        self.deny("carries no OPEN condition", conditions=[cond(status="CLOSED", closed_by="qa-1")])

    # --- positive controls -----------------------------------------------
    def test_well_formed_open_condition_passes(self):
        gate.validate_conditions(dossier(), ROLES)

    def test_bare_pass_with_no_conditions_passes(self):
        gate.validate_conditions(dossier(disposition="PASS", conditions=[]), ROLES)

    def test_bare_pass_with_only_closed_history_passes(self):
        gate.validate_conditions(
            dossier(disposition="PASS", conditions=[cond(status="CLOSED", closed_by="qa-1")]), ROLES)


if __name__ == "__main__":
    unittest.main()
