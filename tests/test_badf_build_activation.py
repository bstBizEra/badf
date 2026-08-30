"""BLD-E: badf-build admitted SHADOWED -> ACTIVE by registry status flip only (WP-2026-0104, #203).

Pins what activation must and must not change: the root is ACTIVE with the frozen digest; the
family still holds no tools and grants no authority (BUILD != INTEGRATION); the seven controls and
the typed producer are untouched; the doctrine records the operator authorization, the four landing
SHAs and -- verbatim -- the shadow's non-coverage. Failing-first: every test here was red before the flip.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

DOCTRINE = gate.ROOT / "docs/governance/GITHUB_CONTROL_PLANE.md"


def registry():
    r = json.loads((gate.ROOT / "badf/skill-registry.json").read_text(encoding="utf-8"))
    return {s["name"]: s for s in r["skills"]}


class ActivationTests(unittest.TestCase):
    def test_root_is_active_with_the_frozen_digest(self):
        g = registry()["badf-build"]
        self.assertEqual(g["status"], "ACTIVE")
        self.assertEqual(g["digest"], "sha256:" + hashlib.sha256((gate.ROOT / g["source"]).read_bytes()).hexdigest(), "activation must not touch SKILL.md")
        self.assertEqual(g["digest"], "sha256:6cc3266ecde8bf6ed14fc3b5ae3b1de38a42154242d9b7517ca6f0cdb38bf0f3")

    def test_activation_grants_no_authority(self):
        g = registry()["badf-build"]
        self.assertEqual(g["allowed_tools"], []); self.assertEqual(g["risk_class"], "C1")
        self.assertFalse((gate.ROOT / "scripts/badf_build.py").exists())
        text = (gate.ROOT / "skills/badf-build/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("BUILD ≠ INTEGRATION", text); self.assertIn("BLD-I17", text); self.assertIn("BLD-I18", text)

    def test_controls_and_producer_are_untouched_by_the_flip(self):
        src = (gate.ROOT / "scripts/badf_gate.py").read_text(encoding="utf-8")
        for token in ("_require_authorized_demand", "_check_build_budget_and_stop", "_check_delegations", "BLD-I04 / C3", "BLD-I07 / BLD-I08 / C4", "BLD-I09 / C5", "check_g07_binding", "verify_build_ledger"):
            self.assertIn(token, src, token)
        self.assertEqual(len([t for t in ("source-change", "build", "unit-test", "documentation") if (gate.ROOT / "schemas" / f"{t}.schema.json").is_file()]), 4)

    def test_admission_doctrine_cites_authorization_landings_and_non_coverage(self):
        text = DOCTRINE.read_text(encoding="utf-8")
        start = text.find("## badf-build → ACTIVE"); self.assertGreater(start, 0, "no BLD-E admission section")
        end = text.find("\n## ", start + 1); section = text[start:end if end > 0 else None]
        for token in ("#203", "#188", "5469168780", "cf431fa", "6814a24", "8f3d805", "07c23f7", "C3", "C4", "C6", "C7", "scratch", "no build controller",
                      "allowed_tools: []", "BUILD ≠ INTEGRATION", "BADF-MAIN-001", "does not erase"):
            self.assertIn(token, section, token)


if __name__ == "__main__":
    unittest.main()
