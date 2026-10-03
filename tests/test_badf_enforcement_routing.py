"""AET-B S1 (WP-2026-0157): enforcement-surface routing.

docs/governance/AET_B_SUBSTRATE_DESIGN.md F1: in biztrust, the validator that held every pin could be
edited by a seat an agent may hold. In BADF, a work package that touches a pinned enforcement surface
must be C3, the class whose required roles are human-reserved. This is checked on both sides:
  - declared: `badf_gate.py repo` reads each record's expected_surfaces;
  - actual:   `badf_compose.py` reads the composed diff, so an undeclared edit is refused too.
"""
import inspect
import json
import subprocess
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import badf_gate as gate  # noqa: E402
import badf_compose as compose  # noqa: E402

PINNED = (
    ".github/workflows/badf-gates.yml",
    "AGENTS.md",
    "badf/authority-matrix.json",
    "badf/lifecycle.json",
    "badf/seats.json",
    "docs/14-agentic-engineer-team.md",
    "scripts/badf_compose.py",
    "scripts/badf_gate.py",
    "scripts/check_pr_traceability.py",
)
WP = "WP-2026-0950"   # a fixture id above the threshold; never a real record


def record(change_class, *files):
    return {"id": WP, "change_class": change_class, "expected_surfaces": {"files": list(files)}}


class PinnedSurfaces(unittest.TestCase):
    def test_the_pinned_list_is_exactly_this(self):
        """Shrinking the list is an edit to badf_gate.py, which is itself an enforcement surface."""
        self.assertEqual(gate.ENFORCEMENT_SURFACES, PINNED)
        self.assertEqual(gate.ENFORCEMENT_CLASS, "C3")
        self.assertEqual(gate.ENFORCEMENT_ROUTING_THRESHOLD, 157)

    def test_every_pinned_surface_exists(self):
        for p in PINNED:
            with self.subTest(surface=p):
                self.assertTrue((ROOT / p).is_file())

    def test_the_enforcement_class_carries_the_human_reserved_roles(self):
        matrix = json.loads((ROOT / "badf/authority-matrix.json").read_text(encoding="utf-8"))
        required = set(matrix["change_classes"][gate.ENFORCEMENT_CLASS]["required_roles"])
        self.assertTrue(set(matrix["human_reserved_roles"]) <= required,
                        "routing to a class without the human-reserved roles would route to nobody in particular")


class DeclaredSide(unittest.TestCase):
    def test_declaring_an_enforcement_surface_below_c3_is_refused(self):
        for cc in ("C0", "C1", "C2"):
            with self.subTest(change_class=cc):
                problems = gate.check_enforcement_routing(WP, record(cc, "scripts/badf_gate.py"))
                self.assertEqual(len(problems), 1)
                self.assertIn("human-reserved", problems[0])

    def test_a_glob_that_covers_an_enforcement_surface_counts(self):
        self.assertTrue(gate.check_enforcement_routing(WP, record("C1", "scripts/**")))
        self.assertTrue(gate.check_enforcement_routing(WP, record("C1", "badf/*.json")))

    def test_c3_declaring_an_enforcement_surface_passes(self):
        self.assertEqual(gate.check_enforcement_routing(WP, record("C3", "scripts/badf_gate.py")), [])

    def test_unrelated_surfaces_need_no_c3(self):
        self.assertEqual(gate.check_enforcement_routing(WP, record("C1", "docs/governance/X.md", "tests/test_x.py")), [])

    def test_grandfathered_and_sentinel_ids_are_exempt(self):
        for wp in ("WP-2026-0156", "WP-2026-0999", "WP-2026-9999"):
            with self.subTest(wp=wp):
                rec = dict(record("C1", "scripts/badf_gate.py"), id=wp)
                self.assertEqual(gate.check_enforcement_routing(wp, rec), [])

    def test_the_threshold_record_itself_is_bound(self):
        rec = dict(record("C1", "scripts/badf_gate.py"), id="WP-2026-0157")
        self.assertTrue(gate.check_enforcement_routing("WP-2026-0157", rec))


class ActualSide(unittest.TestCase):
    def test_an_undeclared_edit_is_refused_even_at_c3(self):
        problems = gate.check_enforcement_routing(WP, record("C3", "docs/x.md"), ["scripts/badf_gate.py", "docs/x.md"])
        self.assertEqual(len(problems), 1)
        self.assertIn("without declaring", problems[0])

    def test_an_undeclared_edit_below_c3_draws_both_refusals(self):
        problems = gate.check_enforcement_routing(WP, record("C1", "docs/x.md"), ["badf/seats.json"])
        self.assertEqual(len(problems), 2)

    def test_declared_and_c3_passes_on_the_diff(self):
        self.assertEqual(gate.check_enforcement_routing(WP, record("C3", "scripts/badf_gate.py"), ["scripts/badf_gate.py"]), [])


class ComposeReadsTheRealDiff(unittest.TestCase):
    """enforcement_problems runs `git diff --name-only base..head` in a real repository."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="badf-enforcement-"))
        self.addCleanup(shutil.rmtree, self.repo, True)
        self.git("init", "-q")
        self.git("config", "user.email", "t@local"); self.git("config", "user.name", "t")
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts/badf_gate.py").write_text("# gate\n", encoding="utf-8")
        (self.repo / "README.md").write_text("x\n", encoding="utf-8")
        self.base = self.commit("base")

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.repo), *a], capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, msg):
        self.git("add", "-A"); self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def candidate(self, change_class, declared, touch_gate):
        d = self.repo / "work" / WP
        d.mkdir(parents=True, exist_ok=True)
        (d / "work-package.json").write_text(json.dumps(record(change_class, *declared)), encoding="utf-8")
        if touch_gate:
            (self.repo / "scripts/badf_gate.py").write_text("# gate, edited\n", encoding="utf-8")
        else:
            (self.repo / "README.md").write_text("y\n", encoding="utf-8")
        return self.commit("candidate")

    def test_c1_editing_the_gate_undeclared_is_refused(self):
        head = self.candidate("C1", ["README.md"], touch_gate=True)
        problems = compose.enforcement_problems(self.repo, self.base, head, WP)
        self.assertEqual(len(problems), 2, problems)

    def test_c3_declared_gate_edit_passes(self):
        head = self.candidate("C3", ["scripts/badf_gate.py"], touch_gate=True)
        self.assertEqual(compose.enforcement_problems(self.repo, self.base, head, WP), [])

    def test_c1_not_touching_the_gate_passes(self):
        head = self.candidate("C1", ["README.md"], touch_gate=False)
        self.assertEqual(compose.enforcement_problems(self.repo, self.base, head, WP), [])


class Wiring(unittest.TestCase):
    """Both sides are called where they must be. Positive controls on the real call sites."""

    def test_repo_validation_runs_the_declared_side(self):
        self.assertIn("verify_enforcement_routing()", inspect.getsource(gate.validate_repo))

    def test_compose_refuses_on_the_actual_side(self):
        src = inspect.getsource(compose.compose)
        self.assertIn("enforcement_problems(work, base, composed, wp)", src)
        self.assertIn('return fail("enforcement routing: "', src)

    def test_the_real_tree_passes_and_says_so(self):
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BADF ENFORCEMENT ROUTING:", r.stdout)


if __name__ == "__main__":
    unittest.main()
