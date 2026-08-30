"""check_schema scalar/array type conformance (BADF-WP-0097 / GOV-0080, closes #171).

The JSON-schema-lite walker enforced required / enum / pattern / additionalProperties and
the object-must-be-a-mapping rule, but did NOT refuse a value whose JSON type mismatched a
declared scalar/array ``type``: an ``array`` given an object was silently skipped (the
items loop is guarded by ``isinstance(val, list)``), and ``string`` / ``number`` /
``integer`` / ``boolean`` were never type-checked. The typed planning fields the G06 ladder
added (``execution_budget``, ``stop_conditions``, ``dependencies``, ...) were declared but
only value-checked by code controls; a malformed *type* passed the schema layer (#171).

These tests pin the type layer at any depth, using REAL committed examples so a false
positive on a valid record fails loudly. ``bool`` is a Python ``int`` subclass, so
``integer`` / ``number`` must reject it explicitly.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

# work-breakdown carries array/string/integer/number typed fields;
# architecture-assurance carries a boolean (authority.implementation_authority).
WB = json.loads((gate.ROOT / "examples/work-breakdown-planned.json").read_text())
AA = json.loads((gate.ROOT / "examples/architecture-assurance.json").read_text())


class SchemaTypeEnforcementTests(unittest.TestCase):
    def refuse(self, name, doc, needle):
        with self.assertRaises(gate.ValidationError) as cm:
            gate.check_schema(name, doc)
        self.assertIn(needle, str(cm.exception))

    # --- array: the original silent-skip gap (array given a non-list) ---
    def test_type_array_field_rejects_object(self):
        bad = copy.deepcopy(WB)
        bad["tasks"][0]["acceptance"] = {"not": "a list"}
        self.refuse("work-breakdown", bad, "must be an array")

    def test_top_level_array_rejects_object(self):
        bad = copy.deepcopy(WB)
        bad["tasks"] = {"nope": 1}
        self.refuse("work-breakdown", bad, "must be an array")

    # --- string: a genuine `type: string` field (not an enum-only field, which
    # the enum check would catch first) ---
    def test_type_string_field_rejects_non_string(self):
        bad = copy.deepcopy(WB)
        bad["tasks"][0]["description"] = 123
        self.refuse("work-breakdown", bad, "must be a string")

    # --- integer (bool is an int subclass -> must still be rejected) ---
    def test_type_integer_field_rejects_string(self):
        bad = copy.deepcopy(WB)
        bad["tasks"][0]["execution_budget"]["max_attempts"] = "3"
        self.refuse("work-breakdown", bad, "must be an integer")

    def test_type_integer_field_rejects_bool(self):
        bad = copy.deepcopy(WB)
        bad["tasks"][0]["execution_budget"]["max_attempts"] = True
        self.refuse("work-breakdown", bad, "must be an integer")

    # --- number (bool is an int subclass -> must still be rejected) ---
    def test_type_number_field_rejects_bool(self):
        bad = copy.deepcopy(WB)
        bad["tasks"][0]["execution_budget"]["max_elapsed_minutes"] = True
        self.refuse("work-breakdown", bad, "must be a number")

    def test_type_number_field_accepts_int_and_float(self):
        ok = copy.deepcopy(WB)
        for v in (5, 5.5):
            ok["tasks"][0]["execution_budget"]["max_elapsed_minutes"] = v
            gate.check_schema("work-breakdown", ok)  # must not raise

    # --- boolean ---
    def test_type_boolean_field_rejects_non_bool(self):
        bad = copy.deepcopy(AA)
        bad["authority"]["implementation_authority"] = "false"
        self.refuse("architecture-assurance", bad, "must be a boolean")

    # --- no false positives: the real committed examples validate as-is ---
    def test_conforming_examples_still_pass(self):
        gate.check_schema("work-breakdown", WB)
        gate.check_schema("architecture-assurance", AA)


if __name__ == "__main__":
    unittest.main()
