"""GIT-G (BADF-WP-0080): PRESERVE -> IDENTIFY -> CLASSIFY before anything destructive.

The recovery contract stops mutation until unknown state is classified, and GIT-O5
requires an inventory and a preservation of unique state before any exception. Nothing
produced either, and GIT-F's BLOCKED reconcile ended at the words "open recovery".
`badf_gate.py git-recovery [<path>]` renders the before-state record: the baseline plus
the unique-state inventory (uncommitted, stash, dangling reflog commits, unpushed topic
commits, other worktrees), the recovery class and the disposition. `--preserve <label>
--wp <WP>` adds refs under refs/recovery/<WP>/ (HEAD, and `git stash create` of a dirty
tree) and touches nothing else.

Every fixture is a scratch clone removed in cleanup.
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

WP = "WP-2026-9001"
TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/badf_gate.py", "git-recovery", *args], cwd=str(gate.ROOT), capture_output=True, text=True)


def record_of(r: subprocess.CompletedProcess) -> dict:
    lines = r.stdout.rstrip("\n").splitlines()
    assert lines and lines[-1].startswith("BADF GATE "), r.stdout + r.stderr
    return json.loads("\n".join(lines[:-1]))


def commit_file(repo: Path, name: str, text: str, msg: str) -> str:
    (repo / name).write_text(text, encoding="utf-8"); g(repo, "add", name); g(repo, "commit", "-q", "-m", msg)
    return g(repo, "rev-parse", "HEAD")


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-recovery-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "badf"
        self.base = seed_clone(self.repo)

    def snapshot(self) -> tuple:
        return (g(self.repo, "status", "--porcelain=v2"), len(g(self.repo, "reflog").splitlines()), g(self.repo, "stash", "list"),
                hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest(), g(self.repo, "rev-parse", "HEAD"),
                sorted(g(self.repo, "for-each-ref", "--format=%(refname) %(objectname)").splitlines()))


class InventoryTests(_Scratch):
    def test_clean_checkout_is_EVIDENCE_ONLY_and_RECOVERABLE(self):
        g(self.repo, "checkout", "-q", "--detach")   # not the default branch: no PROTECTED signal
        r = cli(str(self.repo)); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = record_of(r)
        self.assertEqual((rec["record"], rec["recovery_class"], rec["disposition"]), ("git-recovery", "EVIDENCE_ONLY", "RECOVERABLE"))
        u = rec["unique_state"]
        self.assertEqual((u["uncommitted"], u["stash"], u["dangling_commits"], u["unpushed_commits"]), (0, 0, [], []))
        self.assertIn("baseline", rec); self.assertEqual(rec["baseline"]["source_head_sha"], self.base)
        self.assertIn("BADF GATE PASS: git-recovery -- EVIDENCE_ONLY", r.stdout.splitlines()[-1])

    def test_uncommitted_and_stash_are_LOCAL_RECOVERY_REQUIRED_without_paths(self):
        g(self.repo, "checkout", "-q", "--detach")
        (self.repo / "README.md").write_text("private-edit-3c9e\n", encoding="utf-8")
        (self.repo / "only-copy-secret.txt").write_text("SECRET-71ab\n", encoding="utf-8")
        (self.repo / "docs/00-operating-model.md").write_text("stash me\n", encoding="utf-8"); g(self.repo, "stash", "push", "-q", "--", "docs/00-operating-model.md")
        r = cli(str(self.repo)); self.assertEqual(r.returncode, 3, r.stdout + r.stderr)   # HELD: unique state needs preserving
        rec = record_of(r)
        self.assertEqual((rec["recovery_class"], rec["disposition"]), ("LOCAL", "RECOVERY_REQUIRED"))
        self.assertEqual(rec["unique_state"]["uncommitted"], 2); self.assertEqual(rec["unique_state"]["stash"], 1)
        for leak in ("README.md", "only-copy-secret", "SECRET-71ab", "3c9e"):
            self.assertNotIn(leak, json.dumps(rec), leak)
        self.assertIn("preserve", rec["least_destructive_path"].lower())

    def test_dangling_reflog_commit_is_inventoried(self):
        g(self.repo, "checkout", "-q", "--detach")
        lost = commit_file(self.repo, "lost.txt", "the only copy\n", "will be reset away")
        g(self.repo, "reset", "-q", "--hard", "HEAD~1")
        rec = record_of(cli(str(self.repo)))
        self.assertIn(lost, rec["unique_state"]["dangling_commits"])
        self.assertEqual((rec["recovery_class"], rec["disposition"]), ("LOCAL", "RECOVERY_REQUIRED"))
        self.assertIn("reflog", rec["least_destructive_path"].lower()); self.assertIn("refs/recovery", rec["least_destructive_path"])

    def test_unpushed_topic_commits_are_TOPIC(self):
        g(self.repo, "checkout", "-q", "-b", "wp/WP-2026-9001-topic"); commit_file(self.repo, "t.txt", "t\n", "topic")
        rec = record_of(cli(str(self.repo)))
        self.assertEqual(rec["recovery_class"], "TOPIC")
        self.assertEqual(len(rec["unique_state"]["unpushed_commits"]), 1)
        self.assertEqual(rec["unique_state"]["unpushed_commits"][0]["branch"], "refs/heads/wp/WP-2026-9001-topic")

    def test_head_on_default_branch_is_PROTECTED(self):
        rec = record_of(cli(str(self.repo)))   # seed_clone leaves HEAD on the default branch
        self.assertEqual(rec["recovery_class"], "PROTECTED")
        self.assertIn("revert", rec["least_destructive_path"].lower())

    def test_other_worktrees_are_listed_but_not_self(self):
        other = self.tmp / "other-wt"
        g(self.repo, "worktree", "add", "-q", str(other), "-b", "wp/WP-2026-9001-elsewhere")
        rec = record_of(cli(str(self.repo)))
        others = rec["unique_state"]["other_worktrees"]
        self.assertEqual(len(others), 1); self.assertEqual(others[0]["branch"], "refs/heads/wp/WP-2026-9001-elsewhere")
        self.assertNotEqual(Path(others[0]["path"]).resolve(), self.repo.resolve())
        rec2 = record_of(cli(str(other)))
        self.assertEqual([Path(o["path"]).resolve() for o in rec2["unique_state"]["other_worktrees"]], [self.repo.resolve()])


class PreserveTests(_Scratch):
    def test_preserve_adds_refs_and_touches_nothing_else(self):
        g(self.repo, "checkout", "-q", "--detach")
        (self.repo / "README.md").write_text("dirty\n", encoding="utf-8"); (self.repo / "new.txt").write_text("new\n", encoding="utf-8"); g(self.repo, "add", "new.txt")
        before = self.snapshot()
        r = cli("--preserve", "before-cleanup", "--wp", WP, str(self.repo)); self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        rec = record_of(r); p = rec["preservation"]
        self.assertEqual(p["refs"], [f"refs/recovery/{WP}/before-cleanup", f"refs/recovery/{WP}/before-cleanup-worktree"])
        after = self.snapshot()
        self.assertEqual(after[:5], before[:5], "status, reflog, stash, index and HEAD must not move")
        self.assertEqual(set(after[5]) - set(before[5]), {f"refs/recovery/{WP}/before-cleanup {self.base}",
                                                          f"refs/recovery/{WP}/before-cleanup-worktree {p['worktree_snapshot']}"})
        # The snapshot holds the dirty content: check it out in a second clone and compare.
        check = self.tmp / "check"; g(self.repo, "worktree", "add", "-q", "--detach", str(check), p["worktree_snapshot"])
        self.assertEqual((check / "README.md").read_text(encoding="utf-8"), "dirty\n"); self.assertEqual((check / "new.txt").read_text(encoding="utf-8"), "new\n")

    def test_preserve_on_clean_tree_adds_one_ref(self):
        g(self.repo, "checkout", "-q", "--detach")
        rec = record_of(cli("--preserve", "clean", "--wp", WP, str(self.repo)))
        self.assertEqual(rec["preservation"]["refs"], [f"refs/recovery/{WP}/clean"]); self.assertIsNone(rec["preservation"]["worktree_snapshot"])

    def test_preserve_refuses_existing_label_and_requires_wp(self):
        g(self.repo, "checkout", "-q", "--detach")
        self.assertEqual(cli("--preserve", "x", "--wp", WP, str(self.repo)).returncode, 0)
        r = cli("--preserve", "x", "--wp", WP, str(self.repo)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("BLOCKED", r.stderr)
        self.assertEqual(g(self.repo, "rev-parse", f"refs/recovery/{WP}/x"), self.base, "an existing recovery ref is never overwritten")
        r = cli("--preserve", "y", str(self.repo)); self.assertEqual(r.returncode, 2, r.stdout + r.stderr); self.assertNotIn("PASS", r.stdout)


class RefusalAndPropertyTests(_Scratch):
    def test_refusals_outside_repo_unborn_head_and_unmerged_paths(self):
        plain = self.tmp / "plain"; plain.mkdir()
        r = cli(str(plain)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("BLOCKED", r.stderr)
        unborn = self.tmp / "unborn"; unborn.mkdir(); g(unborn, "init", "-q")
        g(unborn, "remote", "add", "origin", str(self.repo)); g(unborn, "fetch", "-q", "origin", self.base); g(unborn, "update-ref", TARGET, self.base)
        r = cli(str(unborn)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("BLOCKED", r.stderr)
        g(self.repo, "checkout", "-q", "-b", "a"); commit_file(self.repo, "c.txt", "A\n", "A")
        g(self.repo, "checkout", "-q", "-b", "b", self.base); commit_file(self.repo, "c.txt", "B\n", "B")
        subprocess.run(["git", "-C", str(self.repo), "merge", "-q", "a"], capture_output=True)   # conflict on c.txt
        r = cli(str(self.repo)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("unmerged", r.stderr.lower())

    def test_inventory_is_read_only_and_deterministic(self):
        g(self.repo, "checkout", "-q", "--detach"); (self.repo / "README.md").write_text("dirty\n", encoding="utf-8")
        lost = commit_file(self.repo, "lost.txt", "x\n", "lost"); g(self.repo, "reset", "-q", "--hard", "HEAD~1"); (self.repo / "README.md").write_text("dirty again\n", encoding="utf-8")
        before = self.snapshot()
        a = gate.git_recovery(self.repo); b = gate.git_recovery(self.repo)
        self.assertEqual(self.snapshot(), before)
        a.pop("observed_at"); b.pop("observed_at"); a["baseline"].pop("observed_at"); b["baseline"].pop("observed_at"); self.assertEqual(a, b)
        self.assertIn(lost, a["unique_state"]["dangling_commits"])


class GitRecoverySubskillTests(unittest.TestCase):
    def test_git_recovery_subskill_registered_and_root_is_active(self):
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertIn("git-recovery", by); entry = by["git-recovery"]
        self.assertEqual(entry["source"], "skills/badf-git/subskills/git-recovery/SKILL.md")
        self.assertEqual((entry["status"], entry["risk_class"], entry["allowed_tools"]), ("IMPLEMENTED", "C1", []))
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertEqual(by["badf-git"]["status"], "ACTIVE")
        text = (gate.ROOT / entry["source"]).read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text); self.assertNotIn("Status: `", text)
        for token in ("PRESERVE", "git-recovery", "--preserve", "refs/recovery/", "RECOVERY_REQUIRED", "git revert", "reflog", "stash create"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
