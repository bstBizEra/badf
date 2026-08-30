"""badf-engineering-verification contract freeze (BADF-WP-0100 / WP-VER-A, #195).

G08 -- Engineering verification -- is where BADF separates two planes that every other
review tool blurs: the REVIEWER plane (agentic judgment proposes findings) and the VERIFIER
plane (a deterministic runtime observes test facts). Schemas normalize, the canonical gate
evaluates, quality_authority decides. This WP freezes the contract only: SKILL.md + sixteen
references, registered DESIGNED, no scripts, no schema, no lifecycle change, no gate change.
These tests guard that declarative surface and -- above all -- that the freeze REUSES the
vocabularies BADF already has instead of inventing a fifth one.
"""
import hashlib
import importlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-engineering-verification" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-engineering-verification" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"
LIFECYCLE = ROOT / "badf" / "lifecycle.json"

REFS = {
    "g08-contract.md", "target-binding.md", "review-contract.md", "independence.md", "review-lenses.md",
    "finding-contract.md", "integration-test-contract.md", "contract-test-contract.md",
    "composed-tree-contract.md", "runtime-observation.md", "evidence-normalization.md",
    "verification-matrix.md", "non-coverage.md", "g08-g09-boundary.md", "acceptance.md",
    "external-methodology.md",
}
WORKFLOW = "BIND → SEAL → REVIEW → OBSERVE → NORMALIZE → MATRIX → DECLARE NON-COVERAGE → PACKAGE → HANDOFF"
G08_TYPES = ["independent-review", "integration-test", "contract-test", "composed-tree-test"]
# the finding item BADF already has (schemas/architecture-assurance.schema.json) -- reused, not re-invented
ASSURANCE_FINDING_FIELDS = ("finding_id", "kind", "severity", "baseline_ref", "observed_ref", "affected_elements",
                            "evidence_locations", "expected", "observed", "impact", "failure_scenario",
                            "recommendation_direction", "status", "non_coverage")
COUNCIL_VERDICTS = ("APPROVE", "APPROVE_WITH_CONDITIONS", "REJECT", "ABSTAIN", "INSUFFICIENT_EVIDENCE")


def read(name: str) -> str:
    return (REFERENCES / name).read_text(encoding="utf-8")


def gate_module():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        return importlib.import_module("badf_gate")
    finally:
        sys.path.pop(0)


class BadfEngineeringVerificationContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        self.assertTrue(SKILL.is_file())
        self.assertEqual(REFS, {p.name for p in REFERENCES.glob("*.md")})
        self.assertFalse((ROOT / "scripts" / "badf_engineering_verification.py").exists())  # VER-I20: no second gate
        for name in G08_TYPES:  # VER-B (WP-2026-0103): the typed G08 schemas exist from IMPLEMENTED on
            self.assertTrue((ROOT / "schemas" / f"{name}.schema.json").is_file(), name)

    def test_root_states_all_invariants_and_the_workflow(self):
        text = SKILL.read_text(encoding="utf-8")
        for n in range(1, 21):
            self.assertIn(f"VER-I{n:02d}", text)
        self.assertIn(WORKFLOW, text)
        for token in ("AGENT OUTPUT = DRAFT", "NO FINDINGS ≠ CORRECTNESS", "SOURCE_HEAD_GREEN ≠ COMPOSED_VERIFIED",
                      "G08 ≠ G09", "VERIFICATION ≠ APPROVAL", "Reviewer plane", "Verifier plane",
                      "No findings does not mean correctness", "must not swallow G09"):
            self.assertIn(token, text, token)

    def test_reviewer_output_is_findings_not_pass(self):
        review = read("review-contract.md")
        for token in ("NEVER A BARE PASS", "read-only", "defect-first", "merge base", "call sites",
                      "findings", "non_coverage", "completion", "sealed"):
            self.assertIn(token, review, token)
        for verdict in COUNCIL_VERDICTS:  # docs/03's five -- no sixth
            self.assertIn(verdict, review, verdict)
        finding = read("finding-contract.md")
        for field in ASSURANCE_FINDING_FIELDS + ("lens", "reported_by", "also_reported_by", "requirement_refs"):
            self.assertIn(field, finding, field)
        for token in ("SYNTHESIS MAY", "SYNTHESIS MUST NOT", "deduplicate", "lower severity", "erase",
                      "unknown to pass", "accept risk"):
            self.assertIn(token, finding, token)

    def test_vocabularies_are_reconciled_not_invented(self):
        contract = read("contract-test-contract.md")
        rows = {line.split("|")[1].strip().strip("`"): line for line in contract.splitlines()
                if line.startswith("| `") and line.count("|") >= 3}
        for result, outcome in (("CONFORMANT", "PASS"), ("NONCONFORMANT", "FAIL"),
                                ("INDETERMINATE", "BLOCKED"), ("NOT_APPLICABLE", "NOT_APPLICABLE")):
            self.assertIn(result, rows, result)
            self.assertIn(f"`{outcome}`", rows[result], f"{result} must map onto the evidence outcome `{outcome}`")
        self.assertNotIn("`PASS`", rows["INDETERMINATE"])  # VER-I14: INDETERMINATE is never a pass
        self.assertIn("check_non_coverage", contract)
        norm = read("evidence-normalization.md")
        for token in ("PROPOSED", "OBSERVED", "CANONICAL", "evidence.schema.json", "lockfile", "memory labels"):
            self.assertIn(token, norm, token)
        runtime = read("runtime-observation.md")
        for token in ("controller", "service", "never `agent`", "run-ledger-event", "claimed"):
            self.assertIn(token, runtime, token)

    def test_routes_name_only_existing_targets(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        names = {e["name"] for e in registry["skills"]}
        target = read("target-binding.md")
        for token in ("composition-verification", "expected_content_tree", "git-staleness", "CURRENT",
                      "SOURCE_ADVANCED", "STALE_EVIDENCE", "TARGET_MOVED", "source_revision", "target_base_sha"):
            self.assertIn(token, target, token)
        self.assertNotIn("composed_tree_digest", target)  # bind the record BADF has; do not mint a new field
        lenses = read("review-lenses.md")
        for token in ("badf-architecture", "ASSURE", "badf-security-assurance", "named, not built", "non-coverage",
                      "security-kind", "security lens"):
            self.assertIn(token, lenses, token)
        composed = read("composed-tree-contract.md")
        for token in ("badf_compose.py", "SOURCE_HEAD_GREEN ≠ COMPOSED_VERIFIED", "composition-verification", "BLD-I09"):
            self.assertIn(token, composed, token)
        for existing in ("composition-verification", "commit-integrity", "badf-architecture"):
            self.assertIn(existing, names, existing)
        self.assertNotIn("badf-security-assurance", names)
        self.assertIn("named, not built", SKILL.read_text(encoding="utf-8"))

    def test_independence_is_execution_level_and_deviation_carried(self):
        text = read("independence.md")
        for token in ("reviewer_run_id", "author_run_id", "sealed_input_digest", "prior_findings_visible: false",
                      "author_reasoning_visible: false", "cross_pass_communication_before_ballot: false",
                      "single collaborator", "OPEN condition", "A banner is not authorization",
                      "docs/03-authority-and-agent-councils.md", "same person or model run cannot count twice"):
            self.assertIn(token, text, token)

    def test_no_lifecycle_change_and_composes_into_g08(self):
        lifecycle = json.loads(LIFECYCLE.read_text(encoding="utf-8"))
        by = {g["id"]: g for g in lifecycle["gates"]}
        self.assertEqual(["source-change", "build", "unit-test", "documentation"], by["G07"]["required_evidence"])
        self.assertEqual(G08_TYPES, by["G08"]["required_evidence"])
        self.assertEqual(["quality-validation", "security-validation", "performance-test", "resilience-test"],
                         by["G09"]["required_evidence"])
        self.assertEqual("quality_authority", by["G08"]["owner_role"])
        rules = set(gate_module().EVIDENCE_RULES)
        self.assertEqual(set(G08_TYPES), rules & set(G08_TYPES), "VER-B (WP-2026-0103): the additive check_g08_binding rule covers the four G08 types")
        text = read("g08-contract.md")
        for token in G08_TYPES + ["quality_authority", "non-coverage declared", "does not mean"]:
            self.assertIn(token, text, token)
        boundary = read("g08-g09-boundary.md")
        for token in ("G08", "G09", "C2", "security-validation", "does not replace"):
            self.assertIn(token, boundary, token)

    def test_registry_pin_is_validated_and_tool_empty(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in registry["skills"] if e.get("name") == "badf-engineering-verification"]
        self.assertEqual(1, len(entries)); entry = entries[0]
        self.assertEqual("VALIDATED", entry["status"]);  # VER-C (WP-2026-0105) self.assertEqual([], entry["allowed_tools"]); self.assertEqual("C1", entry["risk_class"])
        self.assertEqual("skills/badf-engineering-verification/SKILL.md", entry["source"])
        self.assertEqual("sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest(), entry["digest"])

    def test_skill_points_to_registry_and_external_methodology_is_reference_only(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `", text)
        ext = read("external-methodology.md")
        for token in ("REFERENCE / ADAPT", "Codex", "Magpie", "qa-tester", "REJECT", "release gate as BADF authority",
                      "Playwright-centric QA as universal G08", "AI review verdict as approval", "all-green as coverage",
                      "not independently fetched"):
            self.assertIn(token, ext, token)


if __name__ == "__main__":
    unittest.main()
