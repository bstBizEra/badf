"""GIT-J: badf-git admitted DESIGNED -> ACTIVE by registry status flip only (WP-2026-0087, #169).

Pins what activation must and must not change: the root is ACTIVE with the frozen digest; the
family still holds no tools and grants no authority; the six subskills stay IMPLEMENTED; the
doctrine records the operator authorization, the evidence SHA and the non-coverage ACTIVE does
not erase. Failing-first: every test here was red before the flip landed.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import badf_gate as gate  # noqa: E402
import _doctrine  # noqa: E402

FREEZE_DIGEST = "sha256:17ea1e412a1c5b35cf87b66797a82872cb2e414cb26be573a8f5ee66fba61778"
SUBSKILLS = ("repository-state", "commit-integrity", "composition-verification",
             "pull-request-integration", "git-recovery", "release-versioning")
DOCTRINE = gate.ROOT / "docs/governance/GITHUB_CONTROL_PLANE.md"


def registry():
    r = json.loads((gate.ROOT / "badf/skill-registry.json").read_text(encoding="utf-8"))
    sk = r.get("skills", r)
    return {s["name"]: s for s in sk} if isinstance(sk, list) else sk


class ActivationTests(unittest.TestCase):
    def test_root_is_active_with_the_frozen_digest(self):
        g = registry()["badf-git"]
        self.assertEqual(g["status"], "ACTIVE")
        self.assertEqual(g["digest"], FREEZE_DIGEST)
        actual = "sha256:" + hashlib.sha256((gate.ROOT / g["source"]).read_bytes()).hexdigest()
        self.assertEqual(actual, FREEZE_DIGEST, "activation must not touch SKILL.md")

    def test_activation_grants_no_authority(self):
        g = registry()["badf-git"]
        self.assertEqual(g["status"], "ACTIVE")
        self.assertEqual(g["allowed_tools"], [])
        self.assertEqual(g["risk_class"], "C1")
        self.assertFalse((gate.ROOT / "scripts/badf_git.py").exists())
        self.assertFalse((gate.ROOT / "schemas/git.schema.json").exists())

    def test_subskills_stay_implemented(self):
        by = registry()
        self.assertEqual(by["badf-git"]["status"], "ACTIVE")
        for name in SUBSKILLS:
            self.assertEqual(by[name]["status"], "IMPLEMENTED", name)
            self.assertEqual(by[name]["allowed_tools"], [], name)

    def test_admission_doctrine_cites_authorization_and_non_coverage(self):
        text = DOCTRINE.read_text(encoding="utf-8")
        section = _doctrine.section(text, "## badf-git → ACTIVE")
        for token in ("#169", "5467417478", "78eab75", "17ea1e41", "allowed_tools: []",
                      "GIT_CAPABILITY != GIT_AUTHORITY", "BADF-MAIN-001", "STALE_EVIDENCE", "synthetic",
                      "dirty state", "signed tag", "#160", "605f97f", "re-shadow", "IMPLEMENTED"):
            self.assertIn(token, section, token)


if __name__ == "__main__":
    unittest.main()
