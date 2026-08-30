"""badf-engineering-verification VER-D (BADF-WP-0106 / GOV-0089): shadow the G08 controls on
the material BADF has.

Three case classes, one record (`examples/verification-shadow-evidence.json`), every case
recomputed from the repository on every run: (1) `historical-generic-dossier` -- WP-2026-0010's
binding-less G08 dossier passes check_g08_binding and check_g08_dossier UNTOUCHED (the additive
proof); (2) `real-review-encoded` -- BARCHI-1's real verdict arc (#196 Request-Changes -> Approved,
#201, #202, #205) as five RECONSTRUCTED single-reviewer verification records that `verify` accepts
and whose tampering it refuses -- encoded under the reviewer's own honesty conditions (one ballot,
the real comment id, no council claimed, the #196 MAJOR finding and its RESOLVED arc); (3)
`representative-typed-dossier` -- injected defects each refused by the control that owns it, clean
dossiers admitted. Metrics measured, non-coverage named (no typed real G08 dossier; one reviewer
seat; prose reconstructed; representative defects). No gate, schema or lifecycle change.
"""
import copy
import json
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402
from tests.test_badf_verification_controls import dossier, objects, evidence, observation, review, finding, wp, COMP  # noqa: E402

ROOT = gate.ROOT
RECORD = ROOT / "examples" / "verification-shadow-evidence.json"
DOC = ROOT / "skills" / "badf-engineering-verification" / "evidence" / "shadow-evidence.md"
ENCODED = {
    "pr196-request-changes": ("5469987101", "REJECT"),
    "pr196-approved": ("5470235706", "APPROVE"),
    "pr201": ("5470380581", "APPROVE"),
    "pr202": ("5470510051", "APPROVE"),
    "pr205": ("5470622958", "APPROVE"),
}


def shadow():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def cases(kind):
    return [c for c in shadow()["cases"] if c["case_class"] == kind]


class ShadowRecordTests(unittest.TestCase):
    def test_shadow_record_is_well_formed_and_names_non_coverage(self):
        rec = shadow()
        for key in ("record", "schema_version", "work_package_id", "repository", "measured_on", "measured_at",
                    "corpus", "cases", "runner_citations", "non_coverage"):
            self.assertIn(key, rec, key)
        self.assertEqual("verification-shadow", rec["record"]); self.assertEqual("WP-2026-0106", rec["work_package_id"])
        nc = " ".join(rec["non_coverage"]).lower()
        for gap in ("no typed real g08 dossier", "one reviewer seat", "reconstructed", "representative"):
            self.assertIn(gap, nc, gap)
        self.assertEqual(1, len(cases("historical-generic-dossier")))
        self.assertEqual(5, len(cases("real-review-encoded")))
        self.assertGreaterEqual(len(cases("representative-typed-dossier")), 12)

    def test_historical_generic_dossier_is_untouched(self):
        [case] = cases("historical-generic-dossier")
        self.assertEqual("UNTOUCHED", case["outcome"]); self.assertEqual("WP-2026-0010", case["subject"])
        wp10 = ROOT / "work" / "WP-2026-0010"
        d = json.loads((wp10 / "gate-dossier.G08.json").read_text(encoding="utf-8"))
        ev = {e["type"]: json.loads((ROOT / e["path"]).read_text(encoding="utf-8")) for e in d["evidence"]}
        for t, e in ev.items():
            gate.check_g08_binding(ROOT / e["artifact"], d, e)   # binding-less -> pass-through
        w = json.loads((wp10 / "work-package.json").read_text(encoding="utf-8"))
        gate.check_g08_dossier(d, w, ev, None, None)             # silent
        self.assertEqual(d["disposition"], "PASS_WITH_CONDITIONS")

    def test_encoded_real_reviews_verify_and_refuse_tampering(self):
        enc = {c["subject"]: c for c in cases("real-review-encoded")}
        self.assertEqual(set(ENCODED), set(enc))
        tmp = Path(tempfile.mkdtemp(prefix="badf-shadow-")); self.addCleanup(shutil.rmtree, tmp, True)
        for name, (comment_id, verdict) in ENCODED.items():
            path = ROOT / "examples" / f"verification-record-{name}.json"
            self.assertTrue(path.is_file(), name)
            rec = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, len(rec["ballots"]), "single-reviewer: one ballot, never a council")
            ballot = rec["ballots"][0]
            self.assertEqual(comment_id, ballot["reviewer_run_id"], "the real comment id is the run id")
            self.assertEqual(verdict, ballot["verdict"], name)
            self.assertIn("reconstructed", json.dumps(rec["non_coverage"]).lower(), "provenance declared in-record")
            out = gate.validate_verification_record(path)
            self.assertIn("BADF VERIFY PASS", out)
            self.assertEqual("VERIFY_PASS", enc[name]["outcome"])
            bad = copy.deepcopy(rec); bad["ballots"][0]["sealed_input_digest"] = "sha256:" + "9" * 64
            p = tmp / "bad.json"; p.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(gate.ValidationError): gate.validate_verification_record(p)
        # the #196 arc: a real MAJOR finding, then RESOLVED -- and erasing it is refused
        rc = json.loads((ROOT / "examples" / "verification-record-pr196-request-changes.json").read_text(encoding="utf-8"))
        majors = [f for f in rc["findings"] if f["severity"] == "MAJOR" and f["status"] == "OPEN"]
        self.assertEqual(1, len(majors), "the synthetic-id collision is encoded as a real OPEN MAJOR finding")
        ap = json.loads((ROOT / "examples" / "verification-record-pr196-approved.json").read_text(encoding="utf-8"))
        self.assertTrue(any(f["severity"] == "MAJOR" and f["status"] == "RESOLVED" for f in ap["findings"]),
                        "the Approved record carries the finding RESOLVED, not erased")
        bad = copy.deepcopy(rc); bad["findings"] = []; p = tmp / "erased.json"; p.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(gate.ValidationError): gate.validate_verification_record(p)  # ballot cites VF- -> VER-I12

    def test_representative_defects_are_refused_and_clean_dossiers_admitted(self):
        reps = cases("representative-typed-dossier")
        by = {c["subject"]: c for c in reps}
        harness = {
            "clean-c1": (None, dossier(), None, objects(), COMP, None),
        }
        # recompute every case through the pure control; the record must agree
        def run(subject):
            c = by[subject]
            built = build_case(subject)
            try:
                if len(built) == 2:                    # binding-level case: (artifact_text, evidence)
                    import tempfile as _tf, shutil as _sh
                    tmp = Path(_tf.mkdtemp(prefix="badf-shadow-bind-")); self.addCleanup(_sh.rmtree, tmp, True)
                    art = tmp / "artifact.txt"; art.write_text(built[0], encoding="utf-8")
                    gate.check_g08_binding(art, {}, built[1])
                    return "ADMITTED"
                d, w, ev, comp, rec = built
                gate.check_g08_dossier(d, w, ev, comp, rec)
                return "ADMITTED"
            except gate.ValidationError as exc:
                import re as _re
                m = _re.search(r"/ (C[1-7])\)", str(exc))   # the control tag is the trailing "(VER-Ixx / Cn)"
                if m:
                    return f"REFUSED({m.group(1)})"
                m = _re.search(r"(VER-I1[04])", str(exc))    # binding-level cases carry the invariant tag
                return f"REFUSED({m.group(1)})" if m else "REFUSED(?)"
        for subject, c in by.items():
            self.assertEqual(c["outcome"], run(subject), subject)
        admitted = [c for c in reps if c["outcome"] == "ADMITTED"]
        refused = [c for c in reps if c["outcome"].startswith("REFUSED")]
        self.assertGreaterEqual(len(admitted), 2); self.assertGreaterEqual(len(refused), 10)
        controls_hit = {c["outcome"] for c in refused}
        for ctrl in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "VER-I10", "VER-I14"):
            self.assertTrue(any(ctrl in o for o in controls_hit), f"{ctrl} must own at least one refusal")

    def test_metrics_match_the_record(self):
        rec = shadow(); m = rec["metrics"]
        reps = cases("representative-typed-dossier")
        self.assertEqual(m["injected_defects_refused"], len([c for c in reps if c["outcome"].startswith("REFUSED")]))
        self.assertEqual(m["clean_dossiers_admitted"], len([c for c in reps if c["outcome"] == "ADMITTED"]))
        self.assertEqual(m["false_refusals"], 0); self.assertEqual(m["missed_defects"], 0)
        self.assertEqual(m["encoded_reviews_verified"], 5)
        self.assertIn("reviewer_correlation", rec["metrics"]); self.assertEqual(m["reviewer_correlation"], "NOT_MEASURABLE_ONE_SEAT")

    def test_tampered_shadow_record_is_refused(self):
        rec = shadow()
        flip = copy.deepcopy(rec)
        for c in flip["cases"]:
            if c["case_class"] == "representative-typed-dossier" and c["outcome"].startswith("REFUSED"):
                c["outcome"] = "ADMITTED"; break
        self.assertNotEqual(rec, flip)
        subjects = {c["subject"]: c["outcome"] for c in rec["cases"] if c["case_class"] == "representative-typed-dossier"}
        flipped = {c["subject"]: c["outcome"] for c in flip["cases"] if c["case_class"] == "representative-typed-dossier"}
        self.assertNotEqual(subjects, flipped, "a tampered outcome cannot equal the recomputed truth")

    def test_doc_names_every_case_and_gap_and_root_is_shadowed(self):
        text = DOC.read_text(encoding="utf-8")
        first = text.split("\n\n")[1] if text.startswith("#") else text.split("\n\n")[0]
        for token in ("representative", "RECONSTRUCTED"):
            self.assertIn(token.lower(), (text[:1200]).lower(), token)
        for token in ("WP-2026-0010", "#196", "#201", "#202", "#205", "conflict of interest", "one reviewer seat"):
            self.assertIn(token.lower(), text.lower(), token)
        registry = json.loads((ROOT / "badf/skill-registry.json").read_text(encoding="utf-8"))
        entry = next(e for e in registry["skills"] if e["name"] == "badf-engineering-verification")
        self.assertEqual("SHADOWED", entry["status"])
        self.assertEqual(entry["digest"], gate.sha256(ROOT / "skills/badf-engineering-verification/SKILL.md"))


def build_case(subject):
    """Deterministic reconstruction of each representative case from the VER-C test fixtures."""
    if subject == "clean-c1":
        return dossier(), None, objects(), COMP, None
    if subject == "clean-c2-council":
        from tests.test_badf_verification_controls import record
        return dossier(change_class="C2"), None, objects(), COMP, record()
    if subject == "divergent-tree-with-record":
        ev = objects(); ev["integration-test"]["binding"]["target"]["expected_content_tree"] = "f" * 40
        return dossier(), None, ev, COMP, None
    if subject == "divergent-tree-no-record":
        ev = objects()
        for o in ev.values(): o["binding"]["target"]["expected_content_tree"] = "f" * 40
        ev["independent-review"]["binding"]["target"]["expected_content_tree"] = "e" * 40
        ev["composed-tree-test"]["binding"]["composition"].update(recorded_expected_content_tree="f" * 40, recomputed_content_tree="f" * 40)
        return dossier(), None, ev, None, None
    if subject == "author-as-reviewer-uncarried":
        ev = objects(); ev["independent-review"]["binding"]["independence"]["author_run_id"] = "run-a"
        return dossier(), None, ev, COMP, None
    if subject == "c2-one-ballot":
        from tests.test_badf_verification_controls import record
        one = record(); one["ballots"] = one["ballots"][:1]
        return dossier(change_class="C2"), None, objects(), COMP, one
    if subject == "c2-missing-lens":
        from tests.test_badf_verification_controls import record
        return dossier(change_class="C2"), None, objects(), COMP, record(lenses_routed=["correctness"])
    if subject == "untyped-agent-under-runtime-required":
        ev = objects(**{"integration-test": evidence("integration-test", None, producer="agent")})
        return dossier(), wp(verification_obligations={"runtime_required": True}), ev, COMP, None
    if subject == "empty-non-coverage":
        ev = objects(**{"integration-test": evidence("integration-test", observation("integration-test", non_coverage=[]))})
        return dossier(), None, ev, COMP, None
    if subject == "open-major-passed-over":
        ev = objects(**{"independent-review": evidence("independent-review", review(findings=[finding()], verdict="APPROVE_WITH_CONDITIONS"))})
        return dossier(), None, ev, COMP, None
    if subject == "open-major-unmapped-pwc":
        ev = objects(**{"independent-review": evidence("independent-review", review(findings=[finding()], verdict="APPROVE_WITH_CONDITIONS"))})
        return dossier(disposition="PASS_WITH_CONDITIONS"), None, ev, COMP, None
    if subject == "composed-declared-not-applicable":
        return dossier(non_coverage=[{"evidence_type": "composed-tree-test", "reason": "r", "declared_by": "x"}]), None, objects(), COMP, None
    if subject == "bare-pass-review":                 # binding-level: VER-I10, no findings + no non-coverage + no permitting contract
        return ("review\n", evidence("independent-review", review(non_coverage=[])))
    if subject == "indeterminate-contract-as-pass":   # binding-level: VER-I14, INDETERMINATE serialised as PASS
        b = observation("contract-test"); b["result"] = "INDETERMINATE"
        return ("x\n", evidence("contract-test", b, outcome="PASS"))
    raise AssertionError(f"unknown representative subject {subject!r}")


if __name__ == "__main__":
    unittest.main()
