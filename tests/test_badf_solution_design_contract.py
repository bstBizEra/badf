"""badf-solution-design contract freeze (BADF-WP-0068 / WP-SOL-A).

badf-solution-design is the declarative composition/orchestration layer over the design
specialists (UX / authorization / data / API / accessibility). It is a router and
constraint contract -- NOT a sixth architecture skill, a new gate, a second validator,
or a document-generation mega-skill. This WP freezes the contract only: SKILL.md +
eleven references, registered DESIGNED, with no runtime, no second validator, and no
lifecycle change. These tests guard that declarative surface.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-solution-design" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-solution-design" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"

REFS = {
    "composition-contract.md", "routing.md", "traceability.md", "ux-contract.md",
    "authorization-contract.md", "data-contract.md", "api-contract.md",
    "accessibility-contract.md", "cross-artifact-consistency.md", "acceptance.md",
    "external-methodology.md",
}


class BadfSolutionDesignContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        self.assertTrue(SKILL.is_file())
        self.assertEqual(REFS, {p.name for p in REFERENCES.glob("*.md")})
        # no mutation engine / second gate (SOL-I12) and no new schema-authority.
        self.assertFalse((ROOT / "scripts" / "badf_solution_design.py").exists())
        self.assertFalse((ROOT / "schemas" / "solution-design.schema.json").exists())
        self.assertFalse((ROOT / "schemas" / "solution-composition.schema.json").exists())

    def test_root_states_all_invariants_and_the_workflow(self):
        text = SKILL.read_text(encoding="utf-8")
        for n in range(1, 13):
            self.assertIn(f"SOL-I{n:02d}", text)
        self.assertIn("FRAME → INGEST → ROUTE → SPECIALIZE → COMPOSE → RECONCILE → CHALLENGE → TRACE → PACKAGE", text)
        self.assertIn("ARCHITECTURE_CHANGE_REQUIRED", text)
        # the architecture-spine boundary is explicit.
        self.assertIn("badf-architecture", text)
        self.assertRegex(text, r"MUST NOT invent")

    def test_cross_artifact_consistency_enumerates_the_seams(self):
        text = (REFERENCES / "cross-artifact-consistency.md").read_text(encoding="utf-8")
        for n in range(1, 13):
            self.assertIn(f"SOL-I{n:02d}", text)
        self.assertIn("NO MATCH = DENY", text)          # SOL-I05 default deny
        self.assertIn("composition matrix", text.lower())

    def test_routing_maps_signals_to_reference_adapters(self):
        text = (REFERENCES / "routing.md").read_text(encoding="utf-8")
        self.assertIn("REFERENCE / ADAPT", text)
        for adapter in ("authorization-design", "database-schema-designer", "api-design", "accessibility"):
            self.assertIn(adapter, text)
        # architecture and research are the spine / evidence, not adapters.
        self.assertIn("badf-architecture", text)
        self.assertIn("badf-research", text)

    def test_no_lifecycle_change_and_composes_into_existing_gates(self):
        lifecycle = json.loads((ROOT / "badf" / "lifecycle.json").read_text())
        gate_names = {g["id"]: g.get("name", "") for g in lifecycle["gates"]}
        # no new "solution design" gate was added.
        self.assertNotIn("solution", " ".join(gate_names.values()).lower())
        # G03/G04 required_evidence is unchanged (the known sets).
        g03 = next(g for g in lifecycle["gates"] if g["id"] == "G03")
        g04 = next(g for g in lifecycle["gates"] if g["id"] == "G04")
        self.assertEqual(set(g03["required_evidence"]), {"journeys", "service-blueprint", "accessibility", "user-validation"})
        self.assertEqual(set(g04["required_evidence"]), {"architecture", "adr", "data-model", "api-contract", "operability-design"})

    def test_registry_pin_is_designed_and_tool_empty(self):
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in reg["skills"] if e.get("name") == "badf-solution-design"]
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual("DESIGNED", entry["status"])
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual("sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest(), entry["digest"])

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `DESIGNED`", text)


if __name__ == "__main__":
    unittest.main()
