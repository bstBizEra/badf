"""GOV-0121 / #279: the doctrine file's guarded sections are delimited, not inferred.

`docs/governance/GITHUB_CONTROL_PLANE.md` carries 104 `## ` headings, two of which are
load-bearing: 32 token assertions across `test_badf_git_activation.py` and
`test_badf_build_activation.py` are scoped to those two sections. Both slices used to end
at the next `## `, so inserting any heading inside a guarded section truncated it and the
failure surfaced as a missing *token* -- sending the editor to re-add prose already present.

These tests pin the three properties that make the sentinel remedy real rather than a
relocation of the same trap:

  1. the sentinels exist, exactly once each, after their own heading;
  2. an inserted `## ` no longer truncates -- with a control showing the OLD slice did;
  3. a DELETED sentinel RAISES and names the coupling -- it never degrades to
     "the rest of the file", which would be the identical silent failure one step over.

Failing-first: (2) and (3) were red against the pre-sentinel slice.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import badf_gate as gate  # noqa: E402
import _doctrine  # noqa: E402

DOCTRINE = gate.ROOT / "docs/governance/GITHUB_CONTROL_PLANE.md"
GUARDED = ("## badf-git → ACTIVE", "## badf-build → ACTIVE")
# one token from each guarded section, drawn from the live assertion lists
SENTRY_TOKEN = {"## badf-git → ACTIVE": "GIT_CAPABILITY != GIT_AUTHORITY",
                "## badf-build → ACTIVE": "BUILD ≠ INTEGRATION"}


def _old_slice(text, heading):
    """The pre-#279 slice, kept as a control so the fix is demonstrable, not asserted."""
    start = text.find(heading)
    end = text.find("\n## ", start + 1)
    return text[start:end if end > 0 else None]


class DoctrineSentinelTests(unittest.TestCase):
    def setUp(self):
        self.text = DOCTRINE.read_text(encoding="utf-8")

    def test_admission_sections_carry_explicit_end_markers(self):
        for heading in GUARDED:
            marker = _doctrine.end_marker(heading)
            self.assertEqual(1, self.text.count(marker), f"{marker!r} must appear exactly once")
            self.assertGreater(self.text.find(marker), self.text.find(heading),
                               f"{marker!r} must FOLLOW the section it closes")
            self.assertIn(SENTRY_TOKEN[heading], _doctrine.section(self.text, heading))

    def test_inserted_heading_does_not_truncate_the_section(self):
        """POSITIVE CONTROL: plant a `## ` inside each guarded section."""
        for heading in GUARDED:
            token = SENTRY_TOKEN[heading]
            at = self.text.find(token)
            self.assertGreater(at, 0, token)
            # insert a heading BEFORE the sentry token but INSIDE the section
            line = self.text.rfind("\n", 0, at) + 1
            mutated = self.text[:line] + "## An editor's new subsection\n\n" + self.text[line:]

            # the control: the old slice LOSES the token -- this is the defect, reproduced
            self.assertNotIn(token, _old_slice(mutated, heading),
                             "control failed: the old slice should truncate here, so this "
                             "test would prove nothing about the new one")
            # the fix: the sentinel-bounded slice still carries it
            self.assertIn(token, _doctrine.section(mutated, heading),
                          f"an inserted heading truncated {heading!r} despite the sentinel")

    def test_missing_end_marker_raises_and_names_the_coupling(self):
        """SARCHI's condition: a DELETED sentinel must raise, never widen the slice."""
        for heading in GUARDED:
            marker = _doctrine.end_marker(heading)
            mutated = self.text.replace(marker, "")
            with self.assertRaises(_doctrine.DoctrineSectionError) as ctx:
                _doctrine.section(mutated, heading)
            msg = str(ctx.exception)
            self.assertIn(marker, msg, "the failure must name the missing sentinel")
            self.assertIn("#279", msg, "the failure must cite the coupling's record")
            self.assertIn("scoped", msg, "the failure must say what depends on it")

    def test_duplicate_end_marker_raises(self):
        """Two sentinels are as ambiguous as none -- the slice must not pick one."""
        for heading in GUARDED:
            marker = _doctrine.end_marker(heading)
            with self.assertRaises(_doctrine.DoctrineSectionError):
                _doctrine.section(self.text + "\n" + marker + "\n", heading)

    def test_a_missing_sentinel_never_returns_the_rest_of_the_file(self):
        """The remedy must not reintroduce the defect it fixes, one step over."""
        for heading in GUARDED:
            mutated = self.text.replace(_doctrine.end_marker(heading), "")
            try:
                got = _doctrine.section(mutated, heading)
            except _doctrine.DoctrineSectionError:
                continue
            self.fail(f"{heading!r} degraded to a {len(got)}-char slice instead of raising")


if __name__ == "__main__":
    unittest.main()
