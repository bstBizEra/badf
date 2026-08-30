"""GIT-H (BADF-WP-0081): a release ref is a checked binding; creating one stays a human act.

The release contract says TAG_EXISTS != RELEASE_AUTHORIZED, release refs are created only
from main and are immutable, and the version comes from an explicit record. The repository
had one unsigned baseline tag that every G00-G02 example depends on, no version source of
truth, no tag ruleset and no tag logic in the gate. `git-release-check <tag>` verifies
annotated / on main's first parent / record-bound / unmoved; `git-release-record <version>`
writes badf/releases/<version>.json (binding an existing tag's commit, else HEAD as a
request) and never runs `git tag`; `repo` refuses a recorded release ref that moved.

Every fixture is a scratch clone removed in cleanup; tags are created locally.
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

BASELINE = "BADF-BASELINE-1.0.0"
TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"


def g(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def cli(cmd: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/badf_gate.py", cmd, *args], cwd=str(gate.ROOT), capture_output=True, text=True)


def record_of(r: subprocess.CompletedProcess) -> dict:
    lines = r.stdout.rstrip("\n").splitlines()
    assert lines and lines[-1].startswith("BADF GATE "), r.stdout + r.stderr
    return json.loads("\n".join(lines[:-1]))


def commit_file(repo: Path, name: str, text: str, msg: str) -> str:
    (repo / name).write_text(text, encoding="utf-8"); g(repo, "add", name); g(repo, "commit", "-q", "-m", msg)
    return g(repo, "rev-parse", "HEAD")


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="badf-git-release-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "badf"
        self.base = seed_clone(self.repo, carry_working_state=True)   # carries badf/releases/ and the gate under test
        (self.repo / "badf/releases").mkdir(parents=True, exist_ok=True)

    def write_record(self, version: str, revision: str, tree: str | None = None, **extra) -> Path:
        rec = {"record": "git-release", "schema_version": "1.0.0", "observed_at": "2026-08-29T00:00:00Z", "version": version,
               "tag_ref": f"refs/tags/{version}", "source_ref": f"refs/heads/{gate.DEFAULT_BRANCH}", "source_revision": revision,
               "source_result_tree": tree or g(self.repo, "rev-parse", f"{revision}^{{tree}}"), "policy_epoch": None,
               "provenance": {"annotated": True, "signed": False, "tagger": "t"}, "release_authority": "HUMAN_REQUIRED",
               "disposition": "HUMAN_REQUIRED", "non_coverage": []}
        rec.update(extra)
        p = self.repo / "badf/releases" / f"{version}.json"; p.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
        return p

    def landed_commit(self, name: str) -> str:
        """A new first-parent commit on the scratch's main (as a squash landing would be)."""
        g(self.repo, "checkout", "-q", "-B", gate.DEFAULT_BRANCH, TARGET)
        sha = commit_file(self.repo, f"docs/{name}.md", f"{name}\n", name); g(self.repo, "update-ref", TARGET, sha)
        return sha


class ReleaseCheckTests(_Scratch):
    def test_baseline_tag_is_RELEASE_BOUND(self):
        r = cli("git-release-check", BASELINE, str(self.repo))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rec = record_of(r)
        self.assertEqual((rec["record"], rec["disposition"], rec["version"]), ("git-release-check", "RELEASE_BOUND", BASELINE))
        self.assertTrue(rec["source_revision"].startswith("3f6119b")); self.assertEqual(rec["provenance"]["annotated"], True); self.assertEqual(rec["provenance"]["signed"], False)
        self.assertIn("RELEASE_BOUND", r.stdout.splitlines()[-1])

    def test_lightweight_tag_is_refused(self):
        sha = self.landed_commit("lw"); g(self.repo, "tag", "v0.9.0", sha); self.write_record("v0.9.0", sha)
        r = cli("git-release-check", "v0.9.0", str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("annotated", r.stderr); self.assertIn("BLOCKED", r.stderr)

    def test_tag_off_main_first_parent_is_refused(self):
        g(self.repo, "checkout", "-q", "-b", "topic", self.base); sha = commit_file(self.repo, "t.txt", "t\n", "topic")
        g(self.repo, "tag", "-a", "v0.9.1", "-m", "topic release", sha); self.write_record("v0.9.1", sha)
        r = cli("git-release-check", "v0.9.1", str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("first-parent", r.stderr)

    def test_tag_without_record_is_BLOCKED_tag_exists_is_not_authorized(self):
        sha = self.landed_commit("norec"); g(self.repo, "tag", "-a", "v0.9.2", "-m", "no record", sha)
        r = cli("git-release-check", "v0.9.2", str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("TAG_EXISTS != RELEASE_AUTHORIZED", r.stderr)

    def test_moved_tag_is_refused_as_immutability_breach(self):
        sha1 = self.landed_commit("one"); g(self.repo, "tag", "-a", "v0.9.3", "-m", "one", sha1); self.write_record("v0.9.3", sha1)
        sha2 = self.landed_commit("two"); g(self.repo, "tag", "-d", "v0.9.3"); g(self.repo, "tag", "-a", "v0.9.3", "-m", "moved", sha2)
        r = cli("git-release-check", "v0.9.3", str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("moved", r.stderr.lower()); self.assertIn(sha1[:7], r.stderr); self.assertIn(sha2[:7], r.stderr)

    def test_record_version_must_equal_tag(self):
        sha = self.landed_commit("ver"); g(self.repo, "tag", "-a", "v0.9.4", "-m", "ver", sha)
        rp = self.write_record("v0.9.4", sha); rec = json.loads(rp.read_text(encoding="utf-8")); rec["version"] = "v9.9.9"
        rp.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")   # the file is v0.9.4.json, the record says v9.9.9
        r = cli("git-release-check", "v0.9.4", str(self.repo))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("v9.9.9", r.stderr)


class ReleaseRecordTests(_Scratch):
    def test_release_record_writes_the_binding_as_HUMAN_REQUIRED_and_never_tags(self):
        sha = self.landed_commit("rel"); tags_before = g(self.repo, "tag", "-l")
        r = cli("git-release-record", "v0.1.0", str(self.repo))
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)   # HELD: a request for release authority
        rec = json.loads((self.repo / "badf/releases/v0.1.0.json").read_text(encoding="utf-8"))
        for k in ("record", "schema_version", "observed_at", "version", "tag_ref", "source_ref", "source_revision", "source_result_tree",
                  "policy_epoch", "provenance", "release_authority", "disposition", "non_coverage"):
            self.assertIn(k, rec, k)
        self.assertEqual((rec["record"], rec["version"], rec["tag_ref"], rec["source_revision"], rec["disposition"]),
                         ("git-release", "v0.1.0", "refs/tags/v0.1.0", sha, "HUMAN_REQUIRED"))
        self.assertEqual(rec["source_result_tree"], g(self.repo, "rev-parse", f"{sha}^{{tree}}")); self.assertIsNone(rec["provenance"])
        self.assertEqual(g(self.repo, "tag", "-l"), tags_before, "the record tool must never create a tag")

    def test_release_record_binds_an_existing_tag_to_its_own_commit(self):
        sha = self.landed_commit("older"); g(self.repo, "tag", "-a", "v0.2.0", "-m", "older", sha); self.landed_commit("newer")
        r = cli("git-release-record", "v0.2.0", str(self.repo)); self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        rec = json.loads((self.repo / "badf/releases/v0.2.0.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["source_revision"], sha); self.assertEqual(rec["provenance"], {"annotated": True, "signed": False, "tagger": "t <t@t>"})
        self.assertEqual(cli("git-release-check", "v0.2.0", str(self.repo)).returncode, 0)

    def test_release_record_refuses_off_main_reuse_and_bad_version_forms(self):
        g(self.repo, "checkout", "-q", "-b", "topic", self.base); commit_file(self.repo, "t.txt", "t\n", "topic")
        r = cli("git-release-record", "v0.3.0", str(self.repo)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("first-parent", r.stderr)
        sha = self.landed_commit("reuse"); self.write_record("v0.3.0", self.base)
        r = cli("git-release-record", "v0.3.0", str(self.repo)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("reuse", r.stderr.lower())
        for bad in ("0.3.0", "release-1", "v1.2"):
            with self.subTest(bad=bad):
                r = cli("git-release-record", bad, str(self.repo)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("vX.Y.Z", r.stderr)


class RepoGuardTests(_Scratch):
    def _repo(self) -> subprocess.CompletedProcess:
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=str(self.repo), capture_output=True, text=True, check=True)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"], cwd=str(self.repo), capture_output=True, text=True)

    def test_repo_guard_refuses_a_moved_recorded_tag_and_tolerates_an_absent_one(self):
        sha1 = self.landed_commit("g1"); g(self.repo, "tag", "-a", "v0.4.0", "-m", "g1", sha1); self.write_record("v0.4.0", sha1)
        self.assertEqual(self._repo().returncode, 0)
        lock = json.loads((self.repo / "badf/lockfile.json").read_text(encoding="utf-8"))
        self.assertTrue(any("badf/releases/v0.4.0.json" in k for k in json.dumps(lock).split('"')), "release records must be lockfile-covered")
        sha2 = self.landed_commit("g2"); g(self.repo, "tag", "-d", "v0.4.0"); g(self.repo, "tag", "-a", "v0.4.0", "-m", "moved", sha2)
        r = self._repo(); self.assertEqual(r.returncode, 1, r.stdout + r.stderr); self.assertIn("moved", (r.stdout + r.stderr).lower())
        g(self.repo, "tag", "-d", "v0.4.0")
        r = self._repo(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class ReleasePropertyTests(_Scratch):
    def test_release_check_is_read_only_and_deterministic(self):
        before = (g(self.repo, "rev-parse", "HEAD"), g(self.repo, "status", "--porcelain=v2"), sorted(g(self.repo, "for-each-ref", "--format=%(refname) %(objectname)").splitlines()))
        a = gate.git_release_check(self.repo, BASELINE); b = gate.git_release_check(self.repo, BASELINE)
        self.assertEqual((g(self.repo, "rev-parse", "HEAD"), g(self.repo, "status", "--porcelain=v2"), sorted(g(self.repo, "for-each-ref", "--format=%(refname) %(objectname)").splitlines())), before)
        a.pop("observed_at"); b.pop("observed_at"); self.assertEqual(a, b)


class ReleaseVersioningSubskillTests(unittest.TestCase):
    def test_release_versioning_subskill_registered_and_root_is_active(self):
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertIn("release-versioning", by); entry = by["release-versioning"]
        self.assertEqual(entry["source"], "skills/badf-git/subskills/release-versioning/SKILL.md")
        self.assertEqual((entry["status"], entry["risk_class"], entry["allowed_tools"]), ("IMPLEMENTED", "C1", []))
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertEqual(by["badf-git"]["status"], "ACTIVE")
        text = (gate.ROOT / entry["source"]).read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text); self.assertNotIn("Status: `", text)
        for token in ("TAG_EXISTS != RELEASE_AUTHORIZED", "git-release-check", "git-release-record", "badf/releases/", "MAJOR", "MINOR", "PATCH", "BADF-BASELINE-", "vX.Y.Z", "never"):
            self.assertIn(token, text)
        self.assertTrue((gate.ROOT / "badf/releases" / f"{BASELINE}.json").is_file(), "the historical baseline must be recorded")


if __name__ == "__main__":
    unittest.main()
