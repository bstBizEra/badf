"""badf-release-validation WP-VAL-B (BADF-WP-0113 / GOV-0103 / #233): typed G09 evidence.

WP-VAL-A froze the contract (VAL-I01..I20); this rung makes the four G09 evidence types
checkable. Four typed schemas specialize evidence for `quality-validation`,
`security-validation`, `performance-test` and `resilience-test` with a CLOSED `binding`
(the VER-B pattern, additive: generic objects stay admissible). `check_g09_binding` in
EVIDENCE_RULES refuses mixed-candidate evidence (VAL-I01), an observation produced or
adjudicated by an agent (VAL-I04/I05), PASS on an unapproved runtime (VAL-I04), empty
non-coverage (VAL-I15), an undeclared NON_PRODUCTION deviation (VAL-I08), a flake policy
that discards failures (VAL-I16), PASS over an open blocking finding (VAL-I14), thresholds
bound after the run began (VAL-I06/I10), and resilience PASS without observed recovery
(VAL-I11/I12). Cross-class candidate identity and slot substitution (VAL-I13) are dossier
controls, deferred to WP-VAL-C; each binding's additionalProperties:false already refuses
one class's payload in another's slot structurally.

Vacuity discipline (#234): every sweep below iterates a literal tuple, and every filtered
lookup is followed by an assertion that the filter matched.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

WP = "WP-2026-9999"  # the unallocatable sentinel (GOV-0085): never a real ledger id
G09 = ("quality-validation", "security-validation", "performance-test", "resilience-test")
SHA = "0" * 40
DIGEST = "sha256:" + "a" * 64
T0, T1, T2 = "2026-08-31T00:00:00Z", "2026-08-31T01:00:00Z", "2026-08-31T02:00:00Z"


def _envelope(kind, **over):
    e = {"schema_version": "1.0.0", "id": f"EVD-{WP}-G09-{kind}", "work_package_id": WP,
         "gate": "G09", "claim": f"{kind} of the candidate", "evidence_type": kind,
         "producer": {"id": "validation-runtime", "type": "controller"},
         "source_revision": SHA, "target": "bstBizEra/badf:main",
         "toolchain": {"name": "badf-validation", "version": "1.0"},
         "operation": f"g09-{kind}", "started_at": T1, "completed_at": T2,
         "outcome": "PASS", "artifact": f"evidence/G09/{kind}.txt", "digest": DIGEST}
    e.update(over)
    return e


def _common_binding():
    return {
        "candidate": {"source_revision": SHA, "content_tree": "b" * 40,
                      "environment_id": "staging-1", "policy_epoch": "BADF-2026-08-25"},
        "risk_hypothesis": "the candidate fails under its declared risk surface",
        "method": "scenario execution against a deterministic oracle",
        "oracle": {"kind": "DETERMINISTIC_CHECK", "locator": "orders.db:order_id",
                   "evaluated_by": {"id": "oracle-runner", "type": "service"}},
        "runtime": {"runtime": "validation-runner-1", "approved": True, "started_at": T1,
                    "finished_at": T2, "exit_code": 0, "output_digest": DIGEST},
        "environment": {"identity": "staging-1", "configuration": {}, "observed_at": T1,
                        "toolchain": {"name": "runner", "version": "1.0"},
                        "production_equivalence": "NON_PRODUCTION",
                        "material_deviations": [{"surface": "payment gateway", "deviation": "sandbox, not live"}]},
        "findings": [],
        "non_coverage": [{"surface": "peak seasonal load", "reason": "not reproducible in staging"}],
        "flake_policy": {"reruns_permitted": 1, "failed_observations_retained": True},
    }


def _class_extra(kind):
    if kind == "quality-validation":
        return {"quality_dimensions": [{"dimension": "FUNCTIONAL", "result": "PASS",
                                        "oracle_locator": "orders.db:order_id"}]}
    if kind == "security-validation":
        return {"security_obligations": [{"obligation_id": "SEC-OB-1", "source": "THREAT_MODEL", "result": "PASS"}],
                "residual_risk": []}
    if kind == "performance-test":
        return {"workload": {"family": "AVERAGE", "profile": "50 VU / 10 min"},
                "measurements": [{"metric": "p95_latency", "observed": 180.0, "unit": "ms",
                                  "slo": {"bound": 250.0, "comparator": "LTE", "bound_at": T0,
                                          "source": "NFR-PERF-01"}}]}
    if kind == "resilience-test":
        return {"steady_state": {"definition": "p95 < 250ms, error rate < 0.1%", "observed_before": True,
                                 "observed_after": True},
                "fault": {"injection": "kill primary db pod", "blast_radius": "staging namespace",
                          "expected_behavior": "replica promotion within 30s",
                          "abort_conditions": [{"condition": "error rate > 5%", "executable": True}]},
                "recovery": {"observed": True, "recovery_time_seconds": 22.0,
                             "integrity_checks": [{"check": "order ledger balanced", "result": "PASS"}]}}
    raise AssertionError(kind)


def typed(kind, **over):
    e = _envelope(kind)
    b = _common_binding()
    b.update(_class_extra(kind))
    e["binding"] = b
    for dotted, val in over.items():
        node = e
        parts = dotted.split("__")
        for p in parts[:-1]:
            node = node[p]
        node[parts[-1]] = val
    return e


ART = Path(tempfile.mkdtemp()) / "artifact.txt"
ART.write_text("g09 observation artifact\n", encoding="utf-8")


def run(evidence):
    return gate.check_g09_binding(ART, {}, evidence)


class AdditiveTests(unittest.TestCase):
    def test_evidence_without_binding_stays_admissible(self):
        for kind in G09:  # literal tuple
            with self.subTest(kind=kind):
                run(_envelope(kind))  # no binding -> pass-through, exactly VER-B's shape

    def test_registered_over_the_four_g09_types(self):
        for kind in G09:  # literal tuple
            self.assertIs(gate.EVIDENCE_RULES.get(kind), gate.check_g09_binding, kind)

    def test_a_well_formed_typed_object_is_admitted_per_class(self):
        for kind in G09:  # literal tuple; the reachability baseline for every refusal below
            with self.subTest(kind=kind):
                run(typed(kind))


class SharedControlTests(unittest.TestCase):
    def test_mixed_candidate_evidence_is_refused(self):  # V1 / VAL-I01
        e = typed("quality-validation")
        e["binding"]["candidate"]["source_revision"] = "f" * 40
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I01"):
            run(e)

    def test_agent_produced_observation_is_refused(self):  # V2 / VAL-I04-I05
        for kind in G09:  # literal tuple
            with self.subTest(kind=kind):
                e = typed(kind)
                e["producer"]["type"] = "agent"
                with self.assertRaisesRegex(gate.ValidationError, "VAL-I04"):
                    run(e)

    def test_agent_as_its_own_oracle_is_refused(self):  # V3 / VAL-I04
        e = typed("quality-validation")
        e["binding"]["oracle"]["evaluated_by"]["type"] = "agent"
        with self.assertRaisesRegex(gate.ValidationError, "outside the agent"):
            run(e)

    def test_empty_oracle_locator_is_refused(self):  # V3b / VAL-I04
        # the schema's minLength:1 is INERT in this walker (it honours only required/enum/
        # pattern/additionalProperties/type), so an empty locator is schema-valid and the
        # refusal must be a code control or it does not exist.
        e = typed("security-validation")
        e["binding"]["oracle"]["locator"] = "   "
        with self.assertRaisesRegex(gate.ValidationError, "names nothing"):
            run(e)

    def test_threshold_ordering_survives_an_equivalent_iso_spelling(self):  # V10 / VAL-I06
        # bound_at is BEFORE started_at but written '+00:00' instead of 'Z'. A raw string
        # comparison is not grounded in time here; parse_time is. Guards the fix, not the bug.
        e = typed("performance-test")
        e["binding"]["runtime"]["started_at"] = "2026-08-31T01:00:00Z"
        e["binding"]["measurements"][0]["slo"]["bound_at"] = "2026-08-31T00:30:00+00:00"
        run(e)  # admissible: the bound genuinely pre-exists the run

    def test_threshold_bound_after_the_run_is_refused_even_when_it_sorts_earlier(self):  # V10 / VAL-I06
        # THE FALSE-ACCEPT DIRECTION, contributed by BADF-QA's near-miss battery. Each bound_at
        # below is semantically AFTER started_at but sorts BEFORE it as a string, so a raw
        # comparison ADMITS a threshold fitted to the result -- a bad verdict passing silently.
        # The equivalence and malformation tests above both survive a revert to string
        # comparison; only these three fail, so this is the guard on the parse_time fix.
        for bound_at in ("2026-08-30T20:00:00-07:00",   # == 03:00Z
                         "2026-08-30T23:30:00-02:00",   # == 01:30Z
                         "2026-08-31T00:30:00-01:00"):  # == 01:30Z
            with self.subTest(bound_at=bound_at):
                self.assertLess(bound_at, "2026-08-31T01:00:00Z", "must sort earlier to be a real probe")
                e = typed("performance-test")
                e["binding"]["runtime"]["started_at"] = "2026-08-31T01:00:00Z"
                e["binding"]["measurements"][0]["slo"]["bound_at"] = bound_at
                with self.assertRaisesRegex(gate.ValidationError, "VAL-I06"):
                    run(e)

    def test_malformed_threshold_timestamp_is_refused(self):  # V10 / VAL-I06
        # `format: date-time` is inert too, so a non-ISO bound_at reaches the control;
        # parse_time refuses it rather than comparing nonsense.
        e = typed("performance-test")
        e["binding"]["measurements"][0]["slo"]["bound_at"] = "yesterday"
        with self.assertRaisesRegex(gate.ValidationError, "ISO 8601"):
            run(e)

    def test_pass_on_unapproved_runtime_is_refused(self):  # V4 / VAL-I04
        e = typed("performance-test")
        e["binding"]["runtime"]["approved"] = False
        # match the INVARIANT id, not the field name: check_schema's own message embeds the
        # field path ("binding.runtime.approved must be a boolean"), so a bare "approved"
        # regex is satisfiable by a schema-layer refusal and would not prove the control ran.
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I04"):
            run(e)

    def test_empty_noncoverage_is_refused(self):  # V5 / VAL-I15
        e = typed("security-validation")
        e["binding"]["non_coverage"] = []
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I15"):
            run(e)

    def test_nonproduction_without_declared_deviation_is_refused(self):  # V6 / VAL-I08
        e = typed("resilience-test")
        e["binding"]["environment"]["material_deviations"] = []
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I08"):
            run(e)

    def test_flake_policy_discarding_failures_is_refused(self):  # V7 / VAL-I16
        e = typed("quality-validation")
        e["binding"]["flake_policy"]["failed_observations_retained"] = False
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I16"):
            run(e)

    def test_pass_over_an_open_blocking_finding_is_refused(self):  # V8 / VAL-I14
        e = typed("security-validation")
        e["binding"]["findings"] = [{"finding_id": "VF-9", "severity": "BLOCKER",
                                     "status": "OPEN", "summary": "auth bypass"}]
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I14"):
            run(e)

    def test_resolved_blocking_finding_does_not_block_pass(self):  # V8 boundary
        e = typed("security-validation")
        e["binding"]["findings"] = [{"finding_id": "VF-9", "severity": "BLOCKER",
                                     "status": "RESOLVED", "summary": "auth bypass",
                                     "disposition": "fixed in candidate"}]
        run(e)


class PerClassControlTests(unittest.TestCase):
    def test_security_with_empty_obligations_is_refused(self):  # V9
        e = typed("security-validation")
        e["binding"]["security_obligations"] = []
        with self.assertRaisesRegex(gate.ValidationError, "routing decision"):
            run(e)

    def test_security_self_accepted_risk_is_unrepresentable(self):  # V9 / VAL-I09 via schema enum
        e = typed("security-validation")
        e["binding"]["residual_risk"] = [{"risk_id": "RR-1", "severity": "MAJOR",
                                          "acceptance": {"state": "ACCEPTED"}}]
        with self.assertRaisesRegex(gate.ValidationError, "acceptance.state"):
            run(e)

    def test_performance_with_no_measurements_is_refused(self):  # V10 / VAL-I10
        e = typed("performance-test")
        e["binding"]["measurements"] = []
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I10"):
            run(e)

    def test_performance_threshold_bound_after_the_run_is_refused(self):  # V10 / VAL-I06
        e = typed("performance-test")
        e["binding"]["measurements"][0]["slo"]["bound_at"] = T2  # after started_at=T1
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I06"):
            run(e)

    def test_performance_measurement_without_slo_is_refused_by_schema(self):  # VAL-I10 structural
        e = typed("performance-test")
        del e["binding"]["measurements"][0]["slo"]
        with self.assertRaisesRegex(gate.ValidationError, "missing slo"):
            run(e)

    def test_resilience_without_prior_steady_state_is_refused(self):  # V11 / VAL-I11
        e = typed("resilience-test")
        e["binding"]["steady_state"]["observed_before"] = False
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I11"):
            run(e)

    def test_resilience_without_abort_conditions_is_refused(self):  # V11 / VAL-I11
        e = typed("resilience-test")
        e["binding"]["fault"]["abort_conditions"] = []
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I11"):
            run(e)

    def test_resilience_nonexecutable_abort_is_refused(self):  # V11 / VAL-I11
        e = typed("resilience-test")
        e["binding"]["fault"]["abort_conditions"][0]["executable"] = False
        with self.assertRaisesRegex(gate.ValidationError, "not executable"):
            run(e)

    def test_resilience_pass_without_observed_recovery_is_refused(self):  # V11 / VAL-I12
        e = typed("resilience-test")
        e["binding"]["recovery"]["observed"] = False
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I12"):
            run(e)

    def test_resilience_pass_with_no_integrity_checks_is_refused(self):  # V11 / VAL-I12
        # distinct from the FAIL-check case below: an EMPTY check list is structurally
        # valid (no minItems) and must be refused by the code control, not the schema.
        e = typed("resilience-test")
        e["binding"]["recovery"]["integrity_checks"] = []
        with self.assertRaisesRegex(gate.ValidationError, "no integrity checks"):
            run(e)

    def test_resilience_pass_with_failed_integrity_check_is_refused(self):  # V11 / VAL-I12
        e = typed("resilience-test")
        e["binding"]["recovery"]["integrity_checks"] = [{"check": "ledger balanced", "result": "FAIL"}]
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I12"):
            run(e)

    def test_resilience_failed_run_may_record_unobserved_recovery(self):  # V11 boundary
        # REACHABILITY, stated so it is not mistaken for a production path: validate_evidence
        # invokes EVIDENCE_RULES only when outcome == PASS (badf_gate.py:1916-1918), so the
        # dispatcher never routes a FAIL object here. This is a UNIT-level over-fire guarantee
        # -- the control must not refuse an honestly-recorded failure if it is ever called on
        # one -- not evidence of a path the gate takes today.
        e = typed("resilience-test", outcome="FAIL")
        e["binding"]["recovery"]["observed"] = False
        run(e)  # honesty about a failed observation is admissible; PASS is what recovery gates

    def test_quality_pass_dimension_without_oracle_is_refused(self):  # V12 / VAL-I04
        e = typed("quality-validation")
        e["binding"]["quality_dimensions"] = [{"dimension": "FUNCTIONAL", "result": "PASS"}]
        # invariant id, not "oracle": the walker's labels contain the field path too.
        with self.assertRaisesRegex(gate.ValidationError, "VAL-I04"):
            run(e)

    def test_quality_with_no_dimensions_is_refused(self):  # V12
        e = typed("quality-validation")
        e["binding"]["quality_dimensions"] = []
        with self.assertRaisesRegex(gate.ValidationError, "validated nothing"):
            run(e)


class StructuralTests(unittest.TestCase):
    def test_one_classes_payload_cannot_fill_anothers_slot(self):  # VAL-I13 structural floor
        e = typed("performance-test")
        donor = typed("resilience-test")
        e["binding"] = donor["binding"]  # a resilience binding in a performance evidence slot
        # MEASURED, not assumed: the walker checks `required` BEFORE additionalProperties, so a
        # WHOLESALE class swap is refused for the keys it LACKS, never reaching the foreign-key
        # check. An earlier version of this test asserted additionalProperties and passed only
        # because it accepted any ValidationError -- the mechanism was wrong and the bare
        # assertRaises hid it. Both floors exist; this one is `required`.
        with self.assertRaisesRegex(gate.ValidationError, "missing measurements"):
            run(e)

    def test_a_foreign_key_smuggled_into_a_complete_binding_is_refused(self):  # VAL-I13 floor 2
        # isolates the OTHER floor: a performance binding that satisfies every required key and
        # then carries one resilience field. `required` is satisfied, so this is the case where
        # additionalProperties:false is the control actually doing the work.
        e = typed("performance-test")
        e["binding"]["recovery"] = {"observed": True, "integrity_checks": []}
        with self.assertRaisesRegex(gate.ValidationError, "undefined key"):
            run(e)

    def test_registry_implemented_and_digest_bound(self):
        registry = json.loads((gate.ROOT / "badf" / "skill-registry.json").read_text(encoding="utf-8"))
        entry = next((s for s in registry["skills"] if s["name"] == "badf-release-validation"), None)
        self.assertIsNotNone(entry, "badf-release-validation must be registered")  # filter matched
        self.assertEqual(entry["status"], "IMPLEMENTED")
        import hashlib
        skill = gate.ROOT / "skills" / "badf-release-validation" / "SKILL.md"
        self.assertEqual(entry["digest"], "sha256:" + hashlib.sha256(skill.read_bytes()).hexdigest())

    def test_no_competing_validator_script_exists(self):  # VAL-I20 at every rung
        self.assertFalse((gate.ROOT / "scripts" / "badf_release_validation.py").exists())


if __name__ == "__main__":
    unittest.main()
