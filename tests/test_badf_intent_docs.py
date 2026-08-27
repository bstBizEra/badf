"""The intent contract cannot drift (BADF-WP-0027, Issue #25).

README documents the `badf init` intent; the gate defines it. Both must
agree, mechanically: the README table's required rows equal INTENT_REQUIRED,
its optional rows equal INTENT_OPTIONAL, the target row names every
INTENT_TARGETS value, the shipped example loads, and an unknown key is
refused rather than silently ignored (a typo of `maturity` would otherwise
become DECLARED_MISSING -- invented, not read).
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

README = (gate.ROOT / "README.md").read_text(encoding="utf-8")
SRC = (gate.ROOT / "scripts/badf_gate.py").read_text(encoding="utf-8")
ROW = re.compile(r"^\| ((?:`[a-z_]+`(?:, )?)+) \| (yes|no) \| (.*) \|$", re.M)


def documented():
    required, optional, target_row = set(), set(), None
    for fields, req, desc in ROW.findall(README):
        names = re.findall(r"`([a-z_]+)`", fields)
        (required if req == "yes" else optional).update(names)
        if "target" in names:
            target_row = desc
    return required, optional, target_row


class IntentDocsMatchCodeTests(unittest.TestCase):

    def test_required_rows_equal_INTENT_REQUIRED(self):
        required, _, _ = documented()
        self.assertEqual(required, gate.INTENT_REQUIRED)

    def test_optional_rows_equal_INTENT_OPTIONAL(self):
        _, optional, _ = documented()
        self.assertEqual(optional, gate.INTENT_OPTIONAL)

    def test_target_row_names_every_target(self):
        _, _, row = documented()
        self.assertIsNotNone(row)
        for t in gate.INTENT_TARGETS:
            self.assertIn(f"`{t}`", row, f"README's target row does not name {t!r}")

    def test_the_gate_reads_exactly_the_optional_keys_it_documents(self):
        """The source is the second document: every optional key the gate reads
        with proj.get(...) must be in INTENT_OPTIONAL, and vice versa."""
        read = set(re.findall(r'proj\.get\("([a-z_]+)"\)', SRC))
        self.assertEqual(read, gate.INTENT_OPTIONAL)

    def test_shipped_example_loads_and_uses_only_documented_keys(self):
        example = gate.ROOT / "examples/intent.json"
        self.assertTrue(example.is_file(), "examples/intent.json is missing")
        proj = gate.load_intent(example)
        self.assertLessEqual(set(proj), gate.INTENT_REQUIRED | gate.INTENT_OPTIONAL)
        self.assertGreaterEqual(set(proj), gate.INTENT_REQUIRED)

    def test_unknown_key_is_refused_not_ignored(self):
        base = json.loads((gate.ROOT / "examples/intent.json").read_text())
        base["project"]["maturty"] = "IDEA"   # a typo of maturity
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(base, f); path = Path(f.name)
        try:
            with self.assertRaisesRegex(gate.ValidationError, "maturty"):
                gate.load_intent(path)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
