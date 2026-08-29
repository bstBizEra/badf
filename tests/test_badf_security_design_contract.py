"""badf-security-design contract freeze (BADF-WP-0078 / WP-SEC-A).

badf-security-design is the pre-implementation G05 security-DESIGN composition/router over the
security specialists (threat-model, security-requirements, privacy, abuse-case, api-security,
iam-security, supply-chain, ai-agent-security). It consumes the architecture + solution baselines,
models abuse, derives controls + security requirements, and NORMALIZES into the existing G05 design
artifacts. It is NOT a scanner, a second gate, a security authority, or a security-ASSURANCE
capability (that is a future badf-security-assurance at G08/G09). OWASP is ADAPT-as-methodology,
never adopt-as-authority. This WP freezes the contract only: SKILL.md + 14 references, registered
DESIGNED, with no runtime, no second validator, no schema, and no lifecycle change. These tests
guard that declarative surface.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-security-design" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-security-design" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"

REFS = {
    "routing.md", "g05-contract.md", "threat-model-contract.md", "security-requirements.md",
    "privacy-contract.md", "abuse-case-contract.md", "api-security-contract.md",
    "iam-security-contract.md", "supply-chain-contract.md", "ai-agent-security-contract.md",
    "normalization.md", "traceability.md", "acceptance.md", "external-methodology.md",
}


class BadfSecurityDesignContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        self.assertTrue(SKILL.is_file())
        self.assertEqual(REFS, {p.name for p in REFERENCES.glob("*.md")})
        # no second gate / runtime (SEC-I15): no standalone validator script...
        self.assertFalse((ROOT / "scripts" / "badf_security_design.py").exists())
        # ...and this skill authors no schema at contract-freeze. (The four G05 evidence schemas
        # -- threat-model / privacy-assessment / supply-chain-plan / security-approval -- pre-date
        # this skill and belong to the gate; security-design normalizes INTO them. A skill-specific
        # security-design/security-composition schema is a WP-SEC-B concern and absent here.)
        for schema in ("security-design.schema.json", "security-composition.schema.json"):
            self.assertFalse((ROOT / "schemas" / schema).exists(), schema)

    def test_root_states_all_invariants_and_the_workflow(self):
        text = SKILL.read_text(encoding="utf-8")
        for n in range(1, 16):
            self.assertIn(f"SEC-I{n:02d}", text)
        self.assertIn(
            "FRAME → INGEST → CLASSIFY → ROUTE → SPECIALIZE → RECONCILE → CHALLENGE → NORMALIZE → PACKAGE",
            text,
        )
        # both escalations (does not silently rewrite architecture or requirements)
        self.assertIn("ARCHITECTURE_CHANGE_REQUIRED", text)
        self.assertIn("REQUIREMENT_CHANGE_REQUIRED", text)
        # consume-not-rediscover boundaries with the two upstream spines
        self.assertIn("badf-architecture", text)
        self.assertIn("badf-solution-design", text)
        # design != assurance, and capability != authority, are stated
        self.assertRegex(text, r"[Dd]esign\s*[≠!=]+\s*assurance|Design ≠ assurance")
        self.assertIn("badf-security-assurance", text)

    def test_normalization_maps_specialists_to_g05_evidence(self):
        text = (REFERENCES / "normalization.md").read_text(encoding="utf-8")
        for artifact in ("threat-model", "privacy-assessment", "supply-chain-plan"):
            self.assertIn(artifact, text)
        # security-approval is the authority's, never authored by the skill (SEC-I13)
        self.assertIn("security-approval", text)
        self.assertIn("security_authority", text)
        self.assertRegex(text, r"NOT produced by the skill|never authored here")

    def test_routing_lists_specialists_as_reference_adapt(self):
        text = (REFERENCES / "routing.md").read_text(encoding="utf-8")
        self.assertIn("REFERENCE / ADAPT", text)
        for spec in ("threat-model", "privacy-analysis", "abuse-case-analysis",
                     "api-security-design", "iam-security-design", "supply-chain-design",
                     "ai-agent-security-design"):
            self.assertIn(spec, text)
        # assurance routes elsewhere, and the two spines are named, not recreated
        self.assertIn("badf-security-assurance", text)
        self.assertIn("badf-architecture", text)
        self.assertIn("badf-solution-design", text)

    def test_external_methodology_is_adapt_not_authority(self):
        text = (REFERENCES / "external-methodology.md").read_text(encoding="utf-8")
        self.assertIn("OWASP", text)
        self.assertIn("ADAPT", text)
        self.assertRegex(text, r"NOT\b.*adopt|does NOT adopt|not:.*BADF authority")
        # a scanner/agent verdict never becomes a gate pass
        self.assertRegex(text, r"never|must never")

    def test_no_lifecycle_change(self):
        lifecycle = json.loads((ROOT / "badf" / "lifecycle.json").read_text())
        gate_names = {g["id"]: g.get("name", "") for g in lifecycle["gates"]}
        # no new "security design" gate was added.
        self.assertNotIn("security design", " ".join(gate_names.values()).lower())
        g05 = next(g for g in lifecycle["gates"] if g["id"] == "G05")
        self.assertEqual(
            set(g05["required_evidence"]),
            {"threat-model", "privacy-assessment", "supply-chain-plan", "security-approval"},
        )
        self.assertEqual(g05.get("owner_role"), "security_authority")

    def test_registry_pin_is_designed_and_tool_empty(self):
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in reg["skills"] if e.get("name") == "badf-security-design"]
        self.assertEqual(1, len(entries))
        entry = entries[0]
        # the ladder can advance later; guard registration + empty tools + a real digest.
        self.assertIn(entry["status"], ("DESIGNED", "IMPLEMENTED", "VALIDATED", "SHADOWED", "APPROVED", "ACTIVE"))
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual("sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest(), entry["digest"])

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `DESIGNED`", text)


if __name__ == "__main__":
    unittest.main()
