"""GIT-F (BADF-WP-0079): MERGED != VERIFIED -- reconcile verifies what actually landed.

The expected-head merge guard protects the source identity but cannot close the window
in which main moves between the last CI run and the merge. GIT-E's committed
composition record states the expected content tree; `badf_gate.py reconcile <WP>`
now reads that record from the LANDED commit's tree, computes the landed content tree
from the object store alone, and refuses a landing whose content is not the one that
was verified. No record stays backward compatible (composition_verified: false).

Also fixes GIT-E's content_tree, which used `git rm --cached` -- refused (silently, to
the helper) whenever the worktree differs from the index, which it never does inside
compose's fresh scratch and always may elsewhere.

Every fixture is a scratch clone removed in cleanup; a landing is simulated as a real
squash onto the scratch's origin/<default>.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
import badf_compose as compose  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

X = "WP-2026-9001"
TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"
RECORD_REL = f"work/{X}/evidence/G07/composition-record.json"


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


class _Landing(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-integration-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "badf"
        self.base = seed_clone(self.repo, carry_working_state=True)
        # Carried, unlanded records would be reported by the ledger; keep the fixture to what it lands.
        on_ledger = set(g(self.repo, "ls-tree", "-r", "--name-only", TARGET, "--", "work/").splitlines())
        for rec in (self.repo / "work").glob("WP-*/work-package.json"):
            if rec.relative_to(self.repo).as_posix() not in on_ledger:
                shutil.rmtree(rec.parent)
        g(self.repo, "checkout", "-q", "-b", f"wp/{X}-landing")
        template = json.loads((gate.ROOT / "work/WP-2026-0079/work-package.json").read_text(encoding="utf-8"))
        template.update(id=X, title="scratch landing", demand="BADF-DEM-0001", status="IN_PROGRESS",
                        external_target={"repository": "bstBizEra/badf", "branch": gate.DEFAULT_BRANCH, "base_revision": self.base[:7]})
        (self.repo / "work" / X).mkdir(parents=True)
        (self.repo / "work" / X / "work-package.json").write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
        (self.repo / "docs/x.md").write_text("content of X\n", encoding="utf-8")
        g(self.repo, "add", "-A"); g(self.repo, "commit", "-q", "-m", f"{X}: content")

    def write_record(self, expected_content_tree: str | None = None, raw: str | None = None) -> None:
        p = self.repo / RECORD_REL; p.parent.mkdir(parents=True, exist_ok=True)
        if raw is None:
            rec = {"record": "git-composition", "schema_version": "1.0.0", "observed_at": "2026-08-29T00:00:00Z",
                   "repository": "bstBizEra/badf", "work_package_id": X, "target_ref": f"refs/heads/{gate.DEFAULT_BRANCH}",
                   "target_base_sha": self.base, "source_ref": f"refs/heads/wp/{X}-landing", "merge_base_sha": self.base,
                   "merge_method": "squash", "expected_result_tree": "0" * 40,
                   "expected_content_tree": expected_content_tree or gate.content_tree(self.repo, X, "HEAD"),
                   "policy_epoch": None, "test_set_epoch": None, "suite_pattern": "test_*.py", "non_coverage": []}
            raw = json.dumps(rec, indent=2)
        p.write_text(raw + "\n", encoding="utf-8")
        g(self.repo, "add", "-A"); g(self.repo, "commit", "-q", "-m", f"{X}: record")

    def land(self) -> str:
        """Squash the branch onto the scratch's origin/<default>, as GitHub would."""
        g(self.repo, "checkout", "-q", "-B", gate.DEFAULT_BRANCH, TARGET)
        g(self.repo, "merge", "--squash", "-q", f"wp/{X}-landing")
        g(self.repo, "commit", "-q", "-m", f"BADF-WP-9001: landing (#0)\n\nWork-Package: {X}\nCloses #0\n")
        sha = g(self.repo, "rev-parse", "HEAD"); g(self.repo, "update-ref", TARGET, sha)
        return sha

    def reconcile(self) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "reconcile", X], cwd=str(self.repo), capture_output=True, text=True)

    def record_of(self) -> dict:
        return json.loads((self.repo / "work" / X / "work-package.json").read_text(encoding="utf-8"))


class LandedContentTests(_Landing):
    def test_reconcile_verifies_landed_content_against_the_record(self):
        self.write_record(); expected = json.loads((self.repo / RECORD_REL).read_text(encoding="utf-8"))["expected_content_tree"]
        sha = self.land(); r = self.reconcile()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertIn("composition_verified", r.stdout)
        rec = self.record_of(); t = rec["external_target"]
        self.assertEqual((rec["status"], t["landed_as"], t["landed_content_tree"], t["composition_verified"]), ("CLOSED", sha, expected, True))

    def test_reconcile_refuses_a_landing_whose_content_moved(self):
        self.write_record()
        (self.repo / "docs/y.md").write_text("landed after the claim\n", encoding="utf-8")
        g(self.repo, "add", "-A"); g(self.repo, "commit", "-q", "-m", f"{X}: more content after the claim")
        self.land(); r = self.reconcile()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stderr); self.assertIn("moved between verification and merge", r.stderr); self.assertNotIn("Traceback", r.stderr)
        rec = self.record_of(); self.assertEqual(rec["status"], "IN_PROGRESS"); self.assertNotIn("landed_as", rec["external_target"])

    def test_reconcile_without_a_record_writes_composition_verified_false(self):
        sha = self.land(); r = self.reconcile()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t = self.record_of()["external_target"]
        self.assertEqual((t["landed_as"], t["composition_verified"]), (sha, False)); self.assertNotIn("landed_content_tree", t)

    def test_reconcile_refuses_a_malformed_record_rather_than_downgrading(self):
        self.write_record(raw='{"hello": 1}'); self.land(); r = self.reconcile()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("git-composition", r.stderr)
        rec = self.record_of(); self.assertEqual(rec["status"], "IN_PROGRESS")

    def test_reconcile_reads_the_record_from_the_landed_tree_not_the_checkout(self):
        """The checkout after a landing may carry anything; the claim is what LANDED (mutation
        survivor, WP-0079: reading the checkout gave the same answer in every other fixture)."""
        self.write_record(); expected = json.loads((self.repo / RECORD_REL).read_text(encoding="utf-8"))["expected_content_tree"]
        sha = self.land()
        (self.repo / RECORD_REL).write_text('{"hello": "corrupted in the checkout only"}\n', encoding="utf-8")
        r = self.reconcile(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t = self.record_of()["external_target"]
        self.assertEqual((t["landed_as"], t["landed_content_tree"], t["composition_verified"]), (sha, expected, True))

    def test_reconcile_is_deterministic_and_reads_only(self):
        self.write_record(); self.land()
        before = (g(self.repo, "rev-parse", "HEAD"), g(self.repo, "rev-parse", TARGET), len(g(self.repo, "reflog").splitlines()),
                  hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest())
        r1 = self.reconcile(); self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr); first = self.record_of()
        self.assertEqual((g(self.repo, "rev-parse", "HEAD"), g(self.repo, "rev-parse", TARGET), len(g(self.repo, "reflog").splitlines()),
                          hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest()), before, "reconcile must not move git state")
        r2 = self.reconcile(); self.assertEqual(r2.returncode, 1); self.assertIn("already claims", r2.stderr)
        self.assertEqual(self.record_of(), first)


class ContentTreeTests(_Landing):
    def test_content_tree_has_one_home_and_compose_imports_it(self):
        self.assertTrue(hasattr(gate, "content_tree")); self.assertIs(compose.content_tree, gate.content_tree)
        src = (gate.ROOT / "scripts/badf_compose.py").read_text(encoding="utf-8")
        self.assertNotIn("def content_tree", src); self.assertIn("content_tree", src)
        self.assertNotIn("def load_composition_record", src); self.assertTrue(hasattr(gate, "load_composition_record"))

    def test_content_tree_is_independent_of_the_worktree(self):
        rev = g(self.repo, "rev-parse", "HEAD")
        at_rev = gate.content_tree(self.repo, X, rev)
        # Check out the BASE: the worktree's badf/lockfile.json and docs/ now differ from rev's index --
        # exactly the state in which `git rm --cached` refused and GIT-E's helper returned the full tree.
        g(self.repo, "checkout", "-q", "--detach", self.base)
        self.assertEqual(gate.content_tree(self.repo, X, rev), at_rev)
        self.assertNotEqual(at_rev, g(self.repo, "rev-parse", f"{rev}^{{tree}}"), "the content tree must exclude the WP dir and the lockfile")
        self.assertEqual(g(self.repo, "rev-parse", "HEAD"), self.base, "content_tree must not move HEAD")


class PullRequestIntegrationSubskillTests(unittest.TestCase):
    def test_pull_request_integration_subskill_registered_and_root_is_active(self):
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertIn("pull-request-integration", by); entry = by["pull-request-integration"]
        self.assertEqual(entry["source"], "skills/badf-git/subskills/pull-request-integration/SKILL.md")
        self.assertEqual((entry["status"], entry["risk_class"], entry["allowed_tools"]), ("IMPLEMENTED", "C1", []))
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertEqual(by["badf-git"]["status"], "ACTIVE")
        text = (gate.ROOT / entry["source"]).read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text); self.assertNotIn("Status: `", text)
        for token in ("MERGED", "VERIFIED", "composition_verified", "mergeable_state", "\"sha\"", "reconcile", "landed_content_tree"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
