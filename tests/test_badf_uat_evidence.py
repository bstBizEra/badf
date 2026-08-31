"""WP-UAT-B (BADF-WP-0124 / GOV-0116): the typed `uat` G10 evidence binding.

Rung A froze the contract and shipped no runtime. This rung types the artifacts and extends the
canonical gate -- additive, so untyped `uat` evidence stays admissible exactly as VER-B and VAL-B
established.

The load-bearing property is not any single control: it is that **the recommendation vocabulary
cannot express an acceptance**. UAT-I14 says the capability that produced the evidence does not
issue the decision. A schema admitting `recommendation: "ACCEPTED"` would defeat that with a
permissive enum rather than an argument -- the producer would not have to disobey a rule, only
decline to read one. So the enum is closed, and the acceptance vocabulary exists only inside the
optional Layer 2 object.

But the two halves are NOT enforced the same way, and the difference is load-bearing:

  recommendation   `enum`  -- check_schema implements enum, so the SCHEMA closes it
  principal_type   `const` -- check_schema has NO const branch, so the schema closes NOTHING
                              and the U5 code control is the sole enforcer

Measured, not assumed (BADF-QA on #264, reproduced here): with U5 bypassed, check_schema ADMITS
`principal_type: "agent"`. The exactly-true claim is therefore narrower than "no encoding admits
an agent acceptance": **the schema plus U5 remove every HONEST encoding of one.** `principal` is
a free string, so `{"principal": "BARCHI-3 (agent)", "principal_type": "human"}` is admitted --
the pair pins a DECLARATION, never an identity, exactly as AGENTS.md says of role banners. What
the rung buys is that an agent acceptance must be written as a lie, and a lie is auditable.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

SCHEMA = gate.ROOT / "schemas" / "uat.schema.json"
DIG = "sha256:" + "a" * 64
DIG2 = "sha256:" + "b" * 64


def scenario(sid="UAT-SCN-001", crit="major"):
    return {"scenario_id": sid, "objective_ref": "OBJ-1", "acceptance_criterion_ref": "AC-1",
            "actor_role": "buyer", "expected_business_outcome": "the order is confirmed",
            "criticality": crit}


def observation(sid="UAT-SCN-001", result="PASS"):
    return {"scenario_id": sid, "adapter": "browser", "observed_outcome": "confirmation shown",
            "result": result, "executed_by": "adapter/browser", "executed_at": "2026-01-01T00:00:00Z"}


def binding(**over):
    b = {"candidate": {"source_digest": DIG},
         "acceptance_basis": {"prd_id": "PRD-1", "prd_digest": DIG,
                              "acceptance_criteria_digest": DIG},
         "scenarios": [scenario()],
         "observations": [observation()],
         "defects": [],
         "coverage": {"criteria": [{"acceptance_criterion_ref": "AC-1", "state": "covered_pass"}],
                      "roles": [{"actor_role": "buyer", "exercised": True}],
                      "journeys": [{"journey": "checkout", "state": "complete"}],
                      "non_coverage": []},
         "recommendation": "RECOMMEND_ACCEPT"}
    b.update(over)
    return b


def evidence(**over):
    e = {"schema_version": "1.0.0", "id": "EVD-UAT-1", "work_package_id": "WP-2026-9999",
         "gate": "G10", "claim": "business acceptance", "evidence_type": "uat",
         "producer": {"id": "t", "type": "controller"}, "source_revision": "HEAD",
         "target": "bstBizEra/badf:main", "toolchain": {"name": "t", "version": "1"},
         "operation": "uat", "started_at": "2026-01-01T00:00:00Z",
         "completed_at": "2026-01-01T00:00:00Z", "outcome": "PASS",
         "artifact": "work/WP-2026-9999/evidence/G10/uat.json", "digest": DIG,
         "binding": binding()}
    e.update(over)
    return e


def check(e):
    gate.EVIDENCE_RULES["uat"](Path("unused"), {"disposition": "PASS"}, e)


class UatTypedEvidenceTests(unittest.TestCase):
    def test_schema_exists_and_specializes_evidence(self):
        self.assertTrue(SCHEMA.is_file())
        d = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual({"const": "uat"}, d["properties"]["evidence_type"])
        self.assertEqual({"const": "G10"}, d["properties"]["gate"])
        for f in ("schema_version", "id", "work_package_id", "gate", "evidence_type",
                  "producer", "outcome", "artifact", "digest"):
            self.assertIn(f, d["required"], f)

    def test_a_clean_typed_binding_is_accepted(self):
        check(evidence())

    def test_untyped_binding_is_still_admissible(self):
        """Additivity -- the property VER-B and VAL-B established. Nothing already landed breaks."""
        e = evidence()
        del e["binding"]
        check(e)

    def test_recommendation_enum_cannot_express_an_acceptance(self):
        """UAT-I14 enforced by the VOCABULARY, not by an argument a producer could decline to read."""
        d = json.loads(SCHEMA.read_text(encoding="utf-8"))
        enum = d["properties"]["binding"]["properties"]["recommendation"]["enum"]
        for verdict in ("ACCEPTED", "ACCEPTED_WITH_CONDITIONS", "REJECTED"):
            self.assertNotIn(verdict, enum, f"{verdict} must not be a recommendation")
        # The INVARIANT is the prefix, not the count. `assertEqual(4, len(enum))` would fail the
        # day someone legitimately adds RECOMMEND_DEFER -- a snapshot (#268). The prefix rule is
        # STRONGER anyway: assertNotIn only catches the three verdicts I happened to name, while
        # this catches any acceptance-shaped value nobody has thought of yet.
        self.assertTrue(all(v.startswith("RECOMMEND_") for v in enum),
                        f"every recommendation must be a RECOMMEND_*; got {enum}")
        self.assertGreaterEqual(len(enum), 4, "the four frozen recommendations are a floor")
        with self.assertRaises(gate.ValidationError):
            check(evidence(binding=binding(recommendation="ACCEPTED")))

    def test_layer2_acceptance_requires_a_human_principal(self):
        """UAT-I14/I15: an agent cannot issue product acceptance by any encoding this schema admits."""
        d = json.loads(SCHEMA.read_text(encoding="utf-8"))
        acc = d["properties"]["binding"]["properties"]["acceptance"]
        self.assertEqual({"const": "human"},
                         acc["properties"]["accepted_by"]["properties"]["principal_type"])
        a = {"acceptance_id": "ACC-1", "candidate_digest": DIG, "acceptance_basis_digest": DIG,
             "scenario_set_digest": DIG, "disposition": "ACCEPTED",
             "accepted_by": {"principal": "bot", "principal_type": "agent"},
             "accepted_at": "2026-01-01T00:00:00Z"}
        with self.assertRaises(gate.ValidationError):
            check(evidence(binding=binding(acceptance=a)))

    def test_const_is_decorative_and_U5_is_the_sole_enforcer(self):
        """The correction to this rung's headline claim, pinned so it cannot drift back.

        `const` reads like enforcement and is not: check_schema implements required /
        additionalProperties / type / enum / pattern / items, with no const branch. So the
        human-principal rule lives entirely in the U5 code control. This test exists because the
        neighbouring docstring correctly says the schema closes the `recommendation` enum -- and
        an author generalising that true sentence four lines to the `const` would delete U5 and
        keep the appearance of the rule. (BADF-QA, #264 review; repo-wide as #265.)
        """
        a = {"acceptance_id": "ACC-1", "candidate_digest": DIG, "acceptance_basis_digest": DIG,
             "scenario_set_digest": DIG, "disposition": "ACCEPTED",
             "accepted_by": {"principal": "bot", "principal_type": "agent"},
             "accepted_at": "2026-01-01T00:00:00Z"}
        # The measurement, asserted as BEHAVIOUR rather than as source text. An earlier version
        # of this test grepped check_schema for '"const"' -- which would have failed the day #265
        # IMPLEMENTS const support, i.e. failed for being right about an improvement. That is the
        # snapshot-worn-as-invariant class (#268), instance four, in my own test, found by the
        # sweep BARCHI-2 suggested. If const is ever implemented THIS assertion fails too, but it
        # fails with an instruction rather than a puzzle:
        try:
            gate.check_schema("uat", evidence(binding=binding(acceptance=a)))
        except gate.ValidationError:
            self.fail("check_schema now REFUSES principal_type='agent', so const is implemented. "
                      "That is an improvement, not a regression: delete this test and remove the "
                      "SOLE ENFORCER comment on U5, which is now false.")
        # and the full rule refuses it, so U5 is doing all of the work
        with self.assertRaisesRegex(gate.ValidationError, "non-human principal"):
            check(evidence(binding=binding(acceptance=a)))

    def test_the_honest_limit_a_lying_declaration_is_admitted(self):
        """Stated as a boundary rather than defended as a stronger claim.

        `principal_type` is pinned; `principal` is a free string. An agent declaring itself human
        is ADMITTED. The rung does not make agent acceptance impossible -- it makes every honest
        encoding of one impossible, which converts a permitted act into a lie. That is the right
        property for a B rung and the wrong thing to overstate.
        """
        a = {"acceptance_id": "ACC-1", "candidate_digest": DIG, "acceptance_basis_digest": DIG,
             "scenario_set_digest": DIG, "disposition": "ACCEPTED",
             "accepted_by": {"principal": "BARCHI-3 (agent)", "principal_type": "human"},
             "accepted_at": "2026-01-01T00:00:00Z"}
        check(evidence(binding=binding(acceptance=a)))   # admitted, and that is the limit

    def test_layer2_must_bind_layer1s_candidate(self):
        """UAT-I16: an acceptance bound to a different candidate is void."""
        a = {"acceptance_id": "ACC-1", "candidate_digest": DIG2, "acceptance_basis_digest": DIG,
             "scenario_set_digest": DIG, "disposition": "ACCEPTED",
             "accepted_by": {"principal": "operator", "principal_type": "human"},
             "accepted_at": "2026-01-01T00:00:00Z"}
        with self.assertRaisesRegex(gate.ValidationError, "candidate_digest"):
            check(evidence(binding=binding(acceptance=a)))
        a["candidate_digest"] = DIG
        check(evidence(binding=binding(acceptance=a)))

    def test_an_unanchored_observation_is_refused(self):
        """U2 / UAT-I01: an observation of a scenario this binding does not carry is a test
        result, not UAT evidence."""
        with self.assertRaisesRegex(gate.ValidationError, "absent from this binding"):
            check(evidence(binding=binding(observations=[observation(sid="UAT-SCN-999")])))

    def test_a_failure_without_a_defect_class_is_refused(self):
        """U3 / UAT-I11: a FAIL or BLOCKED without a class is noise the disposition cannot act on."""
        b = binding(observations=[observation(result="FAIL")],
                    recommendation="RECOMMEND_REJECT")
        with self.assertRaisesRegex(gate.ValidationError, "no defect class"):
            check(evidence(binding=b))
        b["defects"] = [{"scenario_id": "UAT-SCN-001", "defect_class": "IMPLEMENTATION_DEFECT",
                         "statement": "total was wrong"}]
        check(evidence(binding=b))

    def test_defect_class_is_the_frozen_ten(self):
        d = json.loads(SCHEMA.read_text(encoding="utf-8"))
        classes = d["properties"]["binding"]["properties"]["defects"]["items"]["properties"]["defect_class"]["enum"]
        self.assertEqual(10, len(classes))
        self.assertIn("ACCEPTANCE_CRITERION_DEFECT", classes,
                      "the class that routes a bad requirement UPSTREAM must exist, or it gets "
                      "silently absorbed as an implementation bug")
        b = binding(observations=[observation(result="FAIL")], recommendation="RECOMMEND_REJECT",
                    defects=[{"scenario_id": "UAT-SCN-001", "defect_class": "INVENTED_CLASS",
                              "statement": "x"}])
        with self.assertRaises(gate.ValidationError):
            check(evidence(binding=b))

    def test_a_critical_failure_cannot_hide_under_recommend_accept(self):
        """U4 / UAT-I13: mandatory critical criteria cannot be buried by an aggregate."""
        b = binding(scenarios=[scenario(crit="critical"), scenario(sid="UAT-SCN-002")],
                    observations=[observation(result="NOT_EXECUTED"), observation(sid="UAT-SCN-002")],
                    recommendation="RECOMMEND_ACCEPT")
        with self.assertRaisesRegex(gate.ValidationError, "UAT-I13"):
            check(evidence(binding=b))
        # the same evidence is admissible when it stops claiming acceptance
        b["recommendation"] = "RECOMMEND_INSUFFICIENT_EVIDENCE"
        check(evidence(binding=b))

    def test_duplicate_observations_are_refused_not_resolved(self):
        """U6 -- BADF-QA's #264 blocking finding: U4's verdict depended on ARRAY ORDER.

        `by_scn = {o["scenario_id"]: o["result"] for o in observations}` is last-occurrence-wins,
        so the same multiset in two orders gave opposite verdicts -- [FAIL, PASS] ADMITTED under
        RECOMMEND_ACCEPT, [PASS, FAIL] refused. Meanwhile U3 ten lines up read the same array
        set-wise: two controls in one function disagreeing about what the array means.

        Fixed by removing the ambiguity rather than by picking an interpretation. A `uat` object
        is ONE execution pass; a re-run is a new object with its own candidate digest (UAT-I17).
        Any resolution rule -- last, worst, newest -- would be the gate deciding something the
        producer never stated.
        """
        crit = scenario(crit="critical")
        for order in ([observation(result="FAIL"), observation(result="PASS")],
                      [observation(result="PASS"), observation(result="FAIL")]):
            b = binding(scenarios=[crit], observations=order,
                        defects=[{"scenario_id": "UAT-SCN-001",
                                  "defect_class": "IMPLEMENTATION_DEFECT", "statement": "x"}],
                        recommendation="RECOMMEND_ACCEPT")
            with self.assertRaisesRegex(gate.ValidationError, "more than one observation"):
                check(evidence(binding=b))

    def test_the_same_multiset_in_either_order_yields_the_same_verdict(self):
        """Order must not decide. Pinned on the arrangement where order CAN decide.

        The first version of this test used two DISTINCT scenario_ids -- no dict-key collision,
        so order could not have mattered whether or not U6 existed. Measured: with U6 neutered,
        the duplicate-refusal test correctly went red and THIS one stayed green. It exercised the
        one arrangement where the property holds trivially, while its docstring claimed it
        "survives any future change to how duplicates are handled".

        That is the defect this whole rework exists to close -- a property checked on the side
        where it cannot fail -- and it is the third instance in two days of that shape, this one
        inside the test written to prove the second. Found by BADF-REV on #264.

        Now built on the DUPLICATE-key pair, which is the only arrangement where array order can
        reach the verdict, and asserted for EQUALITY rather than refusal: equal-and-refused while
        U6 stands, unequal the moment it is relaxed. The assertion is about order-invariance, so
        it does not care WHICH verdict -- only that both orders agree.
        """
        crit = scenario(crit="critical")
        defect = [{"scenario_id": "UAT-SCN-001", "defect_class": "IMPLEMENTATION_DEFECT",
                   "statement": "x"}]
        verdicts = []
        for order in ([observation(result="FAIL"), observation(result="PASS")],
                      [observation(result="PASS"), observation(result="FAIL")]):
            bnd = binding(scenarios=[crit], observations=order, defects=defect,
                          recommendation="RECOMMEND_ACCEPT")
            try:
                check(evidence(binding=bnd)); verdicts.append("ADMITTED")
            except gate.ValidationError as e:
                verdicts.append("REFUSED")
        self.assertEqual(verdicts[0], verdicts[1],
                         f"array order changed the verdict on a duplicate-key pair: {verdicts}; "
                         f"order must never decide, whatever the semantics")

    def test_executed_at_is_provenance_not_an_ordering_key(self):
        """QA observed `executed_at` is required and never read -- newest-as-FAIL was admitted.

        With U6 refusing duplicates that is now correct BY DESIGN rather than by omission: no
        conflict can be expressed, so nothing resolves one. Pinned so a later change that starts
        reading it has to confront that it is re-introducing an ordering semantics.
        """
        newest_fail = [observation(result="PASS"),
                       dict(observation(result="FAIL"), executed_at="2099-01-01T00:00:00Z")]
        b = binding(scenarios=[scenario(crit="critical")], observations=newest_fail,
                    defects=[{"scenario_id": "UAT-SCN-001",
                              "defect_class": "IMPLEMENTATION_DEFECT", "statement": "x"}],
                    recommendation="RECOMMEND_ACCEPT")
        with self.assertRaisesRegex(gate.ValidationError, "more than one observation"):
            check(evidence(binding=b))

    def test_an_unresolvable_acceptance_basis_is_refused_by_the_SCHEMA(self):
        """UAT-I05: no approved basis -> NO UAT -- and the refusal is the SCHEMA's, not a control.

        This test first asserted only the fragment "prd_digest", which BOTH the schema error and
        a hand-written code control contained. The mutation battery showed the control SURVIVED
        neutering: the schema was doing the work and the test passed on the wrong raise. The
        control was unreachable and has been removed; this asserts the mechanism that actually
        fires, and names it, so the next reader does not re-add a code control the schema
        already makes dead.
        """
        with self.assertRaisesRegex(gate.ValidationError, r"missing.*prd_digest|prd_digest.*missing"):
            check(evidence(binding=binding(
                acceptance_basis={"prd_id": "PRD-1", "acceptance_criteria_digest": DIG})))
        d = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertIn("prd_digest",
                      d["properties"]["binding"]["properties"]["acceptance_basis"]["required"])

    def test_non_coverage_is_required_not_optional(self):
        """UAT-I12: absence from the matrix is a defect, so the field cannot simply be omitted."""
        d = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cov = d["properties"]["binding"]["properties"]["coverage"]
        self.assertIn("non_coverage", cov["required"])
        b = binding()
        del b["coverage"]["non_coverage"]
        with self.assertRaises(gate.ValidationError):
            check(evidence(binding=b))

    def test_no_second_gate_and_no_lifecycle_change(self):
        """UAT-I20: deterministic G10 semantics live in the canonical gate."""
        self.assertFalse((gate.ROOT / "scripts" / "badf_uat.py").exists())
        lifecycle = json.loads((gate.ROOT / "badf" / "lifecycle.json").read_text(encoding="utf-8"))
        g10 = next(g for g in lifecycle["gates"] if g["id"] == "G10")
        self.assertEqual(["uat", "release-packet", "operational-readiness", "go-no-go"],
                         g10["required_evidence"])
        self.assertIs(gate.EVIDENCE_RULES["uat"], gate.check_g10_uat_binding)


if __name__ == "__main__":
    unittest.main()
