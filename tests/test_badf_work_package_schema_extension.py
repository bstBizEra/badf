"""Work Package schema extension for G06 planning (BADF-WP-0092 / WP-IMP-B).

badf-implementation-plan needs the Governed Work Package to carry richer planning fields
(dependencies, source_baselines, expected_surfaces, authority_requirement, risk_factors,
test_obligations, evidence_obligations, execution_budget, stop_conditions, composition). This WP
extends schemas/work-package.schema.json with those fields as **optional** properties so every
existing record still validates (backward-compatible per docs governance) and documents the
external_target keys `reconcile_work_package` writes (landed_content_tree, composition_verified).

The schema walker enforces required/enum/pattern (incl. nested); it does NOT type-check non-object
types (#171 / GOV-0071), so the type/coverage/DAG-derivation controls are WP-IMP-C code controls,
not this schema. These tests guard the additive extension and the walker-enforced constraints.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

EXAMPLE = json.loads((gate.ROOT / "examples/work-package-planned.json").read_text())
SCHEMA = json.loads((gate.ROOT / "schemas/work-package.schema.json").read_text())


class BackwardCompatTests(unittest.TestCase):
    def test_all_existing_wp_records_still_validate(self):
        records = sorted((gate.ROOT / "work").glob("WP-2026-*/work-package.json"))
        self.assertGreaterEqual(len(records), 70, "expected the full ledger")
        for p in records:
            with self.subTest(wp=p.parent.name):
                gate.check_schema("work-package", json.loads(p.read_text()))

    def test_new_planning_fields_are_optional(self):
        # a minimal record carrying none of the new fields still validates (backward-compat).
        minimal = {k: EXAMPLE[k] for k in SCHEMA["required"]}
        gate.check_schema("work-package", minimal)

    def test_none_of_the_new_fields_are_required(self):
        new = {"source_baselines", "expected_surfaces", "authority_requirement", "risk_factors",
               "dependencies", "test_obligations", "evidence_obligations", "execution_budget",
               "stop_conditions", "composition"}
        self.assertEqual(set(), new & set(SCHEMA["required"]))

    def test_schema_stays_open_no_additionalProperties_false(self):
        # tightening additionalProperties would reject `note` and the ledger keys reconcile writes.
        self.assertNotIn("additionalProperties", SCHEMA)


class PlannedRecordTests(unittest.TestCase):
    def test_the_planned_example_conforms(self):
        gate.check_schema("work-package", EXAMPLE)

    def test_external_target_documents_the_reconcile_keys(self):
        et = SCHEMA["properties"]["external_target"]["properties"]
        self.assertIn("landed_content_tree", et)
        self.assertIn("composition_verified", et)
        # a malformed landed_content_tree is refused by the pattern the walker enforces.
        bad = copy.deepcopy(EXAMPLE)
        bad["external_target"] = {"repository": "owner/repo", "branch": "main",
                                  "landed_content_tree": "not-a-tree"}
        with self.assertRaises(gate.ValidationError):
            gate.check_schema("work-package", bad)


class WalkerEnforcedTests(unittest.TestCase):
    """The constraints the schema walker DOES enforce on the new fields: enum, pattern, nested required."""

    def refuse(self, mutate):
        bad = copy.deepcopy(EXAMPLE)
        mutate(bad)
        with self.assertRaises(gate.ValidationError):
            gate.check_schema("work-package", bad)

    def test_unknown_stop_condition_is_refused(self):
        self.refuse(lambda w: w["stop_conditions"].append("PLEASE_STOP"))

    def test_unknown_test_level_is_refused(self):
        self.refuse(lambda w: w["test_obligations"][0].__setitem__("level", "vibes"))

    def test_test_obligation_missing_a_required_key_is_refused(self):
        self.refuse(lambda w: w["test_obligations"][0].pop("claim"))

    def test_dependency_not_matching_the_wp_pattern_is_refused(self):
        self.refuse(lambda w: w["dependencies"]["blocked_by"].append("ISSUE-17"))

    def test_execution_budget_without_max_attempts_is_refused(self):
        self.refuse(lambda w: w["execution_budget"].pop("max_attempts"))

    def test_authority_requirement_bad_change_class_is_refused(self):
        self.refuse(lambda w: w["authority_requirement"].__setitem__("derived_from", "C9"))


class RegistryStatusTests(unittest.TestCase):
    def test_badf_implementation_plan_is_registered_at_least_implemented(self):
        # WP-IMP-B advanced DESIGNED -> IMPLEMENTED; the exact rung is pinned by the current-rung
        # suite (WP-IMP-C: VALIDATED). Guard only that the schema extension shipped at or past
        # IMPLEMENTED, so later advances (VALIDATED/SHADOWED/ACTIVE) do not re-break this test.
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-implementation-plan")
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "SHADOWED", "APPROVED", "ACTIVE"))


if __name__ == "__main__":
    unittest.main()
