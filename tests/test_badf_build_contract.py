"""badf-build contract freeze (BADF-WP-0096 / WP-BLD-A, #188).

badf-build executes exactly one authorized Governed Work Package inside its exact scope,
baseline, budget and stop contract. It is a declarative router over an execution
discipline adapted from Matt Pocock's implement/tdd skills and obra/superpowers -- NOT a
runtime, NOT a second gate, NOT a grant of push/merge/release authority. This WP freezes
the contract only: SKILL.md + fourteen references, registered DESIGNED, no scripts, no
schema, no lifecycle change. These tests guard that declarative surface.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-build" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-build" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"
LIFECYCLE = ROOT / "badf" / "lifecycle.json"

REFS = {
    "g07-contract.md", "preflight.md", "execution-contract.md", "tdd-contract.md", "test-seams.md",
    "delegation.md", "scope-containment.md", "retry-and-budget.md", "stop-conditions.md",
    "self-review.md", "evidence-packaging.md", "handoff-to-g08.md", "acceptance.md",
    "external-methodology.md",
}
WORKFLOW = ("CLAIM → PREFLIGHT → ISOLATE → BASELINE → SLICE → TEST-FIRST/VERIFY-FIRST → IMPLEMENT → "
            "LOCAL VERIFY → SELF-REVIEW → RECONCILE → PACKAGE → HANDOFF")


def read(name: str) -> str:
    return (REFERENCES / name).read_text(encoding="utf-8")


class BadfBuildContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        self.assertTrue(SKILL.is_file())
        self.assertEqual(REFS, {p.name for p in REFERENCES.glob("*.md")})
        self.assertFalse((ROOT / "scripts" / "badf_build.py").exists())  # BLD-I18: no second gate
        for name in ("source-change", "build", "unit-test", "documentation"):  # BLD-B (WP-2026-0098): the typed G07 schemas exist from IMPLEMENTED on
            self.assertTrue((ROOT / "schemas" / f"{name}.schema.json").is_file(), name)

    def test_root_states_all_invariants_and_the_workflow(self):
        text = SKILL.read_text(encoding="utf-8")
        for n in range(1, 19):
            self.assertIn(f"BLD-I{n:02d}", text)
        self.assertIn(WORKFLOW, text)
        self.assertIn("BUILD ≠ INTEGRATION", text)
        self.assertIn("AUTHOR REVIEW ≠ INDEPENDENT ASSURANCE", text)
        self.assertIn("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE", text)
        self.assertIn("A successful build proves only", text)

    def test_tdd_is_governed_not_religious(self):
        text = read("tdd-contract.md")
        for token in ("TDD_REQUIRED", "TDD_NOT_APPLICABLE_WITH_REASON", "NO UNVERIFIED MUTATION", "METHOD OPTION",
                      "business behavior", "bug fix", "migration", "documentation-only", "mechanical refactor"):
            self.assertIn(token, text, token)
        # the religious form appears only struck through -- as the rejected doctrine, never as a rule
        self.assertEqual(text.count("EVERY CHANGE MUST USE TDD"), text.count("~~EVERY CHANGE MUST USE TDD~~"))
        self.assertGreaterEqual(text.count("~~EVERY CHANGE MUST USE TDD~~"), 1)

    def test_seams_come_from_g06_and_defects_route_upstream(self):
        text = read("test-seams.md")
        for token in ("test-plan", "test_obligation", "acceptance_ref", "seam", "TEST_PLAN_DEFECT", "G06 amendment"):
            self.assertIn(token, text, token)

    def test_delegation_cannot_expand_authority(self):
        text = read("delegation.md")
        for token in ("delegated_authority", "WP_authority", "repository_policy", "STRICT SUBSET",
                      "subagent task", "new Work Package", "allowed_paths", "prohibited"):
            self.assertIn(token, text, token)

    def test_scope_containment_and_drift_route_upstream(self):
        scope = read("scope-containment.md"); exe = read("execution-contract.md")
        for token in ("PLANNED SURFACE", "ACTUAL SURFACE", "UNEXPECTED_SCOPE", "bounded discovery"):
            self.assertIn(token, scope, token)
        for token in ("ARCHITECTURE_CHANGE_REQUIRED", "AUTHORIZATION_DESIGN_CHANGE_REQUIRED", "SECURITY_DESIGN_CHANGE_REQUIRED",
                      "REQUIREMENT_CHANGE_REQUIRED", "PRODUCT_REBASE_REQUIRED", "PRE-EXISTING FAILURE", "BUILD-INTRODUCED FAILURE"):
            self.assertIn(token, exe, token)

    def test_no_lifecycle_change_and_composes_into_g07(self):
        lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
        by = {g["id"]: g["required_evidence"] for g in lifecycle["gates"]}
        self.assertEqual(["source-change", "build", "unit-test", "documentation"], by["G07"])
        self.assertEqual(["independent-review", "integration-test", "contract-test", "composed-tree-test"], by["G08"])
        text = read("g07-contract.md")
        for token in ("source-change", "unit-test", "documentation", "does not mean", "independently verified", "approved to merge"):
            self.assertIn(token, text, token)
        self.assertIn("not automatically", read("self-review.md").lower())

    def test_registry_pin_is_implemented_and_tool_empty(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in registry["skills"] if e.get("name") == "badf-build"]
        self.assertEqual(1, len(entries)); entry = entries[0]
        self.assertEqual("IMPLEMENTED", entry["status"]); self.assertEqual([], entry["allowed_tools"]); self.assertEqual("C1", entry["risk_class"])  # BLD-B
        self.assertEqual("skills/badf-build/SKILL.md", entry["source"])
        self.assertEqual("sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest(), entry["digest"])

    def test_skill_points_to_registry_and_external_methodology_is_reference_only(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `", text)
        ext = read("external-methodology.md")
        for token in ("REFERENCE / ADAPT", "mattpocock", "superpowers", "REJECT", "ticket as authority",
                      "agent ruling as authority", "autonomous scope expansion", "branch finish as merge permission",
                      "self-review as independent G08 assurance"):
            self.assertIn(token, ext, token)


if __name__ == "__main__":
    unittest.main()
