import json
import unittest
from pathlib import Path

from scripts.badf_gate import check_schema


ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class DecisionGovernanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load("badf/decision-policy.json")
        cls.risk = load("badf/risk-appetite.json")
        cls.council = load("badf/council-registry.json")
        cls.ballot_schema = load("schemas/ballot.schema.json")
        cls.dossier_schema = load("schemas/decision-dossier.schema.json")
        cls.calibration_schema = load("schemas/calibration-ledger.schema.json")
        cls.doctrine = (ROOT / "docs/governance/DECISION_GOVERNANCE_BOARD_AUTHORITY.md").read_text(encoding="utf-8")
        cls.gate = (ROOT / "scripts/badf_gate.py").read_text(encoding="utf-8")

    def test_policy_documents_conform_to_their_schemas(self):
        check_schema("decision-policy", self.policy)
        check_schema("risk-appetite", self.risk)
        check_schema("council-registry", self.council)

    def test_v01_is_advisory_and_cannot_authorize_or_merge(self):
        for artifact in (self.policy, self.risk, self.council):
            self.assertEqual(artifact["authorization_mode"], "ADVISORY_ONLY")
            self.assertEqual(artifact["authority_source"], "badf/authority-matrix.json")
        self.assertFalse(self.policy["autonomous_merge_enabled"])
        self.assertFalse(self.council["grants_authority"])
        self.assertEqual(self.council["active_members"], 0)
        self.assertNotIn("BOARD_AUTHORIZED", self.policy["v0_1_dispositions"])
        auto = self.dossier_schema["properties"]["autonomous_merge"]["properties"]
        self.assertEqual(auto["eligible"]["const"], False)
        self.assertEqual(auto["policy_active"]["const"], False)
        self.assertEqual(auto["board_authorized"]["const"], False)

    def test_criteria_weights_are_unique_and_sum_to_one(self):
        criteria = self.policy["criteria"]
        ids = [item["id"] for item in criteria]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(sum(item["weight_bp"] for item in criteria), 10000)

    def test_support_thresholds_increase_with_impact_and_c3r_has_no_threshold(self):
        classes = self.policy["decision_classes"]
        self.assertLess(classes["C0"]["support_threshold_bp"], classes["C1"]["support_threshold_bp"])
        self.assertLess(classes["C1"]["support_threshold_bp"], classes["C2"]["support_threshold_bp"])
        self.assertLess(classes["C2"]["support_threshold_bp"], classes["C3A"]["support_threshold_bp"])
        self.assertIsNone(classes["C3R"]["support_threshold_bp"])
        self.assertTrue(classes["C3R"]["human_ratification_required"])
        self.assertEqual(self.policy["c3_routing"]["ambiguity_routes_to"], "C3R")

    def test_weighting_is_integer_deterministic_and_not_self_confidence(self):
        expected = ["domain_relevance_bp", "calibration_bp", "evidence_coverage_bp", "freshness_bp", "independence_bp"]
        self.assertEqual(self.policy["weight_factors"], expected)
        forbidden = {"confidence", "model_brand", "model_price", "seat_prestige"}
        self.assertTrue(forbidden.isdisjoint(self.policy["weight_factors"]))
        self.assertEqual(self.policy["arithmetic"]["rounding"], "INTEGER_ROUND_HALF_UP")
        self.assertFalse(self.policy["arithmetic"]["floating_point_authoritative"])
        # Known vector: weights 2:1 over 7000bp and 4000bp yields exactly 6000bp.
        numerator = 2 * 7000 + 1 * 4000
        denominator = 3
        result = (2 * numerator + denominator) // (2 * denominator)
        self.assertEqual(result, 6000)
        self.assertEqual(self.policy["aggregation"]["criterion_support_formula"], "FLOOR((2 * SUM(raw_weight * probability_satisfy_bp) + SUM(raw_weight)) / (2 * SUM(raw_weight)))")

    def test_correlation_discount_is_fixed_monotonic_and_quorum_uses_clusters(self):
        table = self.policy["correlation_discount"]
        self.assertEqual([row["cluster_size"] for row in table], list(range(1, 9)))
        factors = [row["factor_bp"] for row in table]
        self.assertEqual(factors[0], 10000)
        self.assertEqual(factors, sorted(factors, reverse=True))
        self.assertGreater(self.policy["decision_classes"]["C2"]["minimum_independence_clusters"], 1)
        self.assertIn("model_family", self.council["independence_cluster_key"])
        self.assertEqual(self.council["conflicts"]["same_model_family"], "CORRELATED_NOT_INDEPENDENT")

    def test_chair_is_non_sovereign(self):
        chair = self.council["chair"]
        self.assertFalse(chair["voting"])
        self.assertEqual(chair["weight_bp"], 0)
        for forbidden in ("change_ballot", "waive_blocker", "change_threshold", "suppress_minority_risk", "invent_authority", "break_tie"):
            self.assertIn(forbidden, chair["may_not"])

    def test_hard_rules_precede_weights_and_are_non_compensable(self):
        rules = self.policy["hard_rules"]
        self.assertEqual(rules["evaluation_order"], "BEFORE_WEIGHTED_AGGREGATION")
        self.assertTrue(rules["non_compensable"])
        for required in ("no_verified_blocker", "no_unresolved_condition", "no_self_approval", "artifact_and_policy_digests_current", "independent_quorum_valid"):
            self.assertIn(required, rules["rules"])
        self.assertFalse(self.risk["performance_or_vote_may_waive_blocker"])

    def test_risk_is_dimensioned_and_reserved_risk_is_human_routed(self):
        ids = [row["id"] for row in self.risk["dimensions"]]
        self.assertIn("security", ids)
        self.assertIn("privacy_legal", ids)
        self.assertEqual(self.risk["risk_calculation"]["cross_dimension_aggregation"], "PROHIBITED")
        self.assertEqual(self.risk["risk_acceptance_authority"]["C3R"], "BST_COMPANY_PRINCIPAL")
        self.assertIn("authority_expansion", self.risk["reserved_risks"])
        self.assertIn("constitutional_or_authority_violation", self.risk["verified_blockers"])

    def test_ballot_schema_binds_identity_forecasts_evidence_and_falsifier(self):
        required = set(self.ballot_schema["required"])
        for field in ("input_digest", "artifact_binding", "member", "independence_cluster", "conflict_declaration", "option_assessments", "blocking_findings", "evidence_refs", "non_coverage", "falsification_condition", "calibration_domain", "conditions", "ballot_digest"):
            self.assertIn(field, required)
        member_required = set(self.ballot_schema["properties"]["member"]["required"])
        for field in self.council["runtime_identity_required"]:
            self.assertIn(field, member_required)

    def test_dossier_binds_policies_authority_and_exact_remote_tree(self):
        required = set(self.dossier_schema["required"])
        for field in ("artifact_binding", "policy_bindings", "evidence_manifest", "ballots", "hard_rule_result", "risk_result", "aggregation_result", "authority_envelope", "autonomous_merge", "expires_at", "dossier_digest"):
            self.assertIn(field, required)
        artifact = set(self.dossier_schema["properties"]["artifact_binding"]["required"])
        for field in ("target_base_sha", "source_head_sha", "source_tree_sha", "merge_base_sha", "expected_result_tree", "pr_number"):
            self.assertIn(field, artifact)
        bindings = set(self.dossier_schema["properties"]["policy_bindings"]["required"])
        self.assertEqual(bindings, {"decision_policy_digest", "risk_appetite_digest", "council_registry_digest", "authority_matrix_digest", "calibration_ledger_digest"})

    def test_calibration_ledger_is_hash_chained_and_has_no_authority_effect(self):
        self.assertEqual(self.calibration_schema["properties"]["authority_effect"]["const"], "NONE")
        event_required = set(self.calibration_schema["properties"]["events"]["items"]["required"])
        for field in ("forecast_recorded_at", "outcome_observed_at", "forecast_probability_bp", "observed_outcome", "brier_score_bp", "previous_event_hash", "event_hash", "outcome_evidence_digest"):
            self.assertIn(field, event_required)

    def test_activation_and_shadow_doctrine_is_explicit(self):
        self.assertEqual(self.policy["activation_ladder"], ["DESIGNED", "IMPLEMENTED", "VALIDATED", "SHADOWED", "RATIFIED", "ACTIVE"])
        for invariant in ("MAJORITY != AUTHORITY", "COUNCIL_RECOMMENDATION != EXECUTION_PERMISSION", "MODEL_COUNT != INDEPENDENCE", "CHAIR IS NON-SOVEREIGN", "C3R ALWAYS REQUIRES HUMAN PRINCIPAL"):
            self.assertIn(invariant, self.doctrine)
        for case in ("BADF-DEC-0003", "BADF-DEC-0007", "PR #208", "Issue #211", "#261", "#289"):
            self.assertIn(case, self.doctrine)
        self.assertIn("zero false authorizations", self.doctrine)
        self.assertIn("outcome leakage", self.doctrine)

    def test_every_new_control_surface_is_required_and_integrity_locked(self):
        required_files = [
            "docs/governance/DECISION_GOVERNANCE_BOARD_AUTHORITY.md",
            "badf/decision-policy.json", "badf/risk-appetite.json", "badf/council-registry.json",
            "schemas/decision-policy.schema.json", "schemas/risk-appetite.schema.json", "schemas/council-registry.schema.json",
            "schemas/ballot.schema.json", "schemas/decision-dossier.schema.json", "schemas/calibration-ledger.schema.json",
        ]
        for path in required_files:
            self.assertIn(f'"{path}"', self.gate)
        for path in ("badf/decision-policy.json", "badf/risk-appetite.json", "badf/council-registry.json"):
            self.assertGreaterEqual(self.gate.count(f'"{path}"'), 2)


if __name__ == "__main__":
    unittest.main()
