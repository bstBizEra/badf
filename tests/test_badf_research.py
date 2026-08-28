"""Research record checks (BADF-WP-0036, RSR-002).

The first deterministic controls of the frozen research contract:
`badf_gate.py research <path>` validates a record's schema, the referential
integrity of its source and claim refs, that confidence is DERIVED not
asserted, and that a VERIFIED claim rests on an independent primary source
and an OBSERVED claim on a primary source. Research grants no implementation
authority. Later work packages add challenge, state and traceability
controls. Every test mutates a copy of the shipped example and runs the CLI.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

EXAMPLE = json.loads((gate.ROOT / "examples/research-record.json").read_text())
CHALLENGED = json.loads((gate.ROOT / "examples/research-record-challenged.json").read_text())


class DeriveConfidenceTests(unittest.TestCase):
    """Confidence is a pure function of (independent_primary_sources,
    reproducible, contradictions) -- the table in evidence-contract.md."""

    def d(self, ips, repro, contra):
        return gate.derive_confidence({"independent_primary_sources": ips, "reproducible": repro, "contradictions": contra})

    def test_truth_table(self):
        self.assertEqual(self.d(0, True, 0), "VERY_LOW")
        self.assertEqual(self.d(0, False, 5), "VERY_LOW")
        self.assertEqual(self.d(1, False, 0), "LOW")
        self.assertEqual(self.d(1, True, 0), "MODERATE")
        self.assertEqual(self.d(2, False, 0), "MODERATE")
        self.assertEqual(self.d(3, False, 0), "MODERATE")
        self.assertEqual(self.d(2, True, 1), "HIGH")
        self.assertEqual(self.d(2, True, 0), "VERY_HIGH")
        self.assertEqual(self.d(5, True, 0), "VERY_HIGH")

    def test_every_result_is_a_schema_enum_value(self):
        levels = set(json.loads((gate.ROOT / "schemas/research-record.schema.json").read_text())
                     ["properties"]["claims"]["items"]["properties"]["confidence"]["properties"]["level"]["enum"])
        got = {self.d(i, r, c) for i in range(4) for r in (True, False) for c in range(3)}
        self.assertLessEqual(got, levels)


class ResearchRecordTests(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "research", str(path)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective research record passed")
        self.assertIn(needle, r.stderr, r.stderr)

    def test_shipped_example_passes(self):
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_asserted_confidence_that_is_not_the_derived_level_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["confidence"]["level"] = "LOW"   # basis derives VERY_HIGH
        self.refused(rec, "not the derived level")

    def test_a_dangling_source_reference_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["supporting_sources"].append("S-999")
        self.refused(rec, "S-999")

    def test_a_duplicate_source_id_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["sources"].append(dict(rec["sources"][0]))
        self.refused(rec, "duplicate source")

    def test_verified_without_an_independent_primary_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][1]["confidence"]["basis"]["independent_primary_sources"] = 0
        rec["claims"][1]["confidence"]["level"] = "VERY_LOW"   # keep confidence consistent so THIS control fires
        self.refused(rec, "no independent primary source")

    def test_verified_whose_only_support_is_secondary_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["sources"][1]["source_type"] = "SECONDARY"   # S-002, the only support of C-002 (VERIFIED)
        self.refused(rec, "no independent primary source")

    def test_observed_without_a_primary_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        # C-001 is OBSERVED; make both its supports non-primary while keeping it INFERRED-free
        for s in rec["sources"]:
            if s["id"] in ("S-001", "S-003"):
                s["source_type"] = "COMMUNITY"
        # C-002 (VERIFIED) also supported by S-002 primary still; C-001 now fails OBSERVED-needs-primary
        rec["claims"][0]["status"] = "PARTIALLY_VERIFIED"   # avoid the VERIFIED path so OBSERVED path is what refuses
        self.refused(rec, "cites no primary source")

    def test_implementation_authority_true_is_refused_by_the_schema(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["authority"]["implementation_authority"] = True   # schema fixes this to enum [false]
        self.refused(rec, "implementation_authority")

    def test_a_finding_referencing_an_unknown_claim_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["findings"][0]["claim_refs"].append("C-999")
        self.refused(rec, "C-999")


class ChallengeAndIndependenceTests(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "research", str(path)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective research record passed")
        self.assertIn(needle, r.stderr, r.stderr)

    def test_challenged_example_passes(self):
        r = self.run_cli(copy.deepcopy(CHALLENGED))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_more_independent_primaries_than_cited_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][1]["confidence"]["basis"]["independent_primary_sources"] = 3  # cites one primary (S-002)
        rec["claims"][1]["confidence"]["level"] = "VERY_HIGH"  # keep confidence derivation consistent so control 10 fires
        self.refused(rec, "source count is not independence")

    def test_deep_research_without_a_required_challenge_is_refused(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"] = {"required": False, "council": None}
        self.refused(rec, "requires independent challenge")

    def test_required_challenge_with_no_council_is_refused(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"] = None
        self.refused(rec, "no council record")

    def test_the_researcher_cannot_ballot_on_their_own_research(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"][0]["reviewer"] = rec["researcher"]["principal"]
        self.refused(rec, "cannot ballot on their own")

    def test_a_duplicate_reviewer_identity_is_refused(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"][1]["reviewer"] = rec["challenge"]["council"]["ballots"][0]["reviewer"]
        self.refused(rec, "duplicate reviewer")

    def test_a_ballot_without_declared_non_coverage_is_refused(self):
        rec = copy.deepcopy(CHALLENGED)
        del rec["challenge"]["council"]["ballots"][0]["non_coverage"]
        self.refused(rec, "reviewer, principal_type, verdict, non_coverage")

    def test_non_coverage_that_is_not_a_list_is_refused(self):
        """The key present is not enough -- a reviewer declares non-coverage as
        a list of surfaces, not a bare string (control 13)."""
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"][0]["non_coverage"] = "none"
        self.refused(rec, "non_coverage as a list")

    def test_a_single_reviewer_does_not_meet_quorum(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"] = rec["challenge"]["council"]["ballots"][:1]
        self.refused(rec, "at least two distinct reviewers")

    def test_an_invalid_ballot_verdict_is_refused(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"][0]["verdict"] = "APPROVE"
        self.refused(rec, "verdict")


class ConclusionAndTraceabilityTests(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "research", str(path)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective research record passed")
        self.assertIn(needle, r.stderr, r.stderr)

    def test_a_concluded_disposition_in_a_non_reconciled_state_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["state"] = "EVIDENCE_COLLECTING"   # but disposition is RESEARCH_SUFFICIENT
        self.refused(rec, "not RECONCILED")

    def test_research_blocked_may_be_in_flight(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["state"] = "EVIDENCE_COLLECTING"
        rec["disposition"] = {"state": "RESEARCH_BLOCKED", "reason": "still gathering"}
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)   # RESEARCH_BLOCKED is allowed pre-RECONCILED

    def test_challenged_state_without_a_council_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["state"] = "CHALLENGED"; rec["disposition"] = {"state": "RESEARCH_BLOCKED", "reason": "under challenge"}
        self.refused(rec, "CHALLENGED but no council")

    def test_a_contradiction_referencing_an_unknown_claim_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["contradictions"] = [{"id": "X-001", "claim_refs": ["C-999"], "statement": "x"}]
        self.refused(rec, "C-999")

    def test_a_claim_with_contradicting_sources_not_recorded_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["contradicting_sources"] = ["S-002"]   # cited but no contradictions[] entry
        rec["claims"][0]["confidence"]["basis"]["contradictions"] = 1
        rec["claims"][0]["confidence"]["level"] = "HIGH"   # keep derivation consistent (ips=2,repro,contra=1 -> HIGH)
        self.refused(rec, "no contradictions[] entry records it")

    def test_a_recorded_contradiction_makes_the_claim_valid(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["contradicting_sources"] = ["S-002"]
        rec["claims"][0]["confidence"]["basis"]["contradictions"] = 1
        rec["claims"][0]["confidence"]["level"] = "HIGH"
        rec["contradictions"] = [{"id": "X-001", "claim_refs": ["C-001"], "statement": "S-002 pointed the other way, examined"}]
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)   # material evidence changed -> re-digest (control 17)
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_not_sufficient_research_cannot_name_a_downstream_work_package(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["disposition"] = {"state": "MORE_RESEARCH_REQUIRED", "reason": "gaps remain"}
        rec["downstream"] = {"decision_id": None, "work_package_id": "WP-2026-0001"}
        self.refused(rec, "only RESEARCH_SUFFICIENT makes a work package eligible")

    def test_an_unresolvable_demand_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["demand"] = "BADF-DEM-9999"
        self.refused(rec, "BADF-DEM-9999")

    def test_a_downstream_work_package_with_no_record_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["downstream"] = {"decision_id": None, "work_package_id": "WP-2026-9999"}
        self.refused(rec, "no record")

    def test_a_downstream_decision_that_governs_another_work_package_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        # BADF-DEC-0007 governs WP-2026-0029; point downstream at a different WP that exists
        rec["downstream"] = {"decision_id": "BADF-DEC-0007", "work_package_id": "WP-2026-0001"}
        self.refused(rec, "does not reconstruct")

    def test_a_consistent_downstream_chain_passes(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["downstream"] = {"decision_id": "BADF-DEC-0007", "work_package_id": "WP-2026-0029"}
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)


class EvidenceDigestTests(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "research", str(path)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def rebind(self, rec):
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec); return rec

    def test_shipped_examples_carry_the_computed_digest(self):
        for name in ("research-record.json", "research-record-challenged.json"):
            rec = json.loads((gate.ROOT / "examples" / name).read_text())
            self.assertEqual(rec["evidence_digest"], gate.compute_research_evidence_digest(rec), name)

    def test_a_null_evidence_digest_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["evidence_digest"] = None
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0); self.assertIn("computed, not asserted", r.stderr)

    def test_a_claim_edited_without_re_digesting_is_stale(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["statement"] = "a different claim"   # material evidence changed; digest not updated
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0); self.assertIn("not the digest", r.stderr)

    def test_a_source_edited_without_re_digesting_is_stale(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["sources"][0]["uri"] = "https://example.invalid/moved"
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0); self.assertIn("not the digest", r.stderr)

    def test_editing_interpretation_does_not_change_the_evidence_digest(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["recommendation"] = "a different recommendation, same evidence"
        rec["findings"][0]["statement"] = "reworded finding"
        r = self.run_cli(rec)   # evidence_digest unchanged and still correct -> passes
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_re_digesting_after_a_real_edit_passes(self):
        rec = self.rebind(copy.deepcopy(EXAMPLE))
        rec["claims"][0]["statement"] = "a new, honestly re-digested claim"
        self.rebind(rec)
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
