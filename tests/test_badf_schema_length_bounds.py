"""Rung A (#265, WP-2026-0138): check_schema enforces `minLength` and `minItems`, red-first.

Before this change the walker implemented exactly seven keywords -- `type`, `properties`,
`required`, `additionalProperties`, `enum`, `pattern`, `items` -- established by AST
enumeration over `check_schema`, not by testing a guessed candidate list. `minLength` (377
declarations across 49 files) and `minItems` (48 across 32) were declared everywhere and
enforced nowhere: a `minLength: 1` on a governance field read as a guarantee that the field
was non-empty and was not one.

Two things this battery is careful about, because both were measured on this issue:

1.  **`minLength: 1` is a LENGTH check, not a non-emptiness check.** It refuses `""` and
    admits `"   "` and `" GHOST"`. The compensating code controls use `.strip()` and are
    therefore STRICTLY STRONGER than the declarations they compensate for. Nothing here
    may be read as closing the degenerate-content class (#293); it closes the exact-empty
    instance of it. `test_the_class_is_not_closed_only_its_empty_half` pins that.

2.  **Three of the 425 declaration sites are buried in `anyOf`**, which the walker still has
    no branch for, so this change reaches 422 and not 425.
    `test_the_anyof_buried_sites_are_still_unenforced` pins that too, so a later reader does
    not infer full coverage from a green suite.

The fixture is `badf/seats.json` against `seats.schema.json` -- a REAL landed record, and
the one schema `validate_repo()` actually hands to `check_schema` (measured: instrumenting
the function and running `validate_repo()` yields exactly `['seats']`). It carries both
required depths: a root-level array bound and a bound nested inside array items.
"""
import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GATE_PY = ROOT / "scripts" / "badf_gate.py"
ROSTER = ROOT / "badf" / "seats.json"

# The exact source block this rung adds. The mutation battery removes it verbatim, so a
# drift between this string and the gate fails loudly rather than silently disarming the
# discrimination (an instrument the fix can silence is the defect one level up).
RUNG_A_BRANCH = '''        if "minLength" in spec and isinstance(val, str) and len(val) < spec["minLength"]:
            raise ValidationError(f"{name}: {label}={val!r} is shorter than minLength {spec['minLength']}")
        if "minItems" in spec and isinstance(val, list) and len(val) < spec["minItems"]:
            raise ValidationError(f"{name}: {label} has {len(val)} items, fewer than minItems {spec['minItems']}")
'''


def roster():
    return json.loads(ROSTER.read_text(encoding="utf-8"))


class RungADeclaredSitesTests(unittest.TestCase):
    """The three sites this fixture exercises are declared, at two different depths."""

    def test_the_fixture_carries_both_required_depths(self):
        sch = json.loads((ROOT / "schemas" / "seats.schema.json").read_text(encoding="utf-8"))
        seats = sch["properties"]["seats"]
        self.assertEqual(seats.get("minItems"), 1, "root-level array bound absent")
        item = seats["items"]["properties"]
        self.assertEqual(item["id"].get("minLength"), 1, "nested string bound absent")
        self.assertEqual(item["charter_refs"].get("minItems"), 1, "nested array bound absent")


class RungAEnforcementTests(unittest.TestCase):

    def test_the_real_landed_roster_is_still_admitted(self):
        """NEGATIVE CONTROL (criterion 3). The rule must not refuse conforming records."""
        gate.check_schema("seats", roster())

    def test_minitems_refuses_an_empty_root_level_array(self):
        """DEPTH 1 -- root-level array."""
        r = roster()
        r["seats"] = []
        with self.assertRaises(gate.ValidationError) as cm:
            gate.check_schema("seats", r)
        self.assertIn("minItems", str(cm.exception))

    def test_minlength_refuses_an_empty_string_nested_in_array_items(self):
        """DEPTH 2 -- a string inside array items. A root-only implementation passes the
        depth-1 test above and fails this one, which is the whole reason both exist."""
        r = roster()
        r["seats"][0]["id"] = ""
        with self.assertRaises(gate.ValidationError) as cm:
            gate.check_schema("seats", r)
        self.assertIn("minLength", str(cm.exception))

    def test_minitems_refuses_an_empty_array_nested_in_array_items(self):
        """DEPTH 2 -- an array inside array items."""
        r = roster()
        r["seats"][0]["charter_refs"] = []
        with self.assertRaises(gate.ValidationError) as cm:
            gate.check_schema("seats", r)
        self.assertIn("minItems", str(cm.exception))

    def test_the_refusal_names_path_declared_bound_and_received_value(self):
        """Criterion 1. A refusal that does not say WHERE and WHAT is a puzzle, and
        message-level attribution is what lets a later battery prove the right control
        fired rather than a neighbour."""
        r = roster()
        r["seats"][0]["id"] = ""
        with self.assertRaises(gate.ValidationError) as cm:
            gate.check_schema("seats", r)
        msg = str(cm.exception)
        self.assertIn("seats[0].id", msg, "path absent")
        self.assertIn("''", msg, "received value absent")
        self.assertIn("1", msg, "declared bound absent")

    def test_conforming_values_at_each_bounded_site_are_admitted(self):
        """NEGATIVE CONTROL at each site individually -- a rule that refused these would
        pass every refusal test above while being wrong."""
        for field, good in (("id", "SEAT-OK"), ("charter_refs", ["docs/03-x.md"])):
            with self.subTest(field=field):
                r = roster()
                r["seats"][0][field] = good
                gate.check_schema("seats", r)


class DegenerateContentBoundaryTests(unittest.TestCase):
    """What this rung does NOT close, pinned so nobody infers it from a green suite."""

    def test_the_class_is_not_closed_only_its_empty_half(self):
        """`minLength: 1` is a LENGTH check. Whitespace-only and padded content still pass
        the schema; the `.strip()` code controls are what refuse them, which is why
        criterion 5 forbids removing a code control in this change (#290, #293)."""
        for probe in ("   ", " GHOST"):
            with self.subTest(probe=probe):
                r = roster()
                r["seats"][0]["id"] = probe
                gate.check_schema("seats", r)   # ADMITTED by the schema layer, by design

    def test_the_anyof_buried_sites_are_still_unenforced(self):
        """Three of the 425 declaration sites sit inside `anyOf`, which the walker still has
        no branch for. This rung reaches 422. Pinned as BEHAVIOUR rather than as a source
        grep, so it fails the day `anyOf` is implemented -- with an instruction, not a
        puzzle."""
        sch = json.loads((ROOT / "schemas" / "work-package.schema.json").read_text(encoding="utf-8"))
        self.assertIn("anyOf", sch["properties"]["objective"],
                      "objective is no longer an anyOf; re-count the buried sites")
        wp = json.loads((ROOT / "work" / "WP-2026-0022" / "work-package.json").read_text(encoding="utf-8"))
        wp["objective"] = ""
        try:
            gate.check_schema("work-package", wp)
        except gate.ValidationError:
            self.fail("check_schema now refuses an empty `objective`, so the anyOf-buried "
                      "bound is reached. `anyOf` has been implemented: update this test and "
                      "the 422-of-425 figure in the PR body and in #265, which are now stale.")


class MutationDiscriminationTests(unittest.TestCase):
    """SARCHI C1. Neutering the rung's own branch must redden the battery above. Without
    this, every assertion here could be passing on a neighbouring control -- which is the
    exact defect #265 is about, one level up: a check that appears to guard and does not."""

    @staticmethod
    def _gate_without_rung_a(tmp: Path):
        src = GATE_PY.read_text(encoding="utf-8")
        if src.count(RUNG_A_BRANCH) != 1:
            raise AssertionError(
                f"the rung's source block appears {src.count(RUNG_A_BRANCH)} times, expected 1 -- "
                "this battery can no longer neuter what it claims to test")
        (tmp / "scripts").mkdir(parents=True, exist_ok=True)
        (tmp / "scripts" / "badf_gate.py").write_text(src.replace(RUNG_A_BRANCH, ""), encoding="utf-8")
        shutil.copytree(ROOT / "schemas", tmp / "schemas")
        spec = importlib.util.spec_from_file_location(
            "badf_gate_rung_a_mutant", tmp / "scripts" / "badf_gate.py")
        mod = importlib.util.module_from_spec(spec)
        prior = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.dont_write_bytecode = prior
        return mod

    def test_neutering_the_branch_admits_every_probe_this_battery_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            mutant = self._gate_without_rung_a(Path(td))
            base = roster()
            # POSITIVE CONTROL on the mutant: it must still be a working walker, or its
            # silence on the probes below would mean nothing.
            mutant.check_schema("seats", base)
            broken = copy.deepcopy(base)
            broken["seats"][0]["id"] = 12345          # a type violation the mutant still catches
            with self.assertRaises(mutant.ValidationError):
                mutant.check_schema("seats", broken)

            probes = {
                "empty root array": lambda r: r.__setitem__("seats", []),
                "empty nested string": lambda r: r["seats"][0].__setitem__("id", ""),
                "empty nested array": lambda r: r["seats"][0].__setitem__("charter_refs", []),
            }
            for name, mutate in probes.items():
                with self.subTest(probe=name):
                    r = copy.deepcopy(base)
                    mutate(r)
                    with self.assertRaises(gate.ValidationError):
                        gate.check_schema("seats", r)        # the shipped gate REFUSES
                    mutant.check_schema("seats", r)          # the neutered gate ADMITS


if __name__ == "__main__":
    unittest.main()
