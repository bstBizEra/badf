"""security-composition matrix -- structural controls (BADF-WP-0083 / WP-SEC-B).

`badf_gate.py security <path>` validates a badf-security-design composition matrix's
STRUCTURAL integrity inside the one canonical gate (not a second validator -- SEC-I15):
unique threat ids (SEC-C01), every threat resolving to real provenance (SEC-C02 / SEC-I02),
and every *controlled* threat actually carrying a control (SEC-C03 / SEC-I03). The
residual_risk enum omits a bare `ACCEPTED`, so the skill structurally cannot self-accept
residual risk (SEC-I12). The cross-artifact SEAM controls (SEC-I04 bidirectional trace,
SEC-I01 baseline binding, semantic ref resolution) are WP-SEC-C. Every test mutates a copy
of the shipped example and runs the CLI.
"""

# Rung A (#265, WP-2026-0138): SHADOWED, nothing stronger to re-point at. The control is
# bare list-truthiness, so `minItems: 1` is EXACTLY equivalent and now refuses first.
# The control is RETAINED (criterion 5) and is now unreachable on this path; recorded
# rather than silently re-worded, per SARCHI C2. Disposition deferred, not decided.
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

EXAMPLE = json.loads((gate.ROOT / "examples/security-composition.json").read_text())


class SecurityCompositionBase(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f)
            p = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "security", str(p)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            p.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective matrix was admitted: " + r.stdout)
        self.assertIn(needle, r.stderr, r.stderr)

    def admitted(self, rec):
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)


class StructuralControlTests(SecurityCompositionBase):
    def test_the_shipped_example_passes(self):
        self.admitted(EXAMPLE)

    def test_an_empty_matrix_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"] = []
        self.refused(rec, "threats has 0 items")

    def test_a_duplicate_security_id_is_refused(self):  # SEC-C01
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][1]["security_id"] = rec["threats"][0]["security_id"]
        self.refused(rec, "duplicate")

    def test_a_threat_with_no_provenance_source_is_refused(self):  # SEC-C02 / SEC-I02
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["source"] = {}
        self.refused(rec, "binds no provenance source")

    def test_all_empty_provenance_arrays_still_bind_nothing(self):  # SEC-C02 (present-but-empty)
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["source"] = {"architecture_refs": [], "solution_refs": []}
        self.refused(rec, "binds no provenance source")

    def test_a_controlled_threat_with_no_control_is_refused(self):  # SEC-C03 / SEC-I03
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0].pop("control_refs", None)
        self.refused(rec, "no control_refs")

    def test_a_deferred_or_blocked_threat_needs_no_control(self):  # SEC-C03 is disposition-scoped
        # a non-controlled disposition legitimately carries no control_refs.
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["disposition"] = "deferred"
        rec["threats"][0].pop("control_refs", None)
        self.admitted(rec)


class SchemaEnforcedTests(SecurityCompositionBase):
    """Structural provenance/enum is the schema's job, not a code branch."""

    def test_a_malformed_security_id_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["security_id"] = "THR-1"
        self.refused(rec, "security_id")

    def test_a_missing_disposition_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        del rec["threats"][0]["disposition"]
        self.refused(rec, "disposition")

    def test_an_unknown_disposition_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["disposition"] = "accepted"
        self.refused(rec, "disposition")

    def test_residual_risk_cannot_be_bare_accepted(self):  # SEC-I12 structural
        # the skill cannot self-accept residual risk: `ACCEPTED` is not a value the enum offers.
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["residual_risk"] = "ACCEPTED"
        self.refused(rec, "residual_risk")


class MatrixInternalSeamTests(SecurityCompositionBase):
    """WP-SEC-C: the composition is coherent across concerns at the level the matrix alone can
    decide. The full external-artifact/semantic seams reconcile against artifacts that do not
    exist yet -- deferred. The example carries verification obligations and a coherent
    pending-authority row, so it satisfies every seam."""

    def test_a_controlled_threat_with_no_verification_is_refused(self):  # SEC-C04 / SEC-I04
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0].pop("verification_refs", None)
        self.refused(rec, "no verification_refs")

    def test_a_non_controlled_threat_needs_no_verification(self):  # SEC-C04 is disposition-scoped
        # a threat submitted to authority (not yet controlled) legitimately carries no verification.
        rec = copy.deepcopy(EXAMPLE)
        rec["threats"][0]["disposition"] = "deferred"
        rec["threats"][0].pop("control_refs", None)
        rec["threats"][0].pop("verification_refs", None)
        self.admitted(rec)

    def test_accepted_pending_authority_requires_pending_authority_disposition(self):  # SEC-C05
        rec = copy.deepcopy(EXAMPLE)
        # threats[0] is 'controlled'; claiming ACCEPTED-PENDING-AUTHORITY there is incoherent.
        rec["threats"][0]["residual_risk"] = "ACCEPTED-PENDING-AUTHORITY"
        self.refused(rec, "not 'pending-authority'")

    def test_pending_authority_without_accepted_pending_is_allowed(self):  # SEC-C05 is one-directional
        # a pending-authority threat need not have declared its residual risk yet.
        rec = copy.deepcopy(EXAMPLE)
        # threats[3] is the pending-authority row; drop its residual_risk -> still admitted.
        rec["threats"][3].pop("residual_risk", None)
        self.admitted(rec)


class ShadowCalibrationTests(SecurityCompositionBase):
    """WP-SEC-D: the representative shadow matrices pass, and the shadow-evidence reference
    labels itself REPRESENTATIVE (not real-project) and declares the external-artifact seams
    it does NOT cover -- silence is not coverage."""

    SHADOWS = ("security-composition-shadow-api.json", "security-composition-shadow-data.json")

    def test_representative_shadow_matrices_pass(self):
        for name in self.SHADOWS:
            rec = json.loads((gate.ROOT / "examples" / name).read_text())
            self.admitted(rec)

    def test_shadow_evidence_declares_representative_caveat(self):
        doc = (gate.ROOT / "skills/badf-security-design/references/shadow-evidence.md").read_text()
        self.assertIn("REPRESENTATIVE", doc)
        self.assertIn("no real security-composition matrices yet", doc)

    def test_shadow_evidence_declares_noncoverage(self):
        doc = (gate.ROOT / "skills/badf-security-design/references/shadow-evidence.md").read_text()
        self.assertIn("non-coverage", doc.lower())
        for seam in ("SEC-I04", "SEC-I01", "semantic"):
            self.assertIn(seam, doc, f"{seam} not declared as non-covered")


class RegistryStatusTests(unittest.TestCase):
    def test_badf_security_design_is_registered_active(self):  # WP-SEC-E admitted SHADOWED -> ACTIVE (operator admission)
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-security-design")
        self.assertEqual(entry["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
