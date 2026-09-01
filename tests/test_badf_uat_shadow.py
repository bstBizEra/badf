"""badf-uat WP-UAT-D (WP-2026-0131, #277): the REPRESENTATIVE shadow, and its tripwires.

Read the caveat first: `skills/badf-uat/references/shadow-evidence.md`. BADF has never run a
G10 -- it builds itself and has no product-acceptance event -- so this shadow runs on a
**declared representative** product (`PRD-SHADOW-CHECKOUT`), exactly as `badf-security-design`
was admitted on `PRD-SHADOW-PAYMENTS` (#166) and `badf-solution-design` before it (#145).

SARCHI ruled the disposition on #277 and amended it: an EMPTY-corpus shadow is refused as
vacuous (it exercises no control, so a broken control and a correct one are identically green),
a MANUFACTURED-but-undeclared corpus is refused as proxy-for-property, and a DECLARED
representative corpus with a live trigger is the precedent path. The distinction that carried
it -- vacuity gap vs realism gap -- is what this module is built on: every case here CAN fail,
and each is observed failing against its own control.

Nothing here is trusted from the stored record. Every verdict is RECOMPUTED against the live
gate on every run, so the examples cannot drift from `check_g10_uat_binding`.

TWO TRIPWIRES, because a caveat that depends on someone remembering is the silence C11 refuses:

  1. `test_no_real_g10_dossier_exists_yet` -- asserts against a LIVE SCAN that the corpus is
     still representative. The day a real G10 dossier lands this goes RED and the rung must be
     re-shadowed for real. #166's trigger is prose and has waited on a human noticing since it
     was filed; this one does not.
  2. `test_the_known_substring_hole_in_c7_c9_is_still_open` -- #289. C7/C9 match a scenario id
     by SUBSTRING against joined prose, so a critical failure named only by a LONGER id passes
     as acknowledged. This shadow must not report those controls as sound while that is true.
     When #289 lands, this test goes RED and the shadow's non-coverage entry must be removed.
"""
import ast
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

ART = gate.ROOT / "examples/uat-shadow-checkout.log"
ACCEPTED = gate.ROOT / "examples/uat-shadow-checkout.json"
REJECTED = gate.ROOT / "examples/uat-shadow-checkout-rejected.json"
DOC = gate.ROOT / "skills/badf-uat/references/shadow-evidence.md"
CRIT = "UAT-SCN-CHK-001"
DEFECT = [{"scenario_id": CRIT, "defect_class": "IMPLEMENTATION_DEFECT",
           "statement": "no confirmation number"}]


def check(ev):
    gate.check_g10_uat_binding(ART, {"disposition": "PASS", "work_package_id": "WP-2026-0131"}, ev)


def _crit_fails(b):
    b["observations"][0]["result"] = "FAIL"
    b["defects"] = copy.deepcopy(DEFECT)
    b["coverage"]["criteria"][0]["state"] = "covered_fail"


# One case per control. The KEY is the case name; the VALUE is (mutation, message fragment).
# The fragment is asserted, not merely a non-zero raise -- passing on the wrong raise is how a
# control acquires a test that does not test it.
CASES = {
    "U2-unanchored-observation": (
        lambda b: b["observations"].append(dict(b["observations"][0], scenario_id="UAT-SCN-GHOST")),
        "absent from this binding"),
    "U3-failure-without-defect-class": (
        lambda b: (b["observations"].__setitem__(0, dict(b["observations"][0], result="FAIL")),
                   b.__setitem__("defects", [])),
        "no defect class"),
    "U6-duplicate-observation": (
        lambda b: b["observations"].append(dict(b["observations"][0])),
        "more than one observation"),
    "U4-recommend-accept-over-critical": (
        lambda b: (_crit_fails(b), b.__setitem__("recommendation", "RECOMMEND_ACCEPT")),
        "RECOMMEND_ACCEPT with critical"),
    "U5a-acceptance-bound-to-other-candidate": (
        lambda b: b["acceptance"].__setitem__("candidate_digest", "sha256:" + "9" * 64),
        "candidate_digest does not equal"),
    "U5b-non-human-principal": (
        lambda b: b["acceptance"]["accepted_by"].__setitem__("principal_type", "agent"),
        "non-human principal"),
    "C7-with-conditions-critical-unnamed": (
        lambda b: (_crit_fails(b),
                   b.__setitem__("recommendation", "RECOMMEND_ACCEPT_WITH_CONDITIONS"),
                   b["acceptance"].__setitem__("conditions", ["AC-9 unrelated follow-up"]),
                   b["acceptance"].__setitem__("disposition", "ACCEPTED_WITH_CONDITIONS")),
        "RECOMMEND_ACCEPT_WITH_CONDITIONS with critical"),
    "C8-with-conditions-carries-none": (
        lambda b: b["acceptance"].__setitem__("disposition", "ACCEPTED_WITH_CONDITIONS"),
        "carries no conditions"),
    "C9-unconditional-accept-unacknowledged": (
        lambda b: (_crit_fails(b),
                   b.__setitem__("recommendation", "RECOMMEND_REJECT"),
                   b["acceptance"].__setitem__("disposition", "ACCEPTED")),
        "unconditional ACCEPTED over critical"),
    "C10-stale-scenario-set-digest": (
        lambda b: b["acceptance"].__setitem__("scenario_set_digest", "sha256:" + "8" * 64),
        "scenario_set_digest does not equal"),
    "C11-not-covered-unexplained": (
        lambda b: b["coverage"]["criteria"].__setitem__(
            0, {"acceptance_criterion_ref": "AC-1", "state": "not_covered"}),
        "not_covered with neither"),
}


def gate_control_count():
    """ValidationError sites in check_g10_uat_binding, read from the LIVE gate by AST.

    The shadow's case count is asserted against this rather than against a number written here,
    so a control added later without a shadow case fails instead of being silently unshadowed.
    """
    src = (gate.ROOT / "scripts/badf_gate.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "check_g10_uat_binding")
    return sum(1 for n in ast.walk(fn)
               if isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call)
               and getattr(n.exc.func, "id", "") == "ValidationError")


def defect_classes():
    """The defect_class enum, read from the SCHEMA rather than written here.

    The ladder frozen at rung A asks D to inject defects across ALL TEN classes. Deriving the
    set from the schema is the walk-the-whole-enum form: if a class is added later, the sweep
    below covers it automatically and the count assertion fails if it does not. Written down
    as a literal, this test would only ever confirm the classes I happened to think of -- which
    is exactly how my own control count came out as "ten" when the gate had eleven.
    """
    schema = json.loads((gate.ROOT / "schemas/uat.schema.json").read_text(encoding="utf-8"))
    return schema["properties"]["binding"]["properties"]["defects"]["items"] \
                 ["properties"]["defect_class"]["enum"]


class ShadowCorpusTests(unittest.TestCase):
    """The representative corpus is admitted, and RECOMPUTED rather than trusted."""

    def test_the_accepted_run_is_admitted_and_its_digest_recomputes(self):
        ev = json.loads(ACCEPTED.read_text(encoding="utf-8"))
        self.assertEqual(gate.sha256(ART), ev["digest"],
                         "stored digest does not recompute from the artifact; the record has drifted")
        self.assertEqual(ev["binding"]["candidate"]["source_digest"], ev["digest"])
        check(ev)

    def test_the_rejecting_run_is_admitted_a_rejection_is_evidence_not_a_refusal(self):
        """The shadow must contain a REFUSAL OUTCOME, not only a happy path. A critical failure
        with a classified defect and RECOMMEND_REJECT is valid uat evidence -- the gate refuses
        malformed evidence, never an unfavourable result."""
        ev = json.loads(REJECTED.read_text(encoding="utf-8"))
        b = ev["binding"]
        self.assertEqual("RECOMMEND_REJECT", b["recommendation"])
        self.assertEqual("FAIL", b["observations"][0]["result"])
        self.assertTrue(b["defects"], "a rejecting run must classify its defect (UAT-I11)")
        self.assertNotIn("acceptance", b, "no human decision has been issued on a rejected candidate")
        check(ev)


class ShadowControlCalibrationTests(unittest.TestCase):
    """Every control driven, each observed red against its OWN message fragment."""

    def setUp(self):
        self.ev = json.loads(ACCEPTED.read_text(encoding="utf-8"))

    def test_every_control_refuses_its_own_defect(self):
        for name, (mutate, fragment) in CASES.items():
            with self.subTest(case=name):
                ev = copy.deepcopy(self.ev)
                mutate(ev["binding"])
                with self.assertRaises(gate.ValidationError) as cm:
                    check(ev)
                self.assertIn(fragment, str(cm.exception),
                              f"{name} was refused, but by a different control -- passing on the "
                              f"wrong raise is how a control acquires a test that does not test it")

    def test_the_shadow_covers_every_control_the_gate_actually_has(self):
        """ANTI-VACUITY. The case count is derived from the live gate, not written here, so a
        control added later without a shadow case fails rather than going quietly unshadowed."""
        self.assertEqual(gate_control_count(), len(CASES),
                         "check_g10_uat_binding has a control with no shadow case (or a case with "
                         "no control); the shadow must cover every control the gate has")


class DefectClassCoverageTests(unittest.TestCase):
    """The ladder's ten-class injection, built rather than waived.

    I earlier argued this requirement was unachievable. It is not: `defect_class` is DATA in
    `binding.defects[]`, not something the tool-less router detects, so every class can be
    injected without any runtime. The claim was over-reach in the direction that excused an
    incomplete build, and it is retracted on #277.
    """

    def setUp(self):
        self.ev = json.loads(ACCEPTED.read_text(encoding="utf-8"))

    def test_every_defect_class_in_the_schema_is_exercised_and_admitted(self):
        """A failing critical scenario classified under EACH class satisfies U3 and is admitted.

        This is the positive half: a classified failure is evidence the disposition can act on.
        The refusal half (a failure with NO class) is U3's case in the calibration table above.
        """
        classes = defect_classes()
        self.assertGreaterEqual(len(classes), 10, "the ladder asks for all ten classes")
        for dc in classes:
            with self.subTest(defect_class=dc):
                ev = copy.deepcopy(self.ev)
                b = ev["binding"]
                b["observations"][0]["result"] = "FAIL"
                b["defects"] = [{"scenario_id": CRIT, "defect_class": dc,
                                 "statement": f"representative failure classified {dc}"}]
                b["coverage"]["criteria"][0]["state"] = "covered_fail"
                b["recommendation"] = "RECOMMEND_REJECT"
                del b["acceptance"]
                check(ev)

    def test_an_unknown_defect_class_is_refused_by_the_schema(self):
        """Negative control for the sweep above: without it, "all ten admitted" would be
        indistinguishable from "the field is not validated at all"."""
        ev = copy.deepcopy(self.ev)
        b = ev["binding"]
        b["observations"][0]["result"] = "FAIL"
        b["defects"] = [{"scenario_id": CRIT, "defect_class": "NOT_A_REAL_CLASS",
                         "statement": "x"}]
        b["coverage"]["criteria"][0]["state"] = "covered_fail"
        b["recommendation"] = "RECOMMEND_REJECT"
        del b["acceptance"]
        with self.assertRaises(gate.ValidationError):
            check(ev)

    def test_the_corpus_carries_the_prd_ac_rtm_chain_the_ladder_asks_for(self):
        """`traceability_digest` is optional in the schema and I had left it unset -- the RTM
        third of the ladder's "PRD/AC/RTM chain". Populated, and pinned so it stays."""
        for path in (ACCEPTED, REJECTED):
            with self.subTest(corpus=path.name):
                basis = json.loads(path.read_text(encoding="utf-8"))["binding"]["acceptance_basis"]
                for field in ("prd_digest", "acceptance_criteria_digest", "traceability_digest"):
                    self.assertIn(field, basis, f"{path.name} is missing {field}")


class TripwireTests(unittest.TestCase):
    """The claims that must EXPIRE BY THEMSELVES rather than by anyone remembering."""

    def test_no_real_g10_dossier_exists_yet(self):
        """BINDING per SARCHI's ruling on #277. The representativeness caveat is only honest
        while BADF has no real product-acceptance event. This asserts that against a LIVE SCAN,
        so the day a real G10 dossier lands the claim fails instead of quietly going stale.

        When this goes RED: the caveat in shadow-evidence.md is now false. Re-shadow against the
        real dossier and file the result; do not delete this test to make it pass.
        """
        real = sorted(p.as_posix() for p in (gate.ROOT / "work").glob("*/gate-dossier.G10.json"))
        self.assertEqual([], real,
                         f"a real G10 dossier now exists ({real}); the representative caveat in "
                         f"{DOC.relative_to(gate.ROOT)} is no longer true and the real re-shadow is owed")

    def test_the_known_substring_hole_in_c7_c9_is_still_open(self):
        """#289, declared as non-coverage rather than shadowed as sound.

        C7/C9 decide whether a failing critical scenario is NAMED by substring against joined
        prose, so a scenario named only by a LONGER id passes as acknowledged. This shadow must
        not report those controls as sound while that is true.

        When this goes RED: #289 has landed. Remove this test AND the matching non_coverage entry
        from shadow-evidence.md in the same change.
        """
        ev = copy.deepcopy(json.loads(ACCEPTED.read_text(encoding="utf-8")))
        b = ev["binding"]
        _crit_fails(b)
        b["recommendation"] = "RECOMMEND_ACCEPT_WITH_CONDITIONS"
        b["acceptance"]["disposition"] = "ACCEPTED_WITH_CONDITIONS"
        b["acceptance"]["conditions"] = [f"{CRIT}1 is a DIFFERENT scenario and the only one named"]
        try:
            check(ev)
        except gate.ValidationError as e:  # pragma: no cover - fires only once #289 lands
            self.fail(f"#289 appears fixed -- C7 now refuses the longer-id case ({e}). "
                      f"Remove this test and the #289 non_coverage entry from the shadow doc.")

    def test_the_shadow_doc_states_the_caveat_in_its_first_section(self):
        """The #166 form: the caveat is the FIRST thing a reader meets, not a footnote."""
        text = DOC.read_text(encoding="utf-8")
        head = text.split("\n## ")[1] if "\n## " in text else ""
        self.assertIn("REPRESENTATIVE", head.upper(),
                      "the first section must be the representativeness caveat (#166 form)")
        for token in ("#277", "#289", "#291", "PRD-SHADOW-CHECKOUT"):
            self.assertIn(token, text, f"shadow evidence must name {token}")


if __name__ == "__main__":
    unittest.main()
