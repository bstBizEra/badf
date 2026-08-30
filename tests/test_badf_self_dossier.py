"""Self-work-package dossiers (BADF-WP-0033, Issue #28).

Every BADF work package merged on CI plus traceability without a gate
dossier; authority validation and evidence binding were exercised only for
foreign work. `self-dossier <WP>` assembles a G07 dossier for BADF's OWN work
from measured evidence, as a HUMAN_REQUIRED request. The source-change diff
is taken against HEAD, excluding the work package's own directory and the
lockfile, so it is the same on the branch, in the composed tree and on main
after the squash -- and committing the dossier does not change it. Every test
runs the real gate in a scratch clone.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

def authorized_demand(root, demand_id="BADF-DEM-0001"):
    """C1 (BLD-I03, WP-2026-0099): a scratch request needs a demand AUTHORIZED by a human."""
    import json as _json
    src = _json.loads((root / "badf/demands/BADF-DEM-0001.json").read_text(encoding="utf-8"))
    src["demand_id"] = demand_id; src["status"] = "AUTHORIZED"; src["authorized_by"] = {"principal": "operator", "principal_type": "human"}
    (root / "badf/demands" / f"{demand_id}.json").write_text(_json.dumps(src, indent=2) + "\n", encoding="utf-8")


WP = "WP-2026-0999"


class SelfDossierScratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "badf"
        self.base = seed_clone(self.root, carry_working_state=True)
        self.env = {k: v for k, v in {**__import__("os").environ}.items() if not k.startswith("BADF_")}
        # Normalise the inherited ledger: in the composed world this WP has landed
        # and is LANDED_UNRECONCILED, so a new scratch WP would trip the gate's
        # "reconcile before opening a new one" rule inside validate_repo. Keep only
        # the records origin/main's tree carries; the test adds its own afterward.
        on_ledger = set(self.git("ls-tree", "-r", "--name-only", "origin/main", "--", "work/").splitlines())
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            if rec.relative_to(self.root).as_posix() not in on_ledger:
                shutil.rmtree(rec.parent)
        # ...and reconcile any that the ledger shows landed (in the composed world
        # this very work package is landed-unreconciled), so no debt blocks a new
        # scratch record. reconcile refuses non-landed/foreign records -- ignored.
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            subprocess.run([sys.executable, "scripts/badf_gate.py", "reconcile", rec.parent.name],
                           cwd=self.root, env=self.env, capture_output=True)
        # a real deliverable change on a TRACKED, UNLOCKED file (README is not in
        # INTEGRITY_PATHS), so a later tamper reaches the diff check rather than
        # tripping integrity first.
        (self.root / "README.md").write_text((self.root / "README.md").read_text() + "\n<!-- WP-0999 deliverable -->\n")
        self.git("add", "README.md"); self.commit("deliverable")
        d = self.root / "work" / WP; d.mkdir(parents=True)
        rec = {"$schema": "../../schemas/work-package.schema.json", "schema_version": "1.0.0", "id": WP,
               "title": "scratch self-dossier work package", "owner": "human_sponsor", "repository": "bstBizEra/badf",
               "demand": "BADF-DEM-0001", "objective": "x", "business_value": "x", "in_scope": ["x"], "out_of_scope": ["y"],
               "target_gate": "G07", "change_class": "C2", "data_classification": "internal",
               "acceptance_criteria": ["x"], "permissions": ["write: bstBizEra/badf via PR"], "tests": ["t"],
               "evidence": ["source-change"], "rollback": {"reversible": True, "method": "revert"},
               "status": "IN_PROGRESS", "external_target": {"repository": "bstBizEra/badf", "branch": "main", "base_revision": self.base}}
        (d / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")
        authorized_demand(self.root)
        self.lock()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                              capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, msg):
        self.git("commit", "-q", "-m", msg)

    def lock(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)

    def assemble(self, wp=WP):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "self-dossier", wp],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def validate(self):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", f"work/{WP}/gate-dossier.G07.json"],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def dossier(self):
        return json.loads((self.root / "work" / WP / "gate-dossier.G07.json").read_text())


class AssembleTests(SelfDossierScratch):

    def test_assembled_dossier_is_held_with_four_bound_evidence(self):
        r = self.assemble(); self.assertEqual(r.returncode, 0, r.stderr)
        d = self.dossier()
        self.assertEqual(d["disposition"], "HUMAN_REQUIRED")
        self.assertEqual([e["type"] for e in d["evidence"]], ["source-change", "build", "unit-test", "documentation"])
        for e in d["evidence"]:
            rec = json.loads((self.root / e["path"]).read_text())
            art = self.root / rec["artifact"]
            self.assertTrue(art.is_file(), rec["artifact"])
            self.assertEqual(rec["digest"], gate.sha256(art))
        v = self.validate()
        self.assertEqual(v.returncode, 3, v.stdout + v.stderr)   # HELD
        self.assertIn("HUMAN_REQUIRED", v.stdout)

    def test_carried_condition_records_the_missing_independent_reviewer(self):
        self.assertEqual(self.assemble().returncode, 0)
        conds = self.dossier()["conditions"]
        self.assertEqual(len(conds), 1)
        self.assertEqual(conds[0]["status"], "OPEN")
        self.assertIn("independent reviewer", conds[0]["statement"].lower())
        self.assertEqual(conds[0]["closure_authority"], "quality_authority")

    def test_source_change_artifact_is_the_diff_excluding_its_own_dir_and_lockfile(self):
        self.assertEqual(self.assemble().returncode, 0)
        diff = (self.root / "work" / WP / "evidence/G07/source-change.diff").read_text()
        self.assertIn("README.md", diff)
        self.assertNotIn(f"work/{WP}/", diff, "the dossier's own directory leaked into the diff it records")
        self.assertNotIn("lockfile.json", diff)

    def test_committing_the_dossier_does_not_invalidate_it(self):
        self.assertEqual(self.assemble().returncode, 0)
        self.git("add", f"work/{WP}", "badf/lockfile.json"); self.commit("dossier")
        v = self.validate()
        self.assertEqual(v.returncode, 3, v.stdout + v.stderr)

    def test_a_committed_change_outside_the_dir_after_assembly_invalidates_the_binding(self):
        self.assertEqual(self.assemble().returncode, 0)
        (self.root / "README.md").write_text((self.root / "README.md").read_text() + "\n<!-- tamper -->\n")
        self.git("add", "README.md"); self.commit("tamper")   # README is not locked, so this reaches the diff check
        v = self.validate()
        self.assertNotEqual(v.returncode, 0, "a change after assembly still validated")
        self.assertIn("does not match", v.stderr)

    def test_flipping_to_pass_re_enters_full_validation_and_is_refused(self):
        self.assertEqual(self.assemble().returncode, 0)
        p = self.root / "work" / WP / "gate-dossier.G07.json"
        d = json.loads(p.read_text()); d["disposition"] = "PASS"; p.write_text(json.dumps(d, indent=2) + "\n")
        self.lock()
        v = self.validate()
        self.assertNotEqual(v.returncode, 0, "a self-dossier claiming PASS was accepted with unit-test NOT_RUN and no approvals")

    def test_refuses_a_work_package_with_no_change(self):
        # a fresh WP whose base is HEAD: nothing to govern
        d = self.root / "work" / "WP-2026-0998"; d.mkdir()
        rec = json.loads((self.root / "work" / WP / "work-package.json").read_text())
        rec["id"] = "WP-2026-0998"; rec["external_target"]["base_revision"] = self.git("rev-parse", "HEAD")
        (d / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n"); self.lock()
        r = self.assemble("WP-2026-0998")
        self.assertNotEqual(r.returncode, 0); self.assertIn("nothing to govern", r.stderr)

    def test_refuses_a_foreign_work_package(self):
        d = self.root / "work" / "WP-2026-0997"; d.mkdir()
        rec = json.loads((self.root / "work" / WP / "work-package.json").read_text())
        rec["id"] = "WP-2026-0997"; rec["repository"] = "bstBizEra/secb_pf"
        (d / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n"); self.lock()
        r = self.assemble("WP-2026-0997")
        self.assertNotEqual(r.returncode, 0); self.assertIn("own work only", r.stderr)


if __name__ == "__main__":
    unittest.main()
