"""Mandate section 4: `badf init` accepts a project from a four-line intent.

Measured before this existed: a second BST project could not enter BADF at
all except by an agent hand-writing a work package, three evidence files
and a dossier -- which is what WP-2026-0010 was. PropTech was the probe: a
REAL project (67 files, a 952-line mandate, its own WP admission control),
not a synthetic one, and NOT 'almost zero'.

Two rules this file enforces on init, both derived from measurement:

  1. Of 17 required WP fields, 5 are JUDGMENT (objective, business_value,
     in_scope, out_of_scope, acceptance_criteria). init must NOT fill them
     with invented prose. They are recorded DECLARED_MISSING and the G00
     dossier renders HELD until a human supplies and signs them. init is
     intake, not authoring.
  2. init writes ONLY under BADF's own tree (work/, badf/repositories.json).
     It reads the target project; it never writes to it. The target's tree
     is byte-identical after init. (PropTech's operator asked that artifacts
     be added there only when asked.)

Written to fail before `init` existed.
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

import scripts.badf_gate as gate

PROPTECH = Path("/mnt/c/laragon/www/proptech")
HAVE_PROPTECH = PROPTECH.is_dir() and (PROPTECH / ".git").exists()

INTENT = {"project": {"name": "PropTech", "intent": "Build a land valuation platform for Laos",
                      "owner": "BST", "target": "production",
                      "repository": "bstBizEra/proptech", "local_path": str(PROPTECH),
                     "demand": "BADF-DEM-0003"}}


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-s"], capture_output=True, text=True, check=True)
    h.update(out.stdout.encode())
    st = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True, check=True)
    h.update(st.stdout.encode())
    return h.hexdigest()


class InitScratchMixin:
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "badf"
        subprocess.run(["git", "clone", "-q", str(gate.ROOT), str(self.root)], check=True)
        for rel in ("scripts/badf_gate.py", "badf/repositories.json", "badf/decisions", "badf/demands", "schemas", "work"):
            src, dst = gate.ROOT / rel, self.root / rel
            if src.is_dir():
                shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        self.intent = self.root / "intent.yaml"
        self.intent.write_text(json.dumps(INTENT))   # JSON is valid YAML; no new dependency
        self._wps_before = {q.name for q in (self.root / "work").glob("WP-*")}

    def new_wp(self):
        """The one work package init added. Selecting it by excluding IDs that
        existed when a test was written broke as soon as WP-0016/0018/0019 entered
        the tree -- the exclusions picked whichever record sorted first."""
        new = sorted(q for q in (self.root / "work").glob("WP-*") if q.name not in self._wps_before)
        assert len(new) == 1, f"expected exactly one new WP, got {[q.name for q in new]}"
        return new[0]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def init(self, *extra):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "init", str(self.intent), *extra],
                              cwd=str(self.root), capture_output=True, text=True, env=self.env)


@unittest.skipUnless(HAVE_PROPTECH, "PropTech clone not present on this host")
class InitOnRealProjectTests(InitScratchMixin, unittest.TestCase):

    def test_init_never_writes_to_the_target_project(self):
        before = tree_digest(PROPTECH)
        r = self.init()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(tree_digest(PROPTECH), before, "init modified the target project's tree")

    def test_init_creates_a_work_package_with_judgment_fields_declared_missing(self):
        before = set((self.root / "work").glob("WP-*/work-package.json"))
        r = self.init(); self.assertEqual(r.returncode, 0, r.stderr)
        new = sorted(set((self.root / "work").glob("WP-*/work-package.json")) - before)
        self.assertEqual(len(new), 1, f"expected exactly one new WP, got {[str(p) for p in new]}")
        w = json.loads(new[0].read_text())
        self.assertEqual(w["status"], "DRAFT")
        self.assertEqual(w["target_gate"], "G00")
        for f in ("objective", "business_value", "in_scope", "out_of_scope", "acceptance_criteria"):
            self.assertEqual(w[f], "DECLARED_MISSING", f"{f} must not be invented")
        self.assertIn("declared_missing", w)
        self.assertEqual(set(w["declared_missing"]),
                         {"objective", "business_value", "in_scope", "out_of_scope", "acceptance_criteria"})

    def test_init_derives_change_class_c3_for_a_new_product(self):
        self.init()
        w = json.loads((self.new_wp() / "work-package.json").read_text())
        self.assertEqual(w["change_class"], "C3", "a new production product is high blast radius by the matrix's own definition")

    def test_init_registers_the_repository_as_local_mirror(self):
        self.init()
        reg = json.loads((self.root / "badf/repositories.json").read_text())["repositories"]
        self.assertIn("bstBizEra/proptech", reg)
        self.assertEqual(reg["bstBizEra/proptech"]["resolution"], "LOCAL_MIRROR")

    def test_init_reads_what_the_project_states_rather_than_inventing(self):
        """PropTech's README states a binding boundary. init must carry the
        project's own words into the WP as discovered facts, attributed."""
        self.init()
        w = json.loads((self.new_wp() / "work-package.json").read_text())
        self.assertIn("discovered", w)
        self.assertTrue(any("AGENTS.md" in d.get("source", "") for d in w["discovered"]))
        self.assertTrue(any("existing_wp_admission" in d.get("kind", "") for d in w["discovered"]),
                        "PropTech's own [WP-NNNN] admission control must be discovered, not collided with")

    def test_init_produces_a_g00_dossier_that_is_HELD_not_approved(self):
        """Evidence is PREPARED by init (producer agent). The three G00
        declarations must be SIGNED by a human before the dossier can pass.
        Until then: HELD. AUTHORIZE is a gate outcome, not a chat message."""
        r = self.init(); self.assertEqual(r.returncode, 0, r.stderr)
        d = (self.new_wp() / "gate-dossier.G00.json")
        dossier = json.loads(d.read_text())
        self.assertEqual(dossier["disposition"], "HUMAN_REQUIRED")
        self.assertEqual(dossier["approvals"], [])
        v = subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", str(d)],
                           cwd=str(self.root), capture_output=True, text=True, env=self.env)
        self.assertEqual(v.returncode, 3, v.stdout + v.stderr)   # HELD
        self.assertIn("HUMAN_REQUIRED", v.stdout)

    def test_init_is_idempotent_and_refuses_to_overwrite(self):
        self.init()
        r2 = self.init()
        self.assertNotEqual(r2.returncode, 0)
        self.assertIn("already", r2.stderr.lower())

    def test_init_records_itself_in_the_run_ledger(self):
        self.init()
        wp_dir = self.new_wp()
        ev = gate.read_ledger(wp_dir)
        self.assertGreaterEqual(len(ev), 1)
        self.assertEqual(ev[0]["step"], "init")
        self.assertEqual(ev[0]["actor"]["type"], "controller")


class InitRefusalTests(InitScratchMixin, unittest.TestCase):
    """deny-unless-established, without needing PropTech present"""

    def test_missing_required_intent_field_is_refused(self):
        self.intent.write_text(json.dumps({"project": {"name": "X", "intent": "y"}}))
        r = self.init()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("owner", r.stderr)

    def test_unregistrable_local_path_is_refused(self):
        bad = dict(INTENT); bad["project"] = dict(INTENT["project"], local_path="/nonexistent/path")
        self.intent.write_text(json.dumps(bad))
        r = self.init()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not a git repository", r.stderr)

    def test_target_other_than_production_or_sandbox_is_refused(self):
        bad = dict(INTENT); bad["project"] = dict(INTENT["project"], target="whatever")
        self.intent.write_text(json.dumps(bad))
        r = self.init()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("target", r.stderr)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAVE_PROPTECH, "PropTech clone not present on this host")
class HeldDossierCannotBeLaunderedTests(InitScratchMixin, unittest.TestCase):
    """A HUMAN_REQUIRED dossier's evidence is PREPARED, not proven. The gate
    holds it without validating outcomes. That must not be a laundering path:
    flipping the disposition to PASS re-enters full validation and the
    unsigned declarations are refused."""

    def _g00(self):
        self.init()
        return (self.new_wp() / "gate-dossier.G00.json")

    def _validate(self, path):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", str(path)],
                              cwd=str(self.root), capture_output=True, text=True, env=self.env)

    def _laundered(self, with_approvals=False, with_council=False):
        d = self._g00(); doc = json.loads(d.read_text())
        doc["disposition"] = "PASS"
        if with_approvals:
            doc["approvals"] = [{"role": r, "decision": "APPROVED", "by": f"human-{i}", "principal_type": "human",
                                 "revision": doc["source_revision"], "policy_epoch": doc["policy_epoch"],
                                 "approved_at": "2026-08-28T00:00:00Z"}
                                for i, r in enumerate(["human_sponsor", "security_authority", "release_authority", "service_owner"])]
        if with_council:
            doc["council"] = {"convened_at": "2026-08-28T00:00:00Z", "verdict": "APPROVE",
                              "ballots": [{"by": f"c-{i}", "principal_type": "agent", "verdict": "APPROVE", "sealed": True} for i in range(2)]}
        d.write_text(json.dumps(doc))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True)
        return self._validate(d)

    def test_laundering_is_stopped_by_three_layers_in_order(self):
        """Flipping HELD -> PASS on an init-produced dossier is refused by
        AUTHORITY (no approvals), then COUNCIL (C3 + restricted => challenge
        required, no record), then EVIDENCE (declarations unsigned). Each is
        proven by satisfying the layers before it. A first version of this
        test asserted only on the last layer and passed by fallthrough."""
        r = self._laundered()
        self.assertNotEqual(r.returncode, 0); self.assertIn("requires approvals from", r.stderr)
        r = self._laundered(with_approvals=True)
        self.assertNotEqual(r.returncode, 0); self.assertIn("CHALLENGE_REQUIRED", r.stderr); self.assertIn("no council record", r.stderr)
        r = self._laundered(with_approvals=True, with_council=True)
        self.assertNotEqual(r.returncode, 0); self.assertIn("outcome is not PASS", r.stderr)

    def test_held_dossier_with_a_tampered_artifact_is_still_refused(self):
        """Held does not mean unchecked: a request cannot point at a forged file."""
        d = self._g00()
        art = next((d.parent / "evidence/G00").glob("authority.txt"))
        art.write_text(art.read_text() + "tampered\n")
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True)
        r = self._validate(d)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("digest mismatch", r.stderr)

    def test_held_dossier_renders_exactly_HUMAN_REQUIRED(self):
        d = self._g00()
        r = self._validate(d)
        self.assertEqual(r.returncode, 3)
        self.assertIn("rendered verdict HUMAN_REQUIRED", r.stdout)


@unittest.skipUnless(HAVE_PROPTECH, "PropTech clone not present on this host")
class InitGuardsAreIndependentTests(InitScratchMixin, unittest.TestCase):
    """Two guards refuse a second init: the registry entry, and an existing
    WP for the same repository. Mutation showed each MASKS the other -- strip
    one and the other still refuses, so a single idempotency test cannot
    tell them apart. Each guard gets a test that reaches it exclusively."""

    def test_registry_guard_alone_refuses(self):
        """Repo registered, but NO work package exists for it (simulate a
        registry entry added by hand): the registry guard must fire."""
        reg = self.root / gate.REPOSITORIES
        r = json.loads(reg.read_text()); r["repositories"]["bstBizEra/proptech"] = {
            "local_path": str(PROPTECH), "default_branch": "main", "resolution": "LOCAL_MIRROR"}
        reg.write_text(json.dumps(r))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True)
        out = self.init()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("already registered", out.stderr)

    def test_wp_guard_alone_refuses(self):
        """A work package for the repo exists, but the repo is NOT in the
        registry (simulate a registry entry removed): the WP guard must fire."""
        self.assertEqual(self.init().returncode, 0)
        reg = self.root / gate.REPOSITORIES
        r = json.loads(reg.read_text()); del r["repositories"]["bstBizEra/proptech"]
        reg.write_text(json.dumps(r))
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True)
        out = self.init()
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("already has work package", out.stderr)
