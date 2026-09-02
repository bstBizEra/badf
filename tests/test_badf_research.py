"""Research record checks (BADF-WP-0036, RSR-002).

The first deterministic controls of the frozen research contract:
`badf_gate.py research <path>` validates a record's schema, the referential
integrity of its source and claim refs, that confidence is DERIVED not
asserted, and that a VERIFIED claim rests on an independent primary source
and an OBSERVED claim on a primary source. Research grants no implementation
authority. Later work packages add challenge, state and traceability
controls. Every test mutates a copy of the shipped example and runs the CLI.
"""

# Rung A (#265, WP-2026-0138): probe moved from the empty form to the whitespace form.
# `minLength`/`minItems` are LENGTH bounds and admit "   "; this control uses .strip()
# and is STRICTLY STRONGER, so the re-pointed probe still exercises the control itself.
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
REPO = json.loads((gate.ROOT / "examples/research-record-repo.json").read_text())


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


class RepositoryResearchTests(unittest.TestCase):
    """Control 3: a repo-type (R02/R03) record baselines to a commit that
    resolves in its repository. Mutating a copy of the shipped R02 example."""
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

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective record passed")
        self.assertIn(needle, r.stderr, r.stderr)

    def test_repo_example_passes(self):
        r = self.run_cli(copy.deepcopy(REPO))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_a_baseline_that_does_not_resolve_is_refused(self):
        rec = copy.deepcopy(REPO); rec["baseline"]["revision"] = "0" * 40
        self.refused(self.rebind(rec), "does not resolve")

    def test_a_baseline_in_an_unregistered_repository_is_refused(self):
        rec = copy.deepcopy(REPO); rec["baseline"]["repository"] = "bstBizEra/nope"
        self.refused(self.rebind(rec), "not registered")

    def test_control_3_does_not_apply_to_non_repository_research(self):
        rec = copy.deepcopy(REPO)
        rec["type"] = "R10"; rec["baseline"]["revision"] = "0" * 40   # bogus, but R10 is not repo-type (and needs no alternatives)
        r = self.run_cli(self.rebind(rec))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_root_cause_record_is_also_subject_to_control_3(self):
        rec = copy.deepcopy(REPO)
        rec["type"] = "R03"; rec["baseline"]["revision"] = "0" * 40
        self.refused(self.rebind(rec), "does not resolve")

    def test_an_absent_local_mirror_reports_unresolvable_here(self):
        """A record baselining to a LOCAL_MIRROR that is not on this host is
        UNRESOLVABLE_HERE, not a refusal. Registered against a scratch path so
        the test is host-independent; the registry is restored."""
        import shutil, tempfile as tf
        reg = gate.ROOT / gate.REPOSITORIES; lock = gate.ROOT / gate.LOCKFILE
        backup = Path(tf.mkdtemp())
        shutil.copy2(reg, backup / "r.json"); shutil.copy2(lock, backup / "l.json")
        try:
            d = json.loads(reg.read_text())
            d["repositories"]["bstBizEra/absent-mirror"] = {"local_path": "/no/such/mirror/here", "default_branch": "main", "resolution": "LOCAL_MIRROR"}
            reg.write_text(json.dumps(d, indent=2) + "\n")
            gate.write_lock(gate.ROOT, gate.INTEGRITY_PATHS)
            rec = copy.deepcopy(REPO); rec["baseline"]["repository"] = "bstBizEra/absent-mirror"; rec["baseline"]["revision"] = "abc1234"
            self.refused(self.rebind(rec), "UNRESOLVABLE_HERE")
        finally:
            shutil.copy2(backup / "r.json", reg); shutil.copy2(backup / "l.json", lock)
            shutil.rmtree(backup, ignore_errors=True)


class ScopeContractTests(ResearchRecordTests):
    """Control 19 (BADF-WP-0045): the scope contract is bounded and machine-readable
    -- non-empty stop_conditions, assumptions distinct from evidence, a decision it
    serves -- and these framing fields are excluded from the evidence_digest."""

    def test_empty_stop_conditions_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["stop_conditions"] = []
        self.refused(rec, "no bounded stop_conditions")

    def test_whitespace_only_stop_condition_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["stop_conditions"] = ["   "]
        self.refused(rec, "no bounded stop_conditions")

    def test_absent_stop_conditions_is_refused_by_schema(self):
        rec = copy.deepcopy(EXAMPLE); rec.pop("stop_conditions")
        self.refused(rec, "stop_conditions")

    def test_an_empty_assumption_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["assumptions"] = ["a real assumption", "   "]
        self.refused(rec, "empty assumption")

    def test_an_empty_decision_question_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["decision_context"] = {"decision_question": "   "}
        self.refused(rec, "decision_context.decision_question is empty")

    def test_changing_only_framing_leaves_the_evidence_digest_valid(self):
        # stop_conditions/assumptions/decision_context are framing, not evidence:
        # changing them must not invalidate the stored evidence_digest (control 17).
        rec = copy.deepcopy(EXAMPLE)
        rec["stop_conditions"] = ["a different but still bounded stop condition"]
        rec["assumptions"] = ["a different assumption"]
        rec["decision_context"] = {"decision_question": "a different decision this run serves?"}
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("RESEARCH PASS", r.stdout)


class PreEvidenceGuardTests(ResearchRecordTests):
    """Control 20 (BADF-WP-0046, problem-framing): a record in a pre-evidence state
    carries no claims, sources, or findings -- framing precedes evidence collection."""

    def test_a_framed_record_with_claims_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["state"] = "FRAMED"
        self.refused(rec, "pre-evidence state FRAMED but carries")

    def test_a_proposed_record_with_evidence_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["state"] = "PROPOSED"
        self.refused(rec, "pre-evidence state PROPOSED but carries")

    def test_a_baselined_record_with_evidence_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["state"] = "BASELINED"
        self.refused(rec, "pre-evidence state BASELINED but carries")

    def test_the_reconciled_example_with_claims_still_passes(self):
        # control 20 only guards pre-evidence states; a RECONCILED record carries evidence.
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)


class FactCheckStatusTests(ResearchRecordTests):
    """Control 21 (BADF-WP-0047, fact-checking): a claim's status is consistent with
    its evidence. FALSIFIED needs a contradicting source (NO EVIDENCE != FALSE);
    DISPUTED needs both supporting and contradicting (support and contradiction
    coexist). Records are re-digested so control 17 does not mask the status gap."""

    def refused_redigest(self, rec, needle):
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)
        self.refused(rec, needle)

    def passes_redigest(self, rec):
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_falsified_without_a_contradicting_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["claims"][0]["status"] = "FALSIFIED"; rec["claims"][0]["contradicting_sources"] = []
        self.refused_redigest(rec, "FALSIFIED but cites no contradicting source")

    def test_disputed_without_a_contradicting_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["claims"][0]["status"] = "DISPUTED"; rec["claims"][0]["contradicting_sources"] = []
        self.refused_redigest(rec, "DISPUTED but does not carry both")

    def _with_contradiction(self, rec):
        cid = rec["claims"][0]["id"]; other = rec["sources"][-1]["id"]
        rec["claims"][0]["contradicting_sources"] = [other]
        rec["contradictions"] = [{"id": "X-001", "claim_refs": [cid], "statement": "an independent source contradicts the claim"}]
        return rec

    def test_a_falsified_claim_with_a_contradicting_source_passes(self):
        rec = self._with_contradiction(copy.deepcopy(EXAMPLE)); rec["claims"][0]["status"] = "FALSIFIED"
        self.passes_redigest(rec)

    def test_a_disputed_claim_with_both_sides_passes(self):
        rec = self._with_contradiction(copy.deepcopy(EXAMPLE)); rec["claims"][0]["status"] = "DISPUTED"
        self.passes_redigest(rec)


class SourceFreshnessTests(ResearchRecordTests):
    """Control 6 (BADF-WP-0050): a claim may not rest on a STALE or UNKNOWN source.
    deep-research sets each source's freshness on re-resolution; the gate fails
    closed. freshness is part of the evidence_digest, so records are re-digested."""

    def refused_redigest(self, rec, needle):
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)
        self.refused(rec, needle)

    def test_a_claim_on_a_stale_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); cited = rec["claims"][0]["supporting_sources"][0]
        for s in rec["sources"]:
            if s["id"] == cited:
                s["freshness"] = "STALE"
        self.refused_redigest(rec, "freshness is STALE")

    def test_a_claim_on_an_unknown_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); cited = rec["claims"][0]["supporting_sources"][0]
        for s in rec["sources"]:
            if s["id"] == cited:
                s["freshness"] = "UNKNOWN"
        self.refused_redigest(rec, "freshness is UNKNOWN")

    def test_all_current_sources_pass(self):
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)


class TechnicalResearchTests(ResearchRecordTests):
    """Control 23 (BADF-WP-0051, technical-research): a TECHNICAL_SOLUTION (R04) run
    yields grounded options -- >=1 alternative, each with evidence_refs resolving to
    a claim, finding or source. alternatives/type are not in the evidence_digest."""

    def test_r04_with_zero_alternatives_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R04"; rec["alternatives"] = []
        self.refused(rec, "carries no alternatives")

    def test_an_ungrounded_alternative_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R04"
        rec["alternatives"] = [{"id": "A-001", "mechanism": "an approach", "evidence_refs": ["C-999"]}]
        self.refused(rec, "cites in-record evidence C-999 that is absent")

    def test_a_free_form_evidence_ref_is_allowed(self):
        # evidence_refs are free-form; only id-shaped refs must resolve.
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R04"
        rec["alternatives"] = [{"id": "A-001", "mechanism": "an approach", "evidence_refs": ["see the upstream design note"]}]
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_a_grounded_alternative_passes(self):
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R04"
        rec["alternatives"] = [{"id": "A-001", "mechanism": "an approach", "evidence_refs": [rec["claims"][0]["id"]]}]
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_technical_research_is_registered_implemented(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "technical-research"), None)
        self.assertIsNotNone(entry, "technical-research is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())


CHALLENGED = json.loads((gate.ROOT / "examples/research-record-challenged.json").read_text())


class ShadowEvidenceTests(ResearchRecordTests):
    """BADF-WP-0055: the three shadow records over real historical BADF cases are
    gate-valid, and each exercises the part of the contract it was chosen for."""

    SHADOWS = ("control15", "composed-red", "ci-parity")

    def test_all_three_shadow_records_pass(self):
        for name in self.SHADOWS:
            rec = json.loads((gate.ROOT / f"examples/research-record-shadow-{name}.json").read_text())
            r = self.run_cli(rec)
            self.assertEqual(r.returncode, 0, f"{name}: {r.stderr}")
            self.assertIn("RESEARCH PASS", r.stdout)

    def test_the_falsification_case_carries_a_preserved_contradiction(self):
        rec = json.loads((gate.ROOT / "examples/research-record-shadow-ci-parity.json").read_text())
        self.assertEqual(rec["claims"][0]["status"], "FALSIFIED")
        self.assertTrue(rec["claims"][0]["contradicting_sources"])
        self.assertTrue(rec["contradictions"])

    def test_the_repository_case_baselines_to_a_real_revision(self):
        rec = json.loads((gate.ROOT / "examples/research-record-shadow-control15.json").read_text())
        self.assertEqual(rec["type"], "R02")
        self.assertEqual(rec["baseline"]["revision"], "e7ea929")


class ResearchReconciliationTests(ResearchRecordTests):
    """Control 26 (BADF-WP-0054, research-reconciliation): sufficiency means synthesis
    -- a RESEARCH_SUFFICIENT record carries at least one finding. findings are not in
    the evidence_digest, so the record is re-digested defensively."""

    def _run(self, rec):
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)
        return self.run_cli(rec)

    def test_research_sufficient_with_zero_findings_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["findings"] = []
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)
        self.refused(rec, "RESEARCH_SUFFICIENT but the record carries no findings")

    def test_a_non_sufficient_disposition_with_zero_findings_passes(self):
        rec = copy.deepcopy(EXAMPLE); rec["findings"] = []
        rec["disposition"]["state"] = "MORE_RESEARCH_REQUIRED"
        rec["downstream"] = {"decision_id": None, "work_package_id": None}
        r = self._run(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_sufficient_with_a_finding_passes(self):
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_research_reconciliation_is_registered_implemented(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "research-reconciliation"), None)
        self.assertIsNotNone(entry, "research-reconciliation is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())


class AdversarialResearchTests(ResearchRecordTests):
    """Control 25 (BADF-WP-0053, adversarial-research): an independent refutation is
    not erased by declaring sufficiency -- a challenge council carrying a REFUTED
    ballot cannot reconcile to RESEARCH_SUFFICIENT. Challenge is not in the digest."""

    def test_a_refuted_ballot_blocks_research_sufficient(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"][0]["verdict"] = "REFUTED"
        self.assertEqual(rec["disposition"]["state"], "RESEARCH_SUFFICIENT")
        self.refused(rec, "REFUTED ballot but the disposition is RESEARCH_SUFFICIENT")

    def test_a_refuted_ballot_with_a_non_sufficient_disposition_passes(self):
        rec = copy.deepcopy(CHALLENGED)
        rec["challenge"]["council"]["ballots"][0]["verdict"] = "REFUTED"
        rec["disposition"]["state"] = "CONTRADICTORY_EVIDENCE"
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_confirmed_ballots_remain_sufficient(self):
        r = self.run_cli(copy.deepcopy(CHALLENGED))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_adversarial_research_is_registered_implemented(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "adversarial-research"), None)
        self.assertIsNotNone(entry, "adversarial-research is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())


class ComparativeEvaluationTests(ResearchRecordTests):
    """Control 24 (BADF-WP-0052, comparative-evaluation): a COMPARATIVE (R07) run
    weighs at least two alternatives. type/alternatives are not in the evidence_digest."""

    def test_r07_with_one_alternative_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R07"
        rec["alternatives"] = [{"id": "A-001", "mechanism": "only one option", "evidence_refs": []}]
        self.refused(rec, "fewer than two alternatives")

    def test_r07_with_zero_alternatives_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R07"; rec["alternatives"] = []
        self.refused(rec, "fewer than two alternatives")

    def test_r07_with_two_alternatives_passes(self):
        rec = copy.deepcopy(EXAMPLE); rec["type"] = "R07"
        rec["alternatives"] = [{"id": "A-001", "mechanism": "option one", "evidence_refs": []},
                               {"id": "A-002", "mechanism": "option two", "evidence_refs": []}]
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_comparative_evaluation_is_registered_implemented(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "comparative-evaluation"), None)
        self.assertIsNotNone(entry, "comparative-evaluation is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())


class ProblemFramingRegistrationTests(unittest.TestCase):

    def test_problem_framing_is_registered_implemented_with_a_real_digest(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "problem-framing"), None)
        self.assertIsNotNone(entry, "problem-framing is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertTrue((gate.ROOT / "skills/badf-research/subskills/problem-framing/SKILL.md").is_file())

    def test_fact_checking_is_registered_implemented_with_a_real_digest(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "fact-checking"), None)
        self.assertIsNotNone(entry, "fact-checking is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertTrue((gate.ROOT / "skills/badf-research/subskills/fact-checking/SKILL.md").is_file())

    def test_deep_research_is_registered_implemented_with_a_real_digest(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "deep-research"), None)
        self.assertIsNotNone(entry, "deep-research is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        skill = gate.ROOT / "skills/badf-research/subskills/deep-research/SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertIn("read-only", skill.read_text(encoding="utf-8").lower())


class EvidenceSynthesisTests(ResearchRecordTests):
    """Control 22 (BADF-WP-0048, evidence-synthesis): a finding is grounded in the
    claims it synthesises -- a finding references at least one claim (findings are
    not part of the evidence_digest, so no recompute is needed)."""

    def test_a_finding_with_no_claim_refs_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["findings"][0]["claim_refs"] = []
        self.refused(rec, "rests on no claim")

    def test_a_grounded_finding_passes(self):
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_evidence_synthesis_is_registered_implemented_with_a_real_digest(self):
        import hashlib
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next((e for e in reg["skills"] if e["name"] == "evidence-synthesis"), None)
        self.assertIsNotNone(entry, "evidence-synthesis is not registered")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest())
        self.assertTrue((gate.ROOT / "skills/badf-research/subskills/evidence-synthesis/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
