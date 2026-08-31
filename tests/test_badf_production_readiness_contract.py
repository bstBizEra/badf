"""badf-production-readiness WP-PRDY-A (BADF-WP-0114 / GOV-0105): the G10 readiness
aggregator contract freeze (DESIGNED).

Pins the frozen contract: the 24 invariants PRDY-I01..I24 by id, the nine-stage workflow,
the three fundamental rules, that this skill owns exactly two of G10's four evidence types
(release-packet + operational-readiness -- never uat, never go-no-go), that the readiness
vocabulary is bounded and structurally distinct from the authorization vocabulary, that
rollback and migration are reconciled in one reference rather than duplicated, that no
lifecycle/gate/schema change ships at this rung, and the registry DESIGNED entry
digest-bound to SKILL.md. Contract-only: no scripts/badf_production_readiness.py, no typed
schema, no lifecycle change (PRDY-I24).

Every reference is pinned INDIVIDUALLY (>=2 anchors, >400 bytes). Written that way from the
start rather than retrofitted: on PR #241 nine of badf-uat's fourteen references could be
emptied to zero bytes with the suite green, because they were only reached through a
concatenated blob where a sibling's token satisfied the assertion. Same class as #230.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

ROOT = gate.ROOT
SKILL = ROOT / "skills" / "badf-production-readiness" / "SKILL.md"
REFS_DIR = ROOT / "skills" / "badf-production-readiness" / "references"

REFERENCE_ANCHORS = {
    "g10-contract": ("release-packet", "operational-readiness", "go-no-go", "badf-uat",
                     "READY_FOR_AUTHORITY"),
    "readiness-dimensions": ("READY_WITH_CONDITIONS", "INDETERMINATE", "NOT_APPLICABLE", "STALE",
                             "Artifact/release identity", "PRDY-I07"),
    "candidate-binding": ("composed_tree_digest", "sbom_digest", "migration_digest",
                          "PRDY-I02", "PRDY-I23"),
    "release-delta": ("queue schema", "No diff", "PRDY-I03", "currently released baseline"),
    "evidence-aggregation": ("MUST NOT", "MAY", "PRDY-I01", "PRDY-I04", "re-run G09"),
    "evidence-freshness": ("PRDY-I05", "No credit, not reduced credit", "baseline drift",
                           "policy drift"),
    "contradiction-resolution": ("PRDY-I06", "INDETERMINATE", "NOT_READY",
                                 "favorable claim", "Both sides are recorded"),
    "security-readiness": ("PRDY-I08", "PRDY-I09", "residual", "SEC-I13", "security_authority"),
    "recovery-readiness": ("PRDY-I11", "PRDY-I12", "RPO", "RTO", "backup artifact"),
    "rollback-migration-readiness": ("DEFINED", "VALIDATED", "REHEARSED", "PRDY-I13", "PRDY-I14",
                                     "compatibility matrix"),
    "observability-readiness": ("PRDY-I15", "alert route", "threshold", "response",
                                "Thresholds are predeclared"),
    "operations-support-readiness": ("PRDY-I16", "PRDY-I17", "on-call", "escalation",
                                     "service owner"),
    "release-artifact-identity": ("PRDY-I18", "promotion record", "rebuild", "sbom_digest"),
    "authority-boundary": ("PRDY-I19", "PRDY-I20", "PRDY-I21", "PRDY-I22", "derived predicate",
                           "VER-I18", "SEC-I13"),
    "acceptance": ("WP-PRDY-A", "WP-PRDY-E", "DESIGNED", "ACTIVE", "pointer, not a second"),
    "external-methodology": ("final-release-review", "ADAPT", "REJECT", "GREEN LIGHT TO SHIP",
                             "not independently fetched"),
}
REFS = tuple(REFERENCE_ANCHORS)


def _statements(text):
    """The unit a negation actually governs, which is neither the line nor the paragraph.

    Two failure modes, both hit while writing this test:

    - Physical lines are TOO NARROW for prose. Markdown wraps, so `(no` can sit on the
      line above the term it negates -- reported as a bare assertion (acceptance.md did).
    - Paragraph blocks are TOO WIDE for fenced code. A MUST NOT list is many independent
      statements; joining them lets a SIBLING line's `MUST NOT` vouch for a line that
      asserts the opposite. Verified: with block-joining, rewriting one list entry to
      "This skill emits PRODUCTION_AUTHORIZED ..." did NOT redden the suite -- the same
      a-sibling-satisfies-the-assertion defect as the concatenated reference blob.

    So: inside a fenced code block, one statement per line. Outside, one per paragraph.
    """
    out, para, in_fence = [], [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if para:
                out.append(" ".join(para))
                para = []
            in_fence = not in_fence
            continue
        if in_fence:
            # Inside a fence a statement is a FLUSH line plus its indented continuations.
            # A `MUST NOT` list is flush-per-entry (independent statements); a titled rule
            # block indents its body under the title (one statement). Treating every fenced
            # line as its own statement split the second kind; joining the whole fence
            # merged the first.
            if not line.strip():
                continue
            if line[:1].isspace() and out:
                out[-1] = out[-1] + " " + line.strip()
            else:
                out.append(line)
        elif line.strip():
            para.append(line)
        elif para:
            out.append(" ".join(para))
            para = []
    if para:
        out.append(" ".join(para))
    return out

WORKFLOW_STAGES = (
    "BIND CANDIDATE", "RESOLVE UPSTREAM EVIDENCE", "COMPUTE RELEASE DELTA", "CHECK FRESHNESS",
    "CHECK CONTRADICTIONS", "EVALUATE DIMENSIONS", "DECLARE NON-COVERAGE", "PACKAGE DOSSIER",
    "HANDOFF",
)
READINESS_VOCAB = ("READY", "READY_WITH_CONDITIONS", "NOT_READY", "BLOCKED", "INDETERMINATE",
                   "NOT_APPLICABLE", "STALE")
AUTHORIZATION_VOCAB = ("PRODUCTION_AUTHORIZED", "PRODUCTION_AUTHORIZED_WITH_CONDITIONS",
                       "PRODUCTION_NOT_AUTHORIZED")
SKILL_TEXT = SKILL.read_text(encoding="utf-8") if SKILL.is_file() else ""


class ProductionReadinessContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        """No runtime, no typed schema, no gate code ships at this rung (PRDY-I24)."""
        self.assertTrue(SKILL.is_file(), "SKILL.md must exist")
        for token in ("name: badf-production-readiness", "gate: G10",
                      "owner_role: release_authority", "status: DESIGNED", "allowed_tools: []"):
            self.assertIn(token, SKILL_TEXT, token)
        self.assertFalse((ROOT / "scripts" / "badf_production_readiness.py").exists(),
                         "PRDY-I24: no competing readiness gate script at the DESIGNED rung")
        for schema in ("release-packet.schema.json", "operational-readiness.schema.json",
                       "readiness-dossier.schema.json"):
            self.assertFalse((ROOT / "schemas" / schema).exists(),
                             f"no typed {schema} at this rung")
        self.assertEqual(16, len(REFS), "exactly sixteen references at this rung")

    def test_root_states_all_invariants_and_the_workflow(self):
        for i in range(1, 25):
            self.assertIn(f"PRDY-I{i:02d}", SKILL_TEXT, f"PRDY-I{i:02d} must be named in SKILL.md")
        for stage in WORKFLOW_STAGES:
            self.assertIn(stage, SKILL_TEXT, f"workflow stage {stage}")
        for rule in ("AGGREGATION NOT RE-EXECUTION", "READINESS ≠ AUTHORIZATION",
                     "PRODUCTION_AUTHORIZED IS DERIVED, NEVER WRITTEN"):
            self.assertIn(rule, SKILL_TEXT, f"fundamental rule {rule!r}")

    def test_ownership_is_two_of_four_g10_types(self):
        contract = (REFS_DIR / "g10-contract.md").read_text(encoding="utf-8")
        for owned in ("release-packet", "operational-readiness"):
            self.assertIn(owned, contract, f"must claim {owned}")
        self.assertIn("badf-uat", contract, "uat must be named as badf-uat's, not this skill's")
        self.assertIn("go-no-go", contract)
        self.assertIn("release_authority", contract)
        self.assertIn("human-reserved", contract)

    def test_readiness_vocabulary_is_bounded_and_distinct_from_authorization(self):
        """The readiness vocabulary is this skill's output; the authorization vocabulary is not.

        The first draft of this test asserted the authorization terms appear ONLY in
        authority-boundary.md, and it went red on `MUST NOT issue ... PRODUCTION_AUTHORIZED`
        in evidence-aggregation.md -- a PROHIBITION, which is the opposite of the danger.
        A rule that forbids naming the thing you must never emit would push the prohibitions
        out of the documents that need them. So the property is stated precisely instead:

          - the two COMPOUND predicates are confined to authority-boundary.md; they have no
            reason to exist anywhere else except as an output vocabulary being assembled;
          - the bare predicate may appear elsewhere ONLY on a line that negates it.
        """
        dims = (REFS_DIR / "readiness-dimensions.md").read_text(encoding="utf-8")
        for term in READINESS_VOCAB:
            self.assertIn(term, dims, f"readiness vocabulary term {term}")
        self.assertIn("READY_FOR_AUTHORITY", SKILL_TEXT, "the ceiling must be named in the root")

        negations = ("must not", "never", "cannot", "can never", "no ", "not ")
        compound = ("PRODUCTION_AUTHORIZED_WITH_CONDITIONS", "PRODUCTION_NOT_AUTHORIZED")
        surfaces = {f"{n}.md": (REFS_DIR / f"{n}.md").read_text(encoding="utf-8") for n in REFS}
        surfaces["SKILL.md"] = SKILL_TEXT

        for fname, text in surfaces.items():
            if fname == "authority-boundary.md":
                continue
            for term in compound:
                self.assertNotIn(term, text,
                                 f"{term} belongs only in authority-boundary.md, found in {fname}")
            # Physical lines are a proxy for statements: markdown wraps prose, so a negation
            # can sit on the previous line from the term it negates (it did, in acceptance.md).
            # Collapse each block of consecutive non-blank lines into one logical statement.
            for i, block in enumerate(_statements(text), 1):
                if "PRODUCTION_AUTHORIZED" not in block:
                    continue
                low = block.lower()
                self.assertTrue(
                    any(n in low for n in negations),
                    f"{fname} block {i} names PRODUCTION_AUTHORIZED outside a prohibition: "
                    f"{block.strip()[:160]!r}")

    def test_recovery_and_migration_are_reconciled_not_duplicated(self):
        combined = (REFS_DIR / "rollback-migration-readiness.md").read_text(encoding="utf-8")
        for token in ("DEFINED", "VALIDATED", "REHEARSED", "compatibility matrix",
                      "PRDY-I13", "PRDY-I14"):
            self.assertIn(token, combined, token)
        self.assertFalse((REFS_DIR / "migration-readiness.md").exists(),
                         "migration is reconciled INTO rollback-migration-readiness.md, not split out")
        self.assertFalse((REFS_DIR / "rollback-readiness.md").exists(),
                         "rollback is reconciled INTO rollback-migration-readiness.md, not split out")

    def test_no_lifecycle_change_and_owns_only_its_two_types(self):
        lifecycle = json.loads((ROOT / "badf" / "lifecycle.json").read_text(encoding="utf-8"))
        gates = lifecycle.get("gates", [])
        self.assertEqual(15, len(gates), "no gate added or removed")
        by_id = {g["id"]: g for g in gates}
        self.assertEqual(["uat", "release-packet", "operational-readiness", "go-no-go"],
                         by_id["G10"]["required_evidence"], "G10 evidence list unchanged")
        for gid in ("G09", "G11", "G12"):
            self.assertIn(gid, by_id, f"{gid} must exist")
        for g10_type in ("release-packet", "operational-readiness", "uat", "go-no-go"):
            self.assertNotIn(g10_type, gate.EVIDENCE_RULES,
                             f"EVIDENCE_RULES must carry no G10 type at this rung ({g10_type})")

    def test_registry_pin_is_designed_and_tool_empty(self):
        registry = json.loads((ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        entry = next((e for e in registry["skills"]
                      if e["name"] == "badf-production-readiness"), None)
        self.assertIsNotNone(entry, "badf-production-readiness must be registered")
        self.assertEqual("DESIGNED", entry["status"])
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual("C1", entry["risk_class"])
        expected = "sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest()
        self.assertEqual(expected, entry["digest"], "registry digest must equal sha256(SKILL.md)")

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        self.assertIn("badf/skill-registry.json", SKILL_TEXT)
        ladder = (REFS_DIR / "acceptance.md").read_text(encoding="utf-8")
        self.assertIn("pointer, not a second", ladder)
        for rung in ("WP-PRDY-A", "WP-PRDY-B", "WP-PRDY-C", "WP-PRDY-D", "WP-PRDY-E"):
            self.assertIn(rung, ladder, rung)

    def test_external_methodology_is_reference_adapt_only(self):
        ext = (REFS_DIR / "external-methodology.md").read_text(encoding="utf-8")
        self.assertIn("final-release-review", ext)
        for verdict in ("ADAPT", "EXTEND", "REJECT"):
            self.assertIn(verdict, ext, verdict)
        self.assertIn("GREEN LIGHT TO SHIP", ext,
                      "the rejected local authority must be named, not paraphrased")
        self.assertIn("not independently fetched", ext,
                      "the second-hand characterization must be declared, not implied")

    def test_authority_boundary_cites_precedent_and_forbids_self_authorization(self):
        boundary = (REFS_DIR / "authority-boundary.md").read_text(encoding="utf-8")
        for token in ("PRDY-I19", "PRDY-I20", "PRDY-I21", "PRDY-I22",
                      "SEC-I13", "VER-I18", "UAT-I14", "derived predicate"):
            self.assertIn(token, boundary, token)
        self.assertIn("never the capability that decides progression", boundary,
                      "the generalization across all four precedents must be stated")

    def test_every_reference_carries_its_own_load_bearing_content(self):
        """Each reference is pinned INDIVIDUALLY. Emptying one to zero bytes must redden
        this suite -- see the module docstring for why this is written up front."""
        self.assertEqual(16, len(REFERENCE_ANCHORS),
                         "every reference needs an anchor; an unanchored file can be emptied silently")
        self.assertTrue(REFS_DIR.is_dir(), "references/ dir must exist")
        for name, anchors in REFERENCE_ANCHORS.items():
            path = REFS_DIR / f"{name}.md"
            self.assertTrue(path.is_file(), f"missing reference {name}.md")
            text = path.read_text(encoding="utf-8")
            self.assertGreater(len(text), 400, f"{name}.md is too short to carry its contract")
            self.assertGreaterEqual(len(anchors), 2, f"{name}.md needs >= 2 anchors to be pinned")
            for anchor in anchors:
                self.assertIn(anchor, text, f"{name}.md must state {anchor!r}")

    def test_no_reference_beyond_the_sixteen(self):
        actual = {p.stem for p in REFS_DIR.glob("*.md")}
        self.assertEqual(set(REFS), actual,
                         "the reference set is exactly the sixteen named in the plan")


if __name__ == "__main__":
    unittest.main()
