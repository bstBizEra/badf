"""GIT-C (BADF-WP-0069): the read-only Git baseline inspector.

badf-git's BASELINE stage (references/git-cycle.md section 2) and its
GIT_BASELINED state require an agent to observe before editing and to exit
BASELINE only when "a reproducible baseline exists". Until this WP nothing
produced that record deterministically -- GIT_BASELINED was a claim an agent
typed. `badf_gate.py git-baseline [<path>]` prints one JSON record (identity,
worktree/branch/index as counts only, target/source SHAs and trees, merge base,
ahead/behind, honest no-fetch remote freshness, policy epoch) and a PASS line.
It is GIT-O0: it writes nothing, fetches nothing, and never moves a ref.

Every fixture is a scratch clone built by tests/_scratch.seed_clone and removed
in cleanup -- interrupted runs must not leave the checkout dirty (the integrity
suite's residue blocked a rebase during WP-0070).
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

TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"


def run_cli(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/badf_gate.py", "git-baseline", str(path)],
                          cwd=str(gate.ROOT), capture_output=True, text=True)


def record_of(r: subprocess.CompletedProcess) -> dict:
    lines = r.stdout.rstrip("\n").splitlines()
    assert lines and lines[-1].startswith("BADF GATE PASS: git-baseline"), r.stdout + r.stderr
    return json.loads("\n".join(lines[:-1]))


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def commit_file(repo: Path, name: str, text: str, msg: str) -> str:
    (repo / name).write_text(text, encoding="utf-8")
    g(repo, "add", name); g(repo, "commit", "-q", "-m", msg)
    return g(repo, "rev-parse", "HEAD")


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-baseline-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "badf"
        self.base = seed_clone(self.repo)


class GitBaselineRecordTests(_Scratch):
    def test_baseline_on_clean_clone_reports_GIT_BASELINED(self):
        r = run_cli(self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = record_of(r)
        self.assertEqual(rec["disposition"], "GIT_BASELINED")
        self.assertEqual(rec["source_head_sha"], self.base)
        self.assertEqual(rec["target_sha"], self.base)
        self.assertEqual(rec["merge_base_sha"], self.base)
        self.assertEqual(rec["source_tree"], rec["target_tree"])
        self.assertEqual((rec["ahead"], rec["behind"]), (0, 0))
        self.assertTrue(rec["head_is_ancestor_of_target"])
        self.assertEqual(rec["worktree"]["head_kind"], "branch")
        self.assertEqual(rec["source_ref"], f"refs/heads/{gate.DEFAULT_BRANCH}")
        self.assertEqual(rec["index"], {"staged": 0, "unstaged": 0, "untracked": 0, "unmerged": 0, "stash": 0})
        self.assertIn(f"GIT_BASELINED {self.base[:7]} on {self.base[:7]}", r.stdout.splitlines()[-1])

    def test_baseline_on_topic_branch_reports_ahead_and_merge_base(self):
        g(self.repo, "checkout", "-q", "-b", "wp/WP-2026-0016-topic")
        head = commit_file(self.repo, "topic.txt", "x\n", "topic")
        rec = gate.git_baseline(self.repo)
        self.assertEqual(rec["source_ref"], "refs/heads/wp/WP-2026-0016-topic")
        self.assertEqual(rec["source_head_sha"], head)
        self.assertEqual(rec["merge_base_sha"], self.base)
        self.assertEqual((rec["ahead"], rec["behind"]), (1, 0))
        self.assertFalse(rec["head_is_ancestor_of_target"])
        self.assertEqual(rec["worktree"]["head_kind"], "branch")

    def test_baseline_detects_behind_target(self):
        newer = commit_file(self.repo, "upstream.txt", "y\n", "upstream moved")
        g(self.repo, "update-ref", TARGET, newer)
        g(self.repo, "reset", "-q", "--hard", self.base)
        rec = gate.git_baseline(self.repo)
        self.assertEqual(rec["target_sha"], newer)
        self.assertEqual((rec["ahead"], rec["behind"]), (0, 1))
        self.assertTrue(rec["head_is_ancestor_of_target"])
        self.assertEqual(rec["merge_base_sha"], self.base)

    def test_baseline_reports_detached_head_without_source_ref(self):
        g(self.repo, "checkout", "-q", "--detach")
        rec = gate.git_baseline(self.repo)
        self.assertEqual(rec["worktree"]["head_kind"], "detached")
        self.assertIsNone(rec["source_ref"])
        self.assertEqual(rec["source_head_sha"], self.base)
        self.assertEqual(rec["disposition"], "GIT_BASELINED")

    def test_baseline_reports_dirty_counts_without_paths_or_contents(self):
        secret_name, secret_text = "very-private-untracked-file.txt", "SECRET-CONTENT-8f3a"
        (self.repo / "README.md").write_text("unstaged edit 9c1d\n", encoding="utf-8")           # unstaged
        (self.repo / "AGENTS.md").write_text("staged edit 7b2e\n", encoding="utf-8"); g(self.repo, "add", "AGENTS.md")  # staged
        (self.repo / secret_name).write_text(secret_text + "\n", encoding="utf-8")                 # untracked
        (self.repo / "docs/00-operating-model.md").write_text("stash me\n", encoding="utf-8")
        g(self.repo, "stash", "push", "-q", "--", "docs/00-operating-model.md")                  # stash
        rec = gate.git_baseline(self.repo)
        self.assertEqual(rec["index"], {"staged": 1, "unstaged": 1, "untracked": 1, "unmerged": 0, "stash": 1})
        dump = json.dumps(rec)
        for leak in (secret_name, secret_text, "README.md", "AGENTS.md", "9c1d", "7b2e"):
            self.assertNotIn(leak, dump, f"the record leaks {leak!r}")


class GitBaselineRefusalTests(_Scratch):
    def test_baseline_refuses_outside_a_git_repository(self):
        plain = self.tmp / "plain"; plain.mkdir()
        r = run_cli(plain)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stderr); self.assertNotIn("PASS", r.stdout); self.assertNotIn("Traceback", r.stderr)
        # The refusal must name the actual condition: with this branch removed the origin/<default>
        # check still refuses a plain directory -- with the WRONG diagnosis (mutation survivor, WP-0069).
        self.assertIn("not inside a git working tree", r.stderr)

    def test_baseline_refuses_without_origin_default(self):
        g(self.repo, "update-ref", "-d", TARGET)
        r = run_cli(self.repo)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stderr); self.assertIn(f"origin/{gate.DEFAULT_BRANCH}", r.stderr)
        self.assertNotIn("PASS", r.stdout)

    def test_baseline_refuses_unborn_head(self):
        unborn = self.tmp / "unborn"; unborn.mkdir()
        g(unborn, "init", "-q"); g(unborn, "remote", "add", "origin", str(self.repo))
        g(unborn, "fetch", "-q", "origin", self.base); g(unborn, "update-ref", TARGET, self.base)
        r = run_cli(unborn)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("BLOCKED", r.stderr); self.assertIn("HEAD", r.stderr); self.assertNotIn("PASS", r.stdout)


class GitBaselinePropertyTests(_Scratch):
    def _snapshot(self) -> tuple:
        files = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*") if ".git" not in p.parts)
        index = hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest()
        return (g(self.repo, "status", "--porcelain=v2"), len(g(self.repo, "reflog").splitlines()),
                g(self.repo, "stash", "list"), index, files, g(self.repo, "rev-parse", "HEAD"), g(self.repo, "rev-parse", TARGET))

    def test_baseline_is_read_only_and_creates_no_files(self):
        (self.repo / "README.md").write_text("dirty on purpose\n", encoding="utf-8")
        before = self._snapshot()
        r = run_cli(self.repo); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self._snapshot(), before)

    def test_baseline_is_deterministic_modulo_observed_at(self):
        a, b = gate.git_baseline(self.repo), gate.git_baseline(self.repo)
        self.assertIn("observed_at", a); a.pop("observed_at"); b.pop("observed_at")
        self.assertEqual(a, b)

    def test_baseline_record_covers_contract_baseline_items(self):
        rec = gate.git_baseline(self.repo)
        # git-cycle.md section 2 -- repository identity; worktree/branch/index status; target ref + SHA;
        # source ref + SHA; merge base; remote freshness; policy epoch; unknown local state (stash/untracked).
        for key in ("record", "schema_version", "observed_at", "disposition", "repository", "worktree", "index",
                    "target_ref", "target_sha", "target_tree", "source_ref", "source_head_sha", "source_tree",
                    "merge_base_sha", "ahead", "behind", "head_is_ancestor_of_target", "remote_freshness",
                    "policy_epoch", "non_coverage"):
            self.assertIn(key, rec, key)
        self.assertEqual(rec["record"], "git-baseline")
        self.assertEqual(rec["target_ref"], f"refs/heads/{gate.DEFAULT_BRANCH}")
        self.assertEqual(rec["remote_freshness"]["tracking_ref"], TARGET)
        self.assertTrue(rec["remote_freshness"]["observed_without_fetch"])
        self.assertEqual(rec["policy_epoch"], gate.load_json(gate.ROOT / "badf/lifecycle.json")["policy_epoch"])
        self.assertTrue(any("test_set_epoch" in n for n in rec["non_coverage"]))
        self.assertIn("root", rec["repository"]); self.assertIn("linked", rec["worktree"])


class GitBaselineOnThisCheckoutTests(unittest.TestCase):
    def test_baseline_of_this_checkout_renders(self):
        """The runner's own checkout: a branch locally, a detached merge ref on a pull_request runner."""
        r = run_cli(gate.ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = record_of(r)
        self.assertEqual(rec["disposition"], "GIT_BASELINED")
        self.assertIn(rec["worktree"]["head_kind"], ("branch", "detached"))
        self.assertEqual(rec["repository"]["name"], gate.self_repository())

    def test_repository_state_subskill_registered_and_root_stays_designed(self):
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json")
        by = {s["name"]: s for s in reg["skills"]}
        self.assertIn("repository-state", by)
        entry = by["repository-state"]
        self.assertEqual(entry["source"], "skills/badf-git/subskills/repository-state/SKILL.md")
        self.assertEqual((entry["status"], entry["risk_class"], entry["allowed_tools"]), ("IMPLEMENTED", "C1", []))
        digest = "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest()
        self.assertEqual(entry["digest"], digest)
        self.assertEqual(by["badf-git"]["status"], "DESIGNED")
        text = (gate.ROOT / entry["source"]).read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text); self.assertNotIn("Status: `", text)
        self.assertIn("git-baseline", text); self.assertIn("GIT-O0", text)


if __name__ == "__main__":
    unittest.main()
