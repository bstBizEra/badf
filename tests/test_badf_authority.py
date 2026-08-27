"""Mutation tests for AUTHORITY_SATISFIED(change_class).

Every test below mutates one term of the invariant and asserts the gate DENIES.
A gate that only accepts well-formed input is not an authority control; these
are the negative controls that prove it bites. The two positive controls at the
end exist so a suite that denies everything cannot pass by accident.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.badf_gate as gate

EPOCH = "BADF-2026-08-25"
REV = "REV-1"
AUTHOR = "principal-author"
C3_ROLES = ["human_sponsor", "security_authority", "release_authority", "service_owner"]


def approval(role, by, **over):
    item = {
        "role": role, "decision": "APPROVED", "by": by,
        "revision": REV, "policy_epoch": EPOCH,
        "approved_at": "2026-08-25T01:00:00Z",
    }
    item.update(over)
    return item


def dossier(**over):
    base = {
        "schema_version": "1.0.0", "id": "DOS-WP-2026-0002-G09-v1",
        "work_package_id": "WP-2026-0002", "gate": "G09", "policy_epoch": EPOCH,
        "source_revision": REV, "target": "badf-repository-baseline",
        "change_class": "C3", "evidence": [], "exceptions": [], "risks": [],
        "disposition": "PASS", "created_at": "2026-08-25T00:00:00Z",
        "author": AUTHOR,
        "approvals": [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)],
    }
    base.update(over)
    return base


class AuthoritySatisfiedTests(unittest.TestCase):
    def deny(self, pattern, **over):
        with self.assertRaisesRegex(gate.ValidationError, pattern):
            gate.validate_authority(dossier(**over))

    # --- the seven required negative controls ---------------------------
    def test_zero_approvals_denies(self):
        self.deny("requires approvals from", approvals=[])

    def test_three_of_four_required_roles_denies(self):
        partial = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES[:3])]
        self.deny("requires approvals from: service_owner", approvals=partial)

    def test_one_principal_cannot_fill_two_required_roles(self):
        shared = [approval(r, "principal-same") for r in C3_ROLES]
        self.deny("fills 4 required roles", approvals=shared)

    def test_author_cannot_approve_own_work(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        items[0]["by"] = AUTHOR
        self.deny("approve-own-work is a reserved action", approvals=items)

    def test_approval_bound_to_a_previous_revision_denies(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        items[2]["revision"] = "REV-0"
        self.deny("bound to revision", approvals=items)

    def test_unknown_role_denies(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        items[1]["role"] = "supreme_authority"
        self.deny("unknown role", approvals=items)

    def test_malformed_approval_denies(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        del items[0]["by"]
        self.deny("missing required fields: by", approvals=items)
        self.deny("must be an object", approvals=["human_sponsor"])

    # --- deny-unless-established: UNKNOWN denies as FALSE ----------------
    def test_stale_policy_epoch_denies(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        items[3]["policy_epoch"] = "BADF-2026-01-01"
        self.deny("stale policy epoch", approvals=items)

    def test_approval_predating_the_dossier_denies(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        items[0]["approved_at"] = "2026-08-24T00:00:00Z"
        self.deny("predates the dossier", approvals=items)

    def test_absent_author_denies(self):
        self.deny("author is required", author="")

    def test_non_approved_decision_does_not_count_toward_quorum(self):
        items = [approval(r, f"principal-{i}") for i, r in enumerate(C3_ROLES)]
        items[1]["decision"] = "ABSTAIN"
        self.deny("requires approvals from: security_authority", approvals=items)

    # --- positive controls ----------------------------------------------
    def test_four_distinct_principals_satisfy_c3(self):
        gate.validate_authority(dossier())

    def test_c0_is_satisfied_by_its_single_required_role(self):
        gate.validate_authority(dossier(
            change_class="C0",
            approvals=[approval("reviewer", "principal-reviewer")]))


class AuthorityEndToEndTests(unittest.TestCase):
    """Subprocess-level: a unit test of the validator is necessary, not sufficient."""

    def run_gate(self, payload):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         dir=str(gate.ROOT / "examples")) as handle:
            json.dump(payload, handle)
            path = Path(handle.name)
        try:
            return subprocess.run(
                [sys.executable, "scripts/badf_gate.py", "dossier", str(path)],
                cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def test_cli_denies_a_passing_dossier_with_no_approvals(self):
        source = json.loads((gate.ROOT / "examples/gate-dossier.G00.json").read_text())
        source["approvals"] = []
        result = self.run_gate(source)
        self.assertNotEqual(result.returncode, 0, "empty approvals must not exit 0")
        self.assertIn("requires approvals from", result.stdout + result.stderr)

    def test_cli_denies_self_approval(self):
        source = json.loads((gate.ROOT / "examples/gate-dossier.G00.json").read_text())
        source["approvals"][0]["by"] = source["author"]
        result = self.run_gate(source)
        self.assertNotEqual(result.returncode, 0, "self-approval must not exit 0")
        self.assertIn("approve-own-work", result.stdout + result.stderr)

    def test_cli_accepts_the_shipped_example(self):
        result = self.run_gate(json.loads(
            (gate.ROOT / "examples/gate-dossier.G00.json").read_text()))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
