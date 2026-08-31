"""Every `badf-*` family named in any skill surface resolves — or is declared future.

WP-2026-0120 / GOV (#223). BADF-REV generalized #222's badf-build-only guard across every
family surface and found two unresolved tokens: `badf-security` in badf-solution-design's
routing table (a family that has never existed, while `badf-security-design` is ACTIVE and
owns exactly that concern), and `badf-security-assurance` (a deliberate forward reference).

#223's original criterion permitted an unresolved token when the same surface labelled it
"named, not built" AT THAT USE. Measured across the real corpus, that criterion is backwards:

    badf-security-assurance (legitimate)   17 uses   14 labelled   3 BARE
    badf-security           (the defect)    1 use     1 labelled   0 bare

The defect reads `future **badf-security**` -- it satisfies the label check -- while three
legitimate uses are bare on their line. "Carries a declared-future label" is a PROXY for
"is a deliberately declared future family", and a typo satisfies the proxy simply by being
written apologetically.

So the guard reads a GOVERNED DECLARATION instead: `declared_future_families` in
badf/skill-registry.json. That is the authoritative surface for family names already
(digest-pinned, lockfile-covered), and it makes intent declared rather than inferred from
prose. The controls below NARROW the ways the list itself could become a hole; the one shape
they cannot catch is stated in the DECLARED SCOPE OF THE LIST CONTROLS block, with the
measurement that shows why no mechanism here closes it.
"""
import json
import pathlib
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

ROOT = gate.ROOT
SKILLS = ROOT / "skills"
REGISTRY = ROOT / "badf" / "skill-registry.json"

# Non-family badf-* tokens. Keep minimal: every entry is a hole in the guard.
#   "badf-sa" -- slug of the sibling BST-SA organism repo, never a skill family.
NON_FAMILY = {"badf-sa"}

# Unicode dashes an editor or a paste substitutes for U+002D. Folded before matching:
# `badf‑release‑validation` with U+2011 is the same reference a human meant to write, and
# arrives from copy-paste rather than from an adversary (BADF-QA, #259 review).
UNICODE_DASHES = "\u2010\u2011\u2012\u2013\u2014\u2212"


def _fold_dashes(text):
    for d in UNICODE_DASHES:
        text = text.replace(d, "-")
    return text


# DECLARED SCOPE OF THE MATCHER -- stated so it is a decision, not the next reviewer's finding.
#
# The scan matches `badf-<lowercase>` after folding Unicode dashes. Two forms are deliberately
# OUT of scope, and neither is an oversight:
#
#   UPPERCASE (`BADF-...`) -- measured, not assumed: case-folding this corpus surfaces
#     `BADF-QA`, `BADF-REV` (seat names), `BADF-controlled` and `BADF-native` (adjectives),
#     none of which is a family reference. Uppercase `BADF-` is an ACTIVELY USED DISTINCT
#     CONVENTION here -- roles, work-package ids, prose modifiers -- not a variant spelling of
#     a family name. Folding case would conflate two namespaces and flag four correct uses.
#     So this is not "an evasion we judged unlikely"; it is a fix that would break real usage.
#
#   UNDERSCORE (`badf_...`) -- the SCRIPT namespace: `badf_gate`, `badf_compose`,
#     `badf_id_sweep`. Measured: including it flags 62 tokens, 61 of them `badf_gate`.
#
# A family reference written in either form is not caught. That is the boundary, and closing
# it would require distinguishing intent from spelling, which the corpus does not support.

# DECLARED SCOPE OF THE LIST CONTROLS -- what the declared_future_families checks below do
# and deliberately do not close (BADF-REV's #259 pre-pass, measured, ruled in-rung):
#
#   They REFUSE: dead permission (a declared name no surface references), double registration
#   (a name both registered and declared-future), and absent or unresolvable provenance.
#
#   They CANNOT catch a typo introduced TOGETHER WITH its listing in the same edit -- that
#   shape satisfies every property by construction. Measured before declining to build a
#   closer: a similarity guard would be calibrated on a list with ONE legitimate member, and
#   no threshold separates the legitimate forward reference (0.744 to its nearest registered
#   neighbour) from the original #223 defect (0.788). A threshold tuned on n=1 is a proxy for
#   "is a typo" -- a new proxy, in the guard whose subject is that proxies are not properties.
#
#   The same-edit case is caught by REVIEW of the digest-pinned registry edit. Review does
#   that work, not this guard; the improvement this guard delivers is that the bar moved from
#   a word in prose to a governed edit under review.

SURFACES = sorted(SKILLS.rglob("*.md"))


def _scan():
    """token -> set(files), across every skills/<family>/** markdown surface."""
    found = {}
    for path in SURFACES:
        text = _fold_dashes(path.read_text(encoding="utf-8"))
        for raw in re.findall(r"badf-[a-z0-9-]+", text):
            token = raw.rstrip("-")          # a trailing hyphen can enter the match
            if token in NON_FAMILY:
                continue
            found.setdefault(token, set()).add(str(path.relative_to(ROOT)))
    return found


def _registered():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {e.get("name") for e in reg.get("skills") or []}


def _declared_future():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {e.get("name") for e in reg.get("declared_future_families") or []}


class FamilyNameResolutionTests(unittest.TestCase):
    def test_the_scan_is_not_vacuous(self):
        # Anti-vacuity, per the #229/#234 class: a guard that goes quiet when its subject
        # disappears is not a guard. These fail loudly if the corpus is moved or emptied.
        self.assertTrue(SKILLS.is_dir(), "skills/ is absent; every assertion below would pass on nothing")
        families = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
        self.assertGreaterEqual(len(families), 10, f"scanned only {len(families)} family surfaces: {families}")
        self.assertGreaterEqual(len(SURFACES), 50, f"scanned only {len(SURFACES)} markdown files under skills/")
        found = _scan()
        # the scan must have read something meaningful, not merely opened files
        for anchor in ("badf-build", "badf-solution-design", "badf-release-validation"):
            self.assertIn(anchor, found, f"the scan never found {anchor}; it read files but learned nothing")

    def test_every_family_named_in_any_surface_resolves_or_is_declared_future(self):
        found = _scan()
        permitted = _registered() | _declared_future()
        unresolved = {t: sorted(f) for t, f in found.items() if t not in permitted}
        self.assertEqual({}, unresolved,
                         "badf-* families named in a skill surface but neither registered nor listed in "
                         "declared_future_families: "
                         + "; ".join(f"{t} named in {', '.join(fs)}" for t, fs in sorted(unresolved.items())))

    def test_the_scan_itself_folds_unicode_dashes(self):
        # BADF-QA's #259 finding: U+2011 and friends arrive from paste and dash-substituting
        # editors. Asserting _fold_dashes() in isolation proves the HELPER works, not that
        # the scan is wired to it -- a mutation that dropped the fold from _scan() survived
        # exactly that test. So drive the real _scan() over a real surface file instead.
        victim = SKILLS / "badf-solution-design" / "references" / "routing.md"
        original = victim.read_text(encoding="utf-8")
        try:
            for dash in UNICODE_DASHES:
                with self.subTest(dash=hex(ord(dash))):
                    victim.write_text(original + f"\nrouted to `badf{dash}invented{dash}family`\n",
                                      encoding="utf-8")
                    self.assertIn("badf-invented-family", _scan(),
                                  f"_scan() did not fold U+{ord(dash):04X}; the guard is not wired to the fold")
        finally:
            victim.write_text(original, encoding="utf-8")
        self.assertEqual(original, victim.read_text(encoding="utf-8"), "probe did not restore the surface")

    def test_the_declared_out_of_scope_forms_are_documented_not_merely_absent(self):
        # The boundary must be STATED. A limit nobody wrote down is indistinguishable from
        # an oversight, and the next reviewer re-files it (REV's #258 ruling, adopted here).
        src = pathlib.Path(__file__).read_text(encoding="utf-8")
        # Scope the search to the module-level region ABOVE the first class. Searching the
        # whole file lets this assertion be satisfied by its own string literal -- a mutation
        # that deleted the entire scope note survived, because the needle lived in the needle.
        head = src.split("\nclass ", 1)[0]
        marker = "DECLARED" + " SCOPE OF THE MATCHER"      # split so this line is not the match
        self.assertIn(marker, head, "the scope note must live in the module region, not only in this test")
        for token in ("UPPERCASE", "UNDERSCORE", "BADF-QA", "badf_gate"):
            self.assertIn(token, head, f"the scope note must name {token}")
        # the LIST controls' boundary must be stated too, with its measurement -- a limit
        # backed by a number survives the next reviewer who has the same closing idea
        for token in ("TOGETHER WITH", "0.744", "0.788", "REVIEW of the digest-pinned"):
            self.assertIn(token, head, f"the list-controls scope note must carry {token!r}")

    def test_uppercase_prose_uses_are_not_flagged(self):
        # The reason uppercase is out of scope: these are real, correct uses in the corpus.
        # If case-folding is ever added, these four must be excluded explicitly first.
        joined = " ".join(p.read_text(encoding="utf-8") for p in SURFACES)
        for real in ("BADF-QA", "BADF-REV"):
            self.assertIn(real, joined, f"{real} should still appear in the corpus")
        found = _scan()
        for wrong in ("badf-qa", "badf-rev", "badf-controlled", "badf-native"):
            self.assertNotIn(wrong, found, f"{wrong} is prose, not a family; the scan must not see it")

    def test_declared_future_names_are_not_also_registered(self):
        # A name cannot be both built and declared-future; that would let a real family's
        # removal go unnoticed behind its own forward-reference entry.
        both = _registered() & _declared_future()
        self.assertEqual(set(), both, f"names both registered and declared-future: {sorted(both)}")

    def test_declared_future_entries_carry_their_provenance(self):
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = reg.get("declared_future_families") or []
        self.assertTrue(entries, "declared_future_families is empty; the guard's exception surface must be explicit")
        # declared_by must RESOLVE in the tree, not merely be present -- a field checked for
        # presence only is attribution-shaped without attributing (the decorative-const shape,
        # BADF-REV #259). This kills UNRESOLVABLE provenance -- an id that names nothing; it
        # deliberately does NOT catch resolvable-but-wrong provenance (copied from a real
        # entry, or a common real token like a gate id) -- see DECLARED SCOPE OF THE LIST
        # CONTROLS above for why that shape is review's to catch.
        doctrine = list(SKILLS.rglob("*.md")) + list((ROOT / "docs").rglob("*.md"))
        for e in entries:
            for field in ("name", "declared_by", "gate", "reason"):
                self.assertIn(field, e, f"declared-future entry {e.get('name','?')} is missing {field}; "
                                        "an undocumented exception is indistinguishable from a typo")
            self.assertTrue(str(e["reason"]).strip(), f"{e['name']}: empty reason")
            cited = str(e["declared_by"]).strip()
            # BADF-QA #259: an empty string is "an id that names nothing" and `"" in text`
            # is vacuously true -- assert non-emptiness BEFORE resolution, or the promise
            # above is broken by the emptiest possible input.
            self.assertTrue(cited, f"{e['name']}: empty declared_by; provenance that names "
                                   "nothing attributes nothing")
            hits = [p for p in doctrine if cited in p.read_text(encoding="utf-8")]
            self.assertTrue(hits, f"{e['name']}: declared_by '{cited}' resolves to no doctrine surface "
                                  "under skills/ or docs/ -- provenance that names nothing attributes nothing")

    def test_a_declared_future_name_is_actually_used(self):
        # An entry nobody references is dead permission: it would silently admit that name
        # anywhere, forever, including as a future typo target.
        found = _scan()
        unused = sorted(n for n in _declared_future() if n not in found)
        self.assertEqual([], unused, f"declared-future names referenced by no surface: {unused}")

    def test_the_list_controls_themselves_are_watched(self):
        # BADF-QA #259 finding 2: the declared-future controls fired once, by hand, at
        # authoring time -- nothing re-ran them, so reverting the resolution check to
        # presence-only (or the exclusivity check to an empty literal) reddened nothing.
        # These plants drive the REAL test methods against a planted-bad registry (the
        # same wiring rule as the dash test: exercise the entry point, not the helper),
        # so a neutered control fails HERE, in-suite, on every run.
        original = REGISTRY.read_bytes()

        def plant(mutate):
            reg = json.loads(original)
            mutate(reg)
            REGISTRY.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")

        probes = [
            ("a name both registered and declared-future must be refused",
             lambda reg: reg["declared_future_families"].append(
                 {"name": reg["skills"][0]["name"], "declared_by": "SEC-I14",
                  "gate": "G05", "reason": "probe"}),
             self.test_declared_future_names_are_not_also_registered),
            ("a declared name no surface references must be refused as dead permission",
             lambda reg: reg["declared_future_families"].append(
                 {"name": "badf-never-referenced-anywhere", "declared_by": "SEC-I14",
                  "gate": "G05", "reason": "probe"}),
             self.test_a_declared_future_name_is_actually_used),
            ("an EMPTY declared_by must be refused -- an id that names nothing",
             lambda reg: reg["declared_future_families"][0].update(declared_by=""),
             self.test_declared_future_entries_carry_their_provenance),
            ("an UNRESOLVABLE declared_by must be refused",
             lambda reg: reg["declared_future_families"][0].update(declared_by="SEC-I99-FABRICATED"),
             self.test_declared_future_entries_carry_their_provenance),
        ]
        try:
            for label, mutate, guard in probes:
                with self.subTest(label=label):
                    plant(mutate)
                    with self.assertRaises(AssertionError, msg=f"the guard did not notice: {label}"):
                        guard()
        finally:
            REGISTRY.write_bytes(original)
        self.assertEqual(original, REGISTRY.read_bytes(), "plant did not restore the registry")

    def test_the_security_row_routes_to_the_family_that_owns_it(self):
        # The #223 defect itself, pinned by content rather than only by the generic guard.
        routing = (SKILLS / "badf-solution-design" / "references" / "routing.md").read_text(encoding="utf-8")
        row = [ln for ln in routing.splitlines() if "security threat" in ln]
        self.assertEqual(1, len(row), f"expected exactly one security-threat routing row, found {len(row)}")
        self.assertIn("badf-security-design", row[0], "the security threat / risk decision row must route to the "
                                                      "ACTIVE family that owns it")
        self.assertNotIn("future", row[0].lower(), "badf-security-design is ACTIVE today; 'future' is stale")


if __name__ == "__main__":
    unittest.main()
