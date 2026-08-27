"""BADF governing work that is not BADF: the first non-self-referential proof.

WP-2026-0010 is a real secb_pf fix (branch fix/conflict-protocol-vocabulary-audit,
head 99fc259). The gate PASSED it on first contact, and every negative control
refused -- except one that only foreign work exposes: source_revision was never
RESOLVED. Every check was dossier-vs-evidence equality, so a dossier whose
dossier, evidence and approvals all agreed on the all-zeros SHA passed. For
BADF's own work the SHA was always BADF's, so this never mattered.

These tests were written to fail before the resolver existed.
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
from tests._scratch import seed_clone

WP = gate.ROOT / "work/WP-2026-0010"


def mirror_status():
    """Where is secb_pf, according to the registry, and is it HERE?

    The registry is the same source the gate reads. A test that hard-coded
    the path would drift from it. Returns (present, reason)."""
    reg = json.loads((gate.ROOT / gate.REPOSITORIES).read_text())
    entry = reg["repositories"]["bstBizEra/secb_pf"]
    path = Path(entry["local_path"])
    if entry.get("resolution") != "LOCAL_MIRROR":
        return False, f"secb_pf resolution is {entry.get('resolution')!r}, not LOCAL_MIRROR"
    top = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True)
    if top.returncode != 0:
        return False, f"LOCAL_MIRROR {path} is not present on this host (UNRESOLVABLE_HERE by design: a CI runner)"
    return True, "present"


MIRROR_PRESENT, MIRROR_REASON = mirror_status()
DOSSIER = WP / "gate-dossier.G07.json"
ZEROS = "0" * 40


def cli(dossier_path, **env_over):
    env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
    env.update(env_over)
    return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", str(dossier_path)],
                          cwd=str(gate.ROOT), capture_output=True, text=True, env=env)


class ScratchCloneMixin:
    """Every mutation happens in a scratch clone of BADF with the lockfile
    re-signed there. The first version rewrote work/ in the real tree, and
    since WP-0010 also LOCKS work/, the integrity control refused every test
    before the resolver ran -- one new control correctly blocking the tests
    of the other. Locked trees are not test fixtures."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "badf"
        seed_clone(self.root, carry_working_state=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        self.lock()
        self.wp = self.root / "work/WP-2026-0010"
        self.dossier = self.wp / "gate-dossier.G07.json"
        self.registry = self.root / gate.REPOSITORIES

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def lock(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env,
                       capture_output=True, check=True)

    def cli(self):
        self.lock()   # every mutation is re-signed, so ONLY the resolver decides
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", str(self.dossier)],
                              cwd=str(self.root), capture_output=True, text=True, env=self.env)


@unittest.skipUnless(MIRROR_PRESENT, MIRROR_REASON)
class ForeignWorkTests(ScratchCloneMixin, unittest.TestCase):
    """Skipped, with the reason named, on any host where the secb_pf mirror is
    absent -- every CI runner. That is not a gap: it is the UNRESOLVABLE_HERE
    contract, and ResolutionScopeTests below proves CI reports it as such."""

    def rewrite_revision(self, sha):
        d = json.loads(self.dossier.read_text()); d["source_revision"] = sha
        for a in d["approvals"]:
            a["revision"] = sha
        self.dossier.write_text(json.dumps(d))
        for f in (self.wp / "evidence/G07").glob("*.json"):
            e = json.loads(f.read_text()); e["source_revision"] = sha; f.write_text(json.dumps(e))

    # --- the proof: real foreign work passes -------------------------------
    def test_real_secb_pf_fix_is_approved(self):
        r = self.cli()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("rendered verdict APPROVED", r.stdout)

    # --- the bypass: a commit that does not exist ---------------------------
    def test_nonexistent_foreign_commit_is_refused_even_when_everything_agrees(self):
        self.rewrite_revision(ZEROS)
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a dossier governing a commit that does not exist PASSED")
        self.assertIn("cannot be resolved", r.stderr)

    def test_unmapped_foreign_repository_is_refused_not_skipped(self):
        d = json.loads(self.dossier.read_text()); d["target"] = "example/unmapped:main"; self.dossier.write_text(json.dumps(d))
        for f in (self.wp / "evidence/G07").glob("*.json"):
            e = json.loads(f.read_text()); e["target"] = "example/unmapped:main"; f.write_text(json.dumps(e))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not a registered repository", r.stderr)

    def test_registered_path_that_is_not_a_repo_is_refused(self):
        reg = json.loads(self.registry.read_text())
        reg["repositories"]["bstBizEra/secb_pf"]["local_path"] = self.tmp   # a dir, not a git repo
        self.registry.write_text(json.dumps(reg))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("is not a git repository", r.stderr)

    # --- the resolver must verify CONTENT, not just existence ---------------
    def test_diff_artifact_must_match_what_the_foreign_commit_actually_changed(self):
        """A real commit whose recorded diff has been swapped for another real diff."""
        diff = self.wp / "evidence/G07/source-change.diff"
        diff.write_text("diff --git a/README.md b/README.md\n--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-x\n+y\n")
        ev = self.wp / "evidence/G07/source-change.json"
        e = json.loads(ev.read_text()); e["digest"] = gate.sha256(diff); ev.write_text(json.dumps(e))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not match", r.stderr)

    # --- the target's declared base must be an ancestor of the revision -----
    def test_revision_not_descended_from_declared_base_is_refused(self):
        wp = self.wp / "work-package.json"
        w = json.loads(wp.read_text())
        w["external_target"]["base_revision"] = ZEROS
        wp.write_text(json.dumps(w))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        # Specific: an unresolvable base must be named as such. The first version
        # asserted only "base_revision", which the downstream ancestry refusal
        # also contains -- so removing this check survived mutation by fallthrough.
        self.assertIn("declared base_revision", r.stderr)
        self.assertIn("cannot be resolved", r.stderr)
        self.assertNotIn("not descended from", r.stderr)

    def test_real_base_that_is_not_an_ancestor_is_refused(self):
        """A base that EXISTS but is not on the revision's history: ancestry, not resolution."""
        wp = self.wp / "work-package.json"; w = json.loads(wp.read_text())
        # the secb_pf fix branch's own head is a real commit that is NOT an ancestor of itself's parent chain base
        other = subprocess.run(["git", "-C", "/mnt/c/laragon/www/SecB_PF", "rev-parse", "origin/main~3"],
                               capture_output=True, text=True).stdout.strip()
        w["external_target"]["base_revision"] = subprocess.run(
            ["git", "-C", "/mnt/c/laragon/www/SecB_PF", "rev-parse", "origin/fix/budget-declaration-single-line"],
            capture_output=True, text=True).stdout.strip()   # a sibling branch tip: real, not an ancestor
        wp.write_text(json.dumps(w))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not descended from", r.stderr)


if __name__ == "__main__":
    unittest.main()


class ResolutionScopeTests(ScratchCloneMixin, unittest.TestCase):
    """Where the gate runs decides what it can resolve. On a CI runner no
    LOCAL_MIRROR exists; that must surface as UNRESOLVABLE_HERE, not as a
    refusal of the work."""

    def test_local_mirror_absent_on_this_host_is_named_not_masked(self):
        reg = json.loads(self.registry.read_text())
        reg["repositories"]["bstBizEra/secb_pf"]["local_path"] = "/nonexistent/mirror/secb_pf"
        self.registry.write_text(json.dumps(reg))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("UNRESOLVABLE_HERE", r.stderr)
        self.assertNotIn("not a git repository", r.stderr)

    def test_mirror_absence_is_declared_not_silent(self):
        """On a host without the mirror, the skip above must be for the registry's
        stated reason. A skip with any other reason -- or none -- is a silent
        green, which is the failure mode this framework exists to refuse."""
        present, reason = mirror_status()
        if present:
            self.skipTest("mirror present: the foreign suite ran instead")
        self.assertIn("UNRESOLVABLE_HERE", reason)
        self.assertIn("not present on this host", reason)

    def test_repository_without_resolution_field_is_refused(self):
        reg = json.loads(self.registry.read_text())
        del reg["repositories"]["bstBizEra/secb_pf"]["resolution"]
        self.registry.write_text(json.dumps(reg))
        r = self.cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("declares no valid resolution", r.stderr)


if __name__ == "__main__":
    unittest.main()
