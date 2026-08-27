"""Instance validation (BADF-WP-0022, Issue #35).

`badf_gate.py instance <path>` is what makes a project's badf/ governed
rather than decorative: the documents parse and pass their schemas, they
agree with each other, they agree with git (the instance's baseline commit,
the framework's own history for the pinned revision), and a per-instance
lockfile written by init corroborates every governed file. Deny unless
established. Every instance here is a scratch repository.
"""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests.test_badf_instance import InstanceScratch, git, snapshot  # noqa: E402

ZERO = "0" * 40


class ValidatedInstance(InstanceScratch):
    """A fresh instance per test, plus helpers to edit-and-resign it."""

    def setUp(self):
        super().setUp()
        self.t = self.target()
        r = self.init(self.intent(self.t))
        assert r.returncode == 0, r.stderr
        self.receipt_path = sorted((self.t / "badf/evidence/receipts").glob("init-*.json"))[0]

    def instance(self, path=None, **env_over):
        env = dict(self.env); env.update(env_over)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "instance", str(path or self.t)],
                              cwd=str(self.root), capture_output=True, text=True, env=env)

    def resign(self):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "lock", "--instance", str(self.t)],
                              cwd=str(self.root), capture_output=True, text=True, env=self.env)

    def edit_json(self, rel, fn):
        p = self.t / rel; d = json.loads(p.read_text()); fn(d); p.write_text(json.dumps(d, indent=2) + "\n")

    def edit_yaml(self, fn):
        p = self.t / "badf/project.yaml"; d = gate.parse_yaml_subset(p.read_text()); fn(d); p.write_text(gate.emit_yaml(d))

    def state(self):
        return json.loads((self.t / "badf/state.json").read_text())


class InstanceLockfileTests(ValidatedInstance):

    def test_init_writes_a_lockfile_over_the_governed_files_only(self):
        lock = json.loads((self.t / "badf/lockfile.json").read_text())
        self.assertEqual(sorted(lock["digests"]), sorted(["AGENTS.md", "badf/project.yaml", "badf/state.json",
                                                           self.receipt_path.relative_to(self.t).as_posix()]))
        for rel, digest in lock["digests"].items():
            self.assertEqual(digest, "sha256:" + hashlib.sha256((self.t / rel).read_bytes()).hexdigest(), rel)
        rec = json.loads(self.receipt_path.read_text())
        self.assertNotIn("badf/lockfile.json", [g["path"] for g in rec["generated"]], "the lockfile is not a generated claim; it is the signature")

    def test_preserved_agents_md_is_not_locked(self):
        from tests.test_badf_demand import demand
        d = demand(demand_id="BADF-DEM-0901", kind="token", source={"repository": "bstBizEra/brown", "token": "[WP-0001]", "url": None})
        (self.root / gate.DEMANDS_DIR / "BADF-DEM-0901.json").write_text(json.dumps(d))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        t3 = self.target({"AGENTS.md": "# theirs\n", "README.md": "# p\n"}, name="brown")
        r = self.init(self.intent(t3, repository="bstBizEra/brown", demand="BADF-DEM-0901")); self.assertEqual(r.returncode, 0, r.stderr)
        lock = json.loads((t3 / "badf/lockfile.json").read_text())
        self.assertNotIn("AGENTS.md", lock["digests"], "a preserved AGENTS.md is the project's file, not BADF's to lock")
        r = self.instance(t3); self.assertEqual(r.returncode, 0, r.stderr)
        (t3 / "AGENTS.md").write_text("# theirs, edited\n")
        r = self.instance(t3)
        self.assertEqual(r.returncode, 0, "a project editing its own charter was refused: " + r.stderr)
        self.assertIn("AGENTS.md changed since baseline", r.stdout)

class InstanceValidationTests(ValidatedInstance):

    def test_fresh_instance_passes_and_says_where_it_is(self):
        r = self.instance()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("BADF INSTANCE PASS", r.stdout)
        self.assertIn("G00", r.stdout); self.assertIn("INITIALIZED", r.stdout); self.assertIn("BST-PROPTECH", r.stdout)

    def test_hand_edited_state_is_refused_as_drift(self):
        self.edit_json("badf/state.json", lambda d: d["lifecycle"].update(current_gate="G12", state="APPROVED"))
        r = self.instance()
        self.assertNotEqual(r.returncode, 0, "a hand-typed G12/APPROVED passed")
        self.assertIn("drift", r.stderr)

    def test_resigned_disagreement_is_refused_on_corroboration(self):
        self.edit_json("badf/state.json", lambda d: d.update(active_work_package="WP-2026-0999"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0, "state and receipt disagree on the work package, yet passed")
        self.assertIn("disagree", r.stderr)

    def test_resigned_state_transition_without_authority_is_refused(self):
        """Re-signing does not launder a state the receipt cannot corroborate."""
        self.edit_json("badf/state.json", lambda d: d["lifecycle"].update(current_gate="G12", state="APPROVED"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0, "re-signing laundered a G12/APPROVED state")

    def test_generated_agents_md_edit_is_drift(self):
        (self.t / "AGENTS.md").write_text("# rewritten\n")
        r = self.instance()
        self.assertNotEqual(r.returncode, 0); self.assertIn("AGENTS.md", r.stderr)

    def test_baseline_commit_unknown_to_the_instance_is_refused(self):
        self.edit_json("badf/state.json", lambda d: d["derived_from"].update(baseline_commit=ZERO))
        self.edit_json(self.receipt_path.relative_to(self.t).as_posix(), lambda d: d.update(baseline_commit=ZERO))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0); self.assertIn("unknown to the instance", r.stderr)

    def test_project_yaml_and_receipt_disagreeing_is_refused(self):
        """The derived-state comparison covers every state-side field; only the
        cross-document agreement covers project.yaml vs the receipt. Both must hold."""
        self.edit_yaml(lambda d: d["project"].update(repository="bstBizEra/other"))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0, "project.yaml and the receipt disagree on the repository, yet passed")
        self.assertIn("disagree on repository", r.stderr)

    def test_baseline_commit_that_is_not_an_ancestor_of_head_is_refused(self):
        git(self.t, "checkout", "-q", "-b", "side"); (self.t / "side.txt").write_text("x\n")
        git(self.t, "add", "side.txt"); git(self.t, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "side")
        side = git(self.t, "rev-parse", "HEAD")
        git(self.t, "checkout", "-q", "-")   # back to the baseline branch; side is NOT an ancestor
        self.edit_json("badf/state.json", lambda d: d["derived_from"].update(baseline_commit=side))
        self.edit_json(self.receipt_path.relative_to(self.t).as_posix(), lambda d: d.update(baseline_commit=side))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0); self.assertIn("ancestor", r.stderr)

    def test_instance_that_moved_on_still_passes(self):
        """The baseline is an ancestor, not HEAD: a project keeps committing."""
        git(self.t, "add", "-A"); git(self.t, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "adopt BADF")
        (self.t / "src.txt").write_text("work\n"); git(self.t, "add", "src.txt")
        git(self.t, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "more work")
        r = self.instance(); self.assertEqual(r.returncode, 0, r.stderr)

    def test_framework_revision_unknown_to_this_framework_is_refused(self):
        self.edit_yaml(lambda d: d["badf"].update(framework_revision=ZERO))
        self.edit_json("badf/state.json", lambda d: d.update(framework_revision=ZERO))
        self.edit_json(self.receipt_path.relative_to(self.t).as_posix(), lambda d: d.update(framework_revision=ZERO))
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance()
        self.assertNotEqual(r.returncode, 0); self.assertIn("framework", r.stderr)

    def test_project_yaml_outside_the_subset_is_refused(self):
        (self.t / "badf/project.yaml").write_text((self.t / "badf/project.yaml").read_text() + "extra: {flow: 1}\n")
        self.assertEqual(self.resign().returncode, 0)
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("YAML subset", r.stderr)

    def test_missing_lockfile_cannot_be_established(self):
        (self.t / "badf/lockfile.json").unlink()
        r = self.instance(); self.assertNotEqual(r.returncode, 0); self.assertIn("cannot be established", r.stderr)

    def test_the_framework_is_refused_as_an_instance(self):
        r = self.instance(self.root)
        self.assertNotEqual(r.returncode, 0); self.assertIn("framework", r.stderr)

    def test_a_directory_without_an_instance_is_refused_not_initialised(self):
        empty = self.target(name="empty"); before = snapshot(empty)
        r = self.instance(empty)
        self.assertNotEqual(r.returncode, 0); self.assertIn("no instance", r.stderr)
        self.assertEqual(snapshot(empty), before, "validation wrote something")

    def test_validation_writes_nothing(self):
        before = snapshot(self.t)
        self.assertEqual(self.instance().returncode, 0)
        self.assertEqual(snapshot(self.t), before)


if __name__ == "__main__":
    unittest.main()
