"""Authority instance with a framework floor (BADF-WP-0023, Issue #37, BADF-DEC-0006).

badf/authority/charter.json binds an instance to the framework's authority
matrix AT THE PINNED framework_revision and may only ADD constraints: no role
removed from any change class, no class missing or invented, no reserved
action dropped, no human-reserved role opened, no rule floor lowered. There
is no downgrade acknowledgement for instances. authority.status is DERIVED
from a valid charter by derive_state, never typed. Scratch instances only.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests.test_badf_instance_validation import ValidatedInstance  # noqa: E402
from tests.test_badf_instance import git, snapshot  # noqa: E402

CHARTER = "badf/authority/charter.json"


class CharteredInstance(ValidatedInstance):

    def charter(self, path=None, **env_over):
        env = dict(self.env); env.update(env_over)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "charter", str(path or self.t)],
                              cwd=str(self.root), capture_output=True, text=True, env=env)

    def edit_charter(self, fn):
        self.edit_json(CHARTER, fn)

    def pinned_matrix(self):
        rev = self.state()["framework_revision"]
        return json.loads(git(self.root, "show", f"{rev}:badf/authority-matrix.json"))


class CharterLifecycleTests(CharteredInstance):

    def test_fresh_instance_is_unresolved_and_a_charter_resolves_it_as_a_derived_fact(self):
        r = self.instance(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("authority UNRESOLVED", r.stdout)
        r = self.charter(); self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        ch = json.loads((self.t / CHARTER).read_text()); floor = self.pinned_matrix()
        for key in ("change_classes", "reserved_actions", "human_reserved_roles", "rules"):
            self.assertEqual(ch[key], floor[key], f"default charter differs from the pinned floor on {key}")
        self.assertEqual(ch["framework_revision"], self.state()["framework_revision"])
        self.assertEqual(self.state()["authority"], {"status": "RESOLVED", "charter": CHARTER})
        self.assertEqual(gate.parse_yaml_subset((self.t / "badf/project.yaml").read_text())["authority"]["policy"], CHARTER)
        r = self.instance(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("authority RESOLVED", r.stdout)

    def test_charter_writes_exactly_the_four_governed_files(self):
        before = snapshot(self.t)
        self.assertEqual(self.charter().returncode, 0)
        after = snapshot(self.t)
        changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
        self.assertEqual(changed, {CHARTER, "badf/state.json", "badf/project.yaml", "badf/lockfile.json"})

    def test_charter_refuses_a_second_time_the_framework_and_a_drifted_instance(self):
        self.assertEqual(self.charter().returncode, 0)
        r = self.charter(); self.assertNotEqual(r.returncode, 0); self.assertIn("already", r.stderr)
        r = self.charter(self.root); self.assertNotEqual(r.returncode, 0); self.assertIn("framework", r.stderr)
        t2 = self.target(name="drifted")
        # a second repository needs its own demand; reuse the token-demand route
        from tests.test_badf_demand import demand
        (self.root / gate.DEMANDS_DIR / "BADF-DEM-0902.json").write_text(json.dumps(demand(demand_id="BADF-DEM-0902", kind="token", source={"repository": "bstBizEra/drifted", "token": "[WP-0001]", "url": None})))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        self.assertEqual(self.init(self.intent(t2, repository="bstBizEra/drifted", demand="BADF-DEM-0902")).returncode, 0)
        (t2 / "badf/state.json").write_text("{}\n"); before = snapshot(t2)
        r = self.charter(t2); self.assertNotEqual(r.returncode, 0, "a charter was written onto a drifted instance"); self.assertIn("drift", r.stderr)
        self.assertEqual(snapshot(t2), before, "charter wrote something after refusing")


class CharterFloorTests(CharteredInstance):
    def setUp(self):
        super().setUp()
        assert self.charter().returncode == 0

    def test_removing_a_role_is_refused_and_no_acknowledgement_admits_it(self):
        self.edit_charter(lambda c: c["change_classes"]["C3"]["required_roles"].remove("security_authority"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0, "a charter below the framework floor passed")
        self.assertIn("lowers the framework floor", r.stderr); self.assertIn("security_authority", r.stderr)
        r = self.instance(BADF_AUTHORITY_DOWNGRADE_ACK="BADF-DEC-0001")
        self.assertNotEqual(r.returncode, 0, "an acknowledgement admitted an instance below the floor")

    def test_removing_a_reserved_action_is_refused(self):
        self.edit_charter(lambda c: c["reserved_actions"].remove("approve-own-work"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("approve-own-work", r.stderr)

    def test_opening_a_human_reserved_role_is_refused(self):
        self.edit_charter(lambda c: c["human_reserved_roles"].remove("human_sponsor"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("human_sponsor", r.stderr)

    def test_lowering_a_rule_floor_is_refused(self):
        floor = self.pinned_matrix()
        rule = next(r for r in floor["rules"] if r.get("minimum_class") not in (None, "C0"))
        def lower(c):
            for r in c["rules"]:
                if r["action"] == rule["action"]:
                    r["minimum_class"] = "C0"
        self.edit_charter(lower); self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn(rule["action"], r.stderr)

    def test_adding_constraints_passes(self):
        def narrow(c):
            c["change_classes"]["C1"]["required_roles"].append("data_protection_officer")
            c["reserved_actions"].append("export-personal-data")
            c["human_reserved_roles"].append("data_protection_officer")
        self.edit_charter(narrow); self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("authority RESOLVED", r.stdout)

    def test_unknown_or_missing_change_class_is_refused(self):
        self.edit_charter(lambda c: c["change_classes"].update(C4={"description": "x", "required_roles": ["a"]}))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("C4", r.stderr)
        self.edit_charter(lambda c: (c["change_classes"].pop("C4"), c["change_classes"].pop("C0")))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("C0", r.stderr)

    def test_charter_bound_to_a_different_matrix_is_refused(self):
        self.edit_charter(lambda c: c.update(framework_matrix_digest="sha256:" + "0" * 64))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("bound", r.stderr)

    def test_state_must_agree_with_the_charter_in_both_directions(self):
        self.edit_json("badf/state.json", lambda d: d.update(authority={"status": "UNRESOLVED"}))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("disagrees", r.stderr)
        self.edit_json("badf/state.json", lambda d: d.update(authority={"status": "RESOLVED", "charter": CHARTER}))
        (self.t / CHARTER).unlink(); (self.t / "badf/authority").rmdir()
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0, "state claims RESOLVED with no charter")

    def test_framework_matrix_moved_since_the_pin_is_reported_not_refused(self):
        m = json.loads((self.root / "badf/authority-matrix.json").read_text())
        m["reserved_actions"].append("rotate-signing-keys")
        (self.root / "badf/authority-matrix.json").write_text(json.dumps(m, indent=2) + "\n")
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        git(self.root, "add", "-A"); git(self.root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "strengthen matrix")
        r = self.instance()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("moved since the pin", r.stdout)


if __name__ == "__main__":
    unittest.main()
