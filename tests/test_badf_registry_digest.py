"""Registry digests are real and checked (BADF-WP-0032, Issue #52).

docs/07 says ACTIVE means a pinned digest in badf/skill-registry.json; the
field carried the placeholder GENERATED_AT_RELEASE from the start and the
gate never compared it to anything. `repo` now refuses any skill entry whose
digest is not sha256 of its source: placeholder, stale, malformed, or a
source that is gone. Each test injects its own defect into a backup-restored
registry and re-signs the lockfile, so only the digest check decides.
"""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

REGISTRY = gate.ROOT / "badf/skill-registry.json"
GUARDED = [REGISTRY, gate.ROOT / gate.LOCKFILE, gate.ROOT / "skills/badf-delivery/SKILL.md"]


class RegistryDigestTests(unittest.TestCase):
    def setUp(self):
        self.backup = tempfile.mkdtemp()
        for p in GUARDED:
            dst = Path(self.backup) / p.relative_to(gate.ROOT); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dst)

    def tearDown(self):
        for p in GUARDED:
            shutil.copy2(Path(self.backup) / p.relative_to(gate.ROOT), p)
        shutil.rmtree(self.backup, ignore_errors=True)

    def entry(self, name="badf-delivery", **fields):
        reg = json.loads(REGISTRY.read_text())
        e = next(x for x in reg["skills"] if x["name"] == name); e.update(fields)
        REGISTRY.write_text(json.dumps(reg, indent=2) + "\n")
        gate.write_lock(gate.ROOT, gate.INTEGRITY_PATHS)   # re-signed: only the digest check may refuse

    def refused(self, needle):
        with self.assertRaisesRegex(gate.ValidationError, needle):
            gate.validate_repo()

    def test_clean_registry_passes(self):
        gate.validate_repo()

    def test_every_shipped_entry_digest_is_the_sha256_of_its_source(self):
        for e in json.loads(REGISTRY.read_text())["skills"]:
            with self.subTest(skill=e["name"]):
                self.assertEqual(e["digest"], "sha256:" + hashlib.sha256((gate.ROOT / e["source"]).read_bytes()).hexdigest())

    def test_placeholder_digest_is_refused_naming_the_entry(self):
        self.entry(digest="GENERATED_AT_RELEASE")
        self.refused("badf-delivery.*digest")

    def test_stale_digest_after_an_edited_and_resigned_source_is_refused(self):
        src = gate.ROOT / "skills/badf-delivery/SKILL.md"; src.write_text(src.read_text() + "\n10. (edited without re-pinning)\n")
        gate.write_lock(gate.ROOT, gate.INTEGRITY_PATHS)
        self.refused("badf-delivery.*does not match")

    def test_malformed_digest_is_refused(self):
        self.entry(digest="md5:abc")
        self.refused("badf-delivery.*digest")

    def test_missing_source_is_refused(self):
        self.entry(source="skills/badf-delivery/GONE.md")
        self.refused("badf-delivery.*source")


if __name__ == "__main__":
    unittest.main()
