"""Schemas are documentation, and documentation must not lie.

Decision BADF-DEC-0002 (option A): the gate does not apply schemas/*.json --
it hand-codes every field set and stays stdlib-only. That leaves the schemas
free to drift from the code, and they did: three of the four the gate never
reads REQUIRED properties they never DEFINED (work-package.schema.json
required 17 and defined 7), and lifecycle.schema.json did not require
minimum_change_class after WP-0006 made the gate hard-require it.

These tests make every schema agree with the code and with itself. They do
not make the schemas authoritative -- the gate is -- they make them honest.
"""
import json
import re
import unittest

import scripts.badf_gate as gate

SRC = (gate.ROOT / "scripts" / "badf_gate.py").read_text(encoding="utf-8")
SHIPPED = {
    "gate-dossier": [gate.ROOT / "examples/gate-dossier.G00.json", gate.ROOT / "examples/gate-dossier.G01.json"],
    "evidence": [gate.ROOT / "examples/evidence/G00/authority.json", gate.ROOT / "examples/evidence/G01/prd.json"],
    "prd": [gate.ROOT / "examples/evidence/G01/prd.artifact.json"],
    "acceptance-criteria": [gate.ROOT / "examples/evidence/G01/acceptance-criteria.artifact.json"],
    "product-approval": [gate.ROOT / "examples/evidence/G01/product-approval.artifact.json"],
    "lifecycle": [gate.ROOT / "badf/lifecycle.json"],
    "demand": sorted((gate.ROOT / "badf/demands").glob("BADF-DEM-*.json")),
    "work-package": sorted(gate.ROOT.glob("work/WP-*/work-package.json")),
}
assert SHIPPED["demand"] and SHIPPED["work-package"], "an empty shipped set would make these tests vacuous"


def shipped():
    for name, paths in SHIPPED.items():
        for path in paths:
            yield name, path


def code_set(name):
    m = re.search(rf"^{name} = \{{(.*?)\}}", SRC, re.S | re.M)
    assert m, f"{name} not found in gate"
    return {s.strip().strip('"') for s in m.group(1).replace("\n", "").split(",") if s.strip()}


def schema(name):
    return json.loads((gate.ROOT / "schemas" / f"{name}.schema.json").read_text())


def enum_violations(props, inst, trail=""):
    """Every enum-constrained property, at any depth, whose shipped value is not
    in the enum. Module-level so instance tests can hold GENERATED files to the
    same bar as shipped ones."""
    out = []
    for key, spec in props.items():
        if key not in inst:
            continue
        val = inst[key]
        if "enum" in spec and val not in spec["enum"]:
            out.append((trail + key, val, spec["enum"]))
        if spec.get("type") == "object" and "properties" in spec and isinstance(val, dict):
            out += enum_violations(spec["properties"], val, trail + key + ".")
        if spec.get("type") == "array" and "properties" in spec.get("items", {}) and isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    out += enum_violations(spec["items"]["properties"], item, f"{trail}{key}[{i}].")
    return out


def unknown_keys(sch, inst):
    """Keys the instance carries that the schema does not define (additionalProperties: false)."""
    if sch.get("additionalProperties", True) is not False:
        return set()
    return set(inst) - set(sch.get("properties", {}))


class SchemaMirrorsCodeTests(unittest.TestCase):
    """Schemas the gate reads: required[] must equal the gate's field set."""

    def test_dossier_required_equals_DOSSIER_FIELDS(self):
        self.assertEqual(set(schema("gate-dossier")["required"]), code_set("DOSSIER_FIELDS"))

    def test_evidence_required_equals_EVIDENCE_FIELDS(self):
        self.assertEqual(set(schema("evidence")["required"]), code_set("EVIDENCE_FIELDS"))

    def test_condition_items_required_equals_CONDITION_FIELDS(self):
        items = schema("gate-dossier")["properties"]["conditions"]["items"]
        self.assertEqual(set(items["required"]), code_set("CONDITION_FIELDS"))

    def test_approval_items_required_equals_APPROVAL_FIELDS(self):
        items = schema("gate-dossier")["properties"]["approvals"]["items"]
        self.assertEqual(set(items["required"]), code_set("APPROVAL_FIELDS"))

    def test_enums_match_code(self):
        props = schema("gate-dossier")["properties"]
        self.assertEqual(set(props["approvals"]["items"]["properties"]["decision"]["enum"]),
                         code_set("APPROVAL_DECISIONS"))
        self.assertEqual(set(props["conditions"]["items"]["properties"]["status"]["enum"]),
                         code_set("CONDITION_STATUSES"))
        self.assertEqual(set(props["conditions"]["items"]["properties"]["severity"]["enum"]),
                         code_set("CONDITION_SEVERITIES"))
        self.assertEqual(set(props["change_class"]["enum"]), set(gate.CLASS_RANK))
        self.assertEqual(set(props["obligation_posture"]["enum"]), gate.POSTURES)

    def test_lifecycle_schema_requires_what_the_gate_requires_per_gate(self):
        """WP-0006 made minimum_change_class a hard requirement; the schema must say so."""
        per_gate = set(schema("lifecycle")["properties"]["gates"]["items"]["required"])
        self.assertIn("minimum_change_class", per_gate)
        self.assertTrue({"id", "name", "owner_role", "required_evidence", "exit_criteria"} <= per_gate)


class SchemaInternalConsistencyTests(unittest.TestCase):
    """Every schema, read or not: a required property must be defined."""

    def test_no_schema_requires_an_undefined_property(self):
        for name in ("gate-dossier", "evidence", "lifecycle", "memory", "session", "work-package", "demand", "project", "state", "init-receipt", "charter", "prd", "acceptance-criteria", "product-approval"):
            with self.subTest(schema=name):
                s = schema(name)
                undefined = set(s.get("required", [])) - set(s.get("properties", {}))
                self.assertEqual(undefined, set(), f"{name}.schema.json requires undefined: {sorted(undefined)}")

    def test_shipped_instances_satisfy_their_schema_required_sets(self):
        """Structural only (no jsonschema dependency): every required key present."""
        for name, path in shipped():
            with self.subTest(schema=name, file=path.name):
                inst = json.loads(path.read_text())
                missing = set(schema(name)["required"]) - set(inst)
                self.assertEqual(missing, set(), f"{path.name} lacks {sorted(missing)}")

    def test_shipped_instances_use_only_enum_values(self):
        """The first version of this file checked required KEYS only, and passed
        while every shipped evidence example carried producer.type
        'human-template' -- a value in NO vocabulary. Keys present is not
        values valid. Walk every enum-constrained property, at any depth, and
        assert the shipped value is in it."""
        def walk(props, inst, trail):
            for key, spec in props.items():
                if key not in inst:
                    continue
                val = inst[key]
                if "enum" in spec:
                    yield trail + key, val, spec["enum"]
                if spec.get("type") == "object" and "properties" in spec and isinstance(val, dict):
                    yield from walk(spec["properties"], val, trail + key + ".")
                if spec.get("type") == "array" and "properties" in spec.get("items", {}) and isinstance(val, list):
                    for i, item in enumerate(val):
                        if isinstance(item, dict):
                            yield from walk(spec["items"]["properties"], item, f"{trail}{key}[{i}].")
        for name, path in shipped():
            inst = json.loads(path.read_text())
            for where, val, allowed in walk(schema(name)["properties"], inst, ""):
                with self.subTest(schema=name, file=path.name, field=where):
                    self.assertIn(val, allowed, f"{path.name} {where}={val!r} not in {allowed}")


if __name__ == "__main__":
    unittest.main()
