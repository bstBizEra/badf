"""BADF-AET-A (WP-2026-0122, #236): guards on the frozen Agentic Engineer Team contract.

The contract is doctrine, and doctrine drifts silently (#216/#230: references pinned by
filename only; #235: a section attributed to the wrong work package for days). So the
freeze ships with content-anchor guards per the house REFERENCE_ANCHORS remedy: each
load-bearing declaration is asserted by distinctive anchors compared against NON-EMPTY
reference lists (the vacuity discriminator -- an assertion against an empty literal can
never fail), red-observed before the document existed, and gut-tested by mutation.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "14-agentic-engineer-team.md"

PLANES = ("deterministic control plane", "agentic execution plane",
          "independent assurance plane", "learning plane")
SEATS = ("coordinator", "builder controller", "independent reviewer",
         "verifier", "release/runtime observer", "librarian")
OUTCOME_CLASSES = ("COMMITTED", "PROVEN_ABSENT", "OUTCOME_UNKNOWN",
                   "COMPENSATED", "MANUAL_REMEDIATION_REQUIRED")
RUNGS = ("AET-B", "AET-C", "AET-D", "AET-E")
INVARIANT_IDS = tuple(f"AET-I{n:02d}" for n in range(1, 14))


class ContractAnchors(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DOC.is_file(), f"{DOC} does not exist -- the contract is not frozen")
        self.text = DOC.read_text(encoding="utf-8")
        self.lower = self.text.lower()

    def test_contract_has_substance(self):
        self.assertGreater(len(self.text), 6000, "a contract this short froze nothing")

    def test_four_planes_and_six_seats_declared(self):
        self.assertTrue(PLANES and SEATS)  # positive control: the reference lists are non-empty
        for p in PLANES:
            self.assertIn(p, self.lower, p)
        for s in SEATS:
            self.assertIn(s, self.lower, s)

    def test_non_expansion_invariant_chain_present(self):
        self.assertIn("AET-I01", self.text)
        self.assertIn("delegated_authority ⊆ work_package_authority ⊆ repository_policy", self.text)
        self.assertIn("project_team_capability ⊆ BADF_authorized_capability", self.text)

    def test_all_invariants_and_outcome_classes_present(self):
        self.assertTrue(INVARIANT_IDS and OUTCOME_CLASSES)
        for i in INVARIANT_IDS:
            self.assertIn(i, self.text, i)
        for oc in OUTCOME_CLASSES:
            self.assertIn(oc, self.text, oc)

    def test_authority_is_referenced_never_restated(self):
        """A copy of the reserved-role list would fork the law (#216-class drift, on the
        one document where drift grants authority). The contract points; it never holds.
        Matched on the NORMALISED payload, not any spelling: BADF-REV evaded the original
        quoted-key check with a prose restatement, and BADF-QA then evaded the payload
        check with prose/hyphen/Title/UPPER forms (#258 review) -- key -> payload ->
        payload-spelling is the same proxy class three times, so separators and casing
        are erased before matching. Zero false positives on the document today, measured
        by QA before this form was adopted.

        Threat model, stated so the boundary is a decision rather than a finding (REV,
        round 3): normalised matching covers RESTATEMENT DRIFT -- underscore, hyphen,
        prose, casing. It does not defend against deliberate evasion (homoglyphs,
        zero-width characters, unusual separators); that is not this control's threat
        model, and a test asserting on document text is the wrong layer for it."""
        self.assertIn("badf/authority-matrix.json", self.text)
        self.assertNotIn('"human_reserved_roles"', self.text,
                         "the contract must not carry a copy of the reserved-role list")
        import re
        norm = re.sub(r"[\s_\-]+", " ", self.text.lower())
        for role in ("human sponsor", "security authority", "release authority"):
            self.assertNotIn(role, norm,
                             f"the contract restates the reserved role {role!r}; a restated "
                             f"list is a forked law in any spelling, casing or separator")

    def test_channel_bound_authorization_invariant_present(self):
        """AET-I13, earned live: a coordinator's relay of an operator utterance is context
        for another seat's own ask, never a substitute for it (#236 D3 correction)."""
        self.assertIn("AET-I13", self.text)
        self.assertIn("binds the commitments of the session it was made in", self.text)

    def test_rungs_declared_and_gated(self):
        self.assertTrue(RUNGS)
        for r in RUNGS:
            self.assertIn(r, self.text, r)
        self.assertIn("P1-before-P3", self.text)
        self.assertIn("grants no additional authority", self.lower)


class NormativeRootReference(unittest.TestCase):
    def test_agents_md_points_at_the_contract(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/14-agentic-engineer-team.md", agents,
                      "an unreferenced normative doc is doctrine nobody loads")


if __name__ == "__main__":
    unittest.main()
