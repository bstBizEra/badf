"""WP-2026-0156 (#355): fifteen skills vendored from Agent-Skills-for-Context-Engineering.

The vendoring makes four claims, and each one is a test here, not prose:

1. **Upstream bytes are unmodified.** Every file listed in a skill's `BADF-PROVENANCE.json`
   still hashes to the digest recorded at the pinned commit `58b55a8`. BADF changes live
   only in `BADF-OVERLAY.md`, so an edit to vendored text is drift.
2. **Each skill is registered at IMPLEMENTED, not routed.** This is an EXACT status pin,
   which the #218 guard (`test_badf_registry_status_pins`) requires of every registry
   entry. Promotion is a later work package with owner and security approval.
3. **Every skill rated ADOPT-WITH-NOTES carries its overlay; none rated ADOPT-AS-IS does.**
4. **The three EXCLUDED skills are not present**, either on disk or in the registry.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
REGISTRY = ROOT / "badf" / "skill-registry.json"
UPSTREAM_COMMIT = "58b55a8921758d13453b440704fb1b5b208c0b0e"

AS_IS = ("context-fundamentals", "context-degradation", "context-compression", "context-optimization",
         "project-development", "bdi-mental-states", "latent-briefing")
WITH_NOTES = ("advanced-evaluation", "evaluation", "filesystem-context", "harness-engineering",
              "long-horizon-prompting", "memory-systems", "multi-agent-patterns", "tool-design")
VENDORED = AS_IS + WITH_NOTES
EXCLUDED = ("hosted-agents", "self-improvement-loops", "self-managed-context")


def registry():
    return {e["name"]: e for e in json.loads(REGISTRY.read_text(encoding="utf-8"))["skills"]}


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class VendoredUpstreamIsUnmodified(unittest.TestCase):
    def test_every_upstream_file_matches_its_pinned_digest(self):
        checked = 0
        for name in VENDORED:
            prov = json.loads((SKILLS / name / "BADF-PROVENANCE.json").read_text(encoding="utf-8"))
            self.assertEqual(prov["upstream"]["commit"], UPSTREAM_COMMIT, name)
            self.assertIn("SKILL.md", prov["upstream_files"], name)
            for rel, digest in prov["upstream_files"].items():
                with self.subTest(skill=name, file=rel):
                    self.assertEqual(sha256(SKILLS / name / rel), digest, "vendored text edited; BADF changes go in BADF-OVERLAY.md")
                checked += 1
        self.assertGreaterEqual(checked, 15, f"only {checked} files checked; the scan is vacuous")

    def test_no_unlisted_file_was_added_beside_the_upstream_ones(self):
        own = {"BADF-PROVENANCE.json", "BADF-OVERLAY.md", "UPSTREAM-LICENSE"}
        for name in VENDORED:
            prov = json.loads((SKILLS / name / "BADF-PROVENANCE.json").read_text(encoding="utf-8"))
            on_disk = {str(p.relative_to(SKILLS / name)) for p in (SKILLS / name).rglob("*")
                       if p.is_file() and "__pycache__" not in p.parts}
            with self.subTest(skill=name):
                self.assertEqual(on_disk - own, set(prov["upstream_files"]))

    def test_the_digest_check_reads_the_bytes_it_names(self):
        """Positive control: a one-byte change to a vendored file must change its digest."""
        target = SKILLS / AS_IS[0] / "SKILL.md"
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.write_bytes(original + b"\n")
        prov = json.loads((SKILLS / AS_IS[0] / "BADF-PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertNotEqual(sha256(target), prov["upstream_files"]["SKILL.md"])


class VendoredRegistryStatus(unittest.TestCase):
    def test_each_vendored_skill_is_implemented_not_routed(self):
        # Two loops over the literal tuples, not one over VENDORED: the #218 scanner reads a
        # loop-driven pin only from a module-level literal sequence, and VENDORED is a sum.
        # Distinct loop variables: the scanner binds a loop variable to one sequence per function.
        by = registry()
        for plain in AS_IS:
            self.assertEqual(by[plain]["status"], "IMPLEMENTED")
        for noted in WITH_NOTES:
            self.assertEqual(by[noted]["status"], "IMPLEMENTED")

    def test_registry_source_is_the_vendored_skill_md(self):
        by = registry()
        for name in VENDORED:
            with self.subTest(skill=name):
                self.assertEqual(by[name]["source"], f"skills/{name}/SKILL.md")


class OverlaysAndExclusions(unittest.TestCase):
    def test_with_notes_skills_carry_an_overlay_and_as_is_skills_do_not(self):
        for name in WITH_NOTES:
            with self.subTest(skill=name):
                overlay = SKILLS / name / "BADF-OVERLAY.md"
                self.assertTrue(overlay.is_file())
                self.assertIn("takes precedence over the upstream", overlay.read_text(encoding="utf-8"))
        for name in AS_IS:
            with self.subTest(skill=name):
                self.assertFalse((SKILLS / name / "BADF-OVERLAY.md").exists())

    def test_excluded_skills_are_absent_from_disk_and_registry(self):
        by = registry()
        for name in EXCLUDED:
            with self.subTest(skill=name):
                self.assertFalse((SKILLS / name).exists())
                self.assertNotIn(name, by)

    def test_vendored_scripts_are_declared_not_executable(self):
        for name in VENDORED:
            prov = json.loads((SKILLS / name / "BADF-PROVENANCE.json").read_text(encoding="utf-8"))
            with self.subTest(skill=name):
                self.assertIs(prov["scripts_executable"], False)


if __name__ == "__main__":
    unittest.main()
