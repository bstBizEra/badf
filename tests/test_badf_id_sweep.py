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
import os
import re
import shutil
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
        # An honest empty gather, DECLARED (#323): a 0-byte dump is refused because it is
        # indistinguishable from a gather that failed after `>` truncated the file.
        self.write("pr_files.txt", "# gathered OK: no open PRs\n")
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


class CommentSurfaceTests(_SweepFixture):
    """#282 (the remainder of #227): the session's actual claim surface is comments.
    Four allocation incidents shared this blind spot; the terminal demonstration was
    the fix WP's own allocation sweep reporting two comment-claimed ids as free."""

    def test_comment_id_at_or_above_next_free_warns_and_does_not_advance(self):
        self.write("comments.txt", "Claiming WP-2026-0800 for my next WP; ceiling printed.\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        warn = [l for l in r.stdout.splitlines() if "WARNING" in l and "WP-2026-0800" in l]
        self.assertTrue(warn, r.stdout)
        self.assertIn("binding", warn[0].lower(), "the warning names the claim mechanism, not just the id")
        self.assertIn("WP-2026-0111", r.stdout, "next-free computes from claim-shaped surfaces only")
        self.assertNotIn("WP-2026-0801", r.stdout)

    def test_absent_comments_surface_is_reported_not_omitted(self):
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        surf = [l for l in r.stdout.splitlines() if "SURFACES" in l or "NOT PROVIDED" in l]
        self.assertTrue(any("comments" in l and "NOT PROVIDED" in l for l in surf),
                        "an unread surface stated is a caution; omitted is a false clean\n" + r.stdout)

    def test_surfaces_header_reports_read_counts(self):
        self.write("comments.txt", "quiet thread\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SURFACES:", r.stdout, "the readability report has a named header, not loose rows")
        for name in ("ledger", "branches", "pr_files", "bodies", "comments"):
            self.assertTrue(any(name in l and "READ" in l for l in r.stdout.splitlines()),
                            f"surface {name} not reported as READ\n" + r.stdout)

    def test_actively_wrong_surface_shows_both_and_warns(self):
        """The field fixture: the ledger confidently reports one id while the binding
        claim for the same work lives in a comment the file surface contradicts."""
        self.append("ledger.txt", "badf/demands/BADF-DEM-0107.json\n")
        self.write("comments.txt", "WP-2026-0121 binds BADF-DEM-0112 (the file on disk is misnamed 0107).\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(any("CLAIMED" in l and "BADF-DEM-0107" in l for l in r.stdout.splitlines()))
        warn = [l for l in r.stdout.splitlines() if "WARNING" in l and "BADF-DEM-0112" in l]
        self.assertTrue(warn, r.stdout)


class DegenerateSurfaceTests(_SweepFixture):
    """#323 (WP-2026-0152): a required surface that is PRESENT but carries nothing usable
    was read as clean -- exit 0, `READ (0 id occurrence(s))`, next-free wrong by twenty
    -- because the positive-control anchors live only in `ledger`. Absent produces a
    refusal; present-and-empty produced a confident wrong answer. `branches` claims
    WP-2026-0140 here, so a sweep that really read it reports WP-2026-0141.

    Ruling on #323 (criterion 6): content cannot separate a gather that failed after
    `>` truncated the file from one that succeeded and found nothing -- both are 0
    bytes. A 0-byte or whitespace-only required dump is therefore refused, with the
    remedy named; a non-empty dump with no ids is an honest zero and stays READ. The
    legitimately-empty gather written as 0 bytes is the declared non-covered case."""

    REQUIRED = ("ledger", "branches", "pr_files", "bodies")

    def setUp(self):
        super().setUp()
        self.append("branches.txt", "1" * 40 + "\trefs/heads/wp/WP-2026-0140-x\n")

    def surfaces_header(self, out):
        lines = out.splitlines()
        start = lines.index("SURFACES:")
        return {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip() for l in lines[start + 1:start + 6]}

    def test_control_reads_the_claim_and_reports_the_true_next_free(self):
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("NEXT FREE (claim-shaped surfaces only): WP-2026-0141", r.stdout)

    def test_empty_required_surface_is_refused_not_read(self):
        self.write("branches.txt", "")
        r = self.sweep()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("branches.txt is PRESENT BUT UNUSABLE (empty: 0 bytes)", r.stderr)
        self.assertNotIn("missing surface dump", r.stderr, "must be distinguishable from the missing-dump refusal")
        self.assertNotIn("NEXT FREE", r.stdout)

    def test_whitespace_only_required_surface_is_refused_not_read(self):
        self.write("branches.txt", " \n\t\n")
        r = self.sweep()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("branches.txt is PRESENT BUT UNUSABLE (whitespace only)", r.stderr)

    def test_undecodable_required_surface_is_not_silently_replaced(self):
        (self.dir / "branches.txt").write_bytes("refs/heads/wp/WP-2026-0140-x\n".encode("utf-16"))
        r = self.sweep()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("branches.txt is PRESENT BUT UNUSABLE (not UTF-8", r.stderr)

    def test_unreadable_required_surface_is_a_refusal_not_a_traceback(self):
        # chmod 000 does not deny under a root-run harness, so the OSError is injected.
        sys.path.insert(0, str(TOOL.parent))
        import badf_id_sweep as tool
        real = Path.read_bytes

        def denied(path):
            if path.name == "branches.txt":
                raise PermissionError(13, "Permission denied", str(path))
            return real(path)
        Path.read_bytes = denied
        self.addCleanup(setattr, Path, "read_bytes", real)
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = tool.main(["--from-dir", str(self.dir)])
        self.assertEqual(code, 1)
        self.assertIn("branches.txt is PRESENT BUT UNUSABLE (unreadable: PermissionError", err.getvalue())

    def test_each_required_surface_is_checked_not_just_the_anchor_one(self):
        sys.path.insert(0, str(TOOL.parent))
        import badf_id_sweep as tool
        self.assertEqual(tool.CLAIM_SURFACES + tool.PROSE_SURFACES, self.REQUIRED)
        for name in tool.CLAIM_SURFACES + tool.PROSE_SURFACES:
            with self.subTest(surface=name):
                saved = (self.dir / f"{name}.txt").read_bytes()
                self.write(f"{name}.txt", "")
                r = self.sweep()
                (self.dir / f"{name}.txt").write_bytes(saved)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn(f"{name}.txt is PRESENT BUT UNUSABLE", r.stderr)

    def test_read_is_not_printed_for_a_degenerate_optional_surface(self):
        self.write("comments.txt", "")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        header = self.surfaces_header(r.stdout)
        self.assertFalse(header["comments"].startswith("READ"), header)
        self.assertIn("PRESENT BUT UNUSABLE (empty: 0 bytes)", header["comments"])
        for name in self.REQUIRED:
            self.assertTrue(header[name].startswith("READ ("), header)

    def test_a_legitimately_empty_surface_is_still_distinguishable(self):
        """Criterion 6: a declared honest zero (non-empty, no ids) is READ, not refused."""
        self.write("pr_files.txt", "# gathered OK: no open PRs\n")
        r = self.sweep(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.surfaces_header(r.stdout)["pr_files"], "READ (0 id occurrence(s))")

    def test_refusal_names_the_remedy_for_an_honest_empty_gather(self):
        self.write("pr_files.txt", "")
        r = self.sweep()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("declare it in the dump", r.stderr)


DOC = ROOT / "docs" / "governance" / "GITHUB_CONTROL_PLANE.md"

GH_STUB = r'''
import os, re, sys
a = sys.argv[1:]; fail = os.environ.get("GH_FAIL", "").split()
def out(*lines):
    for l in lines: print(l)
if a[:2] == ["pr", "list"]:
    if "pr-list" in fail: sys.exit("gh: HTTP 502")
    out(*os.environ.get("GH_PRS", "").split())
elif a[:2] == ["issue", "list"]:
    if "issue-list" in fail: sys.exit("gh: HTTP 502")
    out(*os.environ.get("GH_ISSUES", "").split())
elif a[0] == "api" and "search/issues" in a:
    out("GOV-0097 governs the double-claim episode.")
elif a[0] == "api" and (m := re.search(r"/pulls/(\d+)/files$", a[1])):
    if f"pr-files-{m[1]}" in fail: sys.exit("gh: HTTP 403 rate limited")
    out(f"work/WP-2026-{548 + int(m[1]):04d}/work-package.json")
elif a[0] == "api" and (m := re.search(r"/issues/(\d+)/comments$", a[1])):
    out(f"claiming WP-2026-0600 on #{m[1]}")
else:
    sys.exit(f"gh stub: unexpected {a}")
'''


@unittest.skipUnless(shutil.which("bash") and os.name == "posix", "runs the documented bash gather")
class DocumentedGatherTests(unittest.TestCase):
    """#349 (WP-2026-0153): runs THE BLOCK FROM GITHUB_CONTROL_PLANE.md, unedited, against stub
    `gh`/`git`, then the real sweep -- so the doctrine cannot drift from what is tested.

    #323 made the sweep refuse a 0-byte dump; the documented loop gathers produced one for an honest
    empty result AND for a failed `gh pr list`, and a part-way failure left a non-empty, partial dump
    the sweep READ. A loop gather must fail closed: a failure leaves the dump MISSING, a successful
    empty gather leaves a non-empty DECLARED one. Not covered: the single-command gathers (ledger,
    branches, bodies) -- their failure leaves 0 bytes, which #323's refusal already catches."""

    def setUp(self):
        blocks = [b for b in re.findall(r"^```bash\n(.*?)^```", DOC.read_text(encoding="utf-8"), re.S | re.M)
                  if "badf_id_sweep.py --from-dir" in b]
        self.assertEqual(len(blocks), 1, "exactly one documented gather block")
        self.block = blocks[0]
        self.root = Path(tempfile.mkdtemp(prefix="badf-gather-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / "work" / "WP-2026-0110").mkdir(parents=True)
        (self.root / "badf" / "demands").mkdir(parents=True)
        (self.root / "badf" / "demands" / "BADF-DEM-0097.json").write_text("{}")
        (self.root / "scripts").mkdir()
        shutil.copy(TOOL, self.root / "scripts" / TOOL.name)
        self.bin = self.root / "bin"; self.bin.mkdir()
        (self.root / "tmp").mkdir()
        self.stub("gh", f"#!{sys.executable}\n{GH_STUB}")
        self.stub("git", "#!/bin/sh\n[ \"$1\" = ls-remote ] || exit 2\n"
                         "printf '%s\\trefs/heads/main\\n' 0000000000000000000000000000000000000000\n")
        self.stub("python3", f"#!/bin/sh\nexec {sys.executable} \"$@\"\n")

    def stub(self, name, text):
        p = self.bin / name; p.write_text(text); p.chmod(0o755)

    def gather(self, prs="", issues="", fail=""):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}", TMPDIR=str(self.root / "tmp"),
                   GH_PRS=prs, GH_ISSUES=issues, GH_FAIL=fail)
        return subprocess.run(["bash", "-c", self.block], cwd=self.root, env=env, capture_output=True, text=True)

    def header(self, r):
        lines = r.stdout.splitlines()
        start = lines.index("SURFACES:")
        return {l.split(":", 1)[0].strip(): l.split(":", 1)[1].strip() for l in lines[start + 1:start + 6]}

    def test_control_open_prs_and_comments_are_read_and_claimed(self):
        r = self.gather(prs="7 8", issues="12")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.header(r)["pr_files"], "READ (2 id occurrence(s))")
        self.assertIn("NEXT FREE (claim-shaped surfaces only): WP-2026-0557", r.stdout)
        self.assertIn("WARNING: comment surface shows WP-2026-0600", r.stdout)

    def test_no_open_prs_is_an_honest_zero_not_a_refusal(self):
        r = self.gather()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.header(r)["pr_files"], "READ (0 id occurrence(s))")

    def test_failed_pr_list_leaves_the_dump_missing(self):
        r = self.gather(prs="7", fail="pr-list")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("missing surface dump pr_files.txt", r.stderr)

    def test_partial_gather_is_refused_never_read(self):
        """PR 7's files arrive, PR 8's call fails: the loop used to carry on and the sweep READ a
        dump missing PR 8's claims. `set -e` cannot fix this left of `&&` -- bash ignores it there."""
        r = self.gather(prs="7 8", fail="pr-files-8")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("missing surface dump pr_files.txt", r.stderr)
        self.assertNotIn("READ", r.stdout)

    def test_comments_no_open_issues_is_read_and_a_failed_list_is_not_provided(self):
        r = self.gather()
        self.assertEqual(self.header(r)["comments"], "READ (0 id occurrence(s))")
        r = self.gather(fail="issue-list")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.header(r)["comments"].startswith("NOT PROVIDED"), self.header(r))
