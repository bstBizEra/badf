"""badf-implementation-plan contract freeze (BADF-WP-0091 / WP-IMP-A).

badf-implementation-plan is the G06 planning composition/router: it turns an approved G01-G05
design into a governed Work Package DAG and normalizes it into the EXISTING G06 evidence
(work-breakdown / test-plan / release-plan / rollback-plan). It is a router and constraint
contract -- NOT an execution engine, a second gate, a Git realizer, or a source of authority.
This WP freezes the contract only: SKILL.md + 16 references, registered DESIGNED, with no
runtime, no second validator, no schema, and no lifecycle change. These tests guard that surface.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-implementation-plan" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-implementation-plan" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"

REFS = {
    "g06-contract.md", "work-package-contract.md", "decomposition.md", "vertical-slicing.md",
    "dependency-graph.md", "composition-order.md", "authority-and-risk.md", "test-planning.md",
    "evidence-planning.md", "execution-budget.md", "stop-conditions.md", "release-planning.md",
    "rollback-planning.md", "issue-projection.md", "acceptance.md", "external-methodology.md",
}


class BadfImplementationPlanContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        self.assertTrue(SKILL.is_file())
        self.assertEqual(REFS, {p.name for p in REFERENCES.glob("*.md")})
        # no second gate / runtime (IMP-I17): no standalone validator, no skill-owned schema.
        self.assertFalse((ROOT / "scripts" / "badf_implementation_plan.py").exists())
        self.assertFalse((ROOT / "schemas" / "implementation-plan.schema.json").exists())

    def test_root_states_all_invariants_and_the_workflow(self):
        text = SKILL.read_text(encoding="utf-8")
        for n in range(1, 18):
            self.assertIn(f"IMP-I{n:02d}", text)
        self.assertIn(
            "FRAME → INGEST → CLASSIFY → DECOMPOSE → SLICE → GRAPH → GOVERN → PROJECT → PACKAGE",
            text,
        )
        # the WP != task != issue != branch doctrine, and plan != authority
        for token in ("Task", "Work Package", "GitHub Issue", "Branch"):
            self.assertIn(token, text)
        self.assertRegex(text, r"Implementation Plan\s*[≠!=]+\s*Authority|Implementation Plan ≠ Authority")

    def test_composes_existing_g06_no_new_artifact(self):
        lifecycle = json.loads((ROOT / "badf" / "lifecycle.json").read_text())
        gate_names = {g["id"]: g.get("name", "") for g in lifecycle["gates"]}
        g06 = next(g for g in lifecycle["gates"] if g["id"] == "G06")
        # G06 is unchanged: the four existing artifacts, engineering_owner.
        self.assertEqual(
            set(g06["required_evidence"]),
            {"work-breakdown", "test-plan", "release-plan", "rollback-plan"},
        )
        self.assertEqual(g06.get("owner_role"), "engineering_owner")
        # no NEW gate named for implementation-plan beyond the existing G06.
        self.assertNotIn("implementation-plan", " ".join(gate_names.values()).lower())

    def test_authority_is_derived_from_change_class(self):
        text = (REFERENCES / "authority-and-risk.md").read_text(encoding="utf-8")
        self.assertIn("change_class", text)
        self.assertIn("authority matrix", text)
        # the plan cannot invent a parallel authority-class system.
        self.assertRegex(text, r"A0/A1/A2|A0/A2")
        self.assertRegex(text, r"[Dd]erived")

    def test_declares_topology_git_realizes(self):
        # planning declares execution topology; badf-git realizes it.
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf-git", skill)
        self.assertRegex(skill, r"realize")

    def test_external_methodology_is_adapt_not_authority(self):
        text = (REFERENCES / "external-methodology.md").read_text(encoding="utf-8")
        self.assertIn("ADAPT", text)
        for src in ("Spec Kit", "Superpowers", "to-tickets"):
            self.assertIn(src, text)
        self.assertRegex(text, r"never expand authority|NOT.*authority|not.*authority")

    def test_registry_pin_is_designed_and_tool_empty(self):
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in reg["skills"] if e.get("name") == "badf-implementation-plan"]
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertIn(entry["status"], ("DESIGNED", "IMPLEMENTED", "VALIDATED", "SHADOWED", "APPROVED", "ACTIVE"))
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual("sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest(), entry["digest"])

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `DESIGNED`", text)


if __name__ == "__main__":
    unittest.main()
