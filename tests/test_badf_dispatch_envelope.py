"""AET-B S2 (WP-2026-0159): the dispatch envelope.

docs/governance/AET_B_SUBSTRATE_DESIGN.md S2: a dispatch hands one bounded piece of a work package to
one seat, and it may only narrow the work package. Each claim is a test here:
  - record:  check_dispatch_envelope (run by `repo`) refuses a vacant or unknown seat, a path, glob,
             tool, budget or stop-condition set that widens the work package, an invalid review
             designation, and a missing, misplaced or altered brief;
  - read-back: dispatch_check, on a real git repository, refuses a change outside the envelope and
             holds required-review work until S3 records a CURRENT APPROVE by the named seat.
"""
import copy
import hashlib
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
BRIEF_PATH = f"work/{WP}/dispatch/DSP-01.brief.md"
BRIEF = b"Implement the parser change in src/parser.py; add its test.\n"

SEATS = {"BUILDER": {"id": "BUILDER", "status": "HELD"}, "REVIEWER": {"id": "REVIEWER", "status": "HELD"},
         "EMPTY": {"id": "EMPTY", "status": "VACANT"}}
TOOLS = {"local-filesystem": "ACTIVE", "local-shell": "ACTIVE", "evoskill": "PROPOSED"}


def digest(b):
    return "sha256:" + hashlib.sha256(b).hexdigest()


def record():
    return {"id": WP, "change_class": "C1",
            "expected_surfaces": {"files": ["src/parser.py", "tests/**", "docs/*.md"]},
            "execution_budget": {"max_attempts": 3},
            "stop_conditions": ["AUTHORITY_CONFLICT", "BUDGET_EXHAUSTED"]}


def envelope(**over):
    env = {
        "schema_version": "1.0.0", "id": "DSP-01", "work_package_id": WP, "seat": "BUILDER",
        "base_sha": "a" * 40, "allowed_paths": ["src/parser.py", "tests/**"], "allowed_tools": ["local-filesystem"],
        "budget": {"max_attempts": 2}, "stop_conditions": ["AUTHORITY_CONFLICT", "BUDGET_EXHAUSTED", "POLICY_BYPASS"],
        "required_evidence": ["unit-test log"], "review": {"required": True, "reviewer_seat": "REVIEWER"},
        "brief": {"path": BRIEF_PATH, "digest": digest(BRIEF)},
        "issued_by_run_id": "run-dispatcher", "recorded_at": "2026-10-04T00:00:00Z",
    }
    env.update(over)
    return env


class EnvelopeRecord(unittest.TestCase):
    def problems(self, env, rec=None, brief=BRIEF):
        return " ".join(gate.check_dispatch_envelope(env, WP, rec or record(), SEATS, TOOLS, brief))

    def test_a_well_formed_envelope_passes(self):
        self.assertEqual(self.problems(envelope()), "")

    def test_the_seat_must_be_rostered_and_held(self):
        self.assertIn("is not a seat", self.problems(envelope(seat="NOBODY")))
        self.assertIn("never to a vacancy", self.problems(envelope(seat="EMPTY")))

    def test_an_allowed_path_outside_the_surfaces_is_refused(self):
        self.assertIn("not within", self.problems(envelope(allowed_paths=["src/parser.py", "scripts/badf_gate.py"])))

    def test_literal_paths_covered_by_a_surface_glob_pass(self):
        self.assertEqual(self.problems(envelope(allowed_paths=["tests/test_parser.py", "docs/a.md"])), "")

    def test_a_new_glob_is_refused_even_if_narrower(self):
        self.assertIn("not within", self.problems(envelope(allowed_paths=["tests/unit/**"])))
        self.assertIn("not within", self.problems(envelope(allowed_paths=["src/*.py"])))

    def test_empty_allowed_paths_tools_stops_or_evidence_are_refused(self):
        for key, msg in (("allowed_paths", "allows nothing"), ("allowed_tools", "allowed_tools is empty"),
                         ("required_evidence", "required_evidence is empty")):
            with self.subTest(key=key):
                self.assertIn(msg, self.problems(envelope(**{key: []})))
        rec = record()
        rec["stop_conditions"] = []
        self.assertIn("stop_conditions is empty", self.problems(envelope(stop_conditions=[]), rec))

    def test_tools_must_be_registered_and_active(self):
        self.assertIn("not registered", self.problems(envelope(allowed_tools=["curl"])))
        self.assertIn("not ACTIVE", self.problems(envelope(allowed_tools=["evoskill"])))

    def test_the_budget_is_bounded_by_the_work_package(self):
        self.assertIn("outside 1..3", self.problems(envelope(budget={"max_attempts": 4})))
        self.assertIn("outside 1..3", self.problems(envelope(budget={"max_attempts": 0})))
        self.assertEqual(self.problems(envelope(budget={"max_attempts": 3})), "")
        rec = record()
        del rec["execution_budget"]
        self.assertIn("declares no execution_budget", self.problems(envelope(), rec))

    def test_a_work_package_stop_condition_cannot_be_dropped(self):
        self.assertIn("are dropped", self.problems(envelope(stop_conditions=["AUTHORITY_CONFLICT"])))

    def test_review_designation(self):
        self.assertIn("names no reviewer_seat", self.problems(envelope(review={"required": True})))
        self.assertIn("does not review its own dispatch", self.problems(envelope(review={"required": True, "reviewer_seat": "BUILDER"})))
        self.assertIn("never to a vacancy", self.problems(envelope(review={"required": True, "reviewer_seat": "EMPTY"})))
        self.assertIn("is decoration", self.problems(envelope(review={"required": False, "reviewer_seat": "REVIEWER"})))
        self.assertEqual(self.problems(envelope(review={"required": False})), "")

    def test_the_brief_is_placed_present_and_bound(self):
        self.assertIn("is not present", self.problems(envelope(), brief=None))
        self.assertIn("does not match brief.digest", self.problems(envelope(), brief=BRIEF + b"and more\n"))
        for bad in ("work/WP-2026-0951/dispatch/x.md", f"work/{WP}/dispatch/../../../etc/x.md", f"work/{WP}/dispatch/x.txt", "x.md"):
            with self.subTest(path=bad):
                self.assertIn("is not a .md file under", self.problems(envelope(brief={"path": bad, "digest": digest(BRIEF)})))

    def test_another_work_packages_envelope_is_refused(self):
        self.assertIn("is not the work package", self.problems(envelope(work_package_id="WP-2026-0951")))

    def test_an_undeclared_key_is_refused(self):
        self.assertIn("undefined key", self.problems(envelope(granted_authority="all")))


class DispatchRepo:
    """A real git repository with the registries, a work package record, an envelope and its brief."""

    def __init__(self, case, review_required=True):
        self.root = Path(tempfile.mkdtemp(prefix="badf-dispatch-"))
        case.addCleanup(shutil.rmtree, self.root, True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@local")
        self.git("config", "user.name", "t")
        self.write("badf/seats.json", json.dumps({"seats": list(SEATS.values())}))
        self.write("badf/tool-registry.json", json.dumps({"tools": [{"id": k, "status": v} for k, v in TOOLS.items()]}))
        self.write(f"work/{WP}/work-package.json", json.dumps(record()))
        self.write("src/parser.py", "x = 1\n")
        self.base = self.commit("base")
        review = {"required": True, "reviewer_seat": "REVIEWER"} if review_required else {"required": False}
        self.write(BRIEF_PATH, BRIEF.decode())
        self.write(f"work/{WP}/dispatch/DSP-01.json", json.dumps(envelope(base_sha=self.base, review=review)))
        self.commit("dispatch")

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

    def record_verdict(self, vid="REV-01", outcome="APPROVE", identity="REVIEWER", prior=None):
        pkg = gate.build_review_package(self.root, WP, self.base, "HEAD")
        v = {"schema_version": "1.0.0", "id": vid, "work_package_id": WP, "candidate": pkg, "author_run_id": "run-builder",
             "reviewer": {"identity": identity, "reviewer_run_id": f"run-{vid}", "principal_type": "agent"},
             "verdict": outcome, "findings": [], "non_coverage": ["performance not assessed"], "recorded_at": "2026-10-04T00:00:00Z"}
        if prior:
            v["prior_review"] = prior
            v["prior_findings"] = []
        self.write(f"work/{WP}/reviews/{vid}.json", json.dumps(v))
        self.commit(f"record {vid}")


class DispatchCheck(unittest.TestCase):
    def test_work_within_the_envelope_with_no_review_required_is_complete(self):
        r = DispatchRepo(self, review_required=False)
        r.write("src/parser.py", "x = 2\n")
        r.write("tests/test_parser.py", "pass\n")
        r.commit("work")
        v = gate.dispatch_check(r.root, WP, "DSP-01")
        self.assertEqual((v["scope"], v["review"], v["disposition"]), ("WITHIN_ENVELOPE", "NOT_REQUIRED", "COMPLETE"))
        self.assertEqual(v["changed_files"], ["src/parser.py", "tests/test_parser.py"])

    def test_a_change_outside_the_envelope_is_refused(self):
        r = DispatchRepo(self, review_required=False)
        r.write("src/parser.py", "x = 2\n")
        r.write("docs/notes.md", "within the work package, but not the envelope\n")
        r.commit("work")
        with self.assertRaisesRegex(gate.ValidationError, r"changed \['docs/notes.md'\], outside its allowed_paths"):
            gate.dispatch_check(r.root, WP, "DSP-01")

    def test_required_review_holds_until_a_current_approve_by_the_named_seat(self):
        r = DispatchRepo(self)
        r.write("src/parser.py", "x = 2\n")
        r.commit("work")
        v = gate.dispatch_check(r.root, WP, "DSP-01")
        self.assertEqual((v["disposition"], v["review"]), ("HELD", "NONE"))
        r.record_verdict("REV-01", outcome="REQUEST_CHANGES")
        v = gate.dispatch_check(r.root, WP, "DSP-01")
        self.assertEqual(v["disposition"], "HELD")
        self.assertIn("REQUEST_CHANGES", v["held_because"])
        r.record_verdict("REV-02", outcome="APPROVE", identity="BUILDER", prior="REV-01")
        v = gate.dispatch_check(r.root, WP, "DSP-01")
        self.assertEqual(v["disposition"], "HELD")
        self.assertIn("not the envelope's reviewer_seat", v["held_because"])
        r.record_verdict("REV-03", outcome="APPROVE", identity="REVIEWER", prior="REV-02")
        self.assertEqual(gate.dispatch_check(r.root, WP, "DSP-01")["disposition"], "COMPLETE")
        r.write("src/parser.py", "x = 3\n")
        r.commit("move after approval")
        v = gate.dispatch_check(r.root, WP, "DSP-01")
        self.assertEqual((v["disposition"], v["review"]), ("HELD", "STALE"))

    def test_an_unknown_dispatch_and_an_invalid_envelope_are_refused(self):
        r = DispatchRepo(self, review_required=False)
        r.write("src/parser.py", "x = 2\n")
        r.commit("work")
        with self.assertRaisesRegex(gate.ValidationError, "no dispatch envelope DSP-09"):
            gate.dispatch_check(r.root, WP, "DSP-09")
        r.write(BRIEF_PATH, "edited after dispatch\n")
        r.commit("edit the brief")
        with self.assertRaisesRegex(gate.ValidationError, "does not match brief.digest"):
            gate.dispatch_check(r.root, WP, "DSP-01")

    def test_a_file_not_named_by_its_id_is_refused(self):
        r = DispatchRepo(self, review_required=False)
        (r.root / f"work/{WP}/dispatch/DSP-01.json").rename(r.root / f"work/{WP}/dispatch/DSP-07.json")
        with self.assertRaisesRegex(gate.ValidationError, "file name must be its id"):
            gate.load_dispatch_envelopes(r.root, WP)

    def test_the_cli_exit_codes(self):
        def cli(*a):
            return subprocess.run([sys.executable, str(ROOT / "scripts/badf_gate.py"), "dispatch-check", WP, "DSP-01", str(r.root), *a],
                                  capture_output=True, text=True)
        r = DispatchRepo(self)
        r.write("src/parser.py", "x = 2\n")
        r.commit("work")
        p = cli()
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
        r.record_verdict("REV-01")
        p = cli()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        r.write("scripts/x.py", "outside\n")
        r.commit("stray")
        p = cli()
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("outside its allowed_paths", p.stderr)


class Wiring(unittest.TestCase):
    def test_repo_validation_runs_the_envelope_check(self):
        self.assertIn("verify_dispatch_envelopes()", inspect.getsource(gate.validate_repo))

    def test_the_real_tree_passes_and_says_so(self):
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BADF DISPATCH ENVELOPES:", r.stdout)

    def test_the_schema_stop_conditions_are_the_work_package_schemas(self):
        env = json.loads((ROOT / "schemas/dispatch-envelope.schema.json").read_text(encoding="utf-8"))
        wp = json.loads((ROOT / "schemas/work-package.schema.json").read_text(encoding="utf-8"))
        self.assertIs(env["additionalProperties"], False)
        self.assertEqual(env["properties"]["stop_conditions"]["items"]["enum"], wp["properties"]["stop_conditions"]["items"]["enum"])


if __name__ == "__main__":
    unittest.main()
