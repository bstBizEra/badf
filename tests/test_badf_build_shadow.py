"""badf-build BLD-D (BADF-WP-0101, #197): the shadow of badf-build on every G07 self-dossier BADF
has landed. The record in examples/build-shadow-evidence.json is generated once from history and
RECOMPUTED here on every run with the real tools -- artifact digests at the landed tree, the demand
record, content_tree -- so it cannot drift from the object store; a tampered record is refused; a
control with no historical corpus is declared non-coverage, never implied.
"""
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

SHADOW = gate.ROOT / "examples/build-shadow-evidence.json"
DOC = gate.ROOT / "skills/badf-build/evidence/shadow-evidence.md"
ALLOWED_CASES = {"request-digest-bound", "authority-replayed", "typed-binding-recomputed", "fresh-verification-replayed", "dossier-not-on-ledger"}


def load_shadow() -> dict:
    return json.loads(SHADOW.read_text(encoding="utf-8"))


def cases(kind: str) -> list:
    return [c for c in load_shadow()["cases"] if c["case"] == kind]


def show(rev: str, path: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(gate.ROOT), "show", f"{rev}:{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


class BuildShadowTests(unittest.TestCase):
    def test_shadow_record_is_well_formed_and_names_non_coverage(self):
        s = load_shadow()
        self.assertEqual(s["record"], "build-shadow"); self.assertEqual(s["repository"], gate.self_repository())
        self.assertTrue(s["cases"]); self.assertTrue(s["non_coverage"])
        for c in s["cases"]:
            self.assertIn(c["case"], ALLOWED_CASES, f"{c['case']}: a case that cannot be recomputed offline belongs in non_coverage"); self.assertIn("verdict", c)
        for gap in ("C3", "C4", "C6", "C7", "WP-2026-0010"):
            self.assertTrue(any(gap in n for n in s["non_coverage"]), f"non_coverage must name {gap}")

    def test_every_request_is_digest_bound_at_its_landing(self):
        landings = gate.ledger_landings(); seen = cases("request-digest-bound"); self.assertGreaterEqual(len(seen), 66)
        for c in seen:
            with self.subTest(wp=c["wp"]):
                self.assertEqual(landings[c["wp"]][-1], c["landed_as"])
                dossier = json.loads(show(c["landed_as"], f"work/{c['wp']}/gate-dossier.G07.json"))
                bad = []
                for item in dossier["evidence"]:
                    ev = json.loads(show(c["landed_as"], item["path"])); art = show(c["landed_as"], ev["artifact"])
                    if art is None or "sha256:" + hashlib.sha256(art).hexdigest() != ev["digest"]: bad.append(item["type"])
                self.assertEqual((c["verdict"], c["mismatches"]), ("BOUND" if not bad else "MISMATCH", bad))

    def test_every_authority_case_replays_from_the_demand_record(self):
        """The record is a MEASUREMENT OF THE PAST: each case stores the demand's status as it stood at
        `measured_on`. Reading the LIVE demand measured a different property -- "is it currently
        AUTHORIZED" -- which made the CLOSED_DEMAND branch below UNREACHABLE: element 0 is frozen at
        AUTHORIZED, so a legitimately discharged demand could never satisfy the tuple. One case reddened
        the moment BADF-DEM-0087 was discharged (#224), and all 67 would have under #220's derived
        terminality. Every sibling case class here already recomputes at a pinned revision; this one had
        skipped that convention. Fixed under WP-2026-0111 / #225 -- exact comparison kept, recomputed at
        the revision the record was measured on, so no future lifecycle transition can falsify it."""
        measured_on = load_shadow()["measured_on"]
        seen = cases("authority-replayed"); self.assertGreaterEqual(len(seen), 66)
        for c in seen:
            with self.subTest(wp=c["wp"]):
                blob = show(measured_on, f"badf/demands/{c['demand']}.json")
                dem = json.loads(blob) if blob is not None else {}
                st = dem.get("status", "ABSENT"); ht = (dem.get("authorized_by") or {}).get("principal_type")
                expected = ("AUTHORIZED_HUMAN" if (st == "AUTHORIZED" and ht == "human")
                            else ("CLOSED_DEMAND" if st == "RESOLVED" and ht == "human" else "NOT_AUTHORIZED"))
                self.assertEqual((c["status"], c["principal_type"], c["verdict"]), (st, ht, expected))
                # The one durable check against the LIVE record: a lifecycle transition may legitimately
                # move `status`, but the principal that authorized a demand never stops being a human.
                live = gate.ROOT / "badf/demands" / f"{c['demand']}.json"
                if c["principal_type"] == "human":
                    # `if live.is_file()` here would make this check SILENTLY VACUOUS when a demand
                    # record is absent -- BADF-REV's M2 probe on #226 showed the module reporting OK
                    # with the file deleted, the hole closed only by `repo`'s lockfile drift check
                    # elsewhere. A landed work package's authority anchor must stay on the ledger, so
                    # absence is asserted against rather than skipped.
                    self.assertTrue(live.is_file(), f"{c['demand']} authorized a landed work package and must remain on the ledger")
                    self.assertEqual("human", (json.loads(live.read_text(encoding="utf-8")).get("authorized_by") or {}).get("principal_type"),
                                     f"{c['demand']} no longer records a human authorizing principal")

    def test_typed_bindings_recompute_from_the_object_store(self):
        seen = cases("typed-binding-recomputed"); self.assertGreaterEqual(len(seen), 2)
        for c in seen:
            with self.subTest(wp=c["wp"]):
                b = json.loads(show(c["landed_as"], f"work/{c['wp']}/evidence/G07/source-change.json"))["binding"]
                landed = gate.content_tree(gate.ROOT, c["wp"], c["landed_as"])
                self.assertEqual((b["content_tree"], landed, c["verdict"]), (c["bound_content_tree"], c["landed_content_tree"], "MATCH"))
                self.assertEqual(landed, b["content_tree"])

    def test_fresh_verification_verdicts_replay(self):
        seen = cases("fresh-verification-replayed"); self.assertGreaterEqual(len(seen), 66)
        self.assertFalse([c for c in seen if c["verdict"] == "PASS_WITHOUT_RECORD"], "a unit-test PASS without a composition record would be a C5 violation in history")
        for c in seen:
            with self.subTest(wp=c["wp"]):
                ut = json.loads(show(c["landed_as"], f"work/{c['wp']}/evidence/G07/unit-test.json")) if show(c["landed_as"], f"work/{c['wp']}/evidence/G07/unit-test.json") else {}
                has_rec = show(c["landed_as"], f"work/{c['wp']}/evidence/G07/composition-record.json") is not None
                expected = ("PASS_WITH_RECORD" if has_rec else "PASS_WITHOUT_RECORD") if ut.get("outcome") == "PASS" else ("NOT_RUN_DEFERRED" + ("_WITH_RECORD" if has_rec else ""))
                self.assertEqual((c["unit_test_outcome"], c["composition_record"], c["verdict"]), (ut.get("outcome", "?"), has_rec, expected))

    def test_tampered_shadow_record_is_refused(self):
        s = load_shadow()
        bad = json.loads(json.dumps(s)); v = next(c for c in bad["cases"] if c["case"] == "typed-binding-recomputed"); v["landed_content_tree"] = "0" * 40
        with self.assertRaises(AssertionError):
            for c in bad["cases"]:
                if c["case"] == "typed-binding-recomputed": assert gate.content_tree(gate.ROOT, c["wp"], c["landed_as"]) == c["landed_content_tree"]
        bad = json.loads(json.dumps(s)); v = next(c for c in bad["cases"] if c["case"] == "request-digest-bound"); v["verdict"] = "MISMATCH"; v["mismatches"] = ["source-change:digest"]
        with self.assertRaises(AssertionError):
            for c in bad["cases"]:
                if c["case"] == "request-digest-bound" and c["wp"] == v["wp"]:
                    dossier = json.loads(show(c["landed_as"], f"work/{c['wp']}/gate-dossier.G07.json")); ok = all(show(c["landed_as"], json.loads(show(c["landed_as"], i["path"]))["artifact"]) is not None for i in dossier["evidence"])
                    assert (c["verdict"] == "BOUND") == ok
        bad = json.loads(json.dumps(s)); bad["cases"].append({"case": "delegation-replayed", "wp": "WP-2026-0001", "verdict": "SUBSET"})
        with self.assertRaises(AssertionError):
            for c in bad["cases"]: assert c["case"] in ALLOWED_CASES

    def test_doc_names_every_case_and_gap_and_root_is_active(self):
        text = DOC.read_text(encoding="utf-8")
        for token in ("request-digest-bound", "authority-replayed", "typed-binding-recomputed", "fresh-verification-replayed", "dossier-not-on-ledger",
                      "non-coverage", "C3", "C4", "C6", "C7", "WP-2026-0010", "SHADOWED", "BLD-E", "admission", "run"):
            self.assertIn(token, text, token)
        reg = gate.load_json(gate.ROOT / "badf/skill-registry.json"); by = {s["name"]: s for s in reg["skills"]}
        self.assertEqual(by["badf-build"]["status"], "ACTIVE")  # BLD-E: admitted; the note still records the SHADOWED measurement
        self.assertEqual(hashlib.sha256((gate.ROOT / by["badf-build"]["source"]).read_bytes()).hexdigest(), by["badf-build"]["digest"][7:])


if __name__ == "__main__":
    unittest.main()
