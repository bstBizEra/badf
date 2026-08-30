"""G06 work-breakdown planning controls (BADF-WP-0093 / WP-IMP-C).

`check_work_breakdown` already enforced non-empty / unique ids / resolvable deps / acyclic. WP-IMP-C
adds the deterministic planning controls badf-implementation-plan needs -- the ones the schema walker
cannot do (#171): authority-not-reduced (IMP-C1/I07), acceptance coverage (IMP-C2/I09), a bounded
budget (IMP-C3/I11), a non-empty stop contract (IMP-C4/I12), and a resolvable + acyclic composition
order (IMP-C5/I06). Each fires only when its optional per-task field is present, so a minimal
id/description/depends_on task is unaffected (backward-compatible). Every test mutates a copy of the
enriched example and runs the gate's own check.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

EXAMPLE = json.loads((gate.ROOT / "examples/work-breakdown-planned.json").read_text())


class G06PlanningControlsBase(unittest.TestCase):
    def check(self, doc):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(doc, f)
            p = Path(f.name)
        try:
            gate.check_work_breakdown(p, {}, {})
        finally:
            p.unlink()

    def refuse(self, mutate, needle):
        bad = copy.deepcopy(EXAMPLE)
        mutate(bad)
        with self.assertRaises(gate.ValidationError) as cm:
            self.check(bad)
        self.assertIn(needle, str(cm.exception))


class PlanningControlTests(G06PlanningControlsBase):
    def test_enriched_example_passes(self):
        self.check(EXAMPLE)

    def test_a_minimal_task_still_validates(self):  # backward-compat: no planning fields
        self.check({"schema_version": "1.0.0", "tasks": [{"id": "WBS-001", "description": "do it"}]})

    def test_authority_reduced_below_the_matrix_is_refused(self):  # IMP-C1 / IMP-I07
        self.refuse(lambda w: w["tasks"][0]["authority_requirement"]["required_roles"].remove("quality_authority"),
                    "cannot reduce the authority")

    def test_uncovered_acceptance_is_refused(self):  # IMP-C2 / IMP-I09
        self.refuse(lambda w: w["tasks"][0]["acceptance"].append("AC-099"),
                    "no test_obligation claiming it")

    def test_nonpositive_max_attempts_is_refused(self):  # IMP-C3 / IMP-I11
        self.refuse(lambda w: w["tasks"][0]["execution_budget"].__setitem__("max_attempts", 0),
                    "positive integer")

    def test_boolean_max_attempts_is_refused(self):  # True is an int in python; refused at the schema layer (GOV-0080)
        # Since GOV-0080 the check_schema walker type-checks `integer`, so a bool max_attempts
        # is refused at the schema layer ("must be an integer, got bool") before the IMP-C3
        # positive-integer code control runs. The refusal is preserved; only the layer moved.
        self.refuse(lambda w: w["tasks"][0]["execution_budget"].__setitem__("max_attempts", True),
                    "integer")

    def test_empty_stop_conditions_is_refused(self):  # IMP-C4 / IMP-I12
        self.refuse(lambda w: w["tasks"][0].__setitem__("stop_conditions", []),
                    "stops nothing")

    def test_dangling_composition_after_is_refused(self):  # IMP-C5 / IMP-I06
        self.refuse(lambda w: w["tasks"][1]["composition_after"].append("WBS-404"),
                    "the landing order must resolve")

    def test_cyclic_composition_after_is_refused(self):  # IMP-C5 / IMP-I06
        self.refuse(lambda w: w["tasks"][0].__setitem__("composition_after", ["WBS-002"]),
                    "cycle")

    def test_a_task_without_change_class_needs_no_authority(self):  # IMP-C1 is field-scoped
        # dropping both change_class and authority_requirement is fine (the control is co-occurrence).
        doc = copy.deepcopy(EXAMPLE)
        doc["tasks"][0].pop("change_class"); doc["tasks"][0].pop("authority_requirement")
        self.check(doc)


class ShadowCalibrationTests(G06PlanningControlsBase):
    """WP-IMP-D: the representative shadow breakdowns pass, and the shadow-evidence reference labels
    itself REPRESENTATIVE (not real-project) and declares the non-coverage -- silence is not coverage."""

    SHADOWS = ("work-breakdown-shadow-migration.json", "work-breakdown-shadow-feature.json")
    DOC = gate.ROOT / "skills/badf-implementation-plan/references/shadow-evidence.md"

    def test_representative_shadow_breakdowns_pass(self):
        for name in self.SHADOWS:
            self.check(json.loads((gate.ROOT / "examples" / name).read_text()))

    def test_shadow_evidence_declares_representative_caveat(self):
        doc = self.DOC.read_text()
        self.assertIn("REPRESENTATIVE", doc)
        self.assertIn("no real G06 planning breakdowns yet", doc)

    def test_shadow_evidence_declares_noncoverage(self):
        doc = self.DOC.read_text().lower()
        self.assertIn("non-coverage", doc)
        self.assertIn("execution frontier", doc)
        self.assertIn("semantic resolution", doc)


class RegistryStatusTests(unittest.TestCase):
    def test_badf_implementation_plan_is_registered_active(self):  # WP-IMP-E admitted SHADOWED -> ACTIVE (operator admission)
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-implementation-plan")
        self.assertEqual(entry["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
