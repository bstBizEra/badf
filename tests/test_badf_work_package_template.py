"""Work Package template conforms to its schema (BADF-WP-0089 / WP-IMP-0).

`templates/work-package.json` is the skeleton every new Work Package starts from, so it must
validate against `schemas/work-package.schema.json`. It had drifted -- missing `demand`, an
uppercase `data_classification`, `permissions` as an object, and a `{trigger,procedure,owner}`
rollback -- and nothing tested it, so the drift went unnoticed. These tests are the regression
guard: the shipped template validates via the canonical gate's `check_schema`, and each of the
four drift regressions is refused. This is the prerequisite (WP-IMP-0) for the
badf-implementation-plan (G06) capability; it changes no schema.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

TEMPLATE = json.loads((gate.ROOT / "templates/work-package.json").read_text())


class WorkPackageTemplateTests(unittest.TestCase):
    def test_template_conforms_to_schema(self):
        # the whole point: the skeleton validates against the current schema.
        gate.check_schema("work-package", TEMPLATE)

    def test_template_carries_demand(self):
        self.assertIn("demand", TEMPLATE)
        self.assertRegex(TEMPLATE["demand"], r"^BADF-DEM-[0-9]{4,}$")

    def test_template_data_classification_is_lowercase_enum(self):
        self.assertIn(TEMPLATE["data_classification"],
                      ("public", "internal", "confidential", "restricted"))

    def test_template_permissions_is_an_array(self):
        self.assertIsInstance(TEMPLATE["permissions"], list)

    def test_template_rollback_has_reversible_and_method(self):
        self.assertEqual({"reversible", "method"}, set(TEMPLATE["rollback"]))

    # --- regression guards: each of the four historical drifts is refused by the schema ---

    def test_missing_demand_would_be_refused(self):
        bad = copy.deepcopy(TEMPLATE)
        del bad["demand"]
        with self.assertRaises(gate.ValidationError):
            gate.check_schema("work-package", bad)

    def test_uppercase_data_classification_would_be_refused(self):
        bad = copy.deepcopy(TEMPLATE)
        bad["data_classification"] = "INTERNAL"
        with self.assertRaises(gate.ValidationError):
            gate.check_schema("work-package", bad)

    # NB: the schema walker enforces required/enum/pattern/additionalProperties but NOT a
    # non-object type mismatch -- a `type: array` field given an object is not refused (the
    # walker only iterates items when the value is already a list). So permissions-as-object
    # is caught here by the positive `test_template_permissions_is_an_array` assertion, not by
    # check_schema. (Strengthening the walker to type-check is a gate change, out of scope for
    # this template repair; noted for WP-IMP-B, whose new typed fields would want it.)

    def test_legacy_rollback_shape_would_be_refused(self):
        bad = copy.deepcopy(TEMPLATE)
        bad["rollback"] = {"trigger": "", "procedure": "", "owner": ""}
        with self.assertRaises(gate.ValidationError):
            gate.check_schema("work-package", bad)


if __name__ == "__main__":
    unittest.main()
