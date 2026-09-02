"""Tripwires for four deferred re-shadows, and the convention all four rest on.

Six issues were "deferred, trigger = ..." with the trigger written as PROSE. Only
`badf-uat` had a mechanical watch (`test_badf_uat_shadow.py::TripwireTests`). The
repository's own doctrine, in the file that built that one working example:

    TRIPWIRES, because a caveat that depends on someone remembering is the silence
    C11 refuses.

#166's own module docstring says its trigger "is prose and has waited on a human
noticing". This file discharges that for four of the remaining five:

  #251  badf-release-validation         first real G09 validation evidence
  #217  badf-engineering-verification   typed G08 evidence with a `binding`, or a
                                        verification record
  #166  badf-security-design            first real security-composition matrix
  #185  badf-implementation-plan        first real G06 plan

#212 (badf-build) is DELIBERATELY ABSENT. Its four control inputs are not absent from
the corpus -- they are present in 22, 25, 1 and 0 records respectively -- so its caveat
cannot be watched by a presence scan, and its trigger as written ("executed through
badf-build's workflow by a build controller") names a property `build/session.json`
does not carry at all. It is a reading, not a scan. See #212.

EVERY WATCH HERE CARRIES AN AIM PROOF -- read site, matcher and reach. The file and line
where the code under test reads the fact; WHICH matcher it uses; and how deep that matcher
reaches. Depth belongs to the matcher, not to the pattern, and this gate carries both
semantics in one file: `badf_gate.py:294` `root.glob` is segment-aware, while `:1737`
`_surface_match` is `fnmatch`, whose `*` crosses `/`. This is required because of what a
mutation battery CANNOT establish:

    A positive control cannot detect a mis-aimed watch. Mutate-and-observe-RED proves
    the assertion is wired to its own predicate. It does not prove the predicate points
    where the fact lives -- the mutation manufactures the very condition the aim gets
    wrong. Write a field into the wrong file and the wrong file lights up.

The first draft of this file scanned `build.json` for #212's four fields. It was green,
and its positive control passed, because injecting the field into `build.json` makes a
`build.json`-scanning watch fire whether or not real records ever put it there. Nothing
in the negative/positive matrix could have caught it. Asking "where does the gate READ
this?" caught it immediately.

WHAT MAKES THESE MECHANICAL. Every one waits on "a real X", and in this repository
real evidence lands under `work/` -- a PATH fact rather than a content judgement.

That fact is asserted by the fifth test rather than left as prose, because it is a shared
single point of failure: if it stops holding, the four stay GREEN while scanning the wrong
tree. It is the load-bearing one.

Note the asymmetry, which the fifth test's docstring states in full. "Real evidence is
bound only from under `work/`" is asserted. "Fixtures live under `examples/`" is NOT the
same claim and is NOT asserted -- `templates/` holds a `work-package.json` too, so the
fixture homes are not a two-way split and this file never treats them as one.

#217 COULD NOT BE WRITTEN FROM ITS ISSUE TITLE. Four objects of the named types already
exist under `work/WP-2026-0010/evidence/G08/` -- the VER-D shadow's own corpus -- so a
tripwire keyed on existence is RED on day one. The discriminator is the `binding`.

NONE OF THESE MAY BE DELETED TO MAKE THEM PASS. A red means a caveat became false, which
is the event they exist to catch. Each failure message names what to do instead.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

WORK = gate.ROOT / "work"

# #217 names one type the gate's G08 observation constant does not carry.
G08_TYPED = tuple(gate.G08_OBSERVATIONS) + ("independent-review",)


def _rel(paths):
    return sorted(p.relative_to(gate.ROOT).as_posix() for p in paths)


def _evidence(name: str, gate_dir: str | None = None):
    """Every `<name>.json` filed as evidence under `work/`, AT ANY DEPTH.

    Deliberately `rglob` + a parts filter rather than a fixed-depth glob such as
    `*/evidence/G08/<name>.json`. AIM HAS A DEPTH DIMENSION: this corpus already
    contains a doubled `work/WP-2026-0010/evidence/G07/G07/` directory holding EIGHT
    tracked files, so a depth-fixed pattern is provably blind to real data one level
    down. A watch that cannot see a path the repository actually contains is green for
    a reason unrelated to its trigger.
    """
    for p in WORK.rglob(f"{name}.json"):
        parts = p.parts
        if "evidence" not in parts:
            continue
        if gate_dir is not None and gate_dir not in parts:
            continue
        yield p


class DeferredTripwireTests(unittest.TestCase):
    """Four deferred re-shadows, each watched by a fact instead of by a memory."""

    def test_no_real_g09_validation_evidence_exists_yet(self):
        """GOV-0110 / #251 -- badf-release-validation.

        Its twenty control endpoints were each demonstrated load-bearing by mutation, but
        every one was exercised against FIXTURES. The caveat is honest only while no real
        G09 validation evidence exists.

        AIM PROOF: the four type names are not hardcoded here -- they are read from
        `gate.G09_TYPES` (`badf_gate.py:1992`), the same constant the gate dispatches on at
        `:2072` (V9), `:2078` (V10), `:2090` (V11) and `:2110` (V12). If the G09 vocabulary
        changes, this watch follows it instead of silently ceasing to watch.

        When this goes RED: a real quality / security / performance / resilience record has
        landed. Re-shadow badf-release-validation against it and file the result. Do not
        delete this test to make it pass.
        """
        real = _rel(p for kind in gate.G09_TYPES for p in _evidence(kind))
        self.assertEqual(
            [], real,
            f"real G09 validation evidence now exists ({real}); the fixture-only caveat on "
            f"badf-release-validation (#251) is no longer true and the real re-shadow is owed")

    def test_no_typed_g08_evidence_carries_a_binding_yet(self):
        """GOV-0093 / #217 -- badf-engineering-verification, ACTIVE with four caveats (#214).

        THE TRIGGER HAS TWO ARMS and this watches both:
          (a) a typed G08 observation or independent-review WITH A BINDING, or
          (b) a verification record.

        ARM (a) CANNOT BE KEYED ON EXISTENCE. All four types already exist under
        `work/WP-2026-0010/evidence/G08/` -- the VER-D shadow's own corpus -- so an
        existence-keyed watch is red the day it lands. The discriminator the issue states is
        the `binding`.

        AND IT IS GREEN FOR THE RIGHT REASON, which is the next question a reader asks: all
        four pre-existing objects were inspected and NONE carries a `binding` key. Green
        because the thing watched for is genuinely absent, not because the watch looks where
        it never appears.

        ARM (b) CAN be existence-keyed, and only that one can: verification records exist
        elsewhere in the tree (schema + fixtures under `examples/`) but there are ZERO under
        `work/`, which is where a real one lands.

        AIM PROOF (depth included -- this scans any depth under `work/`, because the tree
        already contains a doubled `evidence/G07/G07/` directory with eight tracked files):
        arm (a)'s types come from `gate.G08_OBSERVATIONS` (`badf_gate.py:2292`),
        the constant `check_g08_dossier` (`:2306`) dispatches on, plus `independent-review`
        which #217 names and that constant does not carry -- stated explicitly rather than
        folded in silently. The `binding` key is the one `check_g08_binding` (`:1933`) reads.
        Arm (b) matches the record `validate_verification_record` (`:4533`) validates via
        `check_schema("verification-record", ...)` (`:4543`).

        When this goes RED: a real verification run produced typed evidence with a binding,
        or a verification record. Re-shadow badf-engineering-verification and discharge the
        four caveats on the ACTIVE admission. Do not delete this test to make it pass.
        """
        bound = _rel(
            p
            for kind in G08_TYPED
            for p in _evidence(kind, "G08")
            if "binding" in json.loads(p.read_text(encoding="utf-8"))
        )
        records = _rel(WORK.rglob("verification-record*.json"))
        self.assertEqual(
            ([], []), (bound, records),
            f"typed G08 evidence now carries a binding ({bound}) or a verification record "
            f"landed ({records}); the four caveats on badf-engineering-verification's ACTIVE "
            f"admission (#217 / #214) are dischargeable")

    def test_no_real_security_composition_matrix_exists_yet(self):
        """GOV-0068 / #166 -- badf-security-design, ACTIVE on a REPRESENTATIVE shadow.

        BADF is a governance framework with no UX / API / authorization / threat surface of
        its own, so the shadow ran on a declared representative product. This issue was filed
        so the caveat "does not silently become permanent" -- and the mechanism guarding it
        was itself prose. Its own docstring says the trigger "is prose and has waited on a
        human noticing".

        AIM PROOF: `validate_security_composition` (`badf_gate.py:4814`) validates exactly
        this document via `check_schema("security-composition", rec)` (`:4826`). A real matrix
        is a `security-composition` document, and real documents land under `work/`.

        When this goes RED: a real project produced a genuine matrix. Run the real re-shadow
        and discharge the representative caveat in
        `skills/badf-security-design/references/shadow-evidence.md`. Do not delete this test.
        """
        real = _rel(WORK.rglob("security-composition*.json"))
        self.assertEqual(
            [], real,
            f"a real security-composition matrix now exists ({real}); the representative caveat "
            f"on badf-security-design (#166) is no longer true and the real re-shadow is owed")

    def test_no_real_g06_plan_exists_yet(self):
        """GOV-0078 / #185 -- badf-implementation-plan, ACTIVE on a REPRESENTATIVE shadow.

        BADF's own work packages are governance work, not product implementation plans that
        pass through G06. Every G06 artifact in the tree is a fixture under `examples/`.

        AIM PROOF: G06's plan document is the `work-breakdown`, validated at
        `badf_gate.py:1607` via `check_schema("work-breakdown", doc)` with its own emptiness
        and dependency rules at `:1611`-`:1619`. This watch scans the `evidence/G06/`
        directory a real one lands in rather than the schema name, because the trigger is
        "a real project plans through G06", not "a work-breakdown validates".

        THIS FIRES EARLY, ON PURPOSE, AND THE MESSAGE SAYS SO. It watches for ANY artifact
        under `work/*/evidence/G06/`, not specifically a work-breakdown with genuine change
        classes, budgets and a dependency graph. A watch that fires early costs one read; one
        that fires late costs the thing this file exists to prevent. So the red does not
        assert the re-shadow is owed -- it asserts something appeared that a human must
        classify.

        Do not delete this test to make it pass.
        """
        appeared = _rel(p for p in WORK.rglob("*.json")
                        if "evidence" in p.parts and "G06" in p.parts)
        self.assertEqual(
            [], appeared,
            f"a G06 artifact appeared under work/ ({appeared}) -- CHECK WHETHER IT IS A FULL "
            f"WORK-BREAKDOWN. If it is, badf-implementation-plan's representative caveat (#185) "
            f"is false and the real re-shadow is owed; if it is not, widen this predicate")

    def test_real_evidence_is_bound_only_from_under_work(self):
        """THE CONVENTION THE OTHER FOUR REST ON -- and the reason this file is five tests.

        Each of the four above decides "is it real?" by asking "is it under `work/`?". That
        makes the question a path fact rather than a content judgement, which is the only
        reason the four can be mechanical at all.

        WHAT THIS ASSERTS, AND WHAT IT DOES NOT. It asserts one direction only: no dossier
        binds evidence from OUTSIDE `work/`. It does NOT enumerate where fixtures live, and
        a reader must not infer an `examples/` | `work/` binary from it -- `templates/`
        holds a `work-package.json` too, a third fixture home outside both. That is
        harmless here (a template carries no evidence bindings, and the measured basis is
        unaffected) but an assertion about a convention has to state its universe, or the
        next reader inherits a two-way split that was never true.

        It is also a single shared point of failure. If a dossier ever binds an artifact from
        outside `work/`, the fixture / real split stops holding -- and the four above would go
        on passing, because they would be scanning the wrong place. Green, and green meaning
        nothing. A convention four tests depend on is not something to leave in a docstring: a
        fact stated in prose is available, a fact enforced by a test is unavoidable.

        AIM PROOF: `evidence[].path` is the field the gate itself resolves -- read at
        `badf_gate.py:1161` (`safe_repo_path(item["path"], ...)` in `_sibling_artifact`),
        indexed at `:4699` (`indexed[item["type"]] = item["path"]`) and resolved again at
        `:4743`. This watch reads the same field from the same documents.

        When this goes RED: a dossier binds evidence from outside `work/`. Fix the binding, or
        -- if the layout genuinely changed -- update the four scans above IN THE SAME CHANGE,
        because until then they are watching nothing.
        """
        stray = []
        dossiers = sorted(WORK.glob("*/gate-dossier.*.json"))
        for p in dossiers:
            for item in (json.loads(p.read_text(encoding="utf-8")).get("evidence") or []):
                path = item.get("path", "")
                if path and not path.startswith("work/"):
                    stray.append(f"{p.relative_to(gate.ROOT).as_posix()} -> {path}")
        self.assertEqual(
            [], sorted(stray),
            f"a dossier binds evidence from outside work/ ({sorted(stray)}); the fixture-vs-real "
            f"path convention no longer holds, so the deferred-re-shadow tripwires in this file "
            f"are scanning the wrong tree and their green means nothing")
        self.assertTrue(dossiers, "no dossiers found under work/ -- this test is watching nothing")


if __name__ == "__main__":
    unittest.main()
