"""Adversarial fixtures for governance integrity.

The baseline shipped six tests, all of which fed the gate well-formed input.
A gate that has only ever seen passing input is untested as a gate: a green
run proves the happy path and says nothing about whether refusal works.

Every test here mutates the tree into a state the framework declares
prohibited and asserts the gate REFUSES. The positive controls at the end
exist so a validator that refused everything could not pass this suite.

Each test restores the tree in tearDown; a failure mid-test must not leave a
tampered registry behind.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import scripts.badf_gate as gate

GUARDED = [Path(p) for p in gate.INTEGRITY_PATHS] + [Path(gate.LOCKFILE)]


class IntegrityRefusalTests(unittest.TestCase):
    def setUp(self):
        self.backup = tempfile.mkdtemp()
        for rel in GUARDED:
            src = gate.ROOT / rel
            if src.is_file():
                dst = Path(self.backup) / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def tearDown(self):
        for rel in GUARDED:
            saved = Path(self.backup) / rel
            if saved.is_file():
                shutil.copy2(saved, gate.ROOT / rel)
        shutil.rmtree(self.backup, ignore_errors=True)

    def flip(self, rel, key, value):
        path = gate.ROOT / rel
        data = json.loads(path.read_text())
        data[key] = value
        path.write_text(json.dumps(data, indent=2))

    # --- the measured bypass: policy weakened, gate previously said PASS ----
    def test_mcp_default_policy_flipped_to_allow_is_refused(self):
        self.flip("badf/mcp-registry.json", "default_policy", "allow")
        with self.assertRaisesRegex(gate.ValidationError, "integrity drift"):
            gate.validate_repo()

    def test_tool_default_policy_flipped_is_refused(self):
        self.flip("badf/tool-registry.json", "default_policy", "allow-mutation")
        with self.assertRaisesRegex(gate.ValidationError, "integrity drift"):
            gate.validate_repo()

    def test_skill_default_policy_flipped_is_refused(self):
        self.flip("badf/skill-registry.json", "default_policy", "allow")
        with self.assertRaisesRegex(gate.ValidationError, "integrity drift"):
            gate.validate_repo()

    def test_authority_matrix_required_roles_weakened_is_refused(self):
        path = gate.ROOT / "badf/authority-matrix.json"
        data = json.loads(path.read_text())
        data["change_classes"]["C3"]["required_roles"] = []
        path.write_text(json.dumps(data, indent=2))
        with self.assertRaisesRegex(gate.ValidationError, "integrity drift"):
            gate.validate_repo()

    def test_reserved_action_removed_is_refused(self):
        path = gate.ROOT / "badf/authority-matrix.json"
        data = json.loads(path.read_text())
        data["reserved_actions"] = [a for a in data["reserved_actions"]
                                    if a != "approve-own-work"]
        path.write_text(json.dumps(data, indent=2))
        with self.assertRaisesRegex(gate.ValidationError, "integrity drift"):
            gate.validate_repo()

    def test_agents_md_edited_out_of_band_is_refused(self):
        p = gate.ROOT / "AGENTS.md"
        p.write_text(p.read_text() + "\n<!-- silent edit -->\n")
        with self.assertRaisesRegex(gate.ValidationError, "integrity drift"):
            gate.validate_repo()

    # --- the lockfile itself is not a soft target -------------------------
    def test_absent_lockfile_is_refused_not_skipped(self):
        (gate.ROOT / gate.LOCKFILE).unlink()
        with self.assertRaisesRegex(gate.ValidationError, "absent"):
            gate.validate_repo()

    def test_lockfile_without_digests_is_refused(self):
        (gate.ROOT / gate.LOCKFILE).write_text('{"schema_version": "1.0.0"}')
        with self.assertRaisesRegex(gate.ValidationError, "no digests"):
            gate.validate_repo()

    def test_guarded_path_dropped_from_lockfile_is_refused(self):
        p = gate.ROOT / gate.LOCKFILE
        lock = json.loads(p.read_text())
        lock["digests"].pop("badf/authority-matrix.json")
        p.write_text(json.dumps(lock, indent=2))
        with self.assertRaisesRegex(gate.ValidationError, "absent from lockfile"):
            gate.validate_repo()

    def test_missing_governance_file_is_refused(self):
        (gate.ROOT / "badf/tool-registry.json").unlink()
        with self.assertRaises(gate.ValidationError):
            gate.validate_repo()

    # --- positive controls: the gate must still accept a legitimate tree ---
    def test_clean_tree_passes(self):
        gate.validate_repo()

    def test_deliberate_change_plus_resign_passes(self):
        """Re-signing is the sanctioned path, and it must actually work."""
        self.flip("badf/mcp-registry.json", "default_policy", "allow")
        gate.write_lockfile()
        gate.validate_repo()

    def test_cli_exits_nonzero_on_drift(self):
        """Subprocess level: a unit test of the validator is not sufficient."""
        self.flip("badf/mcp-registry.json", "default_policy", "allow")
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"],
                           cwd=str(gate.ROOT), capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("integrity drift", r.stdout + r.stderr)

    def test_cli_exits_zero_on_clean_tree(self):
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "repo"],
                           cwd=str(gate.ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
