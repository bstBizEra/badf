"""badf-git declarative contract tests.

GIT-A froze the declarative contract, GIT-B froze/enforced one Work-Package
identity across branch/title/trailer, and GIT-A2 replaces local-worktree
isolation with GitHub Remote Workspace. The skill remains a router/constraint
layer, not Git authority, merge bot, release authority or a second gate.
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
            "OBSERVE → READ → PATCH → BUILD TREE → CREATE COMMIT → ADVANCE REF → VERIFY → RECONCILE → ↺",
            text,
        )
        for token in (
            "SOURCE_HEAD_GREEN != INTEGRATION_SAFE",
            "GIT_CAPABILITY != GIT_AUTHORITY",
            "GITHUB_REMOTE_WORKSPACE != NATIVE_GIT_WORKTREE",
            "REUSED_RESOLUTION != VERIFIED_RESOLUTION",
            "MERGED != RELEASED",
        ):
            self.assertIn(token, text)

    def test_state_machine_contains_progression_and_hold_states(self):
        text = (REFERENCES / "git-state-machine.md").read_text(encoding="utf-8")
        required = {
            "GIT_AUTHORITY_BOUND", "GIT_BASELINED", "GIT_ISOLATED", "GIT_CHANGE_ACTIVE",
            "GIT_SOURCE_VERIFIED", "GIT_PUBLISHED", "GIT_PR_BOUND", "GIT_COMPOSED",
            "GIT_VERIFIED", "GIT_MERGE_AUTHORIZED", "GIT_MERGED", "GIT_RECONCILED",
            "GIT_RELEASED", "GIT_CLEANED", "GIT_LEARNED",
            "STALE_EVIDENCE", "BLOCKED", "HUMAN_REQUIRED", "OUTCOME_UNKNOWN", "RECOVERY_REQUIRED",
        }
        for token in required:
            self.assertIn(token, text)

    def test_branch_contract_preserves_git_b_identity_and_adds_remote_workspace(self):
        text = (REFERENCES / "branch-pr-contract.md").read_text(encoding="utf-8")
        self.assertIn("wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>", text)
        self.assertIn("WP-2026-0070", text)
        self.assertNotIn("branch-name enforcement is deferred", text)
        self.assertIn("github_remote_workspace", text)
        for token in ("target_base_sha", "source_head_sha", "source_head_tree", "pr_number"):
            self.assertIn(token, text)
        self.assertIn("expected prior remote SHA", text)
        self.assertIn("--force-with-lease", text)
        self.assertIn("Bare `--force` is not a normal BADF workflow", text)
        self.assertIn("`git range-diff`", text)

    def test_remote_workspace_replaces_local_worktree_isolation(self):
        root = SKILL.read_text(encoding="utf-8")
        evidence = (REFERENCES / "evidence-contract.md").read_text(encoding="utf-8")
        self.assertIn("GitHub Remote Workspace", root)
        self.assertNotIn("worktree_path:", evidence)
        self.assertNotIn("index_state:", evidence)
        for path in [SKILL, *sorted(REFERENCES.glob("*.md"))]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("git worktree add", text, path.name)
            self.assertNotIn("git worktree remove", text, path.name)
            self.assertNotIn("linked worktree", text.lower(), path.name)

    def test_operation_matrix_is_remote_first(self):
        text = (REFERENCES / "operation-authority-matrix.md").read_text(encoding="utf-8")
        for token in ("GIT-O0", "GIT-O1", "GIT-O2", "GIT-O3", "GIT-O4", "GIT-O5"):
            self.assertIn(token, text)
        for token in ("Remote Observe", "Remote Workspace Mutation", "create branch", "create a blob/tree/commit", "non-force"):
            self.assertIn(token, text)

    def test_composition_contract_binds_exact_identity(self):
        text = (REFERENCES / "composition-and-staleness.md").read_text(encoding="utf-8")
        for token in (
            "target_ref", "target_base_sha", "source_ref", "source_head_sha",
            "merge_base_sha", "merge_method", "expected_result_tree",
            "test_set_epoch", "policy_epoch", "scripts/badf_compose.py",
        ):
            self.assertIn(token, text)

    def test_remote_recovery_and_release_do_not_rewrite_shared_identity(self):
        recovery = (REFERENCES / "recovery-contract.md").read_text(encoding="utf-8")
        release = (REFERENCES / "release-versioning.md").read_text(encoding="utf-8")
        self.assertIn("git revert", recovery)
        self.assertIn("recovery/<WP>-<slug>", recovery)
        self.assertIn("Local `git reflog` is not a required BADF recovery mechanism", recovery)
        self.assertIn("BADF-BASELINE-X.Y.Z", release)
        self.assertIn("vX.Y.Z", release)
        self.assertIn("commit prefixes", release)

    def test_registry_pin_is_designed_tool_empty_and_v02(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in registry["skills"] if e.get("name") == "badf-git"]
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual("DESIGNED", entry["status"])
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual("0.2.0", entry["version"])
        digest = "sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest()
        self.assertEqual(digest, entry["digest"])

    def test_skill_points_to_registry_not_a_hardcoded_status(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("badf/skill-registry.json", text)
        self.assertNotIn("Status: `DESIGNED`", text)


if __name__ == "__main__":
    unittest.main()
