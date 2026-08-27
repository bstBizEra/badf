"""Issue #22: a work package must have a demand record. Doctrine: "No Work
Package without an Issue or authorized demand."

Measured before this existed: `badf init` created a WP from six intent
fields with no demand link; the WP schema had no demand field; both
existing WPs had none. And two facts constrain the fix: the gate makes ZERO
network calls (an Issue's existence is knowable only via the API), and
PropTech -- the intake probe -- has ZERO GitHub Issues; its demand record
is a [WP-NNNN] commit-message token.

So a demand is a RECORD IN THE TREE, badf/demands/<id>.json: the source
Issue's content exported and digest-bound, existence a file check,
forgery caught by the lockfile. Same pattern as badf/decisions/. The
GitHub Issue stays the source; the record is what the gate can verify.
Written to fail before demand records existed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.badf_gate as gate

PROPTECH = Path("/mnt/c/laragon/www/proptech")
HAVE_PROPTECH = PROPTECH.is_dir() and (PROPTECH / ".git").exists()


def demand(**over):
    d = {"schema_version": "1.0.0", "demand_id": "BADF-DEM-0900", "kind": "issue",
         "source": {"repository": "bstBizEra/badf", "issue": 900, "url": "https://github.com/bstBizEra/badf/issues/900"},
         "title": "test demand", "problem": "observed x, expected y", "authorized_by": {"principal": "operator", "principal_type": "human"},
         "recorded_at": "2026-08-28T00:00:00Z", "provenance": "EXPORTED_FROM_SOURCE", "status": "OPEN"}
    d.update(over); return d


class DemandRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = []

    def tearDown(self):
        for p in self.tmp: Path(p).unlink(missing_ok=True)

    def write(self, d):
        p = gate.ROOT / gate.DEMANDS_DIR / f"{d['demand_id']}.json"
        p.write_text(json.dumps(d)); self.tmp.append(p); return p

    def test_well_formed_demand_loads(self):
        self.write(demand())
        self.assertEqual(gate.load_demand("BADF-DEM-0900")["kind"], "issue")

    def test_demand_that_names_no_file_is_refused(self):
        with self.assertRaisesRegex(gate.ValidationError, "does not exist"):
            gate.load_demand("BADF-DEM-0999")

    def test_malformed_id_is_refused(self):
        with self.assertRaisesRegex(gate.ValidationError, "not a demand id"):
            gate.load_demand("issue-19")

    def test_demand_missing_authorizer_is_refused(self):
        d = demand(); del d["authorized_by"]; self.write(d)
        with self.assertRaisesRegex(gate.ValidationError, "missing fields: authorized_by"):
            gate.load_demand("BADF-DEM-0900")

    def test_demand_authorized_by_agent_is_refused(self):
        """A demand is where authority ENTERS the system. An agent may DISCOVER
        (kind=discovery, authorized_by absent) but may not AUTHORIZE."""
        self.write(demand(authorized_by={"principal": "orchestrator", "principal_type": "agent"}))
        with self.assertRaisesRegex(gate.ValidationError, "authorized_by must be a human"):
            gate.load_demand("BADF-DEM-0900")

    def test_reconstructed_provenance_is_allowed_but_stated(self):
        self.write(demand(provenance="RECONSTRUCTED"))
        self.assertEqual(gate.load_demand("BADF-DEM-0900")["provenance"], "RECONSTRUCTED")

    def test_unknown_provenance_is_refused(self):
        self.write(demand(provenance="assumed"))
        with self.assertRaisesRegex(gate.ValidationError, "provenance"):
            gate.load_demand("BADF-DEM-0900")

    def test_shipped_wps_all_carry_a_resolvable_demand(self):
        for w in sorted((gate.ROOT / "work").glob("WP-*/work-package.json")):
            with self.subTest(wp=w.parent.name):
                rec = json.loads(w.read_text())
                self.assertIn("demand", rec, f"{w.parent.name} has no demand")
                gate.load_demand(rec["demand"])

    def test_pre_doctrine_wps_are_reconstructed_not_invented(self):
        for wid in ("WP-2026-0001", "WP-2026-0010"):
            rec = json.loads((gate.ROOT / "work" / wid / "work-package.json").read_text())
            d = gate.load_demand(rec["demand"])
            self.assertEqual(d["provenance"], "RECONSTRUCTED", f"{wid} predates the doctrine; its demand must say so")

    def test_wp_0016_demand_is_an_export_of_issue_19(self):
        rec = json.loads((gate.ROOT / "work/WP-2026-0016/work-package.json").read_text())
        d = gate.load_demand(rec["demand"])
        self.assertEqual(d["provenance"], "EXPORTED_FROM_SOURCE")
        self.assertEqual(d["source"]["issue"], 19)


@unittest.skipUnless(HAVE_PROPTECH, "PropTech clone not present on this host")
class InitRequiresDemandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        subprocess.run(["git", "clone", "-q", str(gate.ROOT), str(self.root)], check=True)
        for rel in ("scripts/badf_gate.py", "badf", "work", "schemas"):
            src, dst = gate.ROOT / rel, self.root / rel
            if src.is_dir(): shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
            else: shutil.copy2(src, dst)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        self.intent = self.root / "intent.json"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def init(self, proj):
        self.intent.write_text(json.dumps({"project": proj}))
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "init", str(self.intent)],
                              cwd=str(self.root), capture_output=True, text=True, env=self.env)

    BASE = {"name": "PropTech", "intent": "Build a land valuation platform for Laos", "owner": "BST",
            "target": "production", "repository": "bstBizEra/proptech", "local_path": str(PROPTECH)}

    def test_init_without_demand_is_refused(self):
        r = self.init(dict(self.BASE))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("demand", r.stderr)

    def test_init_with_unresolvable_demand_is_refused(self):
        r = self.init(dict(self.BASE, demand="BADF-DEM-0999"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not exist", r.stderr)

    def test_init_with_demand_for_another_repository_is_refused(self):
        d = demand(demand_id="BADF-DEM-0901", source={"repository": "bstBizEra/secb_pf", "issue": 5, "url": "x"})
        (self.root / gate.DEMANDS_DIR / "BADF-DEM-0901.json").write_text(json.dumps(d))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True)
        r = self.init(dict(self.BASE, demand="BADF-DEM-0901"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("belongs to bstBizEra/secb_pf", r.stderr)

    def test_init_with_a_token_demand_for_a_project_without_issues_passes(self):
        """PropTech has no Issues; its demand is a [WP-NNNN] token plus who authorized it."""
        d = demand(demand_id="BADF-DEM-0902", kind="token",
                   source={"repository": "bstBizEra/proptech", "token": "[WP-0007]", "url": None},
                   title="PropTech WP-0007", problem="stated in PropTech AGENTS.md section 2")
        (self.root / gate.DEMANDS_DIR / "BADF-DEM-0902.json").write_text(json.dumps(d))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True)
        r = self.init(dict(self.BASE, demand="BADF-DEM-0902"))
        self.assertEqual(r.returncode, 0, r.stderr)
        wp = next(p for p in (self.root / "work").glob("WP-*/work-package.json") if "proptech" in p.read_text())
        self.assertEqual(json.loads(wp.read_text())["demand"], "BADF-DEM-0902")


if __name__ == "__main__":
    unittest.main()
