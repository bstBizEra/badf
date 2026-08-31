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
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-build" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-build" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"
LIFECYCLE = ROOT / "badf" / "lifecycle.json"

SURFACE = sorted((ROOT / "skills" / "badf-build").rglob("*.md"))
# The idiom is tests/test_badf_schema_drift.py:31 -- a module-level non-emptiness assertion whose
# comment names this failure mode. An empty SURFACE would make the family-name guard below pass in
# 0.000s, so absence of the surface would be indistinguishable from a clean surface (GOV-0099 / #229).
# Asserted at import: it fires once per module and cannot be forgotten by whoever adds the next test.
assert SURFACE, "an empty badf-build surface would make the family-name guard vacuous"

REFS = {
    "g07-contract.md", "preflight.md", "execution-contract.md", "tdd-contract.md", "test-seams.md",
    "delegation.md", "scope-containment.md", "retry-and-budget.md", "stop-conditions.md",
    "self-review.md", "evidence-packaging.md", "handoff-to-g08.md", "acceptance.md",
    "external-methodology.md",
}
# #230: six of the fourteen references carried NO content assertion -- `acceptance`,
# `evidence-packaging`, `handoff-to-g08`, `preflight`, `retry-and-budget` and
# `stop-conditions` could each be emptied to zero bytes with this module green. REFS above
# pins FILENAMES; being named is a proxy for being content-asserted, and the proxy was
# satisfied while nothing checked the text.
#
# Anchors pin STRUCTURE, not values, and the precondition matters: a structure-only anchor
# detects deletion, never weakening ("a threshold is stated" is satisfied by 999999). It is
# correct HERE only because none of these files owns a threshold -- `stop-conditions` lists
# conditions, `preflight` asks "budget remaining?" with no figure, and `retry-and-budget`'s
# 1/2/3 is a worked illustration whose own text defers to the Work Package's
# `execution_budget`, guarded in code at badf_gate.py IMP-C3/IMP-I11. Pin the value where the
# file is the source of truth; pin the structure where the value is owned and guarded
# elsewhere. (BADF-QA's test, adopted with its precondition.)
REFERENCE_ANCHORS = {
    "acceptance.md": ("DESIGNED", "IMPLEMENTED", "VALIDATED", "SHADOWED",
                      "badf/skill-registry.json", "pointer, not a second"),
    "evidence-packaging.md": ("source-change", "unit-test", "documentation",
                              "BLD-I16", "BLD-I18", "never a second producer"),
    "handoff-to-g08.md": ("BLD-I17", "badf-git", "G08 independent verification"),
    "preflight.md": ("BLD-I01", "expected surfaces", "stop conditions",
                     "No valid Work Package"),
    "retry-and-budget.md": ("BLD-I11", "BLD-I12", "execution_budget", "ROOT_CAUSE_MODE",
                            "retries must add information"),
    "stop-conditions.md": ("BLD-I13", "stop_conditions", "authority conflict",
                           "credential exposure", "budget exhaustion"),
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

    def test_the_six_unpinned_references_assert_their_own_content(self):
        """#230: each of the six carries load-bearing tokens, so gutting it reddens this module.

        Positive control observed red on all six before this test was written -- and on a tree
        verified clean with `git status`, because an earlier probe had been killed mid-iteration
        and left one reference already gutted, which silently contaminated its own baseline.

        NOT claimed: that this closes the class for badf-build. The eight already-asserted
        references were spot-checked, not exhaustively re-probed, and an anchor pins the tokens
        it names and nothing else.
        """
        self.assertEqual(6, len(REFERENCE_ANCHORS), "the six #230 named; a seventh needs its own probe")
        # `<=`, not `<`: a PROPER subset would fail the day someone anchors all fourteen --
        # a guard that punishes the improvement it exists to encourage. Latent today behind
        # the exact-count pin above; correct whenever that pin is relaxed. (BADF-QA, #255.)
        self.assertTrue(set(REFERENCE_ANCHORS) <= REFS,
                        "every anchored name must be a real reference in REFS")
        for name, anchors in REFERENCE_ANCHORS.items():
            text = read(name)
            self.assertGreater(len(text), 400, f"{name} is too short to carry its contract")
            self.assertGreaterEqual(len(anchors), 3, f"{name} needs >= 3 anchors")
            for tok in anchors:
                self.assertIn(tok, text, f"{name}: {tok}")

    def test_registry_pin_is_active_and_tool_empty(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in registry["skills"] if e.get("name") == "badf-build"]
        self.assertEqual(1, len(entries)); entry = entries[0]
        self.assertEqual("ACTIVE", entry["status"]); self.assertEqual([], entry["allowed_tools"]); self.assertEqual("C1", entry["risk_class"])  # BLD-B
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

    # WP-2026-0109 / #219 -- badf-build's Boundary block named `badf-verification (G08)`, absent from the registry.
    def test_every_family_named_in_the_surface_resolves_in_the_registry(self):
        # Non-family badf-* tokens. Keep this set minimal: every entry is a hole in the guard.
        #   "badf-sa" -- slug of the sibling BST-SA organism repo, never a skill family. Defensive
        #                only: it does not currently appear anywhere under skills/badf-build/.
        NON_FAMILY = {"badf-sa"}
        known = {e.get("name") for e in json.loads(REGISTRY.read_text(encoding="utf-8"))["skills"]}
        found = {}
        # SURFACE is non-empty by the module-level assertion; these catch the PARTIAL cases it cannot:
        # the router gone, a reference deleted, or a scan that read files but learned nothing.
        self.assertTrue(SKILL.is_file(), "the surface's router is absent; the scan below would conclude nothing, quietly")
        self.assertEqual(REFS, {p.name for p in REFERENCES.glob("*.md")}, "the frozen reference set is not what the scan read")
        self.assertGreaterEqual(len(SURFACE), 1 + len(REFS), f"scanned only {len(SURFACE)} files under skills/badf-build/")
        for path in SURFACE:
            for raw in re.findall(r"badf-[a-z0-9-]+", path.read_text(encoding="utf-8")):
                # "badf-git," / "badf-build." never enter the match (the class excludes punctuation);
                # a trailing hyphen can, and a path "badf-build/references/x.md" already stops at "/".
                token = raw.rstrip("-")
                if token in NON_FAMILY:
                    continue
                found.setdefault(token, set()).add(str(path.relative_to(ROOT)))
        self.assertIn("badf-build", found, "the scan did not even find the family naming itself; it read nothing meaningful")
        unresolved = {t: sorted(f) for t, f in found.items() if t not in known}
        self.assertEqual({}, unresolved, "badf-* families named in the badf-build surface but absent from "
                         + f"{REGISTRY.relative_to(ROOT)}: "
                         + "; ".join(f"{t} named in {', '.join(files)}" for t, files in sorted(unresolved.items())))


if __name__ == "__main__":
    unittest.main()
