"""Composed-tree gate (BADF-WP-0024, Issue #21).

PR #30 was green and its squash 30186c5 turned main red: the PR runner's
origin/main was the pre-merge ledger, and the merge itself changed what the
tests read. scripts/badf_compose.py builds the tree that WOULD land -- base +
candidate squashed with the candidate's message -- points origin/main at it,
and runs `repo` and the suite there. It refuses a message the ledger would
not see, refuses to nest, and writes nothing to the source repository. Every
run here uses a scratch framework whose candidate is a commit of the working
tree, so the composed tree is the one that would actually land.
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

COMPOSE = ["python3", "scripts/badf_compose.py"]
WP = "WP-2026-0900"   # the fixture ships its OWN record: never a real WP whose status the ledger may change
MSG = "candidate: exercise the composed-tree gate\n\nWork-Package: BADF-WP-0900\nCloses #21\n"
FAST = "test_badf_traceability.py"   # the inner suite is restricted; compose must SAY so


def git(root, *a):
    return subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t", *a],
                          capture_output=True, text=True, check=True).stdout.strip()


def tree_state(root: Path) -> dict:
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob("*") if p.is_file() and ".git" not in p.parts}
    refs = git(root, "for-each-ref", "--format=%(refname) %(objectname)")
    return {"files": files, "refs": refs}


DEPTH = int(os.environ.get("BADF_COMPOSE_DEPTH", "0") or 0)
MARKER = "badf-compose-candidate.txt"


@unittest.skipIf(DEPTH >= 2, "depth 2 inside a composed-tree run; compose nests one level only")
class ComposeScratch(unittest.TestCase):
    """A scratch framework: origin/main = the real authorized ledger; a
    candidate branch = one commit of the current working tree."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp) / "framework"
        self.base = seed_clone(self.repo)
        git(self.repo, "checkout", "-q", "-B", "cand", self.base)
        for item in gate.ROOT.iterdir():
            if item.name in (".git", "__pycache__"):
                continue
            dst = self.repo / item.name
            if item.is_dir():
                shutil.rmtree(dst, ignore_errors=True)
                shutil.copytree(item, dst, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            else:
                shutil.copy2(item, dst)
        # On main after a merge the working tree IS origin/main and there is
        # nothing to commit (0b88c74, run 33104985912). Every candidate differs
        # from its base by construction.
        (self.repo / MARKER).write_text("this candidate differs from its base by construction\n")
        # its own work-package record, so the ledger has something to see whatever
        # the real records say (WP-0024's was reconciled and broke the first version)
        src = sorted((self.repo / "work").glob("WP-2026-*/work-package.json"))[-1]
        rec = json.loads(src.read_text()); rec["id"] = WP; rec["status"] = "IN_PROGRESS"
        rec["external_target"] = {k: v for k, v in rec.get("external_target", {}).items() if k != "landed_as"}
        rec.pop("landing_not_on_ledger", None)
        (self.repo / "work" / WP).mkdir(); (self.repo / "work" / WP / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")
        subprocess.run(["python3", "scripts/badf_gate.py", "lock"], cwd=self.repo, capture_output=True, check=True)
        self.msg = Path(self.tmp) / "msg.txt"; self.msg.write_text(MSG)
        # keep the depth: stripping it would restart at depth 0 inside the composed run and recurse
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_") or k == "BADF_COMPOSE_DEPTH"}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def commit_candidate(self, message=MSG):
        git(self.repo, "add", "-A")
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-F", "-"],
                       input=message, text=True, check=True)
        return git(self.repo, "rev-parse", "HEAD")

    def compose(self, *extra, base=None, candidate=None, message=None, **env_over):
        env = dict(self.env); env.update(env_over)
        cmd = [*COMPOSE, "--repo", str(self.repo), "--base", base or self.base,
               "--candidate", candidate or git(self.repo, "rev-parse", "cand"),
               "--message-file", str(message or self.msg), "--tests", FAST, *extra]
        return subprocess.run(cmd, cwd=str(gate.ROOT), capture_output=True, text=True, env=env)


class ComposeVerdictTests(ComposeScratch):

    def test_green_candidate_passes_and_the_ledger_sees_the_landing(self):
        self.commit_candidate()
        r = self.compose()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BADF COMPOSE PASS", r.stdout)
        self.assertIn(f"{WP} LANDED_UNRECONCILED", r.stdout, "the composed ledger did not see the landing")
        self.assertIn(f"suite pattern: {FAST}", r.stdout, "a restricted suite must be printed, never silent")
        self.assertIn("shape: host", r.stdout)

    def test_composed_clone_carries_the_framework_tags(self):
        """examples/gate-dossier.G00.json names a TAG as source_revision. The
        first version of compose fetched by SHA without tags and reported the
        dossier tests red on a green tree. test_badf_gate.py needs the tag."""
        self.commit_candidate()
        r = self.compose("--tests", "test_badf_gate.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BADF COMPOSE PASS", r.stdout)

    def test_red_composed_suite_fails_and_names_the_test(self):
        (self.repo / "tests/test_zz_red.py").write_text(
            "import unittest\nclass RedTests(unittest.TestCase):\n    def test_composed_world_is_different(self):\n        self.fail('red on the composed tree')\n")
        subprocess.run(["python3", "scripts/badf_gate.py", "lock"], cwd=self.repo, capture_output=True, check=True, env=self.env)
        self.commit_candidate()
        r = self.compose("--tests", "test_zz_red.py")
        self.assertNotEqual(r.returncode, 0, "a red composed suite passed")
        self.assertIn("BADF COMPOSE FAIL", r.stdout)
        self.assertIn("test_composed_world_is_different", r.stdout)

    def test_red_composed_repo_check_fails(self):
        (self.repo / "AGENTS.md").write_text((self.repo / "AGENTS.md").read_text() + "\n<!-- unsigned edit -->\n")
        self.commit_candidate()   # locked file changed, lockfile not re-signed
        r = self.compose()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("repo: FAIL", r.stdout)
        self.assertIn("integrity drift", r.stdout + r.stderr)

    def test_message_without_a_work_package_line_is_refused_before_any_work(self):
        self.commit_candidate()
        bad = Path(self.tmp) / "bad.txt"; bad.write_text("just a title\n\nCloses #21\n")
        r = self.compose(message=bad)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("carries no Work-Package line", r.stdout + r.stderr)
        self.assertNotIn("BADF COMPOSE:", r.stdout, "work was done before the message was checked")

    def test_message_naming_a_work_package_the_candidate_does_not_carry_fails(self):
        """The line is there, so the pre-check passes; the composed ledger must
        still be asked whether THAT work package actually landed."""
        self.commit_candidate()
        other = Path(self.tmp) / "other.txt"; other.write_text("title\n\nWork-Package: BADF-WP-0099\nCloses #21\n")
        r = self.compose(message=other)
        self.assertNotEqual(r.returncode, 0, "a work package with no record passed")
        self.assertIn("no work package record for WP-2026-0099", r.stdout)

    def test_candidate_that_does_not_compose_fails(self):
        (self.repo / "README.md").write_text("# candidate's README\n")
        cand = self.commit_candidate()
        git(self.repo, "checkout", "-q", "-B", "newmain", self.base)
        (self.repo / "README.md").write_text("# main moved on\n")
        git(self.repo, "add", "-A"); newbase = self.commit_candidate("main moved\n")
        r = self.compose(base=newbase, candidate=cand)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not compose", r.stdout + r.stderr)

    def test_refuses_to_nest_beyond_depth_two(self):
        self.commit_candidate()
        r = self.compose(BADF_COMPOSE_DEPTH="2")
        self.assertNotEqual(r.returncode, 0); self.assertIn("nest", r.stdout + r.stderr)

    def test_candidate_differs_from_base_even_when_the_tree_equals_it(self):
        """The fixture with NOTHING copied: the marker alone must make a commit."""
        bare = Path(self.tmp) / "bare"; base = seed_clone(bare)
        git(bare, "checkout", "-q", "-B", "cand", base)
        (bare / MARKER).write_text("marker\n"); git(bare, "add", "-A")
        subprocess.run(["git", "-C", str(bare), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "cand"], check=True)
        self.assertEqual(git(bare, "diff", "--name-only", base, "cand").splitlines(), [MARKER])

    def test_writes_nothing_to_the_source_repository(self):
        self.commit_candidate(); before = tree_state(self.repo)
        r = self.compose(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(tree_state(self.repo), before, "compose modified the source repository or its refs")

    def test_ci_shape_is_honoured_and_declared(self):
        self.commit_candidate()
        r = self.compose("--ci-shape")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("shape: CI", r.stdout)

    def test_unreachable_candidate_is_refused_not_guessed(self):
        self.commit_candidate()
        r = self.compose(candidate="0" * 40)
        self.assertNotEqual(r.returncode, 0); self.assertIn("not reachable", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
