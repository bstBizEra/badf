"""GIT-I (BADF-WP-0082): the shadow corpus is this program's own history, recomputed.

badf-git integrated every one of its work packages through the tools it was building.
`examples/git-shadow-evidence.json` records what those tools render on that real history --
landings whose content tree matches the committed composition record, landings that predate
records and honestly read `composition_verified: false`, squash landings that conform to the
identity rule, a SOURCE_ADVANCED staleness case between two landings, the RELEASE_BOUND
baseline -- and names what history cannot replay. Every case here is RECOMPUTED from the
object store with the real tools, so the committed record can never drift from history; a
case that cannot be recomputed offline is not allowed in `cases` at all.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

SHADOW = gate.ROOT / "examples/git-shadow-evidence.json"
DOC = gate.ROOT / "skills/badf-git/evidence/shadow-evidence.md"
TARGET = f"refs/remotes/origin/{gate.DEFAULT_BRANCH}"
ALLOWED_CASES = {"landing-verified", "landing-without-record", "identity-conform", "staleness-source-advanced", "release-bound"}


def load_shadow() -> dict:
    return json.loads(SHADOW.read_text(encoding="utf-8"))


def cases(kind: str) -> list:
    return [c for c in load_shadow()["cases"] if c["case"] == kind]


def g(*args: str) -> str:
    return subprocess.run(["git", "-C", str(gate.ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()


class ShadowRecordTests(unittest.TestCase):
    def test_shadow_record_is_well_formed_and_names_non_coverage(self):
        s = load_shadow()
        self.assertEqual(s["record"], "git-shadow"); self.assertEqual(s["repository"], gate.self_repository())
        self.assertTrue(s["cases"]); self.assertTrue(s["non_coverage"])
        for c in s["cases"]:
            self.assertIn(c["case"], ALLOWED_CASES, f"{c['case']}: a case that cannot be recomputed offline belongs in non_coverage")
            self.assertIn("verdict", c)
        self.assertEqual({c["case"] for c in s["cases"]}, ALLOWED_CASES, "every contract part the shadow claims must be present")
        for gap in ("STALE_EVIDENCE", "recovery", "branch", "sign"):
            self.assertTrue(any(gap.lower() in n.lower() for n in s["non_coverage"]), f"non_coverage must name the {gap} gap")

    def test_every_recorded_landing_matches_its_content_tree(self):
        landings = gate.ledger_landings(); seen = cases("landing-verified")
        self.assertGreaterEqual(len(seen), 7)
        for c in seen:
            with self.subTest(wp=c["wp"]):
                self.assertEqual(landings[c["wp"]][-1], c["landed_as"], "the ledger's landing must be the recorded one")
                rec_text = gate._git("show", f"{c['landed_as']}:work/{c['wp']}/evidence/G07/composition-record.json")
                self.assertIsNotNone(rec_text); rec = json.loads(rec_text)
                landed = gate.content_tree(gate.ROOT, c["wp"], c["landed_as"])
                self.assertEqual((rec["expected_content_tree"], landed, c["verdict"]), (c["expected_content_tree"], c["landed_content_tree"], "MATCH"))
                self.assertEqual(landed, rec["expected_content_tree"])

    def test_every_no_record_landing_has_no_record_in_its_landed_tree(self):
        landings = gate.ledger_landings(); seen = cases("landing-without-record")
        self.assertGreaterEqual(len(seen), 15)
        for c in seen:
            with self.subTest(wp=c["wp"]):
                self.assertEqual(landings[c["wp"]][-1], c["landed_as"])
                self.assertIsNone(gate._git("show", f"{c['landed_as']}:work/{c['wp']}/evidence/G07/composition-record.json"))
                self.assertEqual(c["verdict"], "composition_verified: false")

    def test_every_identity_case_conforms_on_real_history(self):
        seen = cases("identity-conform"); self.assertGreaterEqual(len(seen), 21)
        first_parent = set(g("rev-list", "--first-parent", TARGET).split())
        for c in seen:
            with self.subTest(commit=c["commit"][:7]):
                self.assertIn(c["commit"], first_parent, "an identity case must be a first-parent landing on main")
                subject = g("log", "-1", "--format=%s", c["commit"]); body = g("log", "-1", "--format=%b", c["commit"])
                lab = re.match(r"^BADF-WP-([0-9]{4}):", subject); tr = re.search(rf"^Work-Package:\s*({re.escape(gate.WP_NAMESPACE)}[0-9]{{4}})\s*$", body, re.M)
                self.assertTrue(lab and tr and lab.group(1) == tr.group(1)[-4:], f"{c['commit'][:7]}: label/trailer do not conform")
                self.assertEqual((c["label"], c["trailer"], c["verdict"]), (f"BADF-WP-{lab.group(1)}", tr.group(1), "CONFORM"))

    def test_staleness_case_renders_SOURCE_ADVANCED_with_the_real_tool(self):
        (c,) = cases("staleness-source-advanced")
        tmp = Path(tempfile.mkdtemp(prefix="badf-git-shadow-")); self.addCleanup(shutil.rmtree, tmp, True)
        repo = tmp / "badf"; seed_clone(repo)
        subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin", c["baseline_head"], c["head"]], check=True)
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", c["baseline_head"]], check=True)
        baseline = gate.git_baseline(repo)
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", c["head"]], check=True)
        v = gate.git_staleness(baseline, repo)
        self.assertEqual((v["disposition"], v["old_source_head"], v["new_source_head"], v["source_rewritten"]), ("SOURCE_ADVANCED", c["baseline_head"], c["head"], False))
        self.assertEqual(c["verdict"], "SOURCE_ADVANCED")

    def test_release_case_renders_RELEASE_BOUND_with_the_real_tool(self):
        (c,) = cases("release-bound")
        v = gate.git_release_check(gate.ROOT, c["tag"])
        self.assertEqual((v["disposition"], v["source_revision"], c["verdict"]), ("RELEASE_BOUND", c["source_revision"], "RELEASE_BOUND"))

    def test_tampered_shadow_record_is_refused(self):
        """The record is evidence only because the tests recompute it: a wrong tree, a wrong verdict
        and a non-recomputable case must each fail the recomputation."""
        s = load_shadow()
        bad_tree = json.loads(json.dumps(s)); v = next(c for c in bad_tree["cases"] if c["case"] == "landing-verified"); v["landed_content_tree"] = "0" * 40
        bad_verdict = json.loads(json.dumps(s)); w = next(c for c in bad_verdict["cases"] if c["case"] == "identity-conform"); w["verdict"] = "NONCONFORM"
        bad_case = json.loads(json.dumps(s)); bad_case["cases"].append({"case": "rewrite-stale", "verdict": "STALE_EVIDENCE"})
        for label, doc in (("wrong tree", bad_tree), ("wrong verdict", bad_verdict), ("non-recomputable case", bad_case)):
            with self.subTest(label=label):
                with self.assertRaises(AssertionError):
                    self._recompute(doc)

    def _recompute(self, s: dict) -> None:
        for c in s["cases"]:
            assert c["case"] in ALLOWED_CASES
            if c["case"] == "landing-verified":
                assert gate.content_tree(gate.ROOT, c["wp"], c["landed_as"]) == c["landed_content_tree"]
            if c["case"] == "identity-conform":
                assert c["verdict"] == "CONFORM"

    def test_shadow_evidence_doc_names_every_case_and_gap_and_root_is_active(self):
        text = DOC.read_text(encoding="utf-8")
        for token in ("landing-verified", "landing-without-record", "identity-conform", "staleness-source-advanced", "release-bound",
                      "STALE_EVIDENCE", "synthetic", "non-coverage", "DESIGNED", "ACTIVE", "GIT-J", "admission", "#169", "six subskills", "run"):
            self.assertIn(token, text, token)
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertEqual(by["badf-git"]["status"], "ACTIVE")
        self.assertEqual(hashlib.sha256((gate.ROOT / by["badf-git"]["source"]).read_bytes()).hexdigest(), by["badf-git"]["digest"][7:])


if __name__ == "__main__":
    unittest.main()
