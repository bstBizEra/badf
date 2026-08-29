"""badf-requirements authoring skill (BADF-WP-0063; salvage of the superseded PR #47).

badf-requirements decomposes an approved PRD baseline into the four canonical G02
artifacts and validates them with `badf_gate.py dossier` -- it has no validator of
its own. PR #47's obsolete design (a standalone scripts/badf_requirements.py + a
custom RTM schema that duplicated the gate) is explicitly NOT salvaged: the guards
below lock that architecture out. The skill authors artifacts; the canonical gate
verifies them; a human authority decides G02. It lands IMPLEMENTED.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

SKILL_DIR = gate.ROOT / "skills/badf-requirements"
SKILL = SKILL_DIR / "SKILL.md"


class SkillExistsTests(unittest.TestCase):
    def test_the_skill_and_its_two_references_exist(self):
        self.assertTrue(SKILL.is_file(), "skills/badf-requirements/SKILL.md is missing")
        for ref in ("requirements-decomposition.md", "methodology-provenance.md"):
            self.assertTrue((SKILL_DIR / "references" / ref).is_file(), f"references/{ref} is missing")

    def test_registered_implemented_with_a_real_digest(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-requirements")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["source"], "skills/badf-requirements/SKILL.md")
        want = "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest()
        self.assertEqual(entry["digest"], want)


class AuthorityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_declares_no_gate_authority(self):
        self.assertIn("REQ-I01", self.text)
        self.assertRegex(self.text, r"no gate authority|never (emit|approve).*G02|MUST NOT")

    def test_validates_through_the_canonical_gate_not_a_validator_of_its_own(self):
        self.assertIn("badf_gate.py dossier", self.text)
        self.assertNotIn("badf_requirements.py", self.text)

    def test_names_the_four_canonical_g02_artifacts(self):
        for art in ("requirements", "nfr", "traceability", "definition-of-ready"):
            self.assertIn(art, self.text)


class AntiDuplicationGuards(unittest.TestCase):
    """PR #47's obsolete implementation must never be salvaged with the authoring layer."""

    def test_no_standalone_requirements_validator(self):
        self.assertFalse((gate.ROOT / "scripts/badf_requirements.py").exists(),
                         "a standalone requirements validator duplicates the canonical G02 gate")

    def test_no_custom_rtm_schema_or_template(self):
        self.assertFalse((gate.ROOT / "schemas/requirements-rtm.schema.json").exists(),
                         "a custom RTM schema duplicates the canonical G02 artifacts")
        self.assertFalse((gate.ROOT / "templates/requirements-rtm.json").exists(),
                         "a custom RTM template duplicates the canonical G02 artifacts")

    def test_the_gate_remains_the_sole_g02_authority(self):
        # no second module claims to render a G02 verdict.
        self.assertEqual(sorted(p.name for p in (gate.ROOT / "scripts").glob("*requirements*")), [],
                         "a competing requirements module exists beside the gate")


if __name__ == "__main__":
    unittest.main()
