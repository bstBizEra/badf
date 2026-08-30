"""GIT-D (BADF-WP-0075): staleness is a measured verdict, not a remembered rule.

badf-git's state machine names the events that make evidence stale (source head
moved, target moved, rewrite, epoch change) and says recovery is recomputation,
not waiver-by-label; nothing detected them. In this program's last two work
packages the self-dossier was twice bound to a stale base after a rebase.
`badf_gate.py git-staleness <baseline.json> [<path>]` compares a stored
git-baseline record (GIT-C) with the live tree and renders CURRENT (0),
SOURCE_ADVANCED / STALE_EVIDENCE / TARGET_MOVED (HELD, 3), refusing (1) a
malformed record or one taken in another checkout. Read-only.

Every fixture is a scratch clone removed in cleanup.
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
from tests._scratch import seed_clone  # noqa: E402

TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def commit_file(repo: Path, name: str, text: str, msg: str) -> str:
    (repo / name).write_text(text, encoding="utf-8"); g(repo, "add", name); g(repo, "commit", "-q", "-m", msg)
    return g(repo, "rev-parse", "HEAD")


def cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/badf_gate.py", "git-staleness", *args],
                          cwd=str(gate.ROOT), capture_output=True, text=True)


def verdict_of(r: subprocess.CompletedProcess) -> dict:
    lines = r.stdout.rstrip("\n").splitlines()
    assert lines and lines[-1].startswith("BADF GATE "), r.stdout + r.stderr
    return json.loads("\n".join(lines[:-1]))


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-staleness-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "badf"
        self.base = seed_clone(self.repo)

    def baseline(self) -> Path:
        p = self.tmp / "baseline.json"
        p.write_text(json.dumps(gate.git_baseline(self.repo), indent=2) + "\n", encoding="utf-8")
        return p


class StalenessVerdictTests(_Scratch):
    def test_unchanged_tree_is_CURRENT(self):
        r = cli(str(self.baseline()), str(self.repo))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        v = verdict_of(r)
        self.assertEqual(v["disposition"], "CURRENT")
        self.assertFalse(v["source_changed"] or v["source_rewritten"] or v["target_changed"] or v["epoch_changed"])
        self.assertIn("BADF GATE PASS: git-staleness -- CURRENT", r.stdout.splitlines()[-1])

    def test_new_commit_is_SOURCE_ADVANCED_with_ancestor_old_head(self):
        b = self.baseline(); new = commit_file(self.repo, "more.txt", "x\n", "more")
        r = cli(str(b), str(self.repo)); v = verdict_of(r)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertEqual(v["disposition"], "SOURCE_ADVANCED")
        self.assertEqual((v["old_source_head"], v["new_source_head"]), (self.base, new))
        self.assertTrue(v["source_changed"]); self.assertFalse(v["source_rewritten"])
        self.assertIn("HELD", r.stdout.splitlines()[-1])

    def test_amend_is_STALE_EVIDENCE_history_rewrite(self):
        old = commit_file(self.repo, "a.txt", "a\n", "a"); b = self.baseline()
        g(self.repo, "commit", "-q", "--amend", "-m", "a (amended)"); new = g(self.repo, "rev-parse", "HEAD")
        r = cli(str(b), str(self.repo)); v = verdict_of(r)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertEqual(v["disposition"], "STALE_EVIDENCE")
        self.assertTrue(v["source_rewritten"]); self.assertEqual(v["kind"], "history_rewrite")
        self.assertEqual((v["old_source_head"], v["new_source_head"]), (old, new))
        self.assertTrue(v["old_head_still_reachable"])
        self.assertTrue({"source-bound evidence", "composition"} <= set(v["invalidated"]))

    def test_reset_hard_is_STALE_EVIDENCE(self):
        commit_file(self.repo, "a.txt", "a\n", "a"); b = self.baseline()
        g(self.repo, "reset", "-q", "--hard", "HEAD~1")
        v = verdict_of(cli(str(b), str(self.repo)))
        self.assertEqual(v["disposition"], "STALE_EVIDENCE"); self.assertTrue(v["source_rewritten"])

    def test_rebase_onto_moved_target_is_STALE_with_target_and_merge_base_changed(self):
        g(self.repo, "checkout", "-q", "-b", "wp/WP-2026-0016-topic"); commit_file(self.repo, "t.txt", "t\n", "topic")
        b = self.baseline()
        g(self.repo, "checkout", "-q", "-b", "upstream", self.base); moved = commit_file(self.repo, "u.txt", "u\n", "upstream moved")
        g(self.repo, "update-ref", TARGET, moved); g(self.repo, "checkout", "-q", "wp/WP-2026-0016-topic")
        g(self.repo, "rebase", "-q", TARGET)
        v = verdict_of(cli(str(b), str(self.repo)))
        self.assertEqual(v["disposition"], "STALE_EVIDENCE")
        self.assertTrue(v["source_rewritten"] and v["target_changed"] and v["merge_base_changed"])

    def test_target_moved_alone_is_TARGET_MOVED(self):
        b = self.baseline()
        g(self.repo, "checkout", "-q", "-b", "upstream"); moved = commit_file(self.repo, "u.txt", "u\n", "upstream moved")
        g(self.repo, "checkout", "-q", gate.DEFAULT_BRANCH); g(self.repo, "update-ref", TARGET, moved)
        r = cli(str(b), str(self.repo)); v = verdict_of(r)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertEqual(v["disposition"], "TARGET_MOVED")
        self.assertFalse(v["source_changed"]); self.assertTrue(v["target_changed"]); self.assertFalse(v["merge_base_changed"])
        self.assertEqual((v["old_target_sha"], v["new_target_sha"]), (self.base, moved))

    def test_policy_epoch_change_is_STALE_EVIDENCE(self):
        b = self.baseline()
        life = self.repo / "badf/lifecycle.json"; d = json.loads(life.read_text(encoding="utf-8"))
        d["policy_epoch"] = "BADF-9999-01-01"; life.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        v = verdict_of(cli(str(b), str(self.repo)))
        self.assertEqual(v["disposition"], "STALE_EVIDENCE"); self.assertTrue(v["epoch_changed"]); self.assertFalse(v["source_changed"])

    def test_dirty_tree_without_history_change_stays_CURRENT(self):
        b = self.baseline()
        (self.repo / "README.md").write_text("dirty\n", encoding="utf-8"); (self.repo / "new.txt").write_text("n\n", encoding="utf-8")
        (self.repo / "AGENTS.md").write_text("staged\n", encoding="utf-8"); g(self.repo, "add", "AGENTS.md")
        r = cli(str(b), str(self.repo)); v = verdict_of(r)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertEqual(v["disposition"], "CURRENT")
        self.assertNotEqual(v["index_delta"], {"staged": 0, "unstaged": 0, "untracked": 0, "unmerged": 0, "stash": 0})
        self.assertNotIn("README.md", json.dumps(v)); self.assertNotIn("new.txt", json.dumps(v))


class StalenessRefusalTests(_Scratch):
    def test_record_from_another_checkout_is_refused(self):
        other = self.tmp / "other"; seed_clone(other)
        foreign = self.tmp / "foreign.json"; foreign.write_text(json.dumps(gate.git_baseline(other)) + "\n", encoding="utf-8")
        r = cli(str(foreign), str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("BLOCKED", r.stderr); self.assertIn("checkout", r.stderr)
        self.assertNotIn("PASS", r.stdout); self.assertNotIn("Traceback", r.stderr)

    def test_malformed_record_is_refused(self):
        # A COMPLETE record whose `record` field names another kind must be refused for THAT reason:
        # the downstream required-fields check cannot tell a future git-composition record apart
        # (mutation survivor, WP-0075 -- the same class GIT-C's not-a-repo refusal had).
        full = gate.git_baseline(self.repo); full["record"] = "git-composition"
        p = self.tmp / "wrong-kind.json"; p.write_text(json.dumps(full) + "\n", encoding="utf-8")
        r = cli(str(p), str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("record: git-baseline", r.stderr)
        for bad in ('{"hello": 1}', '{"record": "git-baseline"}', 'not json'):
            with self.subTest(bad=bad[:20]):
                p = self.tmp / "bad.json"; p.write_text(bad + "\n", encoding="utf-8")
                r = cli(str(p), str(self.repo))
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("BLOCKED", r.stderr); self.assertNotIn("Traceback", r.stderr)

    def test_redirected_baseline_output_with_trailing_pass_line_parses(self):
        out = subprocess.run([sys.executable, "scripts/badf_gate.py", "git-baseline", str(self.repo)], cwd=str(gate.ROOT),
                             capture_output=True, text=True, check=True).stdout
        self.assertTrue(out.rstrip().splitlines()[-1].startswith("BADF GATE PASS"))
        p = self.tmp / "redirected.json"; p.write_text(out, encoding="utf-8")
        r = cli(str(p), str(self.repo)); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(verdict_of(r)["disposition"], "CURRENT")


class StalenessPropertyTests(_Scratch):
    def _snapshot(self):
        files = sorted(str(p.relative_to(self.repo)) for p in self.repo.rglob("*") if ".git" not in p.parts)
        return (g(self.repo, "status", "--porcelain=v2"), len(g(self.repo, "reflog").splitlines()), g(self.repo, "stash", "list"),
                hashlib.sha256(g(self.repo, "ls-files", "-s").encode()).hexdigest(), files, g(self.repo, "rev-parse", "HEAD"), g(self.repo, "rev-parse", TARGET))

    def test_staleness_is_read_only_and_deterministic(self):
        # Baseline AFTER the commit, so the amend is a rewrite of the recorded head (the first
        # draft baselined before it, and base -> amended is honest forward progress: SOURCE_ADVANCED).
        commit_file(self.repo, "a.txt", "a\n", "a"); b = self.baseline(); g(self.repo, "commit", "-q", "--amend", "-m", "a2")
        (self.repo / "README.md").write_text("dirty\n", encoding="utf-8")
        before = self._snapshot()
        rec = gate.load_git_baseline_record(b)
        v1 = gate.git_staleness(rec, self.repo); v2 = gate.git_staleness(rec, self.repo)
        self.assertEqual(self._snapshot(), before)
        v1.pop("observed_at"); v2.pop("observed_at"); self.assertEqual(v1, v2)
        self.assertEqual(v1["disposition"], "STALE_EVIDENCE")


class CommitIntegritySubskillTests(unittest.TestCase):
    def test_commit_integrity_subskill_registered_and_root_is_active(self):
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertIn("commit-integrity", by); entry = by["commit-integrity"]
        self.assertEqual(entry["source"], "skills/badf-git/subskills/commit-integrity/SKILL.md")
        self.assertEqual((entry["status"], entry["risk_class"], entry["allowed_tools"]), ("IMPLEMENTED", "C1", []))
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertEqual(by["badf-git"]["status"], "ACTIVE")
        text = (gate.ROOT / entry["source"]).read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text); self.assertNotIn("Status: `", text)
        for token in ("git-staleness", "git-baseline", "STALE_EVIDENCE", "GIT-I05", "git add -p"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
