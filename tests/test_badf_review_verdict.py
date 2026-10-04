"""AET-B S3 (WP-2026-0158): the review package and the verdict record.

docs/governance/AET_B_SUBSTRATE_DESIGN.md S3: a review is bound to the exact candidate it read, by a
run that is not the author's; a re-review answers every finding its prior left open; a verdict on a
moved candidate is stale. Each claim is a test here, on a real git repository where git is involved:
  - package:   build_review_package refuses a non-ancestor, empty or unknown range;
  - record:    check_review_verdict (run by `repo`) refuses an unbound, self-reviewed, silent or
               self-contradicting verdict, and an incomplete re-review;
  - staleness: review_check reads CURRENT, then STALE once the candidate moves.
"""
import copy
import inspect
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import badf_gate as gate  # noqa: E402

WP = "WP-2026-0950"   # a fixture id; never a real record


class GitRepo:
    def __init__(self, case: unittest.TestCase):
        self.root = Path(tempfile.mkdtemp(prefix="badf-review-"))
        case.addCleanup(shutil.rmtree, self.root, True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@local")
        self.git("config", "user.name", "t")

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), *a], capture_output=True, text=True, check=True).stdout.strip()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")


def candidate_repo(case):
    """base: one file. head: that file edited and a second added."""
    r = GitRepo(case)
    r.write("src/a.py", "a = 1\n")
    base = r.commit("base")
    r.write("src/a.py", "a = 2\n")
    r.write("src/b.py", "b = 1\n")
    head = r.commit("candidate")
    return r, base, head


def finding(fid="VF-001", severity="MAJOR", status="OPEN"):
    return {"finding_id": fid, "severity": severity, "status": status, "summary": "s", "location": "src/a.py:1"}


def verdict(package, vid="REV-01", author="run-author", reviewer="run-reviewer", outcome="REQUEST_CHANGES", findings=None, non_coverage=None):
    return {
        "schema_version": "1.0.0", "id": vid, "work_package_id": WP, "candidate": dict(package),
        "author_run_id": author,
        "reviewer": {"identity": "reviewer-seat", "reviewer_run_id": reviewer, "principal_type": "agent"},
        "verdict": outcome,
        "findings": [finding()] if findings is None else findings,
        "non_coverage": ["performance not assessed"] if non_coverage is None else non_coverage,
        "recorded_at": "2026-10-04T00:00:00Z",
    }


def fixed_package():
    pkg = {"work_package_id": WP, "base_sha": "a" * 40, "head_sha": "b" * 40, "content_tree": "c" * 40,
           "changed_files": ["src/a.py"], "diff_digest": "sha256:" + "d" * 64}
    pkg["package_digest"] = gate.review_package_digest(pkg)
    return pkg


class ReviewPackage(unittest.TestCase):
    def test_a_real_range_builds_a_reproducible_package(self):
        r, base, head = candidate_repo(self)
        p1 = gate.build_review_package(r.root, WP, base, head)
        p2 = gate.build_review_package(r.root, WP, base, "HEAD")
        self.assertEqual(p1, p2)
        self.assertEqual(p1["changed_files"], ["src/a.py", "src/b.py"])
        self.assertEqual((p1["base_sha"], p1["head_sha"]), (base, head))
        self.assertEqual(p1["package_digest"], gate.review_package_digest(p1))
        self.assertEqual(p1["content_tree"], gate.content_tree(r.root, WP, head))

    def test_a_non_ancestor_base_is_refused(self):
        r, base, head = candidate_repo(self)
        r.git("checkout", "-q", "-b", "side", base)
        r.write("src/c.py", "c = 1\n")
        side = r.commit("side")
        with self.assertRaisesRegex(gate.ValidationError, "not an ancestor"):
            gate.build_review_package(r.root, WP, side, head)

    def test_an_empty_range_is_refused(self):
        r, base, head = candidate_repo(self)
        with self.assertRaisesRegex(gate.ValidationError, "same commit"):
            gate.build_review_package(r.root, WP, head, head)

    def test_a_range_touching_only_the_work_package_records_is_empty(self):
        r, base, head = candidate_repo(self)
        r.write(f"work/{WP}/work-package.json", "{}\n")
        r.write("badf/lockfile.json", "{}\n")
        only_records = r.commit("records only")
        with self.assertRaisesRegex(gate.ValidationError, "changes nothing outside"):
            gate.build_review_package(r.root, WP, head, only_records)

    def test_an_unknown_revision_is_refused(self):
        r, base, head = candidate_repo(self)
        with self.assertRaisesRegex(gate.ValidationError, "is not a commit"):
            gate.build_review_package(r.root, WP, "0" * 40, head)

    def test_recording_a_verdict_does_not_move_the_package(self):
        r, base, head = candidate_repo(self)
        before = gate.build_review_package(r.root, WP, base, head)
        r.write(f"work/{WP}/reviews/REV-01.json", json.dumps(verdict(before)))
        after_head = r.commit("record the verdict")
        after = gate.build_review_package(r.root, WP, base, after_head)
        # The package digest binds the head sha, so it changes; what review-check compares does not.
        for k in ("base_sha", "content_tree", "changed_files", "diff_digest"):
            self.assertEqual(after[k], before[k], k)
        self.assertNotEqual(after["head_sha"], before["head_sha"])


class VerdictRecord(unittest.TestCase):
    def setUp(self):
        self.pkg = fixed_package()

    def problems(self, v, prior=None):
        return gate.check_review_verdict(v, WP, prior)

    def test_a_well_formed_verdict_passes(self):
        self.assertEqual(self.problems(verdict(self.pkg)), [])

    def test_an_edited_binding_is_refused(self):
        v = verdict(self.pkg)
        v["candidate"]["content_tree"] = "e" * 40
        self.assertIn("does not recompute", " ".join(self.problems(v)))

    def test_the_author_run_reviewing_itself_is_refused(self):
        for reviewer in ("run-author", "RUN-Author"):
            with self.subTest(reviewer=reviewer):
                self.assertIn("is the authoring run", " ".join(self.problems(verdict(self.pkg, reviewer=reviewer))))

    def test_blank_run_ids_are_refused_by_the_schema(self):
        self.assertTrue(self.problems(verdict(self.pkg, author=" ")))

    def test_no_findings_and_no_non_coverage_is_refused(self):
        v = verdict(self.pkg, outcome="APPROVE", findings=[], non_coverage=[])
        self.assertIn("comprehensive coverage", " ".join(self.problems(v)))
        self.assertEqual(self.problems(verdict(self.pkg, outcome="APPROVE", findings=[])), [])

    def test_approve_beside_an_open_blocking_finding_is_refused(self):
        for sev in ("MAJOR", "CRITICAL"):
            with self.subTest(severity=sev):
                v = verdict(self.pkg, outcome="APPROVE", findings=[finding(severity=sev)])
                self.assertIn("contradicts its own OPEN blocking", " ".join(self.problems(v)))
        self.assertEqual(self.problems(verdict(self.pkg, outcome="APPROVE", findings=[finding(severity="MINOR")])), [])
        self.assertEqual(self.problems(verdict(self.pkg, outcome="APPROVE", findings=[finding(status="RESOLVED")])), [])

    def test_another_work_packages_package_is_refused(self):
        v = verdict(self.pkg)
        v["candidate"]["work_package_id"] = "WP-2026-0951"
        self.assertIn("package of another work package", " ".join(self.problems(v)))
        self.assertIn("is not the work package it is recorded under", " ".join(gate.check_review_verdict(verdict(self.pkg), "WP-2026-0951")))

    def test_duplicate_finding_ids_are_refused(self):
        v = verdict(self.pkg, findings=[finding(), finding()])
        self.assertIn("duplicate finding id", " ".join(self.problems(v)))

    def test_an_undeclared_key_is_refused(self):
        v = verdict(self.pkg)
        v["approved_by_authority"] = True
        self.assertIn("undefined key", " ".join(self.problems(v)))


class ReReview(unittest.TestCase):
    def setUp(self):
        pkg = fixed_package()
        self.prior = verdict(pkg, findings=[finding("VF-001", "MAJOR"), finding("VF-002", "MINOR"), finding("VF-003", "MAJOR", "RESOLVED")])
        self.pkg = pkg

    def rereview(self, dispositions, outcome="APPROVE"):
        v = verdict(self.pkg, vid="REV-02", outcome=outcome, findings=[])
        v["prior_review"] = "REV-01"
        v["prior_findings"] = [{"finding_id": f, "disposition": d, "note": "n"} for f, d in dispositions]
        return v

    def problems(self, v, prior="default"):
        return gate.check_review_verdict(v, WP, self.prior if prior == "default" else prior)

    def test_a_complete_re_review_passes(self):
        self.assertEqual(self.problems(self.rereview([("VF-001", "ADDRESSED"), ("VF-002", "NOT_ADDRESSED")])), [])

    def test_a_prior_open_finding_left_undispositioned_is_refused(self):
        self.assertIn("without an ADDRESSED / NOT_ADDRESSED disposition", " ".join(self.problems(self.rereview([("VF-001", "ADDRESSED")]))))

    def test_dispositioning_a_finding_that_was_not_open_is_refused(self):
        v = self.rereview([("VF-001", "ADDRESSED"), ("VF-002", "ADDRESSED"), ("VF-003", "ADDRESSED")])
        self.assertIn("did not leave OPEN", " ".join(self.problems(v)))

    def test_a_finding_dispositioned_twice_is_refused(self):
        v = self.rereview([("VF-001", "ADDRESSED"), ("VF-001", "NOT_ADDRESSED"), ("VF-002", "ADDRESSED")])
        self.assertIn("more than once", " ".join(self.problems(v)))

    def test_approve_with_a_blocking_prior_finding_not_addressed_is_refused(self):
        v = self.rereview([("VF-001", "NOT_ADDRESSED"), ("VF-002", "ADDRESSED")])
        self.assertIn("NOT_ADDRESSED", " ".join(self.problems(v)))
        self.assertEqual(self.problems(self.rereview([("VF-001", "NOT_ADDRESSED"), ("VF-002", "ADDRESSED")], outcome="REQUEST_CHANGES")), [])

    def test_a_prior_that_is_not_recorded_is_refused(self):
        self.assertIn("is not recorded", " ".join(self.problems(self.rereview([]), prior=None)))

    def test_dispositions_without_a_prior_review_are_refused(self):
        v = self.rereview([("VF-001", "ADDRESSED"), ("VF-002", "ADDRESSED")])
        del v["prior_review"]
        self.assertIn("without prior_review", " ".join(self.problems(v, prior=None)))


class RecordedChains(unittest.TestCase):
    """load_review_verdicts / review_problems read work/<WP>/reviews/ on disk."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="badf-review-chain-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.dir = self.root / "work" / WP / "reviews"
        self.dir.mkdir(parents=True)
        self.pkg = fixed_package()

    def put(self, v, name=None):
        (self.dir / (name or f"{v['id']}.json")).write_text(json.dumps(v), encoding="utf-8")

    def linked(self, vid, prior):
        v = verdict(self.pkg, vid=vid, findings=[finding()])
        v["prior_review"] = prior
        v["prior_findings"] = [{"finding_id": "VF-001", "disposition": "ADDRESSED", "note": "n"}]
        return v

    def test_a_chain_passes_and_its_end_is_the_latest(self):
        self.put(verdict(self.pkg, vid="REV-01"))
        self.put(self.linked("REV-02", "REV-01"))
        verdicts, problems = gate.review_problems(self.root, WP)
        self.assertEqual(problems, [])
        self.assertEqual(gate.review_latest(verdicts)["id"], "REV-02")

    def test_a_cycle_is_refused(self):
        self.put(self.linked("REV-01", "REV-02"))
        self.put(self.linked("REV-02", "REV-01"))
        self.assertIn("returns to", " ".join(gate.review_problems(self.root, WP)[1]))

    def test_two_unrelated_chains_are_refused(self):
        self.put(verdict(self.pkg, vid="REV-01"))
        self.put(verdict(self.pkg, vid="REV-02"))
        self.assertIn("separate review chain", " ".join(gate.review_problems(self.root, WP)[1]))

    def test_a_file_not_named_by_its_id_is_refused(self):
        self.put(verdict(self.pkg, vid="REV-01"), name="REV-07.json")
        with self.assertRaisesRegex(gate.ValidationError, "file name must be its id"):
            gate.load_review_verdicts(self.root, WP)


class Staleness(unittest.TestCase):
    def setUp(self):
        self.r, self.base, self.head = candidate_repo(self)
        pkg = gate.build_review_package(self.r.root, WP, self.base, self.head)
        self.r.write(f"work/{WP}/reviews/REV-01.json", json.dumps(verdict(pkg)))
        self.r.commit("record the verdict")

    def cli(self, *a):
        return subprocess.run([sys.executable, str(ROOT / "scripts/badf_gate.py"), *a], capture_output=True, text=True)

    def test_current_until_the_candidate_moves_then_stale(self):
        self.assertEqual(gate.review_check(self.r.root, WP)["disposition"], "CURRENT")
        self.r.write("src/a.py", "a = 3\n")
        self.r.commit("move the candidate")
        v = gate.review_check(self.r.root, WP)
        self.assertEqual(v["disposition"], "STALE")
        self.assertIn("content_tree", v["moved"])

    def test_no_verdict_is_none(self):
        shutil.rmtree(self.r.root / "work" / WP)
        self.r.commit("drop the verdict")
        self.assertEqual(gate.review_check(self.r.root, WP)["disposition"], "NONE")

    def test_the_cli_exit_codes(self):
        r = self.cli("review-check", WP, str(self.r.root))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("is CURRENT", r.stdout)
        self.r.write("src/b.py", "b = 2\n")
        self.r.commit("move")
        r = self.cli("review-check", WP, str(self.r.root))
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("STALE", r.stdout)
        r = self.cli("review-package", WP, str(self.r.root), "--base", self.base)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("review-package", WP, str(self.r.root), "--base", "HEAD", "--head", "HEAD")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


class Wiring(unittest.TestCase):
    def test_repo_validation_runs_the_verdict_check(self):
        self.assertIn("verify_review_verdicts()", inspect.getsource(gate.validate_repo))

    def test_the_real_tree_passes_and_says_so(self):
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BADF REVIEW VERDICTS:", r.stdout)

    def test_the_schema_holds_what_the_code_reads(self):
        sch = json.loads((ROOT / "schemas/review-verdict.schema.json").read_text(encoding="utf-8"))
        self.assertIs(sch["additionalProperties"], False)
        self.assertEqual(sorted(sch["properties"]["candidate"]["required"]),
                         sorted(("work_package_id", "package_digest") + gate._REVIEW_PACKAGE_FIELDS))
        self.assertEqual(sch["properties"]["prior_findings"]["items"]["properties"]["disposition"]["enum"],
                         list(gate.REVIEW_FINDING_DISPOSITIONS))


if __name__ == "__main__":
    unittest.main()
