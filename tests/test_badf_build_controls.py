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


class SilenceTests(_Scratch):
    def test_controls_are_silent_when_fields_are_undeclared(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.dossier().returncode, 3)
        b = json.loads((self.wp_dir / "evidence/G07/unit-test.json").read_text())["binding"]; self.assertNotIn("tdd", b)


if __name__ == "__main__":
    unittest.main()
