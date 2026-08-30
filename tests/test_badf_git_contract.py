"""badf-git contract freeze (BADF-WP-0066; salvage of the superseded PR #122).

badf-git is the declarative Git contract for BADF delivery work -- a router and
constraint layer, not a Git authority, merge bot, release authority, or second gate.
This WP freezes the contract only: SKILL.md + eight reference contracts, registered
DESIGNED, with no mutation script (scripts/badf_git.py) and no Git authority. These
tests guard that declarative surface (the salvage kept #122's contract checks and
dropped its temporary lockfile-probe scaffolding).
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-git" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-git" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"


class BadfGitContractTests(unittest.TestCase):
    def test_contract_surface_is_declarative_only(self):
        expected = {
            "git-cycle.md",
            "git-state-machine.md",
            "branch-pr-contract.md",
            "operation-authority-matrix.md",
            "composition-and-staleness.md",
            "recovery-contract.md",
            "release-versioning.md",
            "evidence-contract.md",
        }
        self.assertTrue(SKILL.is_file())
        self.assertEqual(expected, {p.name for p in REFERENCES.glob("*.md")})
        # no mutation engine and no second gate -- badf_gate.py stays the sole authority.
        self.assertFalse((ROOT / "scripts" / "badf_git.py").exists())
        self.assertFalse((ROOT / "schemas" / "git.schema.json").exists())

    def test_root_contract_freezes_all_invariants_and_cycles(self):
        text = SKILL.read_text(encoding="utf-8")
        for n in range(1, 13):
            self.assertIn(f"GIT-I{n:02d}", text)
        self.assertIn(
            "AUTHORITY → BASELINE → ISOLATE → BUILD → VERIFY → PR → COMPOSE → CHALLENGE → AUTHORIZE → SQUASH → RECONCILE → RELEASE → CLEAN → LEARN",
            text,
        )
        self.assertIn(
            "SYNC → INSPECT → EDIT → STAGE → DIFF → COMMIT → VERIFY → RECONCILE → ↺",
            text,
        )
        self.assertIn("SOURCE_HEAD_GREEN != INTEGRATION_SAFE", text)
        self.assertIn("GIT_CAPABILITY != GIT_AUTHORITY", text)

    def test_state_machine_contains_progression_and_hold_states(self):
        text = (REFERENCES / "git-state-machine.md").read_text(encoding="utf-8")
        required = {
            "GIT_AUTHORITY_BOUND", "GIT_BASELINED", "GIT_ISOLATED", "GIT_CHANGE_ACTIVE",
            "GIT_LOCALLY_VERIFIED", "GIT_PUBLISHED", "GIT_PR_BOUND", "GIT_COMPOSED",
            "GIT_VERIFIED", "GIT_MERGE_AUTHORIZED", "GIT_MERGED", "GIT_RECONCILED",
            "GIT_RELEASED", "GIT_CLEANED", "GIT_LEARNED",
            "STALE_EVIDENCE", "BLOCKED", "HUMAN_REQUIRED", "RECOVERY_REQUIRED",
        }
        for token in required:
            self.assertIn(token, text)

    def test_branch_contract_is_frozen_and_enforced_from_git_b(self):
        text = (REFERENCES / "branch-pr-contract.md").read_text(encoding="utf-8")
        self.assertIn("wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>", text)
        # BADF-WP-0070 (GIT-B) froze the machine id and made the branch form live;
        # the deferral wording GIT-A carried is retired with it.
        self.assertNotIn("branch-name enforcement is deferred", text)
        self.assertIn("WP-2026-0070", text)
        self.assertIn("--force-with-lease", text)
        self.assertIn("Bare `--force` is not a normal BADF workflow", text)
        self.assertIn("`git range-diff`", text)

    def test_composition_contract_binds_exact_identity(self):
        text = (REFERENCES / "composition-and-staleness.md").read_text(encoding="utf-8")
        for token in (
            "target_ref", "target_base_sha", "source_ref", "source_head_sha",
            "merge_base_sha", "merge_method", "expected_result_tree",
            "test_set_epoch", "policy_epoch", "scripts/badf_compose.py",
        ):
            self.assertIn(token, text)

    def test_recovery_and_release_do_not_rewrite_shared_identity(self):
        recovery = (REFERENCES / "recovery-contract.md").read_text(encoding="utf-8")
        release = (REFERENCES / "release-versioning.md").read_text(encoding="utf-8")
        self.assertIn("git revert", recovery)
        self.assertIn("git reflog", recovery)
        self.assertIn("rerere.autoUpdate = false", recovery)
        self.assertIn("BADF-BASELINE-X.Y.Z", release)
        self.assertIn("vX.Y.Z", release)
        self.assertIn("commit prefixes", release)

    def test_registry_pin_is_active_and_tool_empty(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in registry["skills"] if e.get("name") == "badf-git"]
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual("ACTIVE", entry["status"])
        self.assertEqual([], entry["allowed_tools"])
        digest = "sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest()
        self.assertEqual(digest, entry["digest"])

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        # the drift discipline: the SKILL.md must not hardcode a live lifecycle status.
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `DESIGNED`", text)


if __name__ == "__main__":
    unittest.main()
