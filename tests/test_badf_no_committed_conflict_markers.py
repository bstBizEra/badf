"""GOV-0147 (#331, WP-2026-0151): a merge conflict committed as content is invisible.

`badf_gate.py repo` passed, the suite passed and `git diff --diff-filter=U` was empty
while docs/governance/GITHUB_CONTROL_PLANE.md carried a live conflict block from #276:
a committed conflict is ordinary text to every instrument that looks at the index or
at bytes-vs-lockfile. This guard reads every tracked file.

A committed conflict block is not frozen -- later commits append into it. #331's block
held one section per side when it was committed and four by the time it was found
(rungs D and E of badf-uat landed inside it), so its sides were never alternatives.
Resolve such a block by reading its history (`git log -S`), not by picking a side.

Matched, at the start of a line outside a fenced code block:
  the ours/theirs markers `<<<<<<<` and `>>>>>>>`, the diff3/zdiff3 base marker
  `|||||||` (a partly hand-resolved diff3 conflict can leave only this one behind),
  each followed by a space or the end of the line; and the separator, exactly seven
  `=` characters alone on the line.
The separator is also a valid CommonMark setext underline. It is matched anyway:
excluding it failed open in #331's first fix (a green guard over a document that
still held the separator), and the tracked tree carried no other such line when this
guard was written. A setext heading can use a longer or shorter run of `=`.
Fences follow CommonMark: an opening run of three or more backticks or tildes with
at most three spaces of indentation, closed by a run of the same character at least
as long. A traceback's `~~~^^^` carets therefore do not open a fence unless they
start the line.

Not covered: a conflict resolved by silently dropping one side leaves no marker and
is out of reach of any textual guard.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

MARKER = re.compile(r"^(?:(?:<{7}|>{7}|\|{7})(?: |$)|={7}$)")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")
FLOOR = 1000   # tracked files; a scan of fewer is vacuous for this repository


def markers_in(text: str) -> list[tuple[int, str]]:
    """(line number, line) of every conflict marker outside a fenced code block."""
    found, fence = [], None
    for number, line in enumerate(text.splitlines(), 1):
        if fence is None:
            opening = FENCE_OPEN.match(line)
            if opening:
                fence = (opening.group(1)[0], len(opening.group(1)))
                continue
            if MARKER.match(line):
                found.append((number, line))
        elif re.match(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}\s*$", line):
            fence = None
    return found


def scan(root: Path) -> tuple[int, list[str], dict[str, list[tuple[int, str]]]]:
    """(files read, files that could not be read as UTF-8 text, {path: markers})."""
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True).stdout
    read, unreadable, offenders = 0, [], {}
    for rel in filter(None, listed.decode("utf-8").split("\0")):
        path = root / rel
        if not path.is_file():   # a tracked path deleted in the working tree
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            unreadable.append(rel)
            continue
        read += 1
        if hits := markers_in(text):
            offenders[rel] = hits
    return read, unreadable, offenders


class NoCommittedConflictMarkers(unittest.TestCase):
    def test_no_tracked_file_carries_a_conflict_marker(self):
        read, unreadable, offenders = scan(gate.ROOT)
        self.assertGreaterEqual(read, FLOOR, f"only {read} tracked files read; the scan is vacuous")
        self.assertEqual(unreadable, [], "tracked files that are not UTF-8 text were skipped unscanned")
        detail = "; ".join(f"{p}:{n}: {line[:40]!r}" for p, hits in sorted(offenders.items()) for n, line in hits)
        self.assertEqual(offenders, {}, "committed conflict markers -- read the block's history (git log -S) "
                                        f"before resolving; its sides may not be alternatives: {detail}")


class ScanPositiveControl(unittest.TestCase):
    """On a clean tree the guard above can only pass; this proves scan() reports a planted
    marker in a tracked file, skips an untracked one, and counts non-UTF-8 text."""

    def test_scan_reports_a_planted_marker_in_a_tracked_file(self):
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="badf-conflict-guard-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
        (tmp / "clean.md").write_text("# fine\n", encoding="utf-8")
        (tmp / "planted.md").write_text(f"a\n{'<' * 7} HEAD\nb\n", encoding="utf-8")
        (tmp / "latin1.txt").write_bytes("caf\xe9\n".encode("latin-1"))
        subprocess.run(["git", "-C", str(tmp), "add", "clean.md", "planted.md", "latin1.txt"], check=True)
        (tmp / "untracked.md").write_text(f"{'>' * 7} x\n", encoding="utf-8")
        read, unreadable, offenders = scan(tmp)
        self.assertEqual((read, unreadable), (2, ["latin1.txt"]))
        self.assertEqual(offenders, {"planted.md": [(2, f"{'<' * 7} HEAD")]})


class MatcherControls(unittest.TestCase):
    """The matcher must see every marker git writes and nothing else it was told to ignore."""

    def test_a_real_diff3_conflict_is_seen_on_every_marker_line(self):
        block = "\n".join([f"{'<' * 7} HEAD", "ours", f"{'|' * 7} 0511328", "base", "=" * 7, "theirs", f"{'>' * 7} other"])
        self.assertEqual([n for n, _ in markers_in(block)], [1, 3, 5, 7])

    def test_a_bare_marker_with_an_empty_label_is_seen(self):
        self.assertEqual(len(markers_in(f"{'<' * 7}\nx\n{'>' * 7}\n")), 2)

    def test_markers_inside_a_fence_are_documentation(self):
        for fence in ("```", "~~~", "````text"):
            doc = "\n".join(["prose", fence, f"{'<' * 7} HEAD", "=" * 7, f"{'>' * 7} x", fence.rstrip("text"), "prose"])
            self.assertEqual(markers_in(doc), [], fence)

    def test_a_shorter_run_does_not_close_a_longer_fence(self):
        doc = "\n".join(["````", "```", f"{'<' * 7} HEAD", "````", f"{'>' * 7} x"])
        self.assertEqual([n for n, _ in markers_in(doc)], [5])

    def test_traceback_carets_do_not_open_a_fence(self):
        doc = "\n".join(["    x = f(y)", "        ~~~~~^^^^", f"{'<' * 7} HEAD"])
        self.assertEqual([n for n, _ in markers_in(doc)], [3])

    def test_lookalikes_are_not_markers(self):
        for line in (f"{'<' * 7}x", f" {'<' * 7} HEAD", "=" * 8, "=" * 3, f"{'=' * 7} ", f"a {'>' * 7} b", "| | |"):
            self.assertEqual(markers_in(line), [], repr(line))


if __name__ == "__main__":
    unittest.main()
