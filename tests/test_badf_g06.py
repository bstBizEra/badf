"""G06 evidence contract (BADF-WP-0067; the gate march reaches implementation planning).

G06's four required evidence types have semantics the gate enforces by opening the
artifact, inside validate_evidence, each mapping to a G06 exit criterion: work is
bounded and its composition order is a real (acyclic) order (a cyclic or empty
work-breakdown is refused); tests are planned before build (an empty test-plan, or a
planned test that targets nothing, is refused); environments and resources are ready
(a release-plan with no environments or no steps is refused); and rollback plus stop
conditions are executable (a rollback-plan with no method or no stop conditions is
refused). Every test runs the real CLI on the shipped G06 example, mutated in a scratch
clone -- the faithful-runner shape.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

DOSSIER = "examples/gate-dossier.G06.json"
EV = "examples/evidence/G06"


class G06Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        seed_clone(self.root, carry_working_state=True)
        for rel in ("schemas", "tests"):
            shutil.rmtree(self.root / rel, ignore_errors=True); shutil.copytree(gate.ROOT / rel, self.root / rel)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", DOSSIER], cwd=self.root, env=self.env, capture_output=True, text=True)

    def artifact(self, t):
        return json.loads((self.root / EV / f"{t}.artifact.json").read_text())

    def rewrite(self, t, obj):
        p = self.root / EV / f"{t}.artifact.json"; p.write_text(json.dumps(obj, indent=2) + "\n")
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text())
        rec["digest"] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest(); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def refused(self, needle):
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a defective G06 dossier rendered APPROVED")
        self.assertIn(needle, r.stderr, r.stderr)


class G06ExampleTests(G06Scratch):
    def test_shipped_example_renders_approved(self):
        r = self.cli(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("APPROVED", r.stdout)

    def test_missing_required_evidence_is_still_refused(self):
        d = json.loads((self.root / DOSSIER).read_text()); d["evidence"] = [e for e in d["evidence"] if e["type"] != "rollback-plan"]
        (self.root / DOSSIER).write_text(json.dumps(d, indent=2) + "\n")
        self.refused("missing evidence")


class WorkBreakdownRuleTests(G06Scratch):
    def test_no_tasks_is_refused(self):
        wb = self.artifact("work-breakdown"); wb["tasks"] = []; self.rewrite("work-breakdown", wb)
        self.refused("an empty breakdown bounds no work")

    def test_a_task_without_a_description_is_refused(self):
        wb = self.artifact("work-breakdown"); wb["tasks"][0]["description"] = ""; self.rewrite("work-breakdown", wb)
        self.refused("has no description")

    def test_a_dangling_dependency_is_refused(self):
        wb = self.artifact("work-breakdown"); wb["tasks"][1]["depends_on"] = ["WBS-999"]; self.rewrite("work-breakdown", wb)
        self.refused("the composition order must resolve")

    def test_a_cyclic_dependency_graph_is_refused(self):
        wb = self.artifact("work-breakdown")
        wb["tasks"][0]["depends_on"] = ["WBS-002"]  # WBS-001 <-> WBS-002 cycle (WBS-002 already depends on WBS-001)
        self.rewrite("work-breakdown", wb)
        self.refused("has a cycle")


class TestPlanRuleTests(G06Scratch):
    def test_no_planned_tests_is_refused(self):
        tp = self.artifact("test-plan"); tp["planned_tests"] = []; self.rewrite("test-plan", tp)
        self.refused("cannot be established from an empty plan")

    def test_a_planned_test_that_verifies_nothing_is_refused(self):
        tp = self.artifact("test-plan"); tp["planned_tests"][0]["verifies"] = ""; self.rewrite("test-plan", tp)
        self.refused("names nothing it verifies")


class ReleasePlanRuleTests(G06Scratch):
    def test_no_environments_is_refused(self):
        rp = self.artifact("release-plan"); rp["environments"] = []; self.rewrite("release-plan", rp)
        self.refused("environments and resources must be ready")

    def test_no_steps_is_refused(self):
        rp = self.artifact("release-plan"); rp["steps"] = []; self.rewrite("release-plan", rp)
        self.refused("a release with no steps is not a plan")


class RollbackPlanRuleTests(G06Scratch):
    def test_no_method_is_refused(self):
        rb = self.artifact("rollback-plan"); rb["method"] = ""; self.rewrite("rollback-plan", rb)
        self.refused("rollback must be executable")

    def test_no_stop_conditions_is_refused(self):
        rb = self.artifact("rollback-plan"); rb["stop_conditions"] = []; self.rewrite("rollback-plan", rb)
        self.refused("a rollback plan states when to stop")


if __name__ == "__main__":
    unittest.main()
