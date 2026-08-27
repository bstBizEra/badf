import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.badf_gate as gate


class BADFGateTests(unittest.TestCase):
    def test_repository_contract(self):
        gate.validate_repo()

    def test_example_dossier(self):
        gate.validate_dossier(gate.ROOT / "examples/gate-dossier.G00.json")

    def test_passing_dossier_fails_closed_when_required_evidence_missing(self):
        source = json.loads((gate.ROOT / "examples/gate-dossier.G00.json").read_text())
        # Drop a REQUIRED evidence type by name, not by position. Dropping [-1]
        # coupled this test to the last index happening to be required; an
        # appended optional item would have silently broken it (QA finding).
        source["evidence"] = [e for e in source["evidence"] if e["type"] != "authority"]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(source, handle)
            path = Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.ValidationError, "missing evidence"):
                gate.validate_dossier(path)
        finally:
            path.unlink()

    def test_digest_mismatch_is_rejected(self):
        dossier = json.loads((gate.ROOT / "examples/gate-dossier.G00.json").read_text())
        evidence_path = gate.ROOT / dossier["evidence"][0]["path"]
        evidence = json.loads(evidence_path.read_text())
        evidence["digest"] = "sha256:" + "0" * 64
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, dir=gate.ROOT) as handle:
            json.dump(evidence, handle)
            replacement = Path(handle.name)
        dossier["evidence"][0]["path"] = replacement.relative_to(gate.ROOT).as_posix()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(dossier, handle)
            dossier_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.ValidationError, "digest mismatch"):
                gate.validate_dossier(dossier_path)
        finally:
            replacement.unlink()
            dossier_path.unlink()

    def test_path_escape_is_rejected(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt") as handle:
            with self.assertRaisesRegex(gate.ValidationError, "escapes repository"):
                gate.safe_repo_path(handle.name, "artifact")

    def test_malformed_evidence_index_is_rejected(self):
        dossier = json.loads((gate.ROOT / "examples/gate-dossier.G00.json").read_text())
        dossier["evidence"][0] = {"path": "examples/evidence/G00/authority.json", "note": "missing type"}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(dossier, handle)
            dossier_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.ValidationError, "require type and path"):
                gate.validate_dossier(dossier_path)
        finally:
            dossier_path.unlink()


if __name__ == "__main__":
    unittest.main()
