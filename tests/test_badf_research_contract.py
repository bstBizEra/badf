"""Research capability contract (BADF-WP-0031; normalized by WP-2026-0041).

The root badf-research family remains DESIGNED. Deterministic research-record
validation and individually registered subskills may exist, but the contract's
meaning must not drift: taxonomy == schema, bounded framing is machine-readable,
implementation authority is fixed false, one router/council/gate is reused, and
the registry entry is digest-pinned.
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
EXAMPLES = [
    gate.ROOT / "examples/research-record.json",
    gate.ROOT / "examples/research-record-challenged.json",
    gate.ROOT / "examples/research-record-repo.json",
]
INVARIANTS = ["RSR-I01", "RSR-I02", "RSR-I03", "RSR-I04", "RSR-I05"]
CANONICAL_REFS = (
    "research-contract.md",
    "research-types.md",
    "research-depth.md",
    "research-state-machine.md",
    "evidence-contract.md",
    "routing-authority.md",
    "acceptance-controls.md",
)


def schema():
    return json.loads(SCHEMA.read_text())


def codes_in_table(doc: Path, first_col_pattern: str) -> set:
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
        self.assertEqual(codes_in_table(REF / "research-depth.md", r"D[0-5]"), enum("depth"))

    def test_states_and_dispositions_documented_equal_schema(self):
        docs = codes_in_table(REF / "research-state-machine.md", r"[A-Z_]+")
        self.assertEqual(docs, enum("state") | enum("disposition.state"))

    def test_claim_vocabulary_documented_equal_schema(self):
        doc = REF / "evidence-contract.md"
        s = schema()["properties"]["claims"]["items"]["properties"]
        self.assertEqual(
            codes_in_table(doc, r"(OBSERVED|REPORTED|INFERRED|HYPOTHESIS|DECIDED)"),
            set(s["classification"]["enum"]),
        )
        self.assertEqual(
            codes_in_table(doc, r"(VERIFIED|PARTIALLY_VERIFIED|DISPUTED|UNVERIFIED|FALSIFIED)"),
            set(s["status"]["enum"]),
        )
        self.assertEqual(
            codes_in_table(doc, r"(VERY_LOW|LOW|MODERATE|HIGH|VERY_HIGH)"),
            set(s["confidence"]["properties"]["level"]["enum"]),
        )

    def test_source_types_documented_equal_schema(self):
        s = schema()["properties"]["sources"]["items"]["properties"]["source_type"]["enum"]
        self.assertEqual(
            codes_in_table(REF / "evidence-contract.md", r"(PRIMARY|AUTHORITATIVE_SECONDARY|SECONDARY|COMMUNITY|UNVERIFIED)"),
            set(s),
        )


class ContractInvariantTests(unittest.TestCase):

    def test_schema_fixes_implementation_authority_to_false(self):
        self.assertEqual(
            schema()["properties"]["authority"]["properties"]["implementation_authority"]["enum"],
            [False],
        )
        rec = json.loads(EXAMPLES[0].read_text())
        rec["authority"]["implementation_authority"] = True
        with self.assertRaisesRegex(gate.ValidationError, "implementation_authority"):
            gate.check_schema("research-record", rec)

    def test_examples_satisfy_schema_and_keep_bounded_framing(self):
        for path in EXAMPLES:
            rec = json.loads(path.read_text())
            gate.check_schema("research-record", rec)
            self.assertIn("assumptions", rec)
            self.assertTrue(rec["decision_context"])
            self.assertTrue(rec["stop_conditions"], f"{path.name} has no stop condition")

    def test_bounded_framing_is_machine_required(self):
        s = schema()
        for name in ("assumptions", "decision_context", "stop_conditions"):
            self.assertIn(name, s["required"])
        self.assertEqual(s["properties"]["stop_conditions"]["minItems"], 1)

    def test_example_record_grants_nothing_downstream(self):
        rec = json.loads(EXAMPLES[0].read_text())
        self.assertFalse(rec["authority"]["implementation_authority"])
        self.assertIsNone(rec["downstream"]["work_package_id"], "a research record cannot name a work package it created")

    def test_invariants_are_stated_verbatim(self):
        text = (REF / "routing-authority.md").read_text(encoding="utf-8")
        for inv in INVARIANTS:
            self.assertIn(inv, text, f"{inv} not stated")
        self.assertIn("RESEARCH_SUFFICIENT", text)
        self.assertIn("IMPLEMENTATION_AUTHORIZED", text)

    def test_registry_entry_is_designed_v02_with_real_digest(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-research")
        self.assertEqual(entry["status"], "DESIGNED")
        self.assertEqual(entry["version"], "0.2.0")
        self.assertEqual(entry["allowed_tools"], [])
        self.assertEqual(
            entry["digest"],
            "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest(),
        )

    def test_no_research_validator_beside_the_gate(self):
        self.assertEqual(
            sorted(p.name for p in (gate.ROOT / "scripts").glob("*research*")),
            [],
            "a competing research validator exists",
        )

    def test_root_skill_names_canonical_reference_surface(self):
        text = (gate.ROOT / "skills/badf-research/SKILL.md").read_text(encoding="utf-8")
        for ref in CANONICAL_REFS:
            self.assertIn(ref, text)

    def test_legacy_reference_names_are_removed(self):
        for legacy in ("lifecycle.md", "routing-and-authority.md", "acceptance.md"):
            self.assertFalse((REF / legacy).exists(), f"duplicate legacy contract remains: {legacy}")

    def test_normative_integration_doc_exists(self):
        doc = gate.ROOT / "docs/14-research-capability.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("RESEARCH_SUFFICIENT", text)
        self.assertIn("IMPLEMENTATION_AUTHORIZED", text)


if __name__ == "__main__":
    unittest.main()
