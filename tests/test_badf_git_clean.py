"""badf-git CLEAN (WP-2026-0147): landed local branches, removed with a way back.

git-cycle.md section 13 allows deleting only known, landed local state. `badf_gate.py
git-clean [<path>]` classifies every local branch against origin/<default> -- PROTECTED
(default or checked out), MERGED (ancestor), SQUASHED (net-diff patch-id already on the
target) or UNMERGED -- and writes nothing. `--apply --wp <WP>` preserves each landed tip
under refs/recovery/<WP>/clean/ and deletes it guarded on the observed SHA.

Every fixture is a scratch clone removed in cleanup.
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

WP = "WP-2026-9001"
TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/badf_gate.py", "git-clean", *args], cwd=str(gate.ROOT), capture_output=True, text=True)


def record_of(r: subprocess.CompletedProcess) -> dict:
    lines = r.stdout.rstrip("\n").splitlines()
    assert lines and lines[-1].startswith("BADF GATE "), r.stdout + r.stderr
    return json.loads("\n".join(lines[:-1]))


def commit_file(repo: Path, name: str, text: str, msg: str) -> str:
    (repo / name).write_text(text, encoding="utf-8"); g(repo, "add", name); g(repo, "commit", "-q", "-m", msg)
    return g(repo, "rev-parse", "HEAD")


class _Scratch(unittest.TestCase):
    """main at the seed; `merged` fast-forwarded in; `squashed` (two commits) squash-landed;
    `partial` squash-landed then extended; `unmerged` never landed; `wtb` checked out in a
    second worktree; `current` checked out here. origin/main is pinned to the landed main."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-clean-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = r = self.tmp / "badf"
        seed_clone(r)
        g(r, "checkout", "-q", "-b", "merged"); commit_file(r, "clean-ff.txt", "ff\n", "ff")
        g(r, "checkout", "-q", gate.DEFAULT_BRANCH); g(r, "merge", "-q", "--ff-only", "merged")
        g(r, "checkout", "-q", "-b", "squashed"); commit_file(r, "clean-sq.txt", "one\n", "sq1"); commit_file(r, "clean-sq.txt", "one\ntwo\n", "sq2")
        g(r, "checkout", "-q", "-b", "partial", gate.DEFAULT_BRANCH); commit_file(r, "clean-pt.txt", "landed\n", "pt1")
        g(r, "checkout", "-q", gate.DEFAULT_BRANCH)
        g(r, "merge", "-q", "--squash", "squashed"); g(r, "commit", "-q", "-m", "squash of squashed")
        g(r, "merge", "-q", "--squash", "partial"); g(r, "commit", "-q", "-m", "squash of partial")
        g(r, "checkout", "-q", "partial"); commit_file(r, "clean-pt.txt", "landed\nnot landed\n", "pt2")
        g(r, "checkout", "-q", "-b", "unmerged", gate.DEFAULT_BRANCH); commit_file(r, "clean-un.txt", "only here\n", "un")
        g(r, "update-ref", TARGET, g(r, "rev-parse", gate.DEFAULT_BRANCH))
        g(r, "branch", "wtb", gate.DEFAULT_BRANCH); g(r, "worktree", "add", "-q", str(self.tmp / "wt"), "wtb")
        g(r, "checkout", "-q", "-b", "current", gate.DEFAULT_BRANCH)

    def refs(self) -> dict:
        return dict(line.split(" ", 1)[::-1] for line in g(self.repo, "for-each-ref", "--format=%(objectname) %(refname)").splitlines())

    def objects(self) -> str:
        return g(self.repo, "count-objects", "-v")

    def classes(self, rec: dict) -> dict:
        return {b["branch"]: b["class"] for b in rec["branches"]}


class DryRunTests(_Scratch):
    def test_classifies_every_local_branch(self):
        r = cli(str(self.repo)); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = record_of(r)
        self.assertEqual(self.classes(rec), {
            "current": "PROTECTED", gate.DEFAULT_BRANCH: "PROTECTED", "wtb": "PROTECTED",
            "merged": "MERGED", "squashed": "SQUASHED", "partial": "UNMERGED", "unmerged": "UNMERGED"})
        self.assertEqual((rec["record"], rec["mode"], rec["disposition"], rec["operation_class"]),
                         ("git-clean", "DRY_RUN", "PLANNED", "GIT-O0 OBSERVE"))
        self.assertEqual(rec["target_sha"], g(self.repo, "rev-parse", TARGET))
        self.assertIn("BADF GATE PASS: git-clean -- PLANNED: planned 2", r.stdout.splitlines()[-1])

    def test_dry_run_writes_no_ref_and_no_object(self):
        refs, objects = self.refs(), self.objects()
        self.assertEqual(cli(str(self.repo)).returncode, 0)
        self.assertEqual((self.refs(), self.objects()), (refs, objects))

    def test_partially_landed_squash_is_kept_with_its_unlanded_count(self):
        rec = record_of(cli(str(self.repo)))
        row = next(b for b in rec["branches"] if b["branch"] == "partial")
        self.assertEqual((row["class"], row["outcome"], row["ahead"]), ("UNMERGED", "KEPT", 2))

    def test_missing_target_is_BLOCKED_not_HEAD(self):
        g(self.repo, "update-ref", "-d", TARGET)
        r = cli(str(self.repo)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stdout + r.stderr)


class ApplyTests(_Scratch):
    def test_apply_requires_a_work_package(self):
        refs = self.refs()
        self.assertEqual(cli(str(self.repo), "--apply").returncode, 2)
        r = cli(str(self.repo), "--apply", "--wp", "not-a-wp"); self.assertEqual(r.returncode, 1)
        self.assertIn("--apply requires --wp", r.stdout + r.stderr)
        self.assertEqual(self.refs(), refs)

    def test_apply_deletes_only_landed_branches_and_preserves_each_tip(self):
        before = self.refs()
        r = cli(str(self.repo), "--apply", "--wp", WP); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = record_of(r)
        self.assertEqual((rec["mode"], rec["disposition"], rec["work_package"]), ("APPLY", "CLEANED", WP))
        after = self.refs()
        for name in ("merged", "squashed"):
            self.assertNotIn(f"refs/heads/{name}", after)
            self.assertEqual(after[f"refs/recovery/{WP}/clean/{name}"], before[f"refs/heads/{name}"])
        for name in ("current", gate.DEFAULT_BRANCH, "wtb", "partial", "unmerged"):
            self.assertEqual(after[f"refs/heads/{name}"], before[f"refs/heads/{name}"])
        self.assertEqual(g(self.repo, "status", "--porcelain"), "")

    def test_restore_command_recreates_the_branch(self):
        rec = record_of(cli(str(self.repo), "--apply", "--wp", WP))
        row = next(b for b in rec["branches"] if b["branch"] == "squashed")
        subprocess.run(row["restore"].split(), cwd=str(self.repo), check=True, capture_output=True)
        self.assertEqual(g(self.repo, "rev-parse", "refs/heads/squashed"), row["sha"])

    def test_existing_recovery_ref_refuses_before_any_deletion(self):
        g(self.repo, "update-ref", f"refs/recovery/{WP}/clean/squashed", g(self.repo, "rev-parse", "merged"))
        refs = self.refs()
        r = cli(str(self.repo), "--apply", "--wp", WP); self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("never overwritten", r.stdout + r.stderr)
        self.assertEqual(self.refs(), refs)

    def test_branch_that_moves_after_observation_is_kept_and_HELD(self):
        real = gate._git_at
        moved = {}

        def racing(root, *args):
            # The preflight probe of the first recovery ref runs after classification and
            # before any deletion: move `merged` there, as a concurrent actor would.
            if args[:3] == ("rev-parse", "--verify", "-q") and args[3].endswith("/clean/merged") and not moved:
                moved["sha"] = commit_on(self.repo, "merged")
            return real(root, *args)

        def commit_on(repo, branch):
            tree = g(repo, "rev-parse", f"{branch}^{{tree}}")
            sha = g(repo, "commit-tree", tree, "-p", branch, "-m", "concurrent")
            g(repo, "update-ref", f"refs/heads/{branch}", sha)
            return sha

        gate._git_at = racing
        self.addCleanup(setattr, gate, "_git_at", real)
        rec = gate.git_clean(self.repo, apply=True, wp=WP)
        row = next(b for b in rec["branches"] if b["branch"] == "merged")
        self.assertEqual((row["outcome"], rec["disposition"]), ("SKIPPED_MOVED", "HELD"))
        self.assertEqual(g(self.repo, "rev-parse", "refs/heads/merged"), moved["sha"])


class ContentLandedTests(unittest.TestCase):
    """WP-2026-0149: a branch whose work landed inside a larger squash -- the reconcile
    cherry-picked into #342 -- has no matching patch-id, yet every path it changed is
    byte-identical on the target. `picked` changes a file and the lockfile, and main lands
    that file inside a bigger commit with a different lockfile; `deleted` removes a file
    main also removes; `superseded` changed a file main has since changed again;
    `lockonly` changed nothing but the lockfile."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-clean-cl-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = r = self.tmp / "badf"
        seed_clone(r)
        commit_file(r, "cl-gone.txt", "doomed\n", "seed a file to delete")
        g(r, "update-ref", TARGET, g(r, "rev-parse", gate.DEFAULT_BRANCH))
        lock = r / gate.LOCKFILE
        g(r, "checkout", "-q", "-b", "picked")
        (r / "cl-picked.txt").write_text("reconcile\n", encoding="utf-8")
        lock.write_text(lock.read_text(encoding="utf-8") + " \n", encoding="utf-8")
        g(r, "add", "cl-picked.txt", gate.LOCKFILE); g(r, "commit", "-q", "-m", "picked")
        g(r, "checkout", "-q", "-b", "deleted", gate.DEFAULT_BRANCH); g(r, "rm", "-q", "cl-gone.txt"); g(r, "commit", "-q", "-m", "deleted")
        g(r, "checkout", "-q", "-b", "superseded", gate.DEFAULT_BRANCH); commit_file(r, "cl-sup.txt", "first\n", "superseded")
        g(r, "checkout", "-q", "-b", "lockonly", gate.DEFAULT_BRANCH)
        lock.write_text(lock.read_text(encoding="utf-8") + "\t\n", encoding="utf-8"); g(r, "commit", "-q", "-am", "lockonly")
        g(r, "checkout", "-q", gate.DEFAULT_BRANCH)
        g(r, "checkout", "picked", "--", "cl-picked.txt"); g(r, "checkout", "superseded", "--", "cl-sup.txt")
        g(r, "rm", "-q", "cl-gone.txt")
        (r / "cl-other.txt").write_text("more of the larger squash\n", encoding="utf-8")
        lock.write_text(lock.read_text(encoding="utf-8") + "  \n", encoding="utf-8")
        g(r, "add", "-A"); g(r, "commit", "-q", "-m", "larger squash carrying picked, deleted and superseded")
        commit_file(r, "cl-sup.txt", "first\nthen changed again\n", "main moves superseded's file on")
        g(r, "update-ref", TARGET, g(r, "rev-parse", gate.DEFAULT_BRANCH))

    def classes(self, rec: dict) -> dict:
        return {b["branch"]: b["class"] for b in rec["branches"]}

    def test_landed_inside_a_larger_squash_is_CONTENT_LANDED(self):
        rec = record_of(cli(str(self.repo)))
        self.assertEqual(self.classes(rec), {gate.DEFAULT_BRANCH: "PROTECTED", "picked": "CONTENT_LANDED",
                                             "deleted": "CONTENT_LANDED", "superseded": "UNMERGED", "lockonly": "UNMERGED"})
        picked = next(b for b in rec["branches"] if b["branch"] == "picked")
        self.assertEqual((picked["outcome"], picked["compared_paths"]), ("PLANNED", 1))   # the lockfile is not compared

    def test_dry_run_still_writes_nothing(self):
        before = (g(self.repo, "for-each-ref"), g(self.repo, "count-objects", "-v"))
        self.assertEqual(cli(str(self.repo)).returncode, 0)
        self.assertEqual((g(self.repo, "for-each-ref"), g(self.repo, "count-objects", "-v")), before)

    def test_apply_deletes_content_landed_and_keeps_the_rest(self):
        tips = {b: g(self.repo, "rev-parse", f"refs/heads/{b}") for b in ("picked", "deleted", "superseded", "lockonly")}
        r = cli(str(self.repo), "--apply", "--wp", WP); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        heads = g(self.repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").split()
        self.assertEqual(sorted(heads), sorted([gate.DEFAULT_BRANCH, "superseded", "lockonly"]))
        for name in ("picked", "deleted"):
            self.assertEqual(g(self.repo, "rev-parse", f"refs/recovery/{WP}/clean/{name}"), tips[name])


if __name__ == "__main__":
    unittest.main()
