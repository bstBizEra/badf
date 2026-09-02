"""G04 evidence contract (BADF-WP-0044, Issue #76; WP-ARCH-B on the frozen
badf-architecture contract).

G04's five required evidence types have semantics the gate enforces by opening
the artifact, inside validate_evidence, with the architecture baseline as the
spine the other four are consistent with: relationships carry direction + intent
and cross boundaries only through a declared interface; elements live inside a
declared boundary; trust-boundary data flows carry a classification; NFRs are
allocated (or deferred with reason) to a mechanism + fitness obligation;
fitness obligations are measurable; ADRs bind to real elements/requirements/NFRs;
data-model entities and api-contract interfaces resolve to the baseline; and
operability declares failure/recovery/observability. Faithful-runner shape.
"""

# Rung A (#265, WP-2026-0138): SHADOWED, nothing stronger to re-point at. The control is
# bare list-truthiness, so `minItems: 1` is EXACTLY equivalent and now refuses first.
# The control is RETAINED (criterion 5) and is now unreachable on this path; recorded
# rather than silently re-worded, per SARCHI C2. Disposition deferred, not decided.
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

DOSSIER = "examples/gate-dossier.G04.json"
EV = "examples/evidence/G04"


class G04Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        seed_clone(self.root, carry_working_state=True)
        for rel in ("schemas", "tests"):
            shutil.rmtree(self.root / rel, ignore_errors=True); shutil.copytree(gate.ROOT / rel, self.root / rel)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", DOSSIER], cwd=self.root, env=self.env, capture_output=True, text=True)

    def artifact(self, t):
        return json.loads((self.root / EV / f"{t}.artifact.json").read_text())

    def rewrite(self, t, obj):
        p = self.root / EV / f"{t}.artifact.json"; p.write_text(json.dumps(obj, indent=2) + "\n")
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text())
        rec["digest"] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest(); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def refused(self, needle):
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a defective G04 dossier rendered APPROVED")
        self.assertIn(needle, r.stderr, r.stderr)


class G04ExampleTests(G04Scratch):

    def test_shipped_example_renders_approved(self):
        r = self.cli(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("APPROVED", r.stdout)

    def test_missing_required_evidence_is_still_refused(self):
        d = json.loads((self.root / DOSSIER).read_text()); d["evidence"] = [e for e in d["evidence"] if e["type"] != "operability-design"]
        (self.root / DOSSIER).write_text(json.dumps(d, indent=2) + "\n")
        self.refused("missing evidence")


class ArchitectureRuleTests(G04Scratch):

    def test_a_relationship_without_intent_is_refused(self):
        a = self.artifact("architecture"); a["relationships"][0]["intent"] = ""; self.rewrite("architecture", a)
        self.refused("has no intent")

    def test_an_element_outside_every_boundary_is_refused(self):
        a = self.artifact("architecture"); a["elements"][0]["boundary"] = "BND-404"; self.rewrite("architecture", a)
        self.refused("is outside every declared boundary")

    def test_a_boundary_crossing_without_a_declared_interface_is_refused(self):
        a = self.artifact("architecture")
        for r in a["relationships"]:
            r.pop("via_interface", None)
        self.rewrite("architecture", a)
        self.refused("not through a declared interface")

    def test_a_trust_boundary_flow_without_classification_is_refused(self):
        a = self.artifact("architecture")
        for df in a["data_flows"]:
            if df["trust_boundary_crossing"]:
                df.pop("data_classification", None)
        self.rewrite("architecture", a)
        self.refused("crosses a trust boundary with no data classification")

    def test_an_allocated_nfr_without_a_mechanism_is_refused(self):
        a = self.artifact("architecture")
        for al in a["nfr_allocations"]:
            if al["disposition"] == "ALLOCATED":
                al["mechanism"] = ""
        self.rewrite("architecture", a)
        self.refused("is ALLOCATED but has no valid element, mechanism")

    def test_a_deferred_nfr_without_a_reason_is_refused(self):
        a = self.artifact("architecture")
        for al in a["nfr_allocations"]:
            if al["disposition"] != "ALLOCATED":
                al.pop("reason", None)
        self.rewrite("architecture", a)
        self.refused("carries no reason")

    def test_a_fitness_obligation_without_scope_is_refused(self):
        a = self.artifact("architecture"); a["fitness_obligations"][0]["scope"] = ""; self.rewrite("architecture", a)
        self.refused("no measurable property or no scope")

    def test_a_c4_view_element_absent_from_the_baseline_is_refused(self):
        a = self.artifact("architecture"); a["c4_views"][0]["elements"].append("EL-404"); self.rewrite("architecture", a)
        self.refused("absent from the baseline")


class AdrRuleTests(G04Scratch):

    def test_an_adr_with_no_affected_element_is_refused(self):
        d = self.artifact("adr"); d["records"][0]["affected_elements"] = []; self.rewrite("adr", d)
        self.refused("affects no architecture element")

    def test_an_adr_with_no_decision_driver_is_refused(self):
        d = self.artifact("adr"); d["records"][0]["decision_drivers"] = []; self.rewrite("adr", d)
        self.refused("has no decision driver")

    def test_an_adr_referencing_an_unknown_requirement_is_refused(self):
        d = self.artifact("adr"); d["records"][0]["requirement_refs"] = ["REQ-999"]; self.rewrite("adr", d)
        self.refused("references unknown requirement")

    def test_an_adr_referencing_an_unknown_nfr_is_refused(self):
        d = self.artifact("adr"); d["records"][0]["nfr_refs"] = ["NFR-999"]; self.rewrite("adr", d)
        self.refused("absent from the baseline")


class DataModelRuleTests(G04Scratch):

    def test_an_entity_with_an_unknown_owner_boundary_is_refused(self):
        d = self.artifact("data-model"); d["entities"][0]["owner_boundary"] = "BND-404"; self.rewrite("data-model", d)
        self.refused("is not a declared architecture boundary")


class ApiContractRuleTests(G04Scratch):

    def test_an_api_with_an_unknown_interface_is_refused(self):
        d = self.artifact("api-contract"); d["apis"][0]["interface"] = "IF-404"; self.rewrite("api-contract", d)
        self.refused("absent from the architecture baseline")


class OperabilityRuleTests(G04Scratch):

    def test_operability_without_failure_modes_is_refused(self):
        d = self.artifact("operability-design"); d["failure_modes"] = []; self.rewrite("operability-design", d)
        self.refused("failure_modes has 0 items")

    def test_a_failure_mode_without_recovery_is_refused(self):
        d = self.artifact("operability-design"); d["failure_modes"][0]["recovery"] = ""; self.rewrite("operability-design", d)
        self.refused("declares no recovery")

    def test_operability_without_observability_is_refused(self):
        d = self.artifact("operability-design"); d["observability"] = []; self.rewrite("operability-design", d)
        self.refused("no observability seams")


if __name__ == "__main__":
    unittest.main()
