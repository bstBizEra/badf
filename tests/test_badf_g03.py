"""G03 evidence contract (BADF-WP-0042, Issue #72; the gate march after G02).

G03's four required evidence types have semantics the gate enforces by opening
the artifact, inside validate_evidence: journeys that design both a happy and an
unhappy path; a service blueprint that covers every journey and no unknown one,
each lane with support actions; accessibility criteria under a declared standard,
each met or justified not-applicable; and a human user-validation with real
participants and every major finding resolved. Every test runs the real CLI on
the shipped G03 example, mutated in a scratch clone -- the faithful-runner shape.
"""

# Rung A (#265, WP-2026-0138): SHADOWED, nothing stronger to re-point at. The control is
# bare list-truthiness, so `minItems: 1` is EXACTLY equivalent and now refuses first.
# The control is RETAINED (criterion 5) and is now unreachable on this path; recorded
# rather than silently re-worded, per SARCHI C2. Disposition deferred, not decided.
# Rung A (#265, WP-2026-0138): probe moved from the empty form to the whitespace form.
# `minLength`/`minItems` are LENGTH bounds and admit "   "; this control uses .strip()
# and is STRICTLY STRONGER, so the re-pointed probe still exercises the control itself.
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

DOSSIER = "examples/gate-dossier.G03.json"
EV = "examples/evidence/G03"


class G03Scratch(unittest.TestCase):
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

    def record(self, t, fn):
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text()); fn(rec); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def refused(self, needle):
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a defective G03 dossier rendered APPROVED")
        self.assertIn(needle, r.stderr, r.stderr)


class G03ExampleTests(G03Scratch):

    def test_shipped_example_renders_approved(self):
        r = self.cli(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("APPROVED", r.stdout)

    def test_missing_required_evidence_is_still_refused(self):
        d = json.loads((self.root / DOSSIER).read_text()); d["evidence"] = [e for e in d["evidence"] if e["type"] != "journeys"]
        (self.root / DOSSIER).write_text(json.dumps(d, indent=2) + "\n")
        self.refused("missing evidence")


class JourneysRuleTests(G03Scratch):

    def test_only_a_happy_path_is_refused(self):
        j = self.artifact("journeys")
        for jr in j["journeys"]:
            jr["path_type"] = "happy"
        self.rewrite("journeys", j)
        self.refused("no unhappy path designed")

    def test_a_journey_with_no_steps_is_refused(self):
        j = self.artifact("journeys"); j["journeys"][0]["steps"] = []; self.rewrite("journeys", j)
        self.refused("steps has 0 items")

    def test_a_duplicate_journey_id_is_refused(self):
        j = self.artifact("journeys"); j["journeys"][1]["id"] = j["journeys"][0]["id"]; self.rewrite("journeys", j)
        self.refused("duplicate journey id")


class ServiceBlueprintRuleTests(G03Scratch):

    def test_an_uncovered_journey_is_refused(self):
        b = self.artifact("service-blueprint"); b["lanes"] = [b["lanes"][0]]; self.rewrite("service-blueprint", b)
        self.refused("uncovered journey")

    def test_a_lane_for_an_unknown_journey_is_refused(self):
        b = self.artifact("service-blueprint")
        b["lanes"].append({"journey": "JRN-404", "frontstage": ["x"], "backstage": ["y"], "support_actions": ["z"]})
        self.rewrite("service-blueprint", b)
        self.refused("absent from the journeys artifact")

    def test_a_lane_without_support_actions_is_refused(self):
        b = self.artifact("service-blueprint"); b["lanes"][0]["support_actions"] = []; self.rewrite("service-blueprint", b)
        self.refused("defines no support actions")


class AccessibilityRuleTests(G03Scratch):

    def test_a_not_applicable_criterion_without_a_rationale_is_refused(self):
        a = self.artifact("accessibility")
        a["criteria"].append({"id": "A11Y-009", "requirement": "screen-reader labels", "status": "not_applicable"})
        self.rewrite("accessibility", a)
        self.refused("not_applicable without a rationale")

    def test_no_declared_standard_is_refused(self):
        a = self.artifact("accessibility"); a["standard"] = "   "; self.rewrite("accessibility", a)
        self.refused("no standard declared")


class UserValidationRuleTests(G03Scratch):

    def test_zero_participants_is_refused(self):
        v = self.artifact("user-validation"); v["participants"] = 0; self.rewrite("user-validation", v)
        self.refused("positive number")

    def test_an_unresolved_major_finding_is_refused(self):
        v = self.artifact("user-validation")
        for f in v["findings"]:
            f.pop("resolution", None)
        self.rewrite("user-validation", v)
        self.refused("carries no resolution")

    def test_a_non_human_user_validation_is_refused(self):
        self.record("user-validation", lambda rec: rec.__setitem__("producer", {"id": "bot", "type": "automation"}))
        self.refused("must be produced by a human")


if __name__ == "__main__":
    unittest.main()
