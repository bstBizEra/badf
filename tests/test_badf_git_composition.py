"""GIT-E (BADF-WP-0076): the composition claim is a committed, recomputed record.

badf-git's core invariant is SOURCE_HEAD_GREEN != INTEGRATION_SAFE and its contract
binds a nine-field composition identity -- yet CI computed all of it on every PR and
recorded none. `badf_compose.py --record` writes a git-composition record whose
binding is the CONTENT TREE (the composed tree with work/<WP>/ and the lockfile
removed), so the record can live inside the PR it verifies; compose then finds it
on the composed tree and refuses a stale base, a changed content tree, a non-squash
method, a foreign target or a malformed record. No record stays backward compatible.

Composes run the real CLI (scripts/badf_compose.py of this checkout) against scratch
clones seeded with this checkout's working state, restricted to one tiny test module.
Every fixture is removed in cleanup.
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

WP = "WP-2026-0076"
TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"
TINY = "test_badf_git_contract.py"
MESSAGE = f"## What\nx\n\n## Verification\nx\n\nWork-Package: {WP}\nCloses #144\n"


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def lock_and_commit(repo: Path, msg: str) -> str:
    subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=str(repo), capture_output=True, text=True, check=True)
    g(repo, "add", "-A"); g(repo, "commit", "-q", "-m", msg)
    return g(repo, "rev-parse", "HEAD")


class _Candidate(unittest.TestCase):
    """A scratch clone carrying this checkout's state, committed on a WP branch over origin/main."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-composition-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "badf"
        self.base = seed_clone(self.repo, carry_working_state=True)
        # The carried work/ may hold THIS checkout's own composition record and G07 dossier
        # (once WP-0076 has committed them); the scratch never carries tests/, so that record
        # cannot match the scratch's content tree -- and every test here builds its own claim.
        shutil.rmtree(self.repo / "work" / WP / "evidence", ignore_errors=True)
        (self.repo / "work" / WP / "gate-dossier.G07.json").unlink(missing_ok=True)
        g(self.repo, "checkout", "-q", "-b", f"wp/{WP}-composition")
        self.head = lock_and_commit(self.repo, f"BADF-WP-0076: candidate\n\nWork-Package: {WP}\n")
        self.msg = self.tmp / "msg.txt"; self.msg.write_text(MESSAGE, encoding="utf-8")
        self.record = self.repo / "work" / WP / "evidence/G07/composition-record.json"

    def run_compose(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "scripts/badf_compose.py", "--repo", str(self.repo), "--base", TARGET,
                               "--candidate", "HEAD", "--message-file", str(self.msg), "--tests", TINY, *extra],
                              cwd=str(gate.ROOT), capture_output=True, text=True)

    def make_record(self, dest: Path | None = None) -> dict:
        dest = dest or self.record
        r = self.run_compose("--record", str(dest))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(dest.is_file(), "the record was not written")
        return json.loads(dest.read_text(encoding="utf-8"))


class CompositionRecordTests(_Candidate):
    def test_record_binds_the_composition_tuple(self):
        rec = self.make_record()
        self.assertEqual(rec["record"], "git-composition")
        for k in ("schema_version", "observed_at", "repository", "target_ref", "target_base_sha", "source_ref", "merge_base_sha",
                  "merge_method", "expected_result_tree", "expected_content_tree", "policy_epoch", "test_set_epoch",
                  "suite_pattern", "work_package_id", "non_coverage"):
            self.assertIn(k, rec, k)
        self.assertEqual(rec["target_ref"], f"refs/heads/{gate.DEFAULT_BRANCH}")
        self.assertEqual(rec["target_base_sha"], self.base); self.assertEqual(rec["merge_base_sha"], self.base)
        self.assertEqual(rec["merge_method"], "squash"); self.assertEqual(rec["work_package_id"], WP)
        self.assertEqual(rec["source_ref"], f"refs/heads/wp/{WP}-composition")
        self.assertRegex(rec["expected_content_tree"], r"^[0-9a-f]{40}$"); self.assertRegex(rec["expected_result_tree"], r"^[0-9a-f]{40}$")
        self.assertNotEqual(rec["expected_content_tree"], rec["expected_result_tree"])
        self.assertIsNone(rec["test_set_epoch"]); self.assertTrue(any("test_set_epoch" in n for n in rec["non_coverage"]))

    def test_content_tree_excludes_own_work_dir_and_lockfile(self):
        t0 = compose.content_tree(self.repo, WP)
        (self.repo / "work" / WP / "evidence").mkdir(parents=True, exist_ok=True)
        (self.repo / "work" / WP / "evidence/extra.txt").write_text("extra\n", encoding="utf-8")
        lock_and_commit(self.repo, "own dir + lockfile only")
        self.assertEqual(compose.content_tree(self.repo, WP), t0, "the WP's own directory and the lockfile must not move the content tree")
        (self.repo / "README.md").write_text("content changed\n", encoding="utf-8")
        lock_and_commit(self.repo, "content changed")
        self.assertNotEqual(compose.content_tree(self.repo, WP), t0)

    def test_current_record_composes_PASS(self):
        self.make_record(); lock_and_commit(self.repo, "record")
        r = self.run_compose()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("composition: CURRENT", r.stdout); self.assertIn("BADF COMPOSE PASS", r.stdout)

    def test_adding_record_lockfile_and_work_dir_keeps_record_current(self):
        self.make_record()
        (self.repo / "work" / WP / "evidence/G07").mkdir(parents=True, exist_ok=True)
        (self.repo / "work" / WP / "evidence/G07/extra.txt").write_text("more evidence\n", encoding="utf-8")
        lock_and_commit(self.repo, "record + more evidence + lockfile")
        r = self.run_compose(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertIn("composition: CURRENT", r.stdout)

    def test_moved_target_makes_the_record_stale_and_compose_refuses(self):
        self.make_record(); lock_and_commit(self.repo, "record")
        g(self.repo, "checkout", "-q", "-b", "upstream", self.base)
        (self.repo / "docs/00-operating-model.md").write_text("upstream moved\n", encoding="utf-8")
        moved = lock_and_commit(self.repo, "upstream moved"); g(self.repo, "update-ref", TARGET, moved)
        g(self.repo, "checkout", "-q", f"wp/{WP}-composition")
        r = self.run_compose()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("stale", r.stdout.lower()); self.assertIn(self.base[:7], r.stdout); self.assertIn(moved[:7], r.stdout); self.assertIn("--record", r.stdout)

    def test_changed_content_after_record_is_refused(self):
        self.make_record(); lock_and_commit(self.repo, "record")
        (self.repo / "README.md").write_text("changed after the claim\n", encoding="utf-8"); lock_and_commit(self.repo, "content after record")
        r = self.run_compose()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("content", r.stdout.lower())

    def test_non_squash_or_foreign_target_ref_is_refused(self):
        # Also a record bound to ANOTHER work package: the binding check needs its own witness
        # (mutation survivor, WP-0076).
        for field, value, marker in (("merge_method", "merge", "squash"), ("target_ref", "refs/heads/develop", gate.DEFAULT_BRANCH),
                                     ("work_package_id", "WP-2026-0001", "WP-2026-0001")):
            with self.subTest(field=field):
                rec = self.make_record(); rec[field] = value
                self.record.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8"); lock_and_commit(self.repo, f"bad {field}")
                r = self.run_compose()
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn(marker, r.stdout)
                g(self.repo, "reset", "-q", "--hard", "HEAD~1")

    def test_malformed_record_is_refused(self):
        # A COMPLETE record of the wrong kind must be refused for THAT reason -- the required-fields
        # check cannot tell a git-baseline record apart (mutation survivor, WP-0076).
        wrong = self.make_record(self.tmp / "wrong.json"); wrong["record"] = "git-baseline"
        self.record.parent.mkdir(parents=True, exist_ok=True)
        for bad, label in ((json.dumps(wrong), "wrong kind"), ('{"hello": 1}', "not a record")):
            with self.subTest(label=label):
                self.record.parent.mkdir(parents=True, exist_ok=True)   # reset --hard prunes the emptied dir
                self.record.write_text(bad + "\n", encoding="utf-8"); lock_and_commit(self.repo, f"malformed record: {label}")
                r = self.run_compose()
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("git-composition", r.stdout)
                g(self.repo, "reset", "-q", "--hard", "HEAD~1")

    def test_missing_record_is_backward_compatible(self):
        r = self.run_compose()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("composition: no record", r.stdout); self.assertIn("BADF COMPOSE PASS", r.stdout)

    def test_record_is_deterministic_and_source_repo_untouched(self):
        before = (g(self.repo, "rev-parse", "HEAD"), g(self.repo, "rev-parse", TARGET), g(self.repo, "status", "--porcelain=v2"),
                  hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest(), len(g(self.repo, "reflog").splitlines()))
        # The record is the requested write; written OUTSIDE the repo here so that "untouched"
        # measures git state (HEAD, refs, index, reflog, status), not the file we asked for.
        a = self.make_record(self.tmp / "a.json"); b = self.make_record(self.tmp / "b.json")
        self.assertEqual((g(self.repo, "rev-parse", "HEAD"), g(self.repo, "rev-parse", TARGET), g(self.repo, "status", "--porcelain=v2"),
                          hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest(), len(g(self.repo, "reflog").splitlines())),
                         before, "the only write is the record file itself; git state must not move")
        a.pop("observed_at"); b.pop("observed_at"); self.assertEqual(a, b)


class CompositionEvidenceTests(_Candidate):
    def test_self_dossier_indexes_composition_evidence_when_present(self):
        def dossier_types() -> set:
            r = subprocess.run([sys.executable, "scripts/badf_gate.py", "self-dossier", WP], cwd=str(self.repo), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            d = json.loads((self.repo / "work" / WP / "gate-dossier.G07.json").read_text(encoding="utf-8"))
            return {e["type"] for e in d["evidence"]}
        self.assertNotIn("composition", dossier_types())
        self.make_record()
        types = dossier_types(); self.assertIn("composition", types)
        ev = json.loads((self.repo / "work" / WP / "evidence/G07/composition.json").read_text(encoding="utf-8"))
        self.assertEqual(ev["evidence_type"], "composition"); self.assertEqual(ev["artifact"], f"work/{WP}/evidence/G07/composition-record.json")
        self.assertEqual(ev["digest"], "sha256:" + hashlib.sha256(self.record.read_bytes()).hexdigest())
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", f"work/{WP}/gate-dossier.G07.json"], cwd=str(self.repo), capture_output=True, text=True)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)   # HELD (HUMAN_REQUIRED), never refused for the extra type


class CompositionVerificationSubskillTests(unittest.TestCase):
    def test_composition_verification_subskill_registered_and_root_stays_designed(self):
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertIn("composition-verification", by); entry = by["composition-verification"]
        self.assertEqual(entry["source"], "skills/badf-git/subskills/composition-verification/SKILL.md")
        self.assertEqual((entry["status"], entry["risk_class"], entry["allowed_tools"]), ("IMPLEMENTED", "C1", []))
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertEqual(by["badf-git"]["status"], "DESIGNED")
        text = (gate.ROOT / entry["source"]).read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text); self.assertNotIn("Status: `", text)
        for token in ("--record", "expected_content_tree", "SOURCE_HEAD_GREEN != INTEGRATION_SAFE", "composition-record.json", "self-dossier"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
