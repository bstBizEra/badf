"""Mandate section 3: Orchestrator != Authority. Intelligence != Authority.

The gate today knows an approver only as a string. It cannot tell a human
from an agent, so an agent that authors work can spawn a second agent to
approve it -- the 'super-agent' the mandate forbids -- and the gate accepts
the approval exactly as it would a human's. WP-2026-0010's own dossier
demonstrates it: 'security-auditor-agent' supplied a required-role approval
and the gate said APPROVED.

These tests were written to FAIL before the control existed. They assert:
  - every approval declares who KIND of principal supplied it
    (human | agent | service | controller -- the vocabulary already used by
    evidence.producer.type and session.actor.type; nothing new is minted);
  - roles the authority matrix marks human_reserved refuse any non-human
    approver, whatever the role label says;
  - an approval with no declared type is refused, not assumed human.
"""
import json
import unittest

import scripts.badf_gate as gate

C3_ROLES = ["human_sponsor", "security_authority", "release_authority", "service_owner"]


def approval(role, by, ptype="human", **over):
    a = {"role": role, "decision": "APPROVED", "by": by, "principal_type": ptype,
         "revision": "REV-1", "policy_epoch": "BADF-2026-08-25", "approved_at": "2026-08-25T01:00:00Z"}
    a.update(over)
    return a


def dossier(**over):
    d = {"schema_version": "1.0.0", "id": "DOS-WP-2026-0011-G09-v1", "work_package_id": "WP-2026-0011",
         "gate": "G09", "policy_epoch": "BADF-2026-08-25", "source_revision": "REV-1",
         "target": "bstBizEra/badf:main", "change_class": "C3", "evidence": [], "exceptions": [],
         "risks": [], "disposition": "PASS", "created_at": "2026-08-25T00:00:00Z",
         "author": "claude-opus-5", "author_type": "agent",
         "approvals": [approval(r, f"human-{i}") for i, r in enumerate(C3_ROLES)]}
    d.update(over)
    return d


class PrincipalTypeTests(unittest.TestCase):
    def deny(self, pattern, **over):
        with self.assertRaisesRegex(gate.ValidationError, pattern):
            gate.validate_authority(dossier(**over))

    # --- the proven bypass: an agent satisfies a human-reserved role --------
    def test_agent_cannot_supply_human_sponsor_approval(self):
        apps = [approval(r, f"p-{i}") for i, r in enumerate(C3_ROLES)]
        apps[0]["principal_type"] = "agent"
        self.deny("human_sponsor is human-reserved", approvals=apps)

    def test_service_cannot_supply_human_sponsor_approval(self):
        apps = [approval(r, f"p-{i}") for i, r in enumerate(C3_ROLES)]
        apps[0]["principal_type"] = "service"
        self.deny("human-reserved", approvals=apps)

    # --- deny-unless-established: an untyped approver is not assumed human --
    def test_approval_without_principal_type_is_refused(self):
        apps = [approval(r, f"p-{i}") for i, r in enumerate(C3_ROLES)]
        del apps[1]["principal_type"]
        self.deny("missing required fields: principal_type", approvals=apps)

    def test_unknown_principal_type_is_refused(self):
        apps = [approval(r, f"p-{i}") for i, r in enumerate(C3_ROLES)]
        apps[2]["principal_type"] = "robot"
        self.deny("invalid principal_type", approvals=apps)

    def test_author_without_type_is_refused(self):
        d = dossier(); del d["author_type"]
        with self.assertRaisesRegex(gate.ValidationError, "author_type"):
            gate.validate_authority(d)

    # --- the mandate's exact scenario: agent authors, second agent approves --
    def test_agent_author_plus_agent_approver_on_reserved_role_is_refused(self):
        apps = [approval(r, f"agent-{i}", ptype="agent") for i, r in enumerate(C3_ROLES)]
        self.deny("human-reserved", author="orchestrator-agent", author_type="agent", approvals=apps)

    # --- positive controls -----------------------------------------------
    def test_human_approvals_on_reserved_roles_pass(self):
        gate.validate_authority(dossier())

    def test_agent_may_approve_a_non_reserved_role(self):
        """independent_reviewer is NOT human-reserved: an agent reviewer is legitimate."""
        d = dossier(change_class="C1",
                    approvals=[approval("engineering_owner", "human-1"),
                               approval("independent_reviewer", "review-agent", ptype="agent")])
        gate.validate_authority(d)

    def test_matrix_declares_which_roles_are_human_reserved(self):
        m = json.loads((gate.ROOT / gate.MATRIX).read_text())
        reserved = m.get("human_reserved_roles")
        self.assertIsInstance(reserved, list, "authority-matrix.json must declare human_reserved_roles")
        self.assertIn("human_sponsor", reserved)


if __name__ == "__main__":
    unittest.main()
