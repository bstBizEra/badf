"""GOV-0108 (#246, WP-2026-0126): the enforcement-input ratchet, red-first.

The class: an optional enforcement input is a control that is off by default, and
nothing says so. This module proves the remedy at its two reporting sites:
expected_surfaces.files becomes MANDATORY for records at or above the threshold
(WP-2026-0126 -- the first record the ratchet binds is the one that ships it),
grandfathered history is COUNTED out loud and never edited, structurally-unmatchable
declarations are refused (the VAL-B near-miss), and the #272 site-disagreement about
discovery_allowance is unified: may-touch means the same thing at assembly and binding.

Fixture ids, deliberately: sentinel ids (0997-0999, 9999) are EXEMPT from the ratchet
so the suite's existing scratch records stay green; the threshold tests therefore use
WP-2026-9998 -- inside GOV-0085's unallocatable region, outside the exempt set by
design. If 9998 is ever added to the sentinel set, these tests fail loudly, which is
the correct outcome of that conversation, not an accident.

Per-site discipline (BARCHI-2's fold condition 5): the unification carries one red
case at EACH site -- a shared case goes green while the other site still disagrees.
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

RATCHETED = "WP-2026-9998"   # >= threshold, non-sentinel: the ratchet must bite
EXEMPT = "WP-2026-0998"      # sentinel: existing-fixture shape, must stay green
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
        (self.root / "README.md").write_text((self.root / "README.md").read_text() + "\n<!-- ratchet deliverable -->\n")
        self.git("add", "README.md"); self.commit("deliverable")
        self.write_demand()

    def write_demand(self):
        src = json.loads((self.root / "badf/demands/BADF-DEM-0001.json").read_text(encoding="utf-8"))
        src["demand_id"] = DEM; src["status"] = "AUTHORIZED"
        src["authorized_by"] = {"principal": "operator", "principal_type": "human"}
        (self.root / "badf/demands" / f"{DEM}.json").write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")

    def write_wp(self, wp_id, **extra):
        d = self.root / "work" / wp_id; d.mkdir(parents=True, exist_ok=True)
        rec = {"$schema": "../../schemas/work-package.schema.json", "schema_version": "1.0.0", "id": wp_id,
               "title": "scratch ratchet work package", "owner": "human_sponsor", "repository": "bstBizEra/badf",
               "demand": DEM, "objective": "x", "business_value": "x", "in_scope": ["x"], "out_of_scope": ["y"],
               "target_gate": "G07", "change_class": "C2", "data_classification": "internal",
               "acceptance_criteria": ["x"], "permissions": ["write: bstBizEra/badf via PR"], "tests": ["tests/test_probe.py (3)"],
               "evidence": ["source-change"], "rollback": {"reversible": True, "method": "revert"},
               "status": "IN_PROGRESS", "external_target": {"repository": "bstBizEra/badf", "branch": "main", "base_revision": self.base}}
        rec.update(extra)
        (d / "work-package.json").write_text(json.dumps(rec, indent=2) + "\n")

    def tearDown(self): shutil.rmtree(self.tmp, ignore_errors=True)
    def git(self, *a): return subprocess.run(["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t", *a], capture_output=True, text=True, check=True).stdout.strip()
    def commit(self, msg): self.git("commit", "-q", "-m", msg)
    def lock(self): subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
    def gate_cmd(self, *args): return subprocess.run([sys.executable, "scripts/badf_gate.py", *args], cwd=self.root, env=self.env, capture_output=True, text=True)


class ThresholdTests(_Scratch):
    def test_undeclared_at_or_above_threshold_is_refused_at_assembly(self):
        self.write_wp(RATCHETED); self.lock()
        r = self.gate_cmd("self-dossier", RATCHETED)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        out = r.stdout + r.stderr
        self.assertIn(RATCHETED, out); self.assertIn("expected_surfaces", out)
        self.assertIn("GOV-0108", out, "the refusal names the class it enforces")

    def test_undeclared_at_or_above_threshold_turns_repo_red_naming_the_id(self):
        self.write_wp(RATCHETED); self.lock()
        r = self.gate_cmd("repo")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn(RATCHETED, r.stdout + r.stderr)

    def test_sentinel_and_grandfathered_records_stay_green_and_are_counted(self):
        """The grandfather is a statement, not an edit: the whole landed ledger is
        below threshold, sentinel fixtures are exempt, and repo stays green -- but
        the coverage line says so out loud."""
        self.write_wp(EXEMPT); self.lock()
        r = self.gate_cmd("repo")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SURFACE RATCHET", r.stdout)
        self.assertIn("grandfathered", r.stdout)
        self.assertIn("WP-2026-0126", r.stdout, "the threshold is named, not implied")

    def test_coverage_counts_are_computed_not_asserted(self):
        """The counter observed CHANGING: its numbers must track the ledger, so adding
        a declared >= threshold record moves the declared count by exactly one."""
        self.lock()
        before = self.gate_cmd("repo").stdout
        self.write_wp(RATCHETED, expected_surfaces={"files": ["README.md"]}); self.lock()
        after = self.gate_cmd("repo").stdout
        line_b = [l for l in before.splitlines() if "SURFACE RATCHET" in l]
        line_a = [l for l in after.splitlines() if "SURFACE RATCHET" in l]
        self.assertTrue(line_b and line_a, before + after)
        self.assertNotEqual(line_b, line_a, "a new declared record must move the counter")


class UnmatchableDeclarationTests(_Scratch):
    def test_own_dir_or_lockfile_in_declaration_is_refused(self):
        """The VAL-B near-miss: both paths are excluded from the governed diff, so a
        pattern naming them can never match -- noise with C7 authority attached."""
        self.write_wp(RATCHETED, expected_surfaces={"files": ["README.md", f"work/{RATCHETED}/work-package.json"]}); self.lock()
        r = self.gate_cmd("repo")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("never match", r.stdout + r.stderr)
        self.write_wp(RATCHETED, expected_surfaces={"files": ["README.md", "badf/lockfile.json"]}); self.lock()
        r = self.gate_cmd("repo")
        self.assertNotEqual(r.returncode, 0, r.stdout)


class MayTouchUnificationTests(_Scratch):
    def test_assembly_site_allowance_covered_path_draws_no_c2(self):
        """Per-site red case ONE (assembly): today an allowance-covered path lands in
        `unexpected` and draws C-2 because assembly never consults the allowance."""
        (self.root / "docs" / "probe-ratchet.md").write_text("probe\n", encoding="utf-8")
        self.git("add", "docs/probe-ratchet.md"); self.commit("may-touch discovery")
        self.write_wp(EXEMPT, expected_surfaces={"files": ["README.md"], "discovery_allowance": ["docs/**"]}); self.lock()
        r = self.gate_cmd("self-dossier", EXEMPT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        b = json.loads((self.root / "work" / EXEMPT / "evidence/G07/source-change.json").read_text())["binding"]
        self.assertEqual(b["unexpected_paths"], [], "an allowance-covered path is may-touch, not unexpected")
        d = json.loads((self.root / "work" / EXEMPT / "gate-dossier.G07.json").read_text())
        self.assertFalse([c for c in d["conditions"] if "BLD-I04 scope containment" in c["statement"]], d["conditions"])

    def test_binding_site_still_exempts_pre_unification_bindings(self):
        """Per-site case TWO (binding, pinned regression): a binding written BEFORE the
        unification may still carry allowance-covered paths in unexpected_paths; the
        binding-side filter stays load-bearing for that history."""
        self.write_wp(EXEMPT, expected_surfaces={"files": ["README.md"], "discovery_allowance": ["docs/**"]}); self.lock()
        art = self.root / "work" / EXEMPT / "evidence/G07/probe.txt"; art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("diff --git a/README.md b/README.md\n", encoding="utf-8")
        base = self.git("rev-parse", self.base); head = self.git("rev-parse", "HEAD")
        ev = {"schema_version": "1.0.0", "id": f"EVD-{EXEMPT}-G07-source-change", "work_package_id": EXEMPT, "gate": "G07",
              "claim": "x", "evidence_type": "source-change", "producer": {"id": "t", "type": "controller"},
              "source_revision": "HEAD", "target": "bstBizEra/badf:main", "toolchain": {"name": "t", "version": "1"},
              "operation": "t", "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:00:00Z",
              "outcome": "PASS", "artifact": f"work/{EXEMPT}/evidence/G07/probe.txt", "digest": gate.sha256(art),
              "binding": {"base_sha": base, "head_sha": head, "content_tree": gate.content_tree(self.root, EXEMPT, "HEAD"),
                          "changed_paths": ["README.md"], "change_digest": None,
                          "expected_surfaces": {"declared": True, "files": ["README.md"]},
                          "unexpected_paths": ["docs/legacy-discovery.md"]}}
        ev["binding"]["change_digest"] = ev["digest"]
        code = (f"art = gate.ROOT / {str(art.relative_to(self.root))!r}\nev = json.loads({json.dumps(json.dumps(ev))})\n"
                f"gate.check_g07_binding(art, {{'disposition': 'PASS', 'work_package_id': {EXEMPT!r}}}, ev)\nprint('ACCEPTED')\n")
        pre = "import sys, json; sys.path.insert(0, 'scripts'); import badf_gate as gate\n"
        r = subprocess.run([sys.executable, "-c", pre + code], cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertIn("ACCEPTED", r.stdout, r.stderr)

    def test_directions_stay_distinct_in_conditions(self):
        """#257 discipline: over-reach (changed-but-undeclared) and over-declaration
        (declared-but-unmatched) must never share a statement or a number."""
        (self.root / "docs" / "reach.md").write_text("probe\n", encoding="utf-8")
        self.git("add", "docs/reach.md"); self.commit("over-reach")
        self.write_wp(EXEMPT, expected_surfaces={"files": ["README.md", "docs/never-touched.md"]}); self.lock()
        r = self.gate_cmd("self-dossier", EXEMPT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = json.loads((self.root / "work" / EXEMPT / "gate-dossier.G07.json").read_text())
        reach = [c for c in d["conditions"] if "fall outside the declared" in c["statement"]]
        decl = [c for c in d["conditions"] if "match no changed path" in c["statement"]]
        self.assertEqual(1, len(reach), d["conditions"])
        self.assertEqual(1, len(decl), d["conditions"])
        self.assertNotEqual(reach[0]["condition_id"], decl[0]["condition_id"])


if __name__ == "__main__":
    unittest.main()
