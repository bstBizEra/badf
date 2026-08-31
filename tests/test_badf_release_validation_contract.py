"""badf-release-validation WP-VAL-A (BADF-WP-0107 / GOV-0090): the G09 independent
pre-release validation router contract freeze (DESIGNED).

This pins the frozen contract: the 20 invariants VAL-I01..I20 by id, the obligation-router
workflow, that it COMPOSES the four G09 evidence types the lifecycle already names (no fifth
type, no gate code / schema / lifecycle change at this rung), the adapt-not-authority
disposition of the three external sources, the G08!=G09!=G10!=G12 boundaries, the 17
references, and the registry DESIGNED entry digest-bound to SKILL.md. Contract-only: this
rung adds no scripts/badf_release_validation.py, no schema, no lifecycle change (VAL-I20).
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

ROOT = gate.ROOT
SKILL = ROOT / "skills" / "badf-release-validation" / "SKILL.md"
REFS_DIR = ROOT / "skills" / "badf-release-validation" / "references"
REFS = (
    "g09-contract", "candidate-binding", "routing", "validation-obligations",
    "class-independence", "quality-validation", "security-validation", "performance-test",
    "resilience-test", "runtime-evidence", "thresholds-and-oracles", "environment-fidelity",
    "findings-and-disposition", "noncoverage", "g08-g09-g10-boundary", "acceptance",
    "external-methodology",
)
G09_QUARTET = ("quality-validation", "security-validation", "performance-test", "resilience-test")
SKILL_TEXT = SKILL.read_text(encoding="utf-8") if SKILL.is_file() else ""


class SkillContractTests(unittest.TestCase):
    def test_skill_exists_and_frontmatter(self):
        self.assertTrue(SKILL.is_file(), "SKILL.md must exist")
        for token in ("name: badf-release-validation", "gate: G09",
                      "owner_role: quality_authority", "status: IMPLEMENTED", "allowed_tools: []"):
            self.assertIn(token, SKILL_TEXT, token)

    def test_all_twenty_invariants_present_by_id(self):
        for i in range(1, 21):
            self.assertIn(f"VAL-I{i:02d}", SKILL_TEXT, f"VAL-I{i:02d} must be named in SKILL.md")

    def test_obligation_router_workflow(self):
        for phase in ("BIND_CANDIDATE", "ROUTE", "CLASS_VALIDATE", "OBSERVE", "THRESHOLD",
                      "NORMALIZE", "DECLARE_NONCOVERAGE", "COMPOSE", "HANDOFF"):
            self.assertIn(phase, SKILL_TEXT, f"workflow phase {phase}")
        self.assertIn("obligation router", SKILL_TEXT.lower())

    def test_composes_the_existing_g09_quartet_and_adds_no_fifth_type(self):
        for t in G09_QUARTET:
            self.assertIn(t, SKILL_TEXT, f"must compose the existing G09 type {t}")
        # no fifth lifecycle evidence type, no gate code, no schema at this rung (VAL-I20)
        self.assertFalse((ROOT / "scripts" / "badf_release_validation.py").exists(),
                         "VAL-I20: no competing validator script at the DESIGNED rung")
        self.assertFalse((ROOT / "schemas" / "release-validation.schema.json").exists(),
                         "no fifth 'release-validation' schema/type")

    def test_g08_g09_g10_g12_boundaries_frozen(self):
        for token in ("VAL-I17", "VAL-I18", "VAL-I19", "release_authority", "quality_authority",
                      "go-no-go", "operational readiness"):
            self.assertIn(token, SKILL_TEXT, token)
        # it must not claim release authority
        self.assertIn("does not", SKILL_TEXT.lower())

    def test_external_sources_are_adapt_not_authority(self):
        low = SKILL_TEXT.lower()
        for src in ("qa-skills", "k6", "owasp"):
            self.assertIn(src, low, f"external source {src} must be named")
        self.assertIn("adapt", low)
        self.assertIn("never authority", low)

    def test_all_seventeen_references_exist(self):
        self.assertTrue(REFS_DIR.is_dir(), "references/ dir must exist")
        for r in REFS:
            self.assertTrue((REFS_DIR / f"{r}.md").is_file(), f"missing reference {r}.md")

    def test_registry_designed_and_digest_bound_to_skill(self):
        registry = json.loads((ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        entry = next((e for e in registry["skills"] if e["name"] == "badf-release-validation"), None)
        self.assertIsNotNone(entry, "badf-release-validation must be registered")
        # WP-VAL-B (WP-2026-0113): the typed G09 contracts land at IMPLEMENTED.
        # The pin advances with the rung rather than loosening -- each advance is
        # then visible in its own diff, the VER-E pattern.
        self.assertEqual(entry["status"], "IMPLEMENTED")
        expected = "sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest()
        self.assertEqual(entry["digest"], expected, "registry digest must equal sha256(SKILL.md)")


if __name__ == "__main__":
    unittest.main()
