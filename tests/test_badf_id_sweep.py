"""GOV-0098 (#227, WP-2026-0118): the id-allocation sweep, mechanized.

The sweep failed five ways in 48 hours: three live collisions (the third-actor 0073
poisoning, the 0110/0097 double-claim bound only in an unlanded PR tree, the 0113/0100
claim published only in an issue body) and two seat-sweep defects (a title-blind sweep;
a `DEM-00xx` regex structurally unable to match ids >= 0100). Each shape is a fixture
here, red-observed before the tool existed. The tool is deterministic and offline: it
reads surface DUMP FILES (--from-dir), never the network -- CI has neither gh nor
credentials, and the doctrine section documents the one-liners that produce the dumps.

Four properties are structure, not convention (BADF-QA's handover, #227):
mentions are never claims (prose may CARRY a binding claim, so mentions are surfaced
for reading, never folded into next-free); sentinel exclusions are declared in the
output; a report is refused unless the sweep can see its known-present anchors (an
empty scan and a clean scan are otherwise identical); and every report ends by naming
the blind half -- unpushed worktrees and independent clones -- out loud.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "badf_id_sweep.py"

# Known-present-forever anchors on this repository's main (the positive control set).
ANCHORS = ("WP-2026-0110", "BADF-DEM-0097", "GOV-0097")


class _SweepFixture(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="badf-idsweep-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))
        # Default surfaces: anchors visible, one landed WP, nothing exotic.
        self.write("ledger.txt", "work/WP-2026-0110\nbadf/demands/BADF-DEM-0097.json\n")
        self.write("branches.txt", "0" * 40 + "\trefs/heads/main\n")
        self.write("pr_files.txt", "")
        self.write("bodies.txt", "GOV-0097 governs the double-claim episode.\n")

    def write(self, name, text):
        (self.dir / name).write_text(text, encoding="utf-8")

    def append(self, name, text):
        with open(self.dir / name, "a", encoding="utf-8") as f:
            f.write(text)

    def sweep(self):
        return subprocess.run([sys.executable, str(TOOL), "--from-dir", str(self.dir)],
                              capture_output=True, text=True, cwd=ROOT)


class ClaimSurfaceTests(_SweepFixture):
    def test_open_pr_file_claim_is_reported_claimed_with_its_source(self):
        """The 0110/0097 shape: an id bound only in a pushed-but-unlanded PR tree."""
        self.append("pr_files.txt", "work/WP-2026-0555/work-package.json\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        claimed = [l for l in r.stdout.splitlines() if "CLAIMED" in l and "WP-2026-0555" in l]
        self.assertTrue(claimed, r.stdout)
        self.assertIn("pr_files", claimed[0], "a claim must name its source surface")

    def test_branch_ref_claim_is_reported_claimed(self):
        self.append("branches.txt", "a" * 40 + "\trefs/heads/wp/WP-2026-0666-some-slug\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        claimed = [l for l in r.stdout.splitlines() if "CLAIMED" in l and "WP-2026-0666" in l]
        self.assertTrue(claimed, r.stdout)
        self.assertIn("branches", claimed[0])

    def test_ids_at_or_above_0100_are_matched(self):
        """BADF-QA's own sweep defect: a DEM-00xx regex cannot see DEM-0104."""
        self.append("ledger.txt", "badf/demands/BADF-DEM-0104.json\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any("CLAIMED" in l and "BADF-DEM-0104" in l for l in r.stdout.splitlines()), r.stdout)


class MentionSeparationTests(_SweepFixture):
    def test_body_mention_is_separated_and_does_not_advance_next_free(self):
        """The 0113/0100 shape: prose may CARRY a binding claim, so mentions are surfaced
        for human reading -- but a body string must never advance the high-water mark
        (BADF-QA's sweep read #199's sentinel DISCUSSION as high-water 0997)."""
        self.append("bodies.txt", "Planning notes discuss WP-2026-0777 hypothetically.\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        mention = [l for l in out.splitlines() if "MENTIONS" in l or "WP-2026-0777" in l]
        self.assertTrue(any("WP-2026-0777" in l for l in mention), out)
        self.assertFalse(any("CLAIMED" in l and "WP-2026-0777" in l for l in out.splitlines()), out)
        self.assertIn("NEXT FREE", out)
        self.assertIn("WP-2026-0111", out, "next-free computes from claim-shaped surfaces only")
        self.assertNotIn("WP-2026-0778", out)
        self.assertIn("READ BEFORE BINDING", out, "mentions carry the read-before-binding banner")


class SentinelTests(_SweepFixture):
    def test_sentinels_are_excluded_from_next_free_and_declared_in_output(self):
        self.append("ledger.txt", "work/WP-2026-0999\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SENTINELS EXCLUDED", r.stdout)
        self.assertIn("0999", r.stdout.split("SENTINELS EXCLUDED", 1)[1].splitlines()[0])
        self.assertIn("WP-2026-0111", r.stdout, "0999 is a fixture sentinel, not the high-water mark")
        self.assertNotIn("WP-2026-1000", r.stdout)
        self.assertNotIn("0900", r.stdout, "0900 is unverified (retracted), not a declared sentinel")


class PositiveControlTests(_SweepFixture):
    def test_report_is_refused_when_the_known_present_anchors_are_invisible(self):
        """An empty scan and a clean scan are identical in output; the sweep must prove
        it can SEE before any negative is trusted."""
        self.write("ledger.txt", "work/WP-2026-0555\n")  # anchors gone
        self.write("bodies.txt", "no anchors here\n")
        r = self.sweep()
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("POSITIVE CONTROL", r.stdout + r.stderr)
        self.assertNotIn("NEXT FREE", r.stdout, "no allocation advice from a scan that cannot see")


class NonCoverageTests(_SweepFixture):
    def test_every_report_ends_by_naming_the_blind_half(self):
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        tail = "\n".join(r.stdout.splitlines()[-4:])
        self.assertIn("NON-COVERAGE", tail)
        for word in ("worktree", "clone", "publish"):
            self.assertIn(word, tail.lower(), tail)


if __name__ == "__main__":
    unittest.main()
