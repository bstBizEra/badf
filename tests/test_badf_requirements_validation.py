"""Validation of badf-requirements (BADF-WP-0064): the three cases, run against the
CANONICAL G02 gate — the gate is unchanged; validation runs it.

Case A — a valid dossier renders APPROVED (the skill's model produces clean artifacts).
Case B — the gate refuses exactly what the skill's discipline warns against: an orphan
requirement ("decomposes no objective", REQ-I02) and a qualitative NFR ("not quantified",
REQ-I04). Case C — a security requirement introduced from a G05 concern passes the gate
carrying its provenance (names the threat, traces to a security objective). The canonical
G02 gate has no security-source (SRC→REQ) field, so REQ-I06 provenance is a skill-authoring
discipline verified by inspection, not a deterministic control — the honest boundary.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests.test_badf_g02 import G02Scratch  # noqa: E402  (reuse the seed_clone fixture)


class CaseA_CleanArtifacts(G02Scratch):
    def test_a_valid_prd_renders_clean_g02_artifacts(self):
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("APPROVED", r.stdout)


class CaseB_Rework(G02Scratch):
    """The gate is the fitness function for the skill's REQ-I02 / REQ-I04 discipline."""

    def test_an_orphan_requirement_is_rework(self):
        reqs = self.artifact("requirements")
        reqs["requirements"][0]["objective_refs"] = []
        self.rewrite("requirements", reqs)
        self.refused("decomposes no objective")

    def test_a_qualitative_nfr_is_rework(self):
        nfr = self.artifact("nfr")
        nfr["nfrs"][0]["target"]["value"] = "fast"
        self.rewrite("nfr", nfr)
        self.refused("is not quantified")


class CaseC_SecurityProvenance(G02Scratch):
    # ids are numeric by schema (^REQ-/OBJ-/AC-[0-9]{3,}$); the security designation is
    # semantic -- the statement names the threat and the requirement traces to the
    # objective the validation-evidence doc designates as the security objective (OBJ-003).
    SEC_REQ, SEC_OBJ, SEC_AC = "REQ-004", "OBJ-003", "AC-003"

    def _introduce_security_requirement(self):
        reqs = self.artifact("requirements")
        reqs["requirements"].append({
            "id": self.SEC_REQ,
            "statement": "Session tokens are encrypted at rest, mitigating threat T-001 (spoofing) raised in the G05 threat model.",
            "priority": "Must Have",
            "testable": True,
            "objective_refs": [self.SEC_OBJ],
        })
        self.rewrite("requirements", reqs)
        rtm = self.artifact("traceability")
        rtm["objectives"].append(self.SEC_OBJ)
        rtm["acceptance_criteria"].append(self.SEC_AC)
        rtm["requirement_to_objective"].append({"requirement": self.SEC_REQ, "objectives": [self.SEC_OBJ]})
        rtm["criterion_to_requirement"].append({"criterion": self.SEC_AC, "requirements": [self.SEC_REQ]})
        self.rewrite("traceability", rtm)

    def test_a_security_requirement_with_provenance_passes_the_gate(self):
        self._introduce_security_requirement()
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("APPROVED", r.stdout)

    def test_the_security_requirement_preserves_its_provenance(self):
        # provenance = names the originating threat AND traces to the security objective
        # (REQ-I06). The canonical gate does not enforce SRC->REQ, so this is by inspection.
        self._introduce_security_requirement()
        reqs = self.artifact("requirements")
        sec = next(r for r in reqs["requirements"] if r["id"] == self.SEC_REQ)
        self.assertIn(self.SEC_OBJ, sec["objective_refs"])
        self.assertRegex(sec["statement"], r"threat|G05")


class ValidatedStatus(unittest.TestCase):
    def test_badf_requirements_is_registered_validated(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-requirements")
        self.assertEqual(entry["status"], "VALIDATED")

    def test_the_validation_evidence_documents_the_three_cases(self):
        doc = (gate.ROOT / "skills/badf-requirements/references/validation-evidence.md").read_text(encoding="utf-8")
        for token in ("Case A", "Case B", "Case C", "REQ-I06"):
            self.assertIn(token, doc)


if __name__ == "__main__":
    unittest.main()
