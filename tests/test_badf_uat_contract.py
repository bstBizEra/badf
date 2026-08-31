"""badf-uat WP-UAT-A (BADF-WP-0115 / GOV-0107): the G10 business-acceptance router
contract freeze (DESIGNED).

Pins the frozen contract: the 20 invariants UAT-I01..I20 by id, the eight-stage workflow,
that this skill owns exactly the `uat` G10 evidence type (never release-packet,
operational-readiness or go-no-go), that scenario derivation reuses the existing
PRD->OBJ->AC->REQ traceability chain rather than re-deriving it, that no execution adapter
is registered as a subskill at this rung, that final product acceptance stays a separate
human decision, that no lifecycle/gate/schema change ships at this rung, and the registry
DESIGNED entry digest-bound to SKILL.md. Contract-only: no scripts/badf_uat.py, no typed
schema, no lifecycle change (UAT-I20).
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

ROOT = gate.ROOT
SKILL = ROOT / "skills" / "badf-uat" / "SKILL.md"
REFS_DIR = ROOT / "skills" / "badf-uat" / "references"
REFS = (
    "g10-uat-contract", "acceptance-provenance", "scenario-contract", "scenario-derivation",
    "execution-adapters", "environment-and-data-fidelity", "diagnostics-vs-oracle",
    "defect-classification", "coverage-matrix", "acceptance-disposition",
    "reuat-and-staleness", "g09-g10-g11-boundary", "acceptance", "external-methodology",
)
WORKFLOW_STAGES = (
    "RESOLVE ACCEPTANCE BASIS", "DERIVE SCENARIOS", "SELECT ADAPTER", "EXECUTE",
    "CLASSIFY DEFECTS", "COMPUTE COVERAGE", "PACKAGE RECOMMENDATION",
    "HANDOFF TO HUMAN ACCEPTANCE",
)
SKILL_TEXT = SKILL.read_text(encoding="utf-8") if SKILL.is_file() else ""
REFS_TEXT = "\n".join(
    (REFS_DIR / f"{r}.md").read_text(encoding="utf-8")
    for r in REFS if (REFS_DIR / f"{r}.md").is_file()
)


class UatContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        """No runtime, no typed schema, no gate code ships at this rung (UAT-I20)."""
        self.assertTrue(SKILL.is_file(), "SKILL.md must exist")
        for token in ("name: badf-uat", "gate: G10", "owner_role: release_authority",
                      "status: DESIGNED", "allowed_tools: []"):
            self.assertIn(token, SKILL_TEXT, token)
        self.assertFalse((ROOT / "scripts" / "badf_uat.py").exists(),
                          "UAT-I20: no competing UAT gate script at the DESIGNED rung")
        self.assertFalse((ROOT / "schemas" / "uat.schema.json").exists(),
                          "no typed uat evidence schema at this rung")
        self.assertFalse((ROOT / "schemas" / "uat-scenario.schema.json").exists(),
                          "no typed scenario schema at this rung")

    def test_root_states_all_invariants_and_the_workflow(self):
        for i in range(1, 21):
            self.assertIn(f"UAT-I{i:02d}", SKILL_TEXT, f"UAT-I{i:02d} must be named in SKILL.md")
        for stage in WORKFLOW_STAGES:
            self.assertIn(stage, SKILL_TEXT, f"workflow stage {stage}")

    def test_ownership_is_uat_only(self):
        """This skill produces exactly the `uat` G10 evidence type -- never the other three."""
        low = SKILL_TEXT.lower()
        self.assertIn("produces exactly one", low)
        for other in ("release-packet", "operational-readiness", "go-no-go"):
            self.assertIn(other, low, f"must name {other} as explicitly out of scope")
        self.assertIn("badf-production-readiness", SKILL_TEXT)

    def test_provenance_chain_reuses_existing_traceability(self):
        """Scenario derivation resolves the existing RTM link maps; it does not rebuild them."""
        prov = (REFS_DIR / "acceptance-provenance.md").read_text(encoding="utf-8")
        for token in ("requirement_to_objective", "criterion_to_requirement",
                      "schemas/traceability.schema.json", "schemas/acceptance-criteria.schema.json"):
            self.assertIn(token, prov, token)
        self.assertIn("resolve", prov.lower())
        self.assertIn("does not build a second one", prov.lower())

    def test_no_subskills_registered_yet(self):
        """No browser-uat / api-uat / manual-uat adapter is registered as a subskill at WP-UAT-A."""
        registry = json.loads((ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        names = {e["name"] for e in registry["skills"]}
        for sub in ("browser-uat", "api-uat", "manual-uat", "hybrid-uat"):
            self.assertNotIn(sub, names, f"{sub} must not be registered at WP-UAT-A")
        adapters = (REFS_DIR / "execution-adapters.md").read_text(encoding="utf-8")
        self.assertIn("No adapter is registered as a subskill at this rung", adapters)

    def test_final_acceptance_stays_human(self):
        disp = (REFS_DIR / "acceptance-disposition.md").read_text(encoding="utf-8")
        for token in ("UAT-I14", "UAT-I15", "Layer 2", "authorized human principal",
                      "cannot issue"):
            self.assertIn(token, disp, token)
        self.assertIn("recommendation", disp.lower())
        self.assertIn("evidence, not a decision", disp.lower())

    def test_no_lifecycle_change(self):
        lifecycle_before = json.loads((ROOT / "badf" / "lifecycle.json").read_text(encoding="utf-8"))
        gates = lifecycle_before.get("gates", [])
        g10 = next((g for g in gates if g.get("id") == "G10"), None)
        self.assertIsNotNone(g10, "G10 must already exist in lifecycle.json")
        self.assertIn("uat", g10.get("required_evidence", []))
        self.assertEqual(len(gates), 15, "no gate added or removed")

    def test_registry_pin_is_designed_and_tool_empty(self):
        registry = json.loads((ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        entry = next((e for e in registry["skills"] if e["name"] == "badf-uat"), None)
        self.assertIsNotNone(entry, "badf-uat must be registered")
        self.assertEqual(entry["status"], "DESIGNED")
        self.assertEqual(entry["allowed_tools"], [])
        self.assertEqual(entry["risk_class"], "C1")
        expected = "sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest()
        self.assertEqual(entry["digest"], expected, "registry digest must equal sha256(SKILL.md)")

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        self.assertIn("badf/skill-registry.json", SKILL_TEXT)
        ladder = (REFS_DIR / "acceptance.md").read_text(encoding="utf-8")
        self.assertIn("pointer, not a second", ladder)
        for rung in ("WP-UAT-A", "WP-UAT-B", "WP-UAT-C", "WP-UAT-D", "WP-UAT-E"):
            self.assertIn(rung, ladder, rung)

    def test_external_methodology_is_reference_adapt_only(self):
        ext = (REFS_DIR / "external-methodology.md").read_text(encoding="utf-8")
        self.assertIn("webapp-uat", ext)
        self.assertIn("adapt", ext.lower())
        self.assertIn("rejected", ext.lower())
        self.assertIn("Confirmed absent from this repository", ext)

    def test_all_fourteen_references_exist(self):
        self.assertTrue(REFS_DIR.is_dir(), "references/ dir must exist")
        for r in REFS:
            self.assertTrue((REFS_DIR / f"{r}.md").is_file(), f"missing reference {r}.md")


if __name__ == "__main__":
    unittest.main()
