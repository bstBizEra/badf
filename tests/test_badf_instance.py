"""Project instance contract (BADF-WP-0021, Issue #33, BADF-DEC-0004 / -0005).

A project governed by BADF must carry its own control plane. `badf init` now
writes a BOUNDED namespace into the target -- AGENTS.md only if absent, plus
badf/{project.yaml,state.json,evidence/receipts/init-*.json} -- and nothing
else: everything outside that namespace is byte-identical before and after,
an existing AGENTS.md is preserved and recorded as a conflict, an existing
badf/ refuses, a dirty tree refuses, the framework itself refuses. The
receipt lists exactly what appeared, digest-bound, and is bound into BADF's
own G00 evidence. No test touches the real PropTech clone: it is cloned.
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
from tests.test_badf_schema_drift import schema, enum_violations, unknown_keys  # noqa: E402
from tests._scratch import pin_origin_main  # noqa: E402

PROPTECH = Path(os.environ.get("BADF_PROPTECH_PATH", "/mnt/c/laragon/www/proptech"))   # CI shape: point it at nothing
HAVE_PROPTECH = PROPTECH.is_dir() and (PROPTECH / ".git").exists()
NAMESPACE = {"AGENTS.md", "badf"}


def snapshot(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and ".git" not in p.parts}


def outside(snap: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in snap.items() if k.split("/", 1)[0] not in NAMESPACE}


def git(root: Path, *a: str) -> str:
    return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True).stdout.strip()


def make_repo(where: Path, files: dict[str, str]) -> Path:
    where.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(where)], check=True)
    for rel, text in files.items():
        p = where / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    subprocess.run(["git", "-C", str(where), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(where), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "baseline"], check=True)
    return where


class InstanceScratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "badf"
        subprocess.run(["git", "clone", "-q", str(gate.ROOT), str(self.root)], check=True)
        pin_origin_main(self.root)
        for rel in ("scripts/badf_gate.py", "badf", "skills", "schemas", "templates", "examples", "docs", "work"):
            src, dst = gate.ROOT / rel, self.root / rel
            if src.is_dir():
                shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def target(self, files=None, name="target"):
        return make_repo(Path(self.tmp) / name, files if files is not None else {"README.md": "# x\n"})

    def intent(self, root: Path, **extra) -> Path:
        proj = {"name": "PropTech", "intent": "Build a land valuation platform for Laos", "owner": "BST",
                "target": "production", "repository": "bstBizEra/proptech", "local_path": str(root),
                "demand": "BADF-DEM-0003"}
        proj.update(extra)
        p = self.root / "intent.json"; p.write_text(json.dumps({"project": proj})); return p

    def init(self, intent_path: Path):
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "init", str(intent_path)],
                              cwd=str(self.root), capture_output=True, text=True, env=self.env)

    def receipt(self, root: Path) -> dict:
        files = sorted((root / "badf/evidence/receipts").glob("init-*.json"))
        self.assertEqual(len(files), 1, f"expected exactly one receipt, got {files}")
        return json.loads(files[0].read_text())

    def wp_id(self) -> str:
        return gate.load_json(self.root / gate.REPOSITORIES)["repositories"]["bstBizEra/proptech"]["work_package"]


class BoundedWriteTests(InstanceScratch):

    def test_greenfield_generates_exactly_the_namespace_and_nothing_else(self):
        t = self.target(); before = snapshot(t)
        r = self.init(self.intent(t))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        after = snapshot(t)
        self.assertEqual(outside(after), outside(before), "init wrote outside its namespace")
        new = sorted(set(after) - set(before))
        self.assertEqual([p for p in new if not p.startswith("badf/evidence/receipts/init-")],
                         ["AGENTS.md", "badf/lockfile.json", "badf/project.yaml", "badf/state.json"])
        self.assertEqual(len([p for p in new if p.startswith("badf/evidence/receipts/init-")]), 1)
        rec = self.receipt(t)
        self.assertEqual(rec["classification"], "GREENFIELD")
        # the receipt cannot carry its own digest; it is bound BADF-side instead
        self.assertEqual(sorted(g["path"] for g in rec["generated"]),
                         [p for p in new if not p.startswith("badf/evidence/receipts/") and p != "badf/lockfile.json"],
                         "receipt.generated != what appeared (the receipt and the lockfile are the signature, not claims)")
        for g in rec["generated"]:
            self.assertEqual(g["digest"], after[g["path"]], f"{g['path']}: receipt digest != file")
        self.assertEqual(rec["preserved"], []); self.assertEqual(rec["conflicts"], [])

    def test_brownfield_preserves_an_existing_agents_md_byte_for_byte(self):
        t = self.target({"AGENTS.md": "# Existing charter\n\nDo not touch.\n", "src/app.py": "print(1)\n", "README.md": "# p\n"})
        agents_before = (t / "AGENTS.md").read_bytes(); before = snapshot(t)
        r = self.init(self.intent(t))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((t / "AGENTS.md").read_bytes(), agents_before, "existing AGENTS.md was modified")
        self.assertEqual(outside(snapshot(t)), outside(before))
        rec = self.receipt(t)
        self.assertEqual(rec["classification"], "BROWNFIELD")
        self.assertEqual([p["path"] for p in rec["preserved"]], ["AGENTS.md"])
        self.assertEqual(rec["preserved"][0]["digest"], before["AGENTS.md"])
        self.assertEqual(rec["conflicts"], [{"path": "AGENTS.md", "disposition": "PRESERVED_MERGE_PLAN_REQUIRED"}])
        self.assertNotIn("AGENTS.md", [g["path"] for g in rec["generated"]])
        state = json.loads((t / "badf/state.json").read_text())
        self.assertEqual(state["entrypoint"], "EXISTING_AGENTS_MD_PRESERVED")

    def test_existing_badf_directory_is_refused_and_nothing_is_written(self):
        t = self.target({"README.md": "# p\n", "badf/state.json": "{}\n"}); before = snapshot(t)
        badf_side_before = set((self.root / "work").glob("WP-*"))
        r = self.init(self.intent(t))
        self.assertNotEqual(r.returncode, 0, "a second init over an existing badf/ was accepted")
        self.assertIn("already", r.stderr)
        self.assertEqual(snapshot(t), before)
        self.assertEqual(set((self.root / "work").glob("WP-*")), badf_side_before, "BADF-side records written for a refused init")

    def test_dirty_working_tree_is_refused_and_nothing_is_written(self):
        t = self.target(); (t / "uncommitted.txt").write_text("x\n"); before = snapshot(t)
        r = self.init(self.intent(t))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("clean", r.stderr)
        self.assertEqual(snapshot(t), before)

    def test_the_framework_itself_is_refused_as_a_target(self):
        r = self.init(self.intent(self.root, repository="bstBizEra/badf", demand="BADF-DEM-0005"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("framework", r.stderr)
        self.assertFalse((self.root / "badf/project.yaml").exists())

    def test_init_reports_what_it_wrote_and_no_longer_claims_it_wrote_nothing(self):
        t = self.target()
        r = self.init(self.intent(t))
        self.assertEqual(r.returncode, 0, r.stderr)
        # #305: whitespace-normalized because this is an ABSENCE claim, and a load-bearing one --
        # it guards a message that was REMOVED (the phrase appears nowhere else in the repository),
        # so it can only ever fire on a regression. A reintroduction that wraps would slip past a
        # literal search silently. The assertIn below is its positive control on the same haystack.
        self.assertNotIn("nothing written to the target", " ".join(r.stdout.split()))
        self.assertIn("badf/evidence/receipts/init-", r.stdout)


class DerivedStateTests(InstanceScratch):

    def test_state_is_derived_from_the_baseline_not_typed(self):
        t = self.target(); head = git(t, "rev-parse", "HEAD")
        r = self.init(self.intent(t)); self.assertEqual(r.returncode, 0, r.stderr)
        st = json.loads((t / "badf/state.json").read_text())
        self.assertEqual(st["derived_from"]["baseline_commit"], head)
        self.assertEqual(st["lifecycle"], {"current_gate": "G00", "state": "INITIALIZED", "target": "PRODUCTION"})
        self.assertEqual(st["authority"], {"status": "UNRESOLVED"})
        self.assertEqual(st["active_work_package"], self.wp_id())
        self.assertEqual(st["framework_revision"], git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(st["readiness"]["production"], "NOT_READY")
        rec = self.receipt(t)
        self.assertEqual(rec["baseline_commit"], head)
        self.assertEqual(st["derived_from"]["receipt"], sorted(p.relative_to(t).as_posix() for p in (t / "badf/evidence/receipts").glob("init-*.json"))[0])

    def test_project_yaml_is_real_yaml_and_round_trips(self):
        t = self.target()
        r = self.init(self.intent(t, project_id="BST-PROPTECH", type="web-platform", maturity="IDEA")); self.assertEqual(r.returncode, 0, r.stderr)
        text = (t / "badf/project.yaml").read_text()
        doc = gate.parse_yaml_subset(text)
        self.assertEqual(doc["project"]["id"], "BST-PROPTECH")
        self.assertEqual(doc["project"]["type"], "web-platform"); self.assertEqual(doc["project"]["maturity"], "IDEA")
        self.assertEqual(doc["badf"]["framework_revision"], git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(doc["delivery"]["work_package"], self.wp_id())
        self.assertEqual(gate.parse_yaml_subset(gate.emit_yaml(doc)), doc, "emit/parse do not round-trip")
        try:
            import yaml  # an INDEPENDENT parser, where present
        except ImportError:
            self.skipTest("PyYAML not present; independent parse skipped (the subset parser ran)")
        self.assertEqual(yaml.safe_load(text), doc, "PyYAML reads this file differently from the subset parser")

    def test_undeclared_judgment_is_declared_missing_not_invented(self):
        t = self.target()
        r = self.init(self.intent(t)); self.assertEqual(r.returncode, 0, r.stderr)
        doc = gate.parse_yaml_subset((t / "badf/project.yaml").read_text())
        self.assertEqual(doc["project"]["type"], "DECLARED_MISSING")
        self.assertEqual(doc["project"]["maturity"], "DECLARED_MISSING")
        self.assertEqual(doc["ownership"]["product_owner"], None)

    def test_generated_files_satisfy_their_schemas(self):
        t = self.target()
        r = self.init(self.intent(t)); self.assertEqual(r.returncode, 0, r.stderr)
        instances = {"project": gate.parse_yaml_subset((t / "badf/project.yaml").read_text()),
                     "state": json.loads((t / "badf/state.json").read_text()),
                     "init-receipt": self.receipt(t)}
        for name, inst in instances.items():
            with self.subTest(schema=name):
                sch = schema(name)
                self.assertEqual(set(sch["required"]) - set(inst), set(), f"{name}: required keys missing")
                self.assertEqual(unknown_keys(sch, inst), set(), f"{name}: keys the schema does not define")
                self.assertEqual(enum_violations(sch["properties"], inst), [], f"{name}: enum violations")

    def test_receipt_is_bound_into_badf_g00_evidence_by_digest(self):
        t = self.target()
        r = self.init(self.intent(t)); self.assertEqual(r.returncode, 0, r.stderr)
        wp = self.wp_id(); ev_dir = self.root / "work" / wp / "evidence/G00"
        ev = json.loads((ev_dir / "init-receipt.json").read_text())
        rec_path = sorted((t / "badf/evidence/receipts").glob("init-*.json"))[0]
        self.assertEqual(ev["digest"], "sha256:" + hashlib.sha256(rec_path.read_bytes()).hexdigest())
        self.assertEqual(gate.sha256(self.root / ev["artifact"]), ev["digest"], "BADF-side artifact is not the receipt's bytes")
        dossier = json.loads((self.root / "work" / wp / "gate-dossier.G00.json").read_text())
        self.assertIn("init-receipt", [e["type"] for e in dossier["evidence"]])
        self.assertEqual(dossier["disposition"], "HUMAN_REQUIRED", "an instance does not grant authority")


class SubsetParserAndValidatorTests(unittest.TestCase):
    """The primitives refuse rather than guess. Without these, a mutant that
    guts the validator survives -- every generated file happens to be valid."""

    def test_round_trip_of_nested_mappings_lists_and_scalars(self):
        doc = {"a": {"b": "x y", "c": 3, "d": True, "e": None}, "f": ["p", "q"], "g": "quote \" and \\ slash"}
        self.assertEqual(gate.parse_yaml_subset(gate.emit_yaml(doc)), doc)

    def test_outside_the_subset_is_refused_not_guessed(self):
        for bad, why in [("a:\n\tb: 1\n", "tab"), ("a: {b: 1}\n", "flow mapping"), ("a: [1, 2]\n", "flow list"),
                         ("a: plain\n", "unquoted string"), ("a: 1\na: 2\n", "duplicate key"),
                         ("# c\na: 1\n", "comment"), ("---\na: 1\n", "document marker"), ("a: &x 1\n", "anchor"),
                         ("a:\n", "key without value"), ("", "empty")]:
            with self.subTest(why=why):
                with self.assertRaises(gate.ValidationError):
                    gate.parse_yaml_subset(bad)

    def test_check_schema_refuses_missing_bad_enum_and_undefined_keys(self):
        good = {"schema_version": "1.0.0", "project_id": "X", "framework_revision": "0" * 40,
                "lifecycle": {"current_gate": "G00", "state": "INITIALIZED", "target": "PRODUCTION"},
                "active_work_package": None, "active_session": None, "authority": {"status": "UNRESOLVED"},
                "entrypoint": "AGENTS_MD_GENERATED",
                "readiness": {"product": "NOT_STARTED", "architecture": "NOT_STARTED", "engineering": "NOT_STARTED",
                              "security": "NOT_STARTED", "release": "NOT_STARTED", "production": "NOT_READY"},
                "derived_from": {"baseline_commit": "0" * 40, "receipt": "badf/evidence/receipts/init-x.json"}}
        gate.check_schema("state", good)
        missing = dict(good); del missing["authority"]
        with self.assertRaises(gate.ValidationError): gate.check_schema("state", missing)
        bad_enum = json.loads(json.dumps(good)); bad_enum["lifecycle"]["state"] = "DONE"
        with self.assertRaises(gate.ValidationError): gate.check_schema("state", bad_enum)
        extra = dict(good, diary="agent notes")
        with self.assertRaises(gate.ValidationError): gate.check_schema("state", extra)
        bad_pattern = dict(good, framework_revision="not-a-sha")
        with self.assertRaises(gate.ValidationError): gate.check_schema("state", bad_pattern)


@unittest.skipUnless(HAVE_PROPTECH, "PropTech clone not present on this host")
class PropTechScratchCloneTests(InstanceScratch):
    """PropTech is the first real brownfield target -- 952-line AGENTS.md. It is
    initialised ONLY as a scratch clone; the real clone must be untouched."""

    @classmethod
    def setUpClass(cls):
        cls.real_before = (git(PROPTECH, "rev-parse", "HEAD"), git(PROPTECH, "status", "--porcelain"))

    @classmethod
    def tearDownClass(cls):
        assert (git(PROPTECH, "rev-parse", "HEAD"), git(PROPTECH, "status", "--porcelain")) == cls.real_before, "REAL PropTech clone was modified"

    def test_proptech_is_brownfield_and_its_charter_is_preserved(self):
        t = Path(self.tmp) / "proptech"
        subprocess.run(["git", "clone", "-q", str(PROPTECH), str(t)], check=True)
        agents_before = (t / "AGENTS.md").read_bytes(); before = snapshot(t)
        r = self.init(self.intent(t))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((t / "AGENTS.md").read_bytes(), agents_before)
        self.assertEqual(outside(snapshot(t)), outside(before))
        rec = self.receipt(t)
        self.assertEqual(rec["classification"], "BROWNFIELD")
        self.assertEqual(rec["conflicts"][0]["path"], "AGENTS.md")
        self.assertEqual(rec["repository"], "bstBizEra/proptech")


if __name__ == "__main__":
    unittest.main()
