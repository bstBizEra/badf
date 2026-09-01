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
REFERENCE_ANCHORS = {
    "g10-uat-contract": ("uat", "release-packet", "operational-readiness", "go-no-go", "UAT-I20"),
    "acceptance-provenance": ("requirement_to_objective", "criterion_to_requirement",
                              "schemas/traceability.schema.json", "UAT-I01", "UAT-I05"),
    "scenario-contract": ("UAT-SCN-", "expected_business_outcome", "actor_role",
                          "criticality", "UAT-I02"),
    "scenario-derivation": ("criticality", "UAT-I01", "UAT-I13", "not derived", "UAT-I12"),
    "execution-adapters": ("browser", "manual", "hybrid", "UAT-I09",
                           "No adapter is registered as a subskill at this rung"),
    "environment-and-data-fidelity": ("test_data_provenance", "permissions_profile",
                                      "ENVIRONMENT_DEFECT", "UAT-I08"),
    "diagnostics-vs-oracle": ("business oracle", "UAT-I10", "UAT-I06", "supplementary"),
    "defect-classification": ("ACCEPTANCE_CRITERION_DEFECT", "IMPLEMENTATION_DEFECT",
                              "NON_REPRODUCIBLE", "UAT-I11", "routes UPSTREAM to PRD/AC authoring"),
    "coverage-matrix": ("not_covered", "Never screens", "UAT-I12", "UAT-I13", "Role coverage"),
    "acceptance-disposition": ("RECOMMEND_ACCEPT", "ACCEPTED_WITH_CONDITIONS", "Layer 2",
                               "UAT-I14", "UAT-I15", "authorized human principal"),
    "reuat-and-staleness": ("SUPERSEDED", "candidate_digest", "UAT-I17", "extend-only"),
    "g09-g10-g11-boundary": ("UAT-I18", "UAT-I19", "release_authority",
                             "badf-production-readiness", "G11"),
    "acceptance": ("WP-UAT-A", "WP-UAT-E", "DESIGNED", "ACTIVE", "pointer, not a second"),
    "external-methodology": ("webapp-uat", "Confirmed absent from this repository",
                             "adapt", "reject"),
}
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
    def test_no_second_gate_and_no_adapter_registered(self):
        """UAT-I20 and the adapter deferral -- the parts of the A-rung floor that OUTLIVE rung A.

        This test previously also asserted `schemas/uat.schema.json` does NOT exist, which was
        correct at rung A and is wrong from WP-UAT-B on: B ships exactly that schema, by A's own
        frozen ladder. A rung-floor assertion that pins the ABSENCE of the next rung's deliverable
        fails the moment the ladder advances -- it reads as a contract but behaves as a freeze.

        What survives every rung is narrower and is what remains here: no COMPETING gate
        (UAT-I20), and no execution adapter registered as a subskill. Those are invariants; "no
        schema yet" was a snapshot. (Caught by the full suite on WP-UAT-B -- the restricted
        compose that ran only the B module was green and could not see it.)
        """
        self.assertTrue(SKILL.is_file(), "SKILL.md must exist")
        for token in ("name: badf-uat", "gate: G10", "owner_role: release_authority",
                      "allowed_tools: []"):
            self.assertIn(token, SKILL_TEXT, token)
        self.assertFalse((ROOT / "scripts" / "badf_uat.py").exists(),
                          "UAT-I20: no competing UAT gate; deterministic semantics stay in badf_gate.py")
        registry = json.loads((ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        names = {e["name"] for e in registry["skills"]}
        # RESIDUAL of the #268 class, kept deliberately and disclosed rather than deleted:
        # adapters ARE scheduled for a later rung (references/execution-adapters.md: "concrete
        # adapters are a later rung"), so this pin WILL fail when that rung lands. It stays
        # because it is the correct contract for every rung up to that one -- but the message
        # tells the next author what to do, which is the difference between a contract and the
        # freezes in #268 instances 1-3.
        for sub in ("browser-uat", "api-uat", "manual-uat", "hybrid-uat"):
            self.assertNotIn(sub, names,
                             f"{sub} is registered. If the adapter rung has landed, that is "
                             f"correct: update THIS assertion and references/acceptance.md's "
                             f"ladder in the same PR. If not, an adapter was registered early.")

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
            self.assertNotIn(sub, names,
                             f"{sub} is registered -- see the note on the sibling assertion; "
                             f"deferred to the adapter rung, not forbidden forever")
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

    def test_registry_pin_is_at_least_implemented_and_tool_empty(self):
        registry = json.loads((ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        entry = next((e for e in registry["skills"] if e["name"] == "badf-uat"), None)
        self.assertIsNotNone(entry, "badf-uat must be registered")
        # The floor: the ladder advances past DESIGNED, so pinning one rung here would fail every
        # time the ladder legitimately moves -- the snapshot-versus-invariant error of #268.
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "SHADOWED", "ACTIVE"))
        # #218: A FLOOR ALONE UNPINS THE STATUS. Every value in that tuple passes, so a silent
        # regression or advance fails nothing. #218 requires exactly ONE exact pin per capability,
        # and this family had ZERO -- measured. The floor above was correct for #268 and CREATED
        # #218: the two issues are in tension, and fixing one naively causes the other.
        #
        # The exact pin lives HERE, and it MOVES with the ladder rather than being relaxed away.
        # WP-UAT-C leaves the rung at IMPLEMENTED (C adds controls; the admission is WP-UAT-E),
        # so the current rung is IMPLEMENTED. A later rung updates this line and the ladder in
        # acceptance.md in the SAME PR -- that co-edit is the point, not an inconvenience.
        self.assertEqual("IMPLEMENTED", entry["status"],
                         "the ONE exact status pin for badf-uat (#218). If a rung advanced the "
                         "registry, update this line and references/acceptance.md together; do "
                         "not relax it to a floor -- a floor alone pins nothing.")
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
        self.assertEqual(14, len(REFS), "the reference set is fourteen; update both if that changes")
        for r in REFS:
            self.assertTrue((REFS_DIR / f"{r}.md").is_file(), f"missing reference {r}.md")

    def test_every_reference_carries_its_own_load_bearing_content(self):
        """Each reference is pinned INDIVIDUALLY, not through the concatenated REFS_TEXT.

        Emptying a file to zero bytes must redden this suite. Without a per-file
        assertion, a token in a sibling satisfies a concatenated check and the gutted
        file passes -- the same defect class as #230 (six of badf-build's fourteen
        references carried no content assertion). Measured before this test existed:
        nine of fourteen here survived being emptied. Found by BADF-QA on PR #241 and
        reproduced independently before fixing.
        """
        self.assertEqual(14, len(REFERENCE_ANCHORS),
                         "every reference needs an anchor; an unanchored file can be emptied silently")
        self.assertEqual(set(REFS), set(REFERENCE_ANCHORS),
                         "the anchor map and the reference list must name the same fourteen files")
        for name, anchors in REFERENCE_ANCHORS.items():
            path = REFS_DIR / f"{name}.md"
            self.assertTrue(path.is_file(), f"missing reference {name}.md")
            text = path.read_text(encoding="utf-8")
            self.assertGreater(len(text), 400, f"{name}.md is too short to carry its contract")
            self.assertGreaterEqual(len(anchors), 2, f"{name}.md needs >= 2 anchors to be pinned")
            for anchor in anchors:
                self.assertIn(anchor, text, f"{name}.md must state {anchor!r}")


if __name__ == "__main__":
    unittest.main()
