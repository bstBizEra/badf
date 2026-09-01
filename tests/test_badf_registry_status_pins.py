"""GOV-0094 (#218): every capability's registry status is asserted somewhere, and
every terminal capability's status is pinned EXACTLY.

The issue predicted that relaxing the last exact pin to a floor would leave a status
unpinned. Measured on `aa49a36`, **that had not happened anywhere: zero families were
floor-only at audit time.** What was unguarded is three families that never received an
assertion at all -- a different mechanism, and the one this module guards.

Past tense throughout, deliberately: **this module's own three floor assertions make that
count three, not zero**, so a present-tense reading of the audit is false of the tree
shipping it. See the note below.

The issue's original rule was "exactly ONE exact pin per capability". That is not a
property this tree has: it holds for 17 of 30 families, and enforcing it would require
deleting 20 correct pins (`badf-git` alone carries 11, each a different module
independently refusing to let the root drift). Duplicate pins are not a defect. The
rule was reframed, and the reframing accepted by the issue's author (BARCHI-3):

    clause 1  every capability carries at least one status assertion (floor OR exact)
    clause 2  every ACTIVE capability carries at least one EXACT pin

**Clause 2 was forward-looking when proposed, and this work package makes it live.**
Measured at `aa49a36`, before this module existed, ZERO families were floor-only: clause
1 and clause 2 failed on exactly the same three families, nothing in the tree told them
apart, and an edit collapsing them into one clause would have broken nothing.

That is no longer true, and **this module is the reason**. The three unasserted families
are pinned below with FLOORS, because all three are mid-ladder and clause 2 applies only
to ACTIVE capabilities. So the tree this work package produces contains the first three
real floor-only families, and the two clauses are now distinguishable on real data --
by exactly the families the guard was built to catch. The remediation supplied the
discriminator the audit could not find.

`SYNTHETIC_FLOOR_ONLY` is kept regardless: it discriminates at unit level, independent
of which families happen to be mid-ladder on any given day, and it does not become
vacuous when `badf-delivery` eventually reaches ACTIVE and grows an exact pin.

*(The first version of this docstring said "no family is floor-only" as a present-tense
claim. It was true of the tree measured and false of the tree shipped -- caught by a test
written in this same commit. Recorded rather than silently corrected: a document
asserting the state it was written against, after the change moved it, is the defect
class this repository keeps paying for.)*

Attribution is by DATA FLOW, never co-occurrence: each `["status"]` assertion is bound to
the family whose registry entry the subscripted expression was *looked up by*. Two prior
sweeps failed here -- one scoped by function and matched by regex, one credited every
family named in a crediting function -- and their failures are this module's fixtures.
"""
import ast
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
REGISTRY = ROOT / "badf/skill-registry.json"
REG_KEYS = ("skills",)


# --------------------------------------------------------------------------- instrument

def _is_registry_iter(node, aliases=()):
    """`X["skills"]`, `X.get("skills", ...)`, or a Name bound to either."""
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
       and node.slice.value in REG_KEYS:
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" \
       and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value in REG_KEYS:
        return True
    return isinstance(node, ast.Name) and node.id in aliases


def _skills_aliases(fn):
    """`sk = r.get("skills", r)` -- the iterable reached through a local name."""
    return {st.targets[0].id for st in ast.walk(fn)
            if isinstance(st, ast.Assign) and len(st.targets) == 1
            and isinstance(st.targets[0], ast.Name) and _is_registry_iter(st.value)}


def _family_from_compare(test, elt):
    """`e["name"] == "FAM"` / `e.get("name") == "FAM"` -> "FAM", either argument order."""
    for cmp_node in ast.walk(test):
        if not isinstance(cmp_node, ast.Compare) or not isinstance(cmp_node.ops[0], ast.Eq):
            continue
        for a, b in ((cmp_node.left, cmp_node.comparators[0]),
                     (cmp_node.comparators[0], cmp_node.left)):
            if not (isinstance(b, ast.Constant) and isinstance(b.value, str)):
                continue
            if isinstance(a, ast.Subscript) and isinstance(a.value, ast.Name) and a.value.id == elt \
               and isinstance(a.slice, ast.Constant) and a.slice.value == "name":
                return b.value
            if isinstance(a, ast.Call) and isinstance(a.func, ast.Attribute) and a.func.attr == "get" \
               and isinstance(a.func.value, ast.Name) and a.func.value.id == elt \
               and a.args and isinstance(a.args[0], ast.Constant) and a.args[0].value == "name":
                return b.value
    return None


def _comprehension_family(node):
    """`next(e for e in reg["skills"] if e["name"] == "FAM")` and the list-comp form."""
    gen = None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "next" and node.args:
        gen = node.args[0]
    elif isinstance(node, (ast.ListComp, ast.GeneratorExp)):
        gen = node
    if not isinstance(gen, (ast.ListComp, ast.GeneratorExp)) or not gen.generators:
        return None
    g = gen.generators[0]
    if not _is_registry_iter(g.iter) or not isinstance(g.target, ast.Name):
        return None
    for cond in g.ifs:
        fam = _family_from_compare(cond, g.target.id)
        if fam:
            return fam
    return None


def _is_name_keyed_map(node, aliases=()):
    return (isinstance(node, ast.DictComp) and bool(node.generators)
            and _is_registry_iter(node.generators[0].iter, aliases))


def _map_helpers(tree):
    """Module-level `def registry(): ... return {e["name"]: e for e in ...}`.

    The return may be wrapped -- `{...} if isinstance(sk, list) else sk` -- so the whole
    return expression is walked rather than matched at its root.
    """
    helpers = set()
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        aliases = _skills_aliases(fn)
        for r in ast.walk(fn):
            if isinstance(r, ast.Return) and r.value is not None \
               and any(_is_name_keyed_map(c, aliases) for c in ast.walk(r.value)):
                helpers.add(fn.name)
                break
    return helpers


def _const_sequences(tree):
    """Module-level `SUBSKILLS = ("a", "b", ...)` -- the source of loop-driven pins."""
    out = {}
    for st in tree.body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name) \
           and isinstance(st.value, (ast.Tuple, ast.List)) and st.value.elts \
           and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in st.value.elts):
            out[st.targets[0].id] = tuple(e.value for e in st.value.elts)
    return out


class _Scope:
    """Per-function value tracing: which registry family does each name hold?"""

    def __init__(self, helpers, const_seqs):
        self.fam_of, self.maps, self.loops = {}, set(), {}
        self.helpers, self.const_seqs = helpers, const_seqs

    def observe(self, node):
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name) \
           and isinstance(node.iter, ast.Name) and node.iter.id in self.const_seqs:
            self.loops[node.target.id] = self.const_seqs[node.iter.id]
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            return
        name, val = node.targets[0].id, node.value
        if _is_name_keyed_map(val) or (isinstance(val, ast.Call) and isinstance(val.func, ast.Name)
                                       and val.func.id in self.helpers):
            self.maps.add(name); return
        fam = _comprehension_family(val)
        if fam:
            self.fam_of[name] = fam; return
        if isinstance(val, ast.Subscript) and isinstance(val.slice, ast.Constant):
            key, base = val.slice.value, val.value
            if isinstance(base, ast.Name) and base.id in self.fam_of and isinstance(key, int):
                self.fam_of[name] = self.fam_of[base.id]; return          # entry = entries[0]
            if isinstance(base, ast.Name) and base.id in self.maps and isinstance(key, str):
                self.fam_of[name] = key; return                            # entry = by["FAM"]
            if isinstance(base, ast.Call) and isinstance(base.func, ast.Name) \
               and base.func.id in self.helpers and isinstance(key, str):
                self.fam_of[name] = key; return                            # g = registry()["FAM"]

    def family(self, node):
        """(family|families-tuple, how) for a `...["status"]` expr; (None, why) otherwise."""
        if not (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
                and node.slice.value == "status"):
            return None, None
        base = node.value
        if isinstance(base, ast.Name):
            return (self.fam_of[base.id], "var") if base.id in self.fam_of \
                else (None, f"unbound:{base.id}")
        if isinstance(base, ast.Subscript):
            outer = base.value
            if isinstance(base.slice, ast.Constant) and isinstance(base.slice.value, str):
                if isinstance(outer, ast.Name) and outer.id in self.maps:
                    return base.slice.value, "map"
                if isinstance(outer, ast.Call) and isinstance(outer.func, ast.Name) \
                   and outer.func.id in self.helpers:
                    return base.slice.value, "helper"
            if isinstance(base.slice, ast.Name) and base.slice.id in self.loops \
               and isinstance(outer, ast.Name) and outer.id in self.maps:
                return tuple(self.loops[base.slice.id]), "loop"
        return None, "unresolvable"


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return "EXACT", node.value
    if isinstance(node, (ast.Tuple, ast.List)) and node.elts \
       and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
        return "FLOOR", tuple(e.value for e in node.elts)
    return None


def scan_source(src, name="<fixture>"):
    """-> (pins, rejects). Each pin: family(str|tuple), pin(EXACT|FLOOR|NON-LITERAL), value."""
    tree = ast.parse(src)
    helpers, const_seqs = _map_helpers(tree), _const_sequences(tree)
    pins, rejects = [], []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        sc = _Scope(helpers, const_seqs)
        for stmt in ast.walk(fn):
            sc.observe(stmt)
        for call in [n for n in ast.walk(fn) if isinstance(n, ast.Call)]:
            if not (isinstance(call.func, ast.Attribute)
                    and call.func.attr in ("assertEqual", "assertIn") and len(call.args) >= 2):
                continue
            a, b = call.args[0], call.args[1]

            def record(fam, how, shape, lit):
                rec = dict(file=name, line=call.lineno, family=fam, how=how, shape=shape,
                           pin=(lit[0] if lit else "NON-LITERAL"), value=(lit[1] if lit else None))
                (pins if fam else rejects).append(rec)

            direct = False
            for subj, obj in ((a, b), (b, a)):
                fam, how = sc.family(subj)
                if how is None:
                    continue
                record(fam, how, "direct", _literal(obj))
                direct = True
                break
            if direct:
                continue
            # tuple-packed: (entry["status"], entry["risk_class"]) == ("ACTIVE", "C1")
            for subj, obj in ((a, b), (b, a)):
                if not (isinstance(subj, (ast.Tuple, ast.List)) and isinstance(obj, (ast.Tuple, ast.List))
                        and len(subj.elts) == len(obj.elts)):
                    continue
                for i, el in enumerate(subj.elts):
                    fam, how = sc.family(el)
                    if how is not None:
                        record(fam, how, f"tuple[{i}]", _literal(obj.elts[i]))
                break
    return pins, rejects


def scan_tree():
    pins, rejects = [], []
    for p in sorted(TESTS.glob("test_*.py")):
        a, b = scan_source(p.read_text(encoding="utf-8"), p.name)
        pins += a
        rejects += b
    return pins, rejects


def by_family(pins, exact_only=False):
    out = {}
    for p in pins:
        if exact_only and p["pin"] != "EXACT":
            continue
        fams = p["family"] if isinstance(p["family"], tuple) else (p["family"],)
        for f in fams:
            out.setdefault(f, []).append(p)
    return out


def registry_status():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {s["name"]: s["status"] for s in reg["skills"]}


# --------------------------------------------------------------------------- fixtures
# Source strings, not live code: `ast.parse` of THIS module sees them as string
# constants, so they never contaminate the scan of the real tree.

TUPLE_PACKED = '''
class T:
    def test_x(self):
        entries = [e for e in reg["skills"] if e.get("name") == "badf-thing"]
        entry = entries[0]
        self.assertEqual((entry["status"], entry["risk_class"]), ("IMPLEMENTED", "C1"))
'''

LOOP_DRIVEN = '''
SUBS = ("alpha", "beta")
def registry():
    r = load()
    return {s["name"]: s for s in r["skills"]}
class T:
    def test_x(self):
        by = registry()
        for name in SUBS:
            self.assertEqual(by[name]["status"], "IMPLEMENTED", name)
'''

ALIASED_ITERABLE = '''
def registry():
    r = load()
    sk = r.get("skills", r)
    return {s["name"]: s for s in sk} if isinstance(sk, list) else sk
class T:
    def test_x(self):
        g = registry()["badf-aliased"]
        self.assertEqual(g["status"], "ACTIVE")
'''

NON_REGISTRY = '''
class T:
    def test_x(self):
        conds = self.dossier()["conditions"]
        self.assertEqual(conds[0]["status"], "OPEN")
        rec = self.record_of()
        self.assertEqual(rec["status"], "CLOSED")
'''

# DECLARED SYNTHETIC. `badf-midladder` is not a capability and never was; the fixture
# is representative-by-declaration, not by sampling, and `test_the_synthetic_family_is_
# actually_synthetic` checks that -- so "synthetic" is a verified property rather than a
# comment that could quietly stop being true if a family of that name were ever added.
#
# It was written when NO REAL FAMILY WAS FLOOR-ONLY, and this work package changed that:
# the three capabilities pinned below are pinned with FLOORS, so real data now
# distinguishes clause 1 from clause 2. KEEP THIS FIXTURE ANYWAY. It discriminates at
# unit level regardless of which families happen to be mid-ladder on a given day, and it
# stays valid when badf-delivery reaches ACTIVE and grows an exact pin -- at which point
# the real discriminators disappear and this is again the only one.
#
# (An earlier version of this comment said "delete it then, not before", with a trigger
# this PR itself meets -- so a reader following it would delete what the module docstring
# preserves for a better reason. Corrected here; the same stale claim had survived on two
# other surfaces after the docstring was fixed. BADF-REV caught both.)
SYNTHETIC_FLOOR_ONLY = '''
class T:
    def test_x(self):
        entry = next(e for e in reg["skills"] if e["name"] == "badf-midladder")
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "ACTIVE"))
'''


class InstrumentTests(unittest.TestCase):
    """The control set (BADF-QA/BARCHI-3's four, plus C5). Each shape is a fixture."""

    def test_c1_resolves_a_pin_that_moved_out_of_the_contract_module(self):
        exact = by_family(scan_tree()[0], exact_only=True)
        for fam, module in (("badf-security-design", "test_badf_security_composition.py"),
                            ("badf-solution-design", "test_badf_solution_composition.py"),
                            ("badf-implementation-plan", "test_badf_g06_planning_controls.py")):
            self.assertTrue(any(p["file"] == module for p in exact.get(fam, [])),
                            f"{fam}: exact pin in {module} not resolved")

    def test_c2_resolves_a_pin_that_stayed_literal_first(self):
        exact = by_family(scan_tree()[0], exact_only=True)
        for fam, module in (("badf-build", "test_badf_build_contract.py"),
                            ("badf-engineering-verification",
                             "test_badf_engineering_verification_contract.py"),
                            ("badf-git", "test_badf_git_contract.py")):
            self.assertTrue(any(p["file"] == module for p in exact.get(fam, [])),
                            f"{fam}: literal-first pin in {module} not resolved")

    def test_c3_resolves_two_family_functions_that_co_occurrence_cannot(self):
        """Six functions name badf-git AND a subskill. No co-occurrence rule resolves them."""
        pins = scan_tree()[0]
        for module in ("test_badf_git_baseline.py", "test_badf_git_composition.py",
                       "test_badf_git_integration.py", "test_badf_git_recovery.py",
                       "test_badf_git_release.py", "test_badf_git_staleness.py"):
            here = [p for p in pins if p["file"] == module]
            self.assertTrue(any(p["family"] == "badf-git" for p in here), module)
            self.assertTrue(any(isinstance(p["family"], str) and p["family"] != "badf-git"
                                for p in here), f"{module}: subskill not resolved")

    def test_c4_rejects_status_subscripts_that_are_not_registry_lookups(self):
        pins, rejects = scan_source(NON_REGISTRY)
        self.assertEqual([], pins, "a condition/WP-record status was read as a registry pin")
        self.assertEqual(2, len(rejects))

    def test_c5_does_not_reject_a_real_pin(self):
        """C4's twin, run EXHAUSTIVELY over the closed set of test modules.

        `must reject X` is satisfied by rejecting X *and more*, so over-rejection reads
        as success -- this is the control that catches it. The must-not-reject case uses
        REAL pins from the tree, never synthetic ones: a synthetic pin would be a fixture
        testing itself (BARCHI-3).

        Sampled at n=1 it passed while saying nothing about the other 78 modules
        (BADF-REV on this PR). `tests/` is a closed enumerable set, so the honest form is
        the loop -- the same standard clause 1 holds itself to over the registry.
        """
        modules = sorted(TESTS.glob("test_*.py"))
        self.assertGreater(len(modules), 1, "the closed set must actually be enumerated")
        false_rejects, resolved = [], 0
        for m in modules:
            pins, rejects = scan_source(m.read_text(encoding="utf-8"), m.name)
            resolved += len(pins)
            false_rejects += [(m.name, r["line"], r["how"]) for r in rejects
                              if r["how"].startswith("unbound:entry")]
        self.assertEqual([], false_rejects,
                         "real registry pins rejected: "
                         + ", ".join(f"{f}:{ln}" for f, ln, _ in false_rejects))
        self.assertGreater(resolved, 0, "no pins resolved at all -- the scan is inert")

    def test_resolves_a_tuple_packed_pin(self):
        """`assertEqual((entry["status"], ...), ("IMPLEMENTED", ...))` -- an exact pin
        sitting positionally inside a tuple. Any matcher keyed on `an argument IS
        entry["status"]` misses it; it is how all six git subskills are pinned."""
        pins, _ = scan_source(TUPLE_PACKED)
        self.assertEqual(1, len(pins))
        self.assertEqual(("badf-thing", "EXACT", "IMPLEMENTED", "tuple[0]"),
                         (pins[0]["family"], pins[0]["pin"], pins[0]["value"], pins[0]["shape"]))

    def test_resolves_a_loop_driven_pin(self):
        """One assertion pinning every family in a module-level literal tuple."""
        pins, _ = scan_source(LOOP_DRIVEN)
        self.assertEqual(1, len(pins))
        self.assertEqual(("alpha", "beta"), pins[0]["family"])
        self.assertEqual("EXACT", pins[0]["pin"])

    def test_resolves_an_aliased_registry_iterable(self):
        """`sk = r.get("skills", r)` then comprehending over `sk`, returned from an IfExp."""
        pins, _ = scan_source(ALIASED_ITERABLE)
        self.assertEqual(1, len(pins))
        self.assertEqual(("badf-aliased", "EXACT", "ACTIVE"),
                         (pins[0]["family"], pins[0]["pin"], pins[0]["value"]))

    def test_argument_order_does_not_change_the_result(self):
        subject_first = 'class T:\n    def test_x(self):\n        e = next(x for x in reg["skills"] if x["name"] == "f")\n        self.assertEqual(e["status"], "ACTIVE")\n'
        literal_first = 'class T:\n    def test_x(self):\n        e = next(x for x in reg["skills"] if x["name"] == "f")\n        self.assertEqual("ACTIVE", e["status"])\n'
        a, b = scan_source(subject_first)[0], scan_source(literal_first)[0]
        self.assertEqual([(p["family"], p["pin"], p["value"]) for p in a],
                         [(p["family"], p["pin"], p["value"]) for p in b])

    def test_the_instrument_can_see_floors_at_all(self):
        """Positive control on the floor path: ANY floor-derived count is meaningless
        until the instrument is shown able to see floors at all, because `found no floors`
        and `cannot see floors` are otherwise the same observation. Stated as a property of
        floor-derived claims in general rather than of one count, since the specific claim
        it originally guarded ("no family is floor-only") was true at audit time and is
        false of the tree this module ships.

        The three modules below are the floors named in #218's own body -- so passing this
        reproduces the issue's own observation.
        """
        floors = [p for p in scan_tree()[0] if p["pin"] == "FLOOR"]
        seen = {p["file"] for p in floors}
        for module in ("test_badf_verification_evidence.py", "test_badf_verification_controls.py",
                       "test_badf_verification_shadow.py"):
            self.assertIn(module, seen, f"{module}: floor named in #218 not found")


class RegistryStatusCoverageTests(unittest.TestCase):
    """The guard itself."""

    def test_every_capability_carries_a_status_assertion(self):
        """Clause 1. A capability nothing asserts can regress or advance silently."""
        covered = by_family(scan_tree()[0])
        missing = sorted(f for f in registry_status() if f not in covered)
        self.assertEqual([], missing,
                         "capabilities with no status assertion anywhere in tests/: "
                         + ", ".join(missing))

    def test_every_active_capability_carries_an_exact_pin(self):
        """Clause 2. Terminal status is pinned exactly; mid-ladder may floor."""
        exact = by_family(scan_tree()[0], exact_only=True)
        status = registry_status()
        missing = sorted(f for f, s in status.items() if s == "ACTIVE" and f not in exact)
        self.assertEqual([], missing,
                         "ACTIVE capabilities with no EXACT status pin: " + ", ".join(missing))

    def test_the_two_clauses_are_distinguishable(self):
        """A floor must satisfy clause 1 and NOT satisfy clause 2.

        When this module was written nothing in the tree was floor-only, so the clauses
        passed and failed together on real data and only this synthetic family could tell
        them apart. This work package's own three floor assertions changed that. The
        fixture is kept because it holds the distinction independently of which families
        are mid-ladder today -- see SYNTHETIC_FLOOR_ONLY.
        """
        pins, _ = scan_source(SYNTHETIC_FLOOR_ONLY)
        covered, exact = by_family(pins), by_family(pins, exact_only=True)
        self.assertIn("badf-midladder", covered, "clause 1 must accept a floor")
        self.assertNotIn("badf-midladder", exact, "clause 2 must not count a floor as a pin")

    def test_the_synthetic_family_is_actually_synthetic(self):
        """Keeps `declared synthetic` honest. If `badf-midladder` ever became a real
        capability, SYNTHETIC_FLOOR_ONLY would silently start describing the tree and
        `test_the_two_clauses_are_distinguishable` would stop being a synthetic control
        without anyone noticing."""
        self.assertNotIn("badf-midladder", registry_status(),
                         "the synthetic fixture's family name is now a real capability; "
                         "rename the fixture so it stays synthetic")

    def test_exact_pins_agree_with_the_registry(self):
        """A pin asserting a status the registry does not carry is a stale pin."""
        status = registry_status()
        disagree = [(f, status[f], p["value"])
                    for f, ps in by_family(scan_tree()[0], exact_only=True).items()
                    if f in status for p in ps if p["value"] != status[f]]
        self.assertEqual([], disagree)


class UnpinnedCapabilityPins(unittest.TestCase):
    """The three capabilities #218's guard found unasserted, pinned here.

    `badf-delivery`, `badf-prd` and `repository-research` have no contract module of
    their own; these assertions live here until one exists. They are floors, not exact
    pins: all three are mid-ladder, and clause 2 applies only to ACTIVE capabilities.
    """

    def setUp(self):
        self.reg = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_badf_delivery_status(self):
        entry = next(e for e in self.reg["skills"] if e["name"] == "badf-delivery")
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "SHADOWED", "ACTIVE"))

    def test_badf_prd_status(self):
        entry = next(e for e in self.reg["skills"] if e["name"] == "badf-prd")
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "SHADOWED", "ACTIVE"))

    def test_repository_research_status(self):
        entry = next(e for e in self.reg["skills"] if e["name"] == "repository-research")
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "SHADOWED", "ACTIVE"))


if __name__ == "__main__":
    unittest.main()
