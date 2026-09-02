"""badf-build BLD-C (BADF-WP-0099, #194): seven deterministic G07 controls in the canonical gate.

C1 authority before mutation (BLD-I03) · C2 exact baseline (BLD-I02) · C3 scope containment
enforced (BLD-I04) · C4 red before green, exceptions explicit (BLD-I07/I08) · C5 fresh verification
(BLD-I09) · C6 budget and stop dominate (BLD-I11..I13) · C7 delegation is a strict subset (BLD-I10).
Each control fires only on the field that declares it; undeclared fields leave BLD-B behaviour intact.
PASS-path rules are exercised at the function level inside the scratch (BADF has no PASS G07 example).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

WP = "WP-2026-0997"
DEM = "BADF-DEM-0997"


class _Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        self.base = seed_clone(self.root, carry_working_state=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        on_ledger = set(self.git("ls-tree", "-r", "--name-only", "origin/main", "--", "work/").splitlines())
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            if rec.relative_to(self.root).as_posix() not in on_ledger:
                shutil.rmtree(rec.parent)
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            subprocess.run([sys.executable, "scripts/badf_gate.py", "reconcile", rec.parent.name], cwd=self.root, env=self.env, capture_output=True)
        (self.root / "README.md").write_text((self.root / "README.md").read_text() + "\n<!-- WP-0997 deliverable -->\n")
        self.git("add", "README.md"); self.commit("deliverable")
        self.wp_dir = self.root / "work" / WP; self.wp_dir.mkdir(parents=True)
        self.write_demand("AUTHORIZED", "human")
        self.write_wp(); self.lock()

    def write_demand(self, status, principal_type):
        src = json.loads((self.root / "badf/demands/BADF-DEM-0001.json").read_text(encoding="utf-8"))
        src["demand_id"] = DEM; src["status"] = status; src["authorized_by"] = {"principal": "operator", "principal_type": principal_type}
        (self.root / "badf/demands" / f"{DEM}.json").write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")

    def write_wp(self, **extra):
        rec = {"$schema": "../../schemas/work-package.schema.json", "schema_version": "1.0.0", "id": WP,
               "title": "scratch build-controls work package", "owner": "human_sponsor", "repository": "bstBizEra/badf",
               "demand": DEM, "objective": "x", "business_value": "x", "in_scope": ["x"], "out_of_scope": ["y"],
               "target_gate": "G07", "change_class": "C2", "data_classification": "internal",
               "acceptance_criteria": ["x"], "permissions": ["write: bstBizEra/badf via PR"], "tests": ["tests/test_probe.py (3)"],
               "evidence": ["source-change"], "rollback": {"reversible": True, "method": "revert"},
               "status": "IN_PROGRESS", "external_target": {"repository": "bstBizEra/badf", "branch": "main", "base_revision": self.base}}
        rec.update(extra); (self.wp_dir / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")

    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def git(self, *a): return subprocess.run(["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t", *a], capture_output=True, text=True, check=True).stdout.strip()
    def commit(self, msg): self.git("commit", "-q", "-m", msg)
    def lock(self): subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
    def gate_cmd(self, *args): return subprocess.run([sys.executable, "scripts/badf_gate.py", *args], cwd=self.root, env=self.env, capture_output=True, text=True)
    def self_dossier(self): return self.gate_cmd("self-dossier", WP)
    def dossier(self): return self.gate_cmd("dossier", f"work/{WP}/gate-dossier.G07.json")
    def in_scratch(self, code):
        """Run python against the SCRATCH's gate (its ROOT), for function-level PASS-path rules."""
        pre = "import sys, json; sys.path.insert(0, 'scripts'); import badf_gate as gate\n"
        return subprocess.run([sys.executable, "-c", pre + code], cwd=self.root, env=self.env, capture_output=True, text=True)

    def evidence_with(self, kind, binding, outcome="PASS"):
        """A minimal evidence dict + artifact for check_g07_binding, written into the scratch WP dir."""
        art = self.wp_dir / "evidence" / "G07" / f"probe-{kind}.txt"; art.parent.mkdir(parents=True, exist_ok=True)
        text = {"source-change": "diff --git a/README.md b/README.md\n", "unit-test": "Ran 3 tests in 0.1s\n\nOK\n", "build": "-> exit 0\n"}[kind]
        art.write_text(text, encoding="utf-8")
        ev = {"schema_version": "1.0.0", "id": f"EVD-{WP}-G07-{kind}", "work_package_id": WP, "gate": "G07", "claim": "x", "evidence_type": kind,
              "producer": {"id": "t", "type": "controller"}, "source_revision": "HEAD", "target": "bstBizEra/badf:main", "toolchain": {"name": "t", "version": "1"},
              "operation": "t", "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:00:00Z", "outcome": outcome,
              "artifact": f"work/{WP}/evidence/G07/probe-{kind}.txt", "digest": gate.sha256(art), "binding": binding}
        return art, ev

    def rule(self, kind, binding, disposition="PASS"):
        art, ev = self.evidence_with(kind, binding)
        code = f"art = gate.ROOT / {str(art.relative_to(self.root))!r}\nev = json.loads({json.dumps(json.dumps(ev))})\n" \
               f"gate.check_g07_binding(art, {{'disposition': {disposition!r}, 'work_package_id': {WP!r}}}, ev)\nprint('ACCEPTED')\n"
        return self.in_scratch(code)


class C1AuthorityTests(_Scratch):
    def test_c1_unauthorized_demand_refuses_assembly(self):
        self.write_demand("DRAFT", "human"); self.lock()
        r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn("AUTHORIZED", r.stdout + r.stderr)
        self.write_demand("AUTHORIZED", "agent"); self.lock()
        r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn("human", r.stdout + r.stderr)
        (self.root / "badf/demands" / f"{DEM}.json").unlink(); self.lock()
        r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn(DEM, r.stdout + r.stderr)
        self.write_demand("AUTHORIZED", "human"); self.lock()
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class C2C3C4C5RuleTests(_Scratch):
    def _sc_binding(self, **over):
        base = self.git("rev-parse", self.base); head = self.git("rev-parse", "HEAD")
        b = {"base_sha": base, "head_sha": head, "content_tree": gate.content_tree(self.root, WP, "HEAD"), "changed_paths": ["README.md"],
             "change_digest": None, "expected_surfaces": {"declared": False, "files": []}, "unexpected_paths": []}
        b.update(over); return b

    def test_c2_base_sha_must_match_base_revision_and_the_composition_record(self):
        art, ev = self.evidence_with("source-change", self._sc_binding()); ev["binding"]["change_digest"] = ev["digest"]
        r = self.rule("source-change", ev["binding"]); self.assertIn("ACCEPTED", r.stdout, r.stderr)
        r = self.rule("source-change", dict(ev["binding"], base_sha="0" * 40)); self.assertNotEqual(r.returncode, 0); self.assertIn("base_revision", r.stderr)
        rec = {"record": "git-composition", "work_package_id": WP, "target_ref": "refs/heads/main", "target_base_sha": ev["binding"]["base_sha"], "source_head_sha": ev["binding"]["head_sha"],
               "merge_base_sha": ev["binding"]["base_sha"], "merge_method": "squash", "expected_result_tree": "0" * 40, "expected_content_tree": "1" * 40}
        (self.wp_dir / "evidence/G07/composition-record.json").write_text(json.dumps(rec) + "\n")
        r = self.rule("source-change", ev["binding"]); self.assertNotEqual(r.returncode, 0); self.assertIn("composition record", r.stderr)

    def test_c3_pass_with_unexpected_paths_refused_unless_discovery_allowance(self):
        self.write_wp(expected_surfaces={"files": ["README.md"]}); self.lock()
        art, ev = self.evidence_with("source-change", self._sc_binding(changed_paths=["README.md"], expected_surfaces={"declared": True, "files": ["README.md"]}, unexpected_paths=["docs/x.md"]))
        ev["binding"]["change_digest"] = ev["digest"]
        r = self.rule("source-change", ev["binding"]); self.assertNotEqual(r.returncode, 0); self.assertIn("BLD-I04", r.stderr)
        r = self.rule("source-change", ev["binding"], disposition="HUMAN_REQUIRED"); self.assertIn("ACCEPTED", r.stdout, "a request may carry unexpected paths (held with C-2); only a PASS is refused")
        self.write_wp(expected_surfaces={"files": ["README.md"], "discovery_allowance": ["docs/**"]}); self.lock()
        r = self.rule("source-change", ev["binding"]); self.assertIn("ACCEPTED", r.stdout, r.stderr)

    def test_c3_mirror_pass_with_declared_pattern_matching_nothing_refused(self):
        """GOV-0102 (#232): the mirror of the loop above -- a declared files pattern the change never
        touched. Recomputed from the record and the equality-bound changed_paths; a PASS is refused,
        a request is not (it is held with a condition at assembly instead)."""
        self.write_wp(expected_surfaces={"files": ["README.md", "docs/never-touched.md"]}); self.lock()
        art, ev = self.evidence_with("source-change", self._sc_binding(
            changed_paths=["README.md"],
            expected_surfaces={"declared": True, "files": ["README.md", "docs/never-touched.md"]},
            unexpected_paths=[]))
        ev["binding"]["change_digest"] = ev["digest"]
        r = self.rule("source-change", ev["binding"])
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("docs/never-touched.md", r.stderr); self.assertIn("GOV-0102", r.stderr)
        r = self.rule("source-change", ev["binding"], disposition="HUMAN_REQUIRED")
        self.assertIn("ACCEPTED", r.stdout, "a request may carry a stale declaration (conditioned at assembly); only a PASS is refused")

    def test_c3_mirror_allowance_matching_nothing_and_full_match_are_not_refused(self):
        self.write_wp(expected_surfaces={"files": ["README.md"], "discovery_allowance": ["docs/**"]}); self.lock()
        art, ev = self.evidence_with("source-change", self._sc_binding(
            changed_paths=["README.md"],
            expected_surfaces={"declared": True, "files": ["README.md"]},
            unexpected_paths=[]))
        ev["binding"]["change_digest"] = ev["digest"]
        r = self.rule("source-change", ev["binding"]); self.assertIn("ACCEPTED", r.stdout, r.stderr)

    def test_c4_red_required_when_unit_obligations_declared_and_exception_must_be_explicit(self):
        self.write_wp(test_obligations=[{"id": "TEST-001", "claim": "x", "level": "unit"}]); self.lock()
        ev = self.wp_dir / "evidence/G07"; ev.mkdir(parents=True, exist_ok=True)
        (ev / "unit-test.log").write_text("python3 -m unittest tests.test_probe\nRan 3 tests in 0.1s\n\nOK\n", encoding="utf-8")
        r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn("red", (r.stdout + r.stderr).lower())
        self.write_wp(test_obligations=[{"id": "TEST-001", "claim": "x", "level": "unit"}], tdd_exception={"reason": "documentation-only change: structural lint is the verification"}); self.lock()
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = json.loads((ev / "unit-test.json").read_text())["binding"]; self.assertEqual(b["tdd"], {"applies": False, "reason": "documentation-only change: structural lint is the verification"})
        (ev / "failing-first.txt").write_text("Ran 3 tests\n\nFAILED (errors=3)\n", encoding="utf-8")
        self.write_wp(test_obligations=[{"id": "TEST-001", "claim": "x", "level": "unit"}]); self.lock()
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = json.loads((ev / "unit-test.json").read_text())["binding"]; self.assertTrue(b["obligations"][0]["red"]["observed"]); self.assertNotIn("tdd", b)

    def test_c5_pass_requires_a_composition_record(self):
        ub = {"obligations": [], "command": "x", "result": "PASS", "tests_run": 3, "failures": 0, "coverage_scope": [], "fresh_run": "x"}
        r = self.rule("unit-test", ub); self.assertNotEqual(r.returncode, 0); self.assertIn("BLD-I09", r.stderr)
        r = self.rule("unit-test", ub, disposition="HUMAN_REQUIRED"); self.assertIn("ACCEPTED", r.stdout, r.stderr)
        (self.wp_dir / "evidence/G07/composition-record.json").write_text(json.dumps({"record": "git-composition", "work_package_id": WP}) + "\n")
        r = self.rule("unit-test", ub); self.assertIn("ACCEPTED", r.stdout, r.stderr)


class C6C7LedgerAndDelegationTests(_Scratch):
    def test_c6_retry_over_budget_and_stop_event_refuse_assembly(self):
        self.write_wp(execution_budget={"max_attempts": 1}); self.lock()
        for step in ("RETRY", "RETRY"):
            self.in_scratch(f"gate.append_build_event({WP!r}, {step!r}, 'FAIL', 'attempt')")
        self.lock(); r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn("max_attempts", r.stdout + r.stderr)
        shutil.rmtree(self.wp_dir / "build"); self.write_wp(execution_budget={"max_attempts": 5}, stop_conditions=["CREDENTIAL_EXPOSURE"]); self.lock()
        self.in_scratch(f"gate.append_build_event({WP!r}, 'STOP', 'CREDENTIAL_EXPOSURE', 'secret in diff')"); self.lock()
        r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn("STOP", r.stdout + r.stderr)
        shutil.rmtree(self.wp_dir / "build"); self.lock(); r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_c7_delegation_outside_the_surface_or_permissions_is_refused(self):
        self.write_wp(expected_surfaces={"files": ["README.md"]}); self.lock()
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertEqual(self.dossier().returncode, 3)
        s = self.wp_dir / "build/session.json"; sess = json.loads(s.read_text())
        sess["delegations"] = [{"task": "slice-A", "allowed_paths": ["scripts/**"], "allowed_tools": ["shell"], "prohibited": ["push", "merge", "release", "credential-use"]}]
        s.write_text(json.dumps(sess, indent=2) + "\n"); self.lock()
        r = self.dossier(); self.assertEqual(r.returncode, 1); self.assertIn("slice-A", r.stdout + r.stderr)
        sess["delegations"] = [{"task": "slice-A", "allowed_paths": ["README.md"], "allowed_tools": ["shell"], "prohibited": ["push", "merge"]}]
        s.write_text(json.dumps(sess, indent=2) + "\n"); self.lock()
        r = self.dossier(); self.assertEqual(r.returncode, 1); self.assertIn("prohibited", r.stdout + r.stderr)
        sess["delegations"] = [{"task": "slice-A", "allowed_paths": ["README.md"], "allowed_tools": ["shell"], "prohibited": ["push", "merge", "release", "credential-use"]}]
        s.write_text(json.dumps(sess, indent=2) + "\n"); self.lock()
        self.assertEqual(self.dossier().returncode, 3)
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(s.read_text())["delegations"][0]["task"], "slice-A", "re-assembly must preserve declared delegations")



class UnwatchedControlTests(_Scratch):
    """#250: three `check_g07_binding` controls were CORRECT but had no refusal test.

    Not the usual shape. These guards fire at runtime and always would have -- what was
    missing is any test that would notice if they stopped, so a future edit could delete
    them with the suite staying green. BADF-REV found them with a mutation battery during
    the #249 review; each is asserted here against its own message fragment, and each was
    observed red against the neutered control before being trusted.

    `:1691` in particular survived because the EXISTING C4 test exercises the ASSEMBLY-side
    check (self-dossier, badf_gate.py:3616) and never the BINDING-side one -- two code paths
    enforcing one rule, with a test on only the first.
    """

    def _sc_binding(self, **over):
        base = self.git("rev-parse", self.base); head = self.git("rev-parse", "HEAD")
        b = {"base_sha": base, "head_sha": head, "content_tree": gate.content_tree(self.root, WP, "HEAD"),
             "changed_paths": ["README.md"], "change_digest": None,
             "expected_surfaces": {"declared": False, "files": []}, "unexpected_paths": []}
        b.update(over); return b

    def test_changed_paths_must_equal_the_paths_in_the_diff_artifact(self):
        """The equality BADF-REV's #249 approval rested on: the two-sided mirror cannot be
        defeated by a forged binding BECAUSE changed_paths is equality-bound before the mirror
        reads it. That guarantee was itself protected by nothing."""
        art, ev = self.evidence_with("source-change", self._sc_binding())
        ev["binding"]["change_digest"] = ev["digest"]
        r = self.rule("source-change", ev["binding"])
        self.assertIn("ACCEPTED", r.stdout, r.stderr)
        # the artifact's diff names README.md; claim something else and the binding is refused
        r = self.rule("source-change", dict(ev["binding"], changed_paths=["docs/forged.md"]))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("do not equal the paths in the diff artifact", r.stderr)
        # a SUPERSET is equally refused -- equality, not containment
        r = self.rule("source-change", dict(ev["binding"], changed_paths=["README.md", "docs/extra.md"]))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("do not equal the paths in the diff artifact", r.stderr)

    def test_content_tree_must_equal_the_composition_records_expected_content_tree(self):
        """What ties a binding to the composition record -- several reconcile-honesty
        arguments rest on it (BLD-I02 / C2)."""
        art, ev = self.evidence_with("source-change", self._sc_binding())
        ev["binding"]["change_digest"] = ev["digest"]
        rec = {"record": "git-composition", "work_package_id": WP, "target_ref": "refs/heads/main",
               "target_base_sha": ev["binding"]["base_sha"], "source_head_sha": ev["binding"]["head_sha"],
               "merge_base_sha": ev["binding"]["base_sha"], "merge_method": "squash",
               "expected_result_tree": "0" * 40,
               "expected_content_tree": ev["binding"]["content_tree"]}
        record = self.wp_dir / "evidence/G07/composition-record.json"
        record.write_text(json.dumps(rec) + "\n")
        r = self.rule("source-change", ev["binding"])
        self.assertIn("ACCEPTED", r.stdout, r.stderr)
        # record says one tree, binding claims another -> refused by name
        rec["expected_content_tree"] = "1" * 40
        record.write_text(json.dumps(rec) + "\n")
        r = self.rule("source-change", ev["binding"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("expected_content_tree", r.stderr)
        self.assertIn("BLD-I02 / C2", r.stderr)

    def test_binding_side_c4_refuses_unit_obligations_with_no_red_and_no_exception(self):
        """The BINDING-side C4 (BLD-I07/I08). The existing C4 test drives self-dossier, which
        is the ASSEMBLY-side check -- this path had no test at all."""
        self.write_wp(test_obligations=[{"id": "TEST-001", "claim": "x", "level": "unit"}])
        self.lock()
        (self.wp_dir / "evidence/G07").mkdir(parents=True, exist_ok=True)
        (self.wp_dir / "evidence/G07/composition-record.json").write_text(
            json.dumps({"record": "git-composition", "work_package_id": WP}) + "\n")
        # obligation shape read from schemas/unit-test.schema.json (id, seam, red, green all
        # required) rather than copied -- a short object is refused by check_schema BEFORE C4,
        # which would have made this probe pass for the wrong reason had it asserted only the
        # exit code instead of the message.
        oblig = {"id": "TEST-001", "seam": {"type": "unit", "ref": "tests/test_probe.py"},
                 "red": {"observed": False}, "green": {"observed": True}}
        no_red = {"obligations": [oblig], "command": "x",
                  "result": "PASS", "tests_run": 3, "failures": 0, "coverage_scope": [], "fresh_run": "x"}
        r = self.rule("unit-test", no_red)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no observed red phase", r.stderr)
        self.assertIn("BLD-I07 / BLD-I08 / C4", r.stderr)
        # an explicit exception WITH a reason is the sanctioned escape
        excepted = dict(no_red, tdd={"applies": False, "reason": "docs-only: structural lint is the verification"})
        r = self.rule("unit-test", excepted)
        self.assertIn("ACCEPTED", r.stdout, r.stderr)
        # an exception with an EMPTY reason is not an exception
        r = self.rule("unit-test", dict(no_red, tdd={"applies": False, "reason": "   "}))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no observed red phase", r.stderr)
        # observed red satisfies it without any exception
        r = self.rule("unit-test", dict(no_red, obligations=[dict(oblig, red={"observed": True})]))
        self.assertIn("ACCEPTED", r.stdout, r.stderr)


    # ---- the two the FULL-SUITE battery found still unwatched (WP-2026-0121) ------------
    # Stage 1 screened all 12 ValidationError sites in check_g07_binding; stage 2 re-ran the
    # survivors against every test in the repo (Ran 1074, loader-count asserted equal). These
    # two survived: correct controls that fire at runtime, with nothing that would notice if
    # a future edit deleted them.

    def test_change_digest_must_equal_the_artifact_digest(self):
        """A binding names the artifact it is bound to BY DIGEST. Without this, a binding could
        carry a digest for one diff while the dossier reads another -- every downstream claim
        that "the binding describes this artifact" rests on it, and nothing tested it."""
        art, ev = self.evidence_with("source-change", self._sc_binding())
        ev["binding"]["change_digest"] = ev["digest"]
        r = self.rule("source-change", ev["binding"])
        self.assertIn("ACCEPTED", r.stdout, r.stderr)
        # a digest for some other artifact
        r = self.rule("source-change", dict(ev["binding"], change_digest="sha256:" + "0" * 64))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("change_digest does not equal the artifact digest", r.stderr)
        # BOUNDARY, and it is not this control's: an ABSENT digest never reaches here --
        # check_schema refuses `None` as "must be a string" first. Asserted so the division of
        # labour is pinned rather than assumed, and so nobody adds a control for the null case
        # believing it reachable. I wrote that assertion first and it failed on the schema's
        # raise, not the control's -- the same wrong-raise trap this WP exists to close.
        r = self.rule("source-change", dict(ev["binding"], change_digest=None))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("must be a string", r.stderr)
        # #305: whitespace-normalized because this is an ABSENCE claim. `r.stderr` is runtime
        # output; if the producer's message is ever reflowed across a line break, a literal
        # search returns 0 and this assertion passes GREEN -- absent-when-present, the direction
        # that reads as success. The presence claims above it would fail RED and self-correct.
        self.assertNotIn("does not equal the artifact digest", " ".join(r.stderr.split()))

    def test_base_sha_must_equal_the_composition_records_target_base_sha(self):
        """The RECORD-side base check, distinct from the work-package-side one.

        Two controls compare `binding.base_sha` against two different sources: the work
        package's `external_target.base_revision`, and the composition record's
        `target_base_sha`. The first had a test; this one did not. Both messages begin
        `binding.base_sha`, so this test discriminates on a fragment UNIQUE to the record-side
        control and asserts the work-package-side wording is ABSENT -- otherwise it would pass
        on the wrong raise, which is exactly how a control gets a test that does not test it.
        """
        art, ev = self.evidence_with("source-change", self._sc_binding())
        ev["binding"]["change_digest"] = ev["digest"]
        rec = {"record": "git-composition", "work_package_id": WP, "target_ref": "refs/heads/main",
               "target_base_sha": ev["binding"]["base_sha"], "source_head_sha": ev["binding"]["head_sha"],
               "merge_base_sha": ev["binding"]["base_sha"], "merge_method": "squash",
               "expected_result_tree": "0" * 40,
               "expected_content_tree": ev["binding"]["content_tree"]}
        record = self.wp_dir / "evidence/G07/composition-record.json"
        record.write_text(json.dumps(rec) + "\n")
        r = self.rule("source-change", ev["binding"])
        self.assertIn("ACCEPTED", r.stdout, r.stderr)
        # the record was computed against a different base than the binding claims
        rec["target_base_sha"] = "1" * 40
        record.write_text(json.dumps(rec) + "\n")
        r = self.rule("source-change", ev["binding"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not equal the composition record\'s target_base_sha", r.stderr)
        self.assertIn("BLD-I02 / C2", r.stderr)
        self.assertNotIn("base_revision", r.stderr,
                         "refused by the work-package-side control, not the record-side one -- "
                         "this test would then pass while :1662 stayed unwatched")


class SilenceTests(_Scratch):
    def test_controls_are_silent_when_fields_are_undeclared(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.dossier().returncode, 3)
        b = json.loads((self.wp_dir / "evidence/G07/unit-test.json").read_text())["binding"]; self.assertNotIn("tdd", b)


if __name__ == "__main__":
    unittest.main()
