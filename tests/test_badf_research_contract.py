"""Research capability contract freeze (BADF-WP-0031, Issue #50).

badf-research exists at DESIGNED and nothing runs. What must not drift is the
MEANING: the documented taxonomy (types, depths, states, dispositions, claim
classes and statuses, source types, confidence levels) equals the schema's
enums; the example record satisfies the schema; the schema itself fixes
implementation_authority to false; the five invariants are stated verbatim;
the registry entry is DESIGNED with a real digest; and no research validator
script exists beside the gate.
"""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

REF = gate.ROOT / "skills/badf-research/references"
SCHEMA = gate.ROOT / "schemas/research-record.schema.json"
EXAMPLE = gate.ROOT / "examples/research-record.json"
INVARIANTS = ["RSR-I01", "RSR-I02", "RSR-I03", "RSR-I04", "RSR-I05"]


def schema():
    return json.loads(SCHEMA.read_text())


def codes_in_table(doc: Path, first_col_pattern: str) -> set:
    """The set of first-column code cells of every table row matching a pattern."""
    out = set()
    for line in doc.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| `([^`]+)` \|", line)
        if m and re.fullmatch(first_col_pattern, m.group(1)):
            out.add(m.group(1))
    return out


def enum(path: str) -> set:
    node = schema()
    for key in path.split("."):
        node = node["properties"][key] if "properties" in node else node["items"]["properties"][key]
    return set(node["enum"])


class TaxonomyMatchesSchemaTests(unittest.TestCase):

    def test_research_types_documented_equal_schema(self):
        self.assertEqual(codes_in_table(REF / "research-types.md", r"R[0-9]{2}"), enum("type"))

    def test_depths_documented_equal_schema(self):
        self.assertEqual(codes_in_table(REF / "research-types.md", r"D[0-5]"), enum("depth"))

    def test_states_documented_equal_schema(self):
        self.assertEqual(codes_in_table(REF / "lifecycle.md", r"[A-Z_]+"), enum("state") | enum("disposition.state"))

    def test_dispositions_documented_equal_schema(self):
        docs = codes_in_table(REF / "lifecycle.md", r"[A-Z_]+")
        self.assertLessEqual(enum("disposition.state"), docs)
        self.assertIn("RESEARCH_SUFFICIENT", enum("disposition.state"))

    def test_claim_vocabulary_documented_equal_schema(self):
        doc = REF / "evidence-contract.md"
        s = schema()["properties"]["claims"]["items"]["properties"]
        self.assertEqual(codes_in_table(doc, r"(OBSERVED|REPORTED|INFERRED|HYPOTHESIS|DECIDED)"), set(s["classification"]["enum"]))
        self.assertEqual(codes_in_table(doc, r"(VERIFIED|PARTIALLY_VERIFIED|DISPUTED|UNVERIFIED|FALSIFIED)"), set(s["status"]["enum"]))
        self.assertEqual(codes_in_table(doc, r"(VERY_LOW|LOW|MODERATE|HIGH|VERY_HIGH)"), set(s["confidence"]["properties"]["level"]["enum"]))

    def test_source_types_documented_equal_schema(self):
        s = schema()["properties"]["sources"]["items"]["properties"]["source_type"]["enum"]
        self.assertEqual(codes_in_table(REF / "evidence-contract.md", r"(PRIMARY|AUTHORITATIVE_SECONDARY|SECONDARY|COMMUNITY|UNVERIFIED)"), set(s))


class ContractInvariantTests(unittest.TestCase):

    def test_schema_fixes_implementation_authority_to_false(self):
        self.assertEqual(schema()["properties"]["authority"]["properties"]["implementation_authority"]["enum"], [False])
        rec = json.loads(EXAMPLE.read_text()); rec["authority"]["implementation_authority"] = True
        with self.assertRaisesRegex(gate.ValidationError, "implementation_authority"):
            gate.check_schema("research-record", rec)

    def test_example_record_satisfies_the_schema(self):
        gate.check_schema("research-record", json.loads(EXAMPLE.read_text()))

    def test_example_record_grants_nothing_downstream(self):
        rec = json.loads(EXAMPLE.read_text())
        self.assertFalse(rec["authority"]["implementation_authority"])
        self.assertIsNone(rec["downstream"]["work_package_id"], "a research record cannot name a work package it created")

    def test_invariants_are_stated_verbatim(self):
        text = (REF / "routing-and-authority.md").read_text(encoding="utf-8")
        for inv in INVARIANTS:
            self.assertIn(inv, text, f"{inv} not stated")
        self.assertIn("RESEARCH_SUFFICIENT", text); self.assertIn("IMPLEMENTATION_AUTHORIZED", text)

    def test_registry_entry_is_designed_with_a_real_digest(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-research")
        self.assertEqual(entry["status"], "DESIGNED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())

    def test_no_research_validator_beside_the_gate(self):
        self.assertEqual(sorted(p.name for p in (gate.ROOT / "scripts").glob("*research*")), [], "a competing research validator exists")

    def test_root_skill_names_the_five_references(self):
        text = (gate.ROOT / "skills/badf-research/SKILL.md").read_text(encoding="utf-8")
        for ref in ("research-types.md", "lifecycle.md", "evidence-contract.md", "routing-and-authority.md", "acceptance.md"):
            self.assertIn(ref, text)


if __name__ == "__main__":
    unittest.main()
