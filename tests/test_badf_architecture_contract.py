"""Architecture capability contract freeze (BADF-WP-0043, Issue #74).

badf-architecture exists at DESIGNED and nothing runs. What must not drift is
the MEANING: the two modes and the canonical-model-vs-diagram distinction are
documented; the twelve invariants ARCH-I01..ARCH-I12 are stated verbatim; the
ADR/BADF-DEC separation and the C4-views-are-projections rule are stated; the
registry entry is DESIGNED with a real digest; G04 is mapped but UNCHANGED
(no authority change); and nothing is IMPLEMENTED yet -- no architecture schema,
no check_* rule, no validator script beside the gate (ARCH-I11).
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

SKILL = gate.ROOT / "skills/badf-architecture/SKILL.md"
REF = gate.ROOT / "skills/badf-architecture/references"
REFERENCES = ["design-mode.md", "assure-mode.md", "architecture-model.md", "c4-contract.md",
              "adr-contract.md", "architecture-fitness.md", "g04-contract.md",
              "external-methodology.md", "acceptance.md"]
INVARIANTS = [f"ARCH-I{n:02d}" for n in range(1, 13)]
G04_EVIDENCE = ["architecture", "adr", "data-model", "api-contract", "operability-design"]


class StructureTests(unittest.TestCase):

    def test_all_references_exist(self):
        for r in REFERENCES:
            self.assertTrue((REF / r).is_file(), f"missing reference {r}")

    def test_root_skill_names_every_reference(self):
        text = SKILL.read_text(encoding="utf-8")
        for r in REFERENCES:
            self.assertIn(r, text, f"SKILL.md does not name {r}")

    def test_skill_states_its_authority_boundary(self):
        # The authority boundary is invariant across status (DESIGNED -> IMPLEMENTED -> ...).
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("does **not** approve G04", text)
        self.assertIn("does **not** advance lifecycle", text)

    def test_both_modes_and_the_model_vs_diagram_distinction_are_documented(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("DESIGN", text)
        self.assertIn("ASSURE", text)
        model = (REF / "architecture-model.md").read_text(encoding="utf-8")
        self.assertIn("never introduces an architectural claim absent from it", model)


class InvariantTests(unittest.TestCase):

    def test_twelve_invariants_stated_verbatim(self):
        text = (REF / "acceptance.md").read_text(encoding="utf-8")
        for inv in INVARIANTS:
            self.assertIn(inv, text, f"{inv} not stated")

    def test_c4_views_are_projections(self):
        text = (REF / "c4-contract.md").read_text(encoding="utf-8")
        self.assertIn("ARCH-I02", text)
        self.assertIn("absent from the baseline is refused", text)

    def test_adr_is_not_a_governance_decision(self):
        text = (REF / "adr-contract.md").read_text(encoding="utf-8")
        self.assertIn("ADR-NNNN", text)
        self.assertIn("BADF-DEC-NNNN", text)
        self.assertIn("ARCH-I10", text)


class RegistryAndAuthorityTests(unittest.TestCase):

    def test_registry_entry_is_validated_with_a_real_digest(self):
        # WP-ARCH-C advanced the capability IMPLEMENTED -> VALIDATED (the ASSURE substrate is deterministic; controls 13-18 pass with mutation).
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-architecture")
        self.assertEqual(entry["status"], "VALIDATED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())

    def test_g04_is_mapped_but_unchanged(self):
        g04text = (REF / "g04-contract.md").read_text(encoding="utf-8")
        for t in G04_EVIDENCE:
            self.assertIn(t, g04text, f"g04-contract.md does not map {t}")
        lifecycle = json.loads((gate.ROOT / "badf/lifecycle.json").read_text())
        g04 = next(g for g in lifecycle["gates"] if g["id"] == "G04")
        self.assertEqual(g04["required_evidence"], G04_EVIDENCE, "the freeze must not change G04's evidence")
        self.assertEqual(g04["owner_role"], "architecture_authority", "the freeze must not change G04 authority")


class ImplementationStatusTests(unittest.TestCase):

    def test_no_architecture_validator_beside_the_gate(self):
        # ARCH-I11 holds at every status: the semantics live in the canonical gate, not a second validator.
        self.assertEqual(sorted(p.name for p in (gate.ROOT / "scripts").glob("*architecture*")), [],
                         "a competing architecture validator exists (ARCH-I11)")

    def test_g04_design_evidence_types_are_enforced(self):
        # WP-ARCH-B: the five G04 DESIGN evidence types now open their artifacts in the gate.
        for t in G04_EVIDENCE:
            self.assertIn(t, gate.EVIDENCE_RULES, f"{t} is a G04 type but has no per-type rule")

    def test_g04_design_and_assurance_schemas_exist(self):
        for name in G04_EVIDENCE:
            self.assertTrue((gate.ROOT / "schemas" / f"{name}.schema.json").is_file(),
                            f"schemas/{name}.schema.json is missing")
        # the ASSURE substrate (WP-ARCH-C) is now built
        self.assertTrue((gate.ROOT / "schemas" / "architecture-assurance.schema.json").is_file(),
                        "the architecture-assurance schema is missing (WP-ARCH-C)")
        self.assertTrue(hasattr(gate, "validate_architecture_assurance"),
                        "the assure validator is missing")


if __name__ == "__main__":
    unittest.main()
