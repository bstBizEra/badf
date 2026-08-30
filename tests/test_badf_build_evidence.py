"""badf-build BLD-B (BADF-WP-0098, #191): G07 evidence schemas, the self-dossier
extension that binds them, and the build ledger.

The canonical producer of G07 evidence for BADF's own work packages is
`badf_gate.py self-dossier` (BLD-I18: no second producer). This rung makes its
four objects EXACT (BLD-I16): source-change binds base/head SHAs, the content tree,
the changed paths and the expected-surface comparison (BLD-I04); build binds the
command, environment identity and exit code; unit-test binds the author's run log
(red/green, counts) and names the composed-tree gate as the fresh run (BLD-I09);
documentation answers what was NOT updated and why. Typed bindings validate against
schemas/<type>.schema.json at production time and on the dossier. The build ledger
is hash-chained and never read for a verdict.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

WP = "WP-2026-0998"
G07 = ("source-change", "build", "unit-test", "documentation")


class SchemaTests(unittest.TestCase):
    def test_four_schemas_specialize_evidence_schema(self):
        core = json.loads((gate.ROOT / "schemas/evidence.schema.json").read_text(encoding="utf-8"))
        for t in G07:
            p = gate.ROOT / "schemas" / f"{t}.schema.json"; self.assertTrue(p.is_file(), t)
            s = json.loads(p.read_text(encoding="utf-8"))
            self.assertTrue(set(core["required"]) <= set(s["required"]), f"{t}: must require the evidence core")
            self.assertIn("binding", s["required"]); self.assertEqual([t], s["properties"]["evidence_type"]["enum"])
            self.assertFalse(s["properties"]["binding"].get("additionalProperties", True), f"{t}: binding must be closed")


class _SelfDossierScratch(unittest.TestCase):
    """A scratch clone carrying this checkout (gate + schemas), one deliverable commit, one WP."""

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
        (self.root / "README.md").write_text((self.root / "README.md").read_text() + "\n<!-- WP-0998 deliverable -->\n")
        self.git("add", "README.md"); self.commit("deliverable")
        self.wp_dir = self.root / "work" / WP; self.wp_dir.mkdir(parents=True)
        self.write_wp()
        self.lock()

    def write_wp(self, **extra):
        rec = {"$schema": "../../schemas/work-package.schema.json", "schema_version": "1.0.0", "id": WP,
               "title": "scratch build-evidence work package", "owner": "human_sponsor", "repository": "bstBizEra/badf",
               "demand": "BADF-DEM-0001", "objective": "x", "business_value": "x", "in_scope": ["x"], "out_of_scope": ["y"],
               "target_gate": "G07", "change_class": "C2", "data_classification": "internal",
               "acceptance_criteria": ["x"], "permissions": ["write: bstBizEra/badf via PR"], "tests": ["tests/test_probe.py (3)"],
               "evidence": ["source-change"], "rollback": {"reversible": True, "method": "revert"},
               "status": "IN_PROGRESS", "external_target": {"repository": "bstBizEra/badf", "branch": "main", "base_revision": self.base}}
        rec.update(extra)
        (self.wp_dir / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")

    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def git(self, *a): return subprocess.run(["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t", *a], capture_output=True, text=True, check=True).stdout.strip()
    def commit(self, msg): self.git("commit", "-q", "-m", msg)
    def lock(self): subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
    def gate_cmd(self, *args): return subprocess.run([sys.executable, "scripts/badf_gate.py", *args], cwd=self.root, env=self.env, capture_output=True, text=True)
    def self_dossier(self):
        r = self.gate_cmd("self-dossier", WP); return r
    def evidence(self, t): return json.loads((self.wp_dir / "evidence/G07" / f"{t}.json").read_text(encoding="utf-8"))
    def dossier(self): return json.loads((self.wp_dir / "gate-dossier.G07.json").read_text(encoding="utf-8"))


class SourceChangeBindingTests(_SelfDossierScratch):
    def test_self_dossier_binds_exact_shas_content_tree_and_changed_paths(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = self.evidence("source-change")["binding"]
        head = self.git("rev-parse", "HEAD"); base = self.git("rev-parse", self.base)
        self.assertEqual((b["base_sha"], b["head_sha"]), (base, head))
        self.assertEqual(b["content_tree"], gate.content_tree(self.root, WP, "HEAD"))
        self.assertEqual(b["changed_paths"], ["README.md"])
        self.assertEqual(b["change_digest"], self.evidence("source-change")["digest"])

    def test_without_expected_surfaces_non_coverage_is_declared(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = self.evidence("source-change")["binding"]
        self.assertFalse(b["expected_surfaces"]["declared"]); self.assertEqual(b["unexpected_paths"], [])
        self.assertTrue(any("expected_surfaces" in n["reason"] for n in self.dossier()["non_coverage"]), "undeclared surface must be non-coverage, not silence")

    def test_expected_surface_comparison_declares_unexpected_paths_and_holds(self):
        (self.root / "docs" / "probe-0998.md").write_text("probe\n", encoding="utf-8")
        self.git("add", "docs/probe-0998.md"); self.commit("out of surface")
        self.write_wp(expected_surfaces={"files": ["README.md"]}); self.lock()
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = self.evidence("source-change")["binding"]
        self.assertTrue(b["expected_surfaces"]["declared"]); self.assertEqual(b["unexpected_paths"], ["docs/probe-0998.md"])
        d = self.dossier(); cond = [c for c in d["conditions"] if "BLD-I04" in c["statement"]]
        self.assertEqual(1, len(cond)); self.assertIn("docs/probe-0998.md", d["held_because"])
        self.assertEqual(self.gate_cmd("dossier", f"work/{WP}/gate-dossier.G07.json").returncode, 3)

    def test_expected_surface_glob_admits_planned_paths(self):
        (self.root / "docs" / "probe-0998.md").write_text("probe\n", encoding="utf-8")
        self.git("add", "docs/probe-0998.md"); self.commit("in surface")
        self.write_wp(expected_surfaces={"files": ["README.md", "docs/**"]}); self.lock()
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.evidence("source-change")["binding"]["unexpected_paths"], [])
        self.assertFalse([c for c in self.dossier()["conditions"] if "BLD-I04" in c["statement"]])


class UnitTestBuildDocumentationBindingTests(_SelfDossierScratch):
    def test_unit_test_binding_parses_the_authors_log_and_names_the_fresh_run(self):
        ev = self.wp_dir / "evidence/G07"; ev.mkdir(parents=True)
        (ev / "unit-test.log").write_text("python3 -m unittest tests.test_probe\n...\nRan 12 tests in 0.5s\n\nOK\n", encoding="utf-8")
        (ev / "failing-first.txt").write_text("Ran 12 tests in 0.4s\n\nFAILED (errors=12)\n", encoding="utf-8")
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        e = self.evidence("unit-test"); b = e["binding"]
        self.assertEqual(e["outcome"], "PASS"); self.assertEqual((b["result"], b["tests_run"], b["failures"]), ("PASS", 12, 0))
        self.assertIn("badf_compose", b["fresh_run"]); self.assertEqual(e["artifact"], f"work/{WP}/evidence/G07/unit-test.log")
        self.assertEqual(b["obligations"][0]["seam"]["ref"], "tests/test_probe.py")
        self.assertTrue(b["obligations"][0]["red"]["observed"]); self.assertTrue(b["obligations"][0]["green"]["observed"])

    def test_failing_log_refuses_assembly_and_missing_log_is_not_run(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        e = self.evidence("unit-test"); self.assertEqual((e["outcome"], e["binding"]["result"]), ("NOT_RUN", "NOT_RUN"))
        (self.wp_dir / "evidence/G07/unit-test.log").write_text("Ran 3 tests in 0.1s\n\nFAILED (failures=1)\n", encoding="utf-8")
        r = self.self_dossier(); self.assertNotEqual(r.returncode, 0); self.assertIn("FAILED", r.stdout + r.stderr)

    def test_build_and_documentation_bindings(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = self.evidence("build")["binding"]
        self.assertEqual(b["exit_code"], 0); self.assertIn("py_compile", b["command"]); self.assertIn("python", b["environment"]); self.assertIn("platform", b["environment"])
        self.assertTrue(all(a["digest"].startswith("sha256:") for a in b["artifacts"]))
        d = self.evidence("documentation")["binding"]
        # README.md is documentation by the producer's definition (docs/, README.md, AGENTS.md)
        self.assertEqual(d["changed"], ["README.md"]); self.assertFalse(d["contract_changed"]); self.assertFalse(d["behavior_changed"])
        self.assertEqual(d["required_updates"], []); self.assertTrue(d["not_updated_with_reason"])


class TypedBindingValidationTests(_SelfDossierScratch):
    def test_malformed_binding_is_refused_on_the_dossier_and_generic_objects_still_pass(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.gate_cmd("dossier", f"work/{WP}/gate-dossier.G07.json").returncode, 3)
        p = self.wp_dir / "evidence/G07/source-change.json"; e = json.loads(p.read_text()); e["binding"]["base_sha"] = "nope"
        p.write_text(json.dumps(e, indent=2) + "\n"); self.lock()
        r = self.gate_cmd("dossier", f"work/{WP}/gate-dossier.G07.json"); self.assertEqual(r.returncode, 1); self.assertIn("source-change", r.stdout + r.stderr)
        e.pop("binding"); p.write_text(json.dumps(e, indent=2) + "\n"); self.lock()
        self.assertEqual(self.gate_cmd("dossier", f"work/{WP}/gate-dossier.G07.json").returncode, 3, "a generic object (no binding) stays admissible")


class BuildLedgerTests(_SelfDossierScratch):
    def test_ledger_is_hash_chained_and_never_read_for_verdict(self):
        r = self.self_dossier(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ledger = self.wp_dir / "build/progress.jsonl"; self.assertTrue(ledger.is_file())
        events = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["step"] for e in events], ["START", "BASELINE", "VERIFY", "HANDOFF"])
        self.assertTrue((self.wp_dir / "build/session.json").is_file())
        self.assertEqual(self.gate_cmd("build-ledger", WP).returncode, 0)
        events[2]["outcome"] = "TAMPERED"; ledger.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8"); self.lock()
        r = self.gate_cmd("build-ledger", WP); self.assertEqual(r.returncode, 1); self.assertIn("chain", (r.stdout + r.stderr).lower())
        self.assertEqual(self.gate_cmd("dossier", f"work/{WP}/gate-dossier.G07.json").returncode, 3, "the ledger is never read for a verdict")


class G07RuleTests(unittest.TestCase):
    """The EVIDENCE_RULES entry for the G07 types (runs on PASS dossiers): a binding must agree with
    the artifact the gate opens; a generic object (no binding) is left alone."""

    def _evidence(self, kind, artifact_text, binding):
        tmp = Path(tempfile.mkdtemp(prefix="badf-g07-rule-")); self.addCleanup(shutil.rmtree, tmp, True)
        art = tmp / "artifact.txt"; art.write_text(artifact_text, encoding="utf-8")
        ev = {"schema_version": "1.0.0", "id": f"EVD-{WP}-G07-{kind}", "work_package_id": WP, "gate": "G07", "claim": "x",
              "evidence_type": kind, "producer": {"id": "t", "type": "controller"}, "source_revision": "HEAD", "target": "bstBizEra/badf:main",
              "toolchain": {"name": "t", "version": "1"}, "operation": "t", "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:00:00Z",
              "outcome": "PASS", "artifact": "x", "digest": gate.sha256(art)}
        if binding is not None:
            ev["binding"] = binding
        return art, ev

    def test_rule_refuses_a_binding_that_disagrees_with_the_artifact_and_ignores_generic_objects(self):
        self.assertIn("source-change", gate.EVIDENCE_RULES); self.assertIn("unit-test", gate.EVIDENCE_RULES)
        diff = "diff --git a/README.md b/README.md\n--- a/README.md\n+++ b/README.md\n"
        sha = "0" * 40
        good = {"base_sha": sha, "head_sha": sha, "content_tree": sha, "changed_paths": ["README.md"], "change_digest": None,
                "expected_surfaces": {"declared": False, "files": []}, "unexpected_paths": []}
        art, ev = self._evidence("source-change", diff, dict(good)); ev["binding"]["change_digest"] = ev["digest"]
        gate.check_g07_binding(art, {}, ev)  # agrees: no error
        art, ev = self._evidence("source-change", diff, dict(good, changed_paths=["docs/other.md"])); ev["binding"]["change_digest"] = ev["digest"]
        with self.assertRaises(gate.ValidationError): gate.check_g07_binding(art, {}, ev)
        art, ev = self._evidence("unit-test", "Ran 12 tests in 0.1s\n\nOK\n", {"obligations": [], "command": "x", "result": "PASS", "tests_run": 11, "failures": 0, "coverage_scope": [], "fresh_run": "x"})
        with self.assertRaises(gate.ValidationError): gate.check_g07_binding(art, {}, ev)
        art, ev = self._evidence("source-change", diff, None)
        gate.check_g07_binding(art, {}, ev)  # generic object: additive, untouched
        # BLD-I16: a build binding is verified against the transcript or refused -- never best-effort
        bb = {"command": "x", "cwd": ".", "environment": {"python": "3", "platform": "p"}, "exit_code": 0, "artifacts": [], "non_coverage": []}
        art, ev = self._evidence("build", "py_compile ... -> exit 0\n", dict(bb)); gate.check_g07_binding(art, {}, ev)
        art, ev = self._evidence("build", "py_compile ... -> exit 1\n", dict(bb))
        with self.assertRaises(gate.ValidationError): gate.check_g07_binding(art, {}, ev)
        art, ev = self._evidence("build", "no exit line here\n", dict(bb))
        with self.assertRaises(gate.ValidationError): gate.check_g07_binding(art, {}, ev)


if __name__ == "__main__":
    unittest.main()
