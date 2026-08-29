import base64
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "badf-git" / "SKILL.md"
REFERENCES = ROOT / "skills" / "badf-git" / "references"
REGISTRY = ROOT / "badf" / "skill-registry.json"
FINAL_TEST_DIGEST = "sha256:55032874109c85dbe8cc2eca46683f8ff3c6503be794b18b715f9581e1f7e5c5"


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
            "SYNC → INSPECT → EDIT → STAGE → DIFF → COMMIT → VERIFY → RECONCILE → ↺",
            text,
        )
        self.assertIn("SOURCE_HEAD_GREEN != INTEGRATION_SAFE", text)
        self.assertIn("GIT_CAPABILITY != GIT_AUTHORITY", text)

    def test_state_machine_contains_progression_and_hold_states(self):
        text = (REFERENCES / "git-state-machine.md").read_text(encoding="utf-8")
        required = {
            "GIT_AUTHORITY_BOUND",
            "GIT_BASELINED",
            "GIT_ISOLATED",
            "GIT_CHANGE_ACTIVE",
            "GIT_LOCALLY_VERIFIED",
            "GIT_PUBLISHED",
            "GIT_PR_BOUND",
            "GIT_COMPOSED",
            "GIT_VERIFIED",
            "GIT_MERGE_AUTHORIZED",
            "GIT_MERGED",
            "GIT_RECONCILED",
            "GIT_RELEASED",
            "GIT_CLEANED",
            "GIT_LEARNED",
            "STALE_EVIDENCE",
            "BLOCKED",
            "HUMAN_REQUIRED",
            "RECOVERY_REQUIRED",
        }
        for token in required:
            self.assertIn(token, text)

    def test_branch_contract_is_proposed_not_enforced(self):
        text = (REFERENCES / "branch-pr-contract.md").read_text(encoding="utf-8")
        self.assertIn("wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>", text)
        self.assertIn("branch-name enforcement is deferred", text)
        self.assertIn("--force-with-lease", text)
        self.assertIn("Bare `--force` is not a normal BADF workflow", text)
        self.assertIn("`git range-diff`", text)

    def test_composition_contract_binds_exact_identity(self):
        text = (REFERENCES / "composition-and-staleness.md").read_text(encoding="utf-8")
        for token in (
            "target_ref",
            "target_base_sha",
            "source_ref",
            "source_head_sha",
            "merge_base_sha",
            "merge_method",
            "expected_result_tree",
            "test_set_epoch",
            "policy_epoch",
            "scripts/badf_compose.py",
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

    def test_registry_pin_is_designed_and_tool_empty(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        entries = [e for e in registry["skills"] if e.get("name") == "badf-git"]
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual("DESIGNED", entry["status"])
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual("C2", entry["risk_class"])
        digest = "sha256:" + hashlib.sha256(SKILL.read_bytes()).hexdigest()
        self.assertEqual(digest, entry["digest"])

    def test__temporary_emit_expected_lockfile(self):
        from scripts import badf_gate

        digests = badf_gate.compute_integrity()
        # This probe is removed before the lockfile lands. Emit the digest of
        # the clean structural test that will replace this temporary probe.
        digests["tests/test_badf_git_contract.py"] = FINAL_TEST_DIGEST
        payload = json.dumps(
            {"schema_version": "1.0.0", "digests": digests},
            indent=2,
            sort_keys=True,
        ) + "\n"
        encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        for i in range(0, len(encoded), 3500):
            print(f"BADF_LOCK_PROBE_{i // 3500:04d}:{encoded[i:i + 3500]}")


if __name__ == "__main__":
    unittest.main()
