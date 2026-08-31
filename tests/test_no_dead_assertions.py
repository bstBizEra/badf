"""#210 criterion 2: the CLASS guard, not just the instance fix.

An assertion spliced into a trailing comment by a semicolon edit runs for nobody and the
suite stays green -- `self.assertEqual([], entry["allowed_tools"])` sat inside a comment in
test_badf_verification_evidence.py and `allowed_tools` appeared exactly once in that module,
in that comment. Fixing that one occurrence closes an instance. This closes the class.

The detection rule is BADF-REV's, adopted with the correction BARCHI-2 measured against it:
a naive `grep -nE '#.*self\\.assert'` FALSE-POSITIVES on a `#` inside a string literal, and
did so on a live, load-bearing assertion. So the rule masks string literals using the AST
before looking, and compares what the text claims against what the parser actually found.

Both controls are asserted, because a detector that has only ever run on the bug that
motivated it has no measured false-positive rate:

  positive -- a synthetic spliced assertion MUST be reported
  negative -- the exact shape that fooled the naive grep (`#` inside a string, live
              assertion after it) MUST NOT be reported
"""
import ast
import re
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ASSERT_RE = re.compile(r"self\.(assert\w+)\s*\(")


def _mask_string_literals(src: str, tree: ast.AST) -> list[str]:
    """Blank out every string literal, so a `#` inside one cannot look like a comment."""
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.lineno and node.end_lineno:
            for ln in range(node.lineno, node.end_lineno + 1):
                i = ln - 1
                if i >= len(lines):
                    continue
                a = node.col_offset if ln == node.lineno else 0
                b = node.end_col_offset if ln == node.end_lineno else len(lines[i])
                lines[i] = lines[i][:a] + " " * (b - a) + lines[i][b:]
    return lines


def find_dead_assertions(src: str, label: str = "<src>") -> list[tuple[str, int, list[str]]]:
    """Lines where the TEXT names more assertions than the PARSER found executing.

    The difference is an assertion the interpreter never sees -- almost always one spliced
    into a trailing comment.
    """
    tree = ast.parse(src)
    executing: dict[int, list[str]] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith("assert"):
            executing.setdefault(n.lineno, []).append(n.func.attr)
    dead = []
    for i, line in enumerate(_mask_string_literals(src, tree), 1):
        named = ASSERT_RE.findall(line)
        live = executing.get(i, [])
        if len(named) > len(live):
            dead.append((label, i, sorted({h for h in named if named.count(h) > live.count(h)})))
    return dead


SPLICED = '''
class T:
    def test_x(self):
        self.assertIn("a", "abc");  # note self.assertEqual([], self.tools)
'''

STRING_HASH = '''
class T:
    def test_x(self):
        start = text.find("## badf-build -> ACTIVE")
        self.assertGreater(start, 0, "no admission section")
'''


class DeadAssertionDetectorTests(unittest.TestCase):
    def test_positive_control_a_spliced_assertion_is_detected(self):
        """The detector must fire on the shape #210 is about. Never trusted unseen."""
        dead = find_dead_assertions(SPLICED, "synthetic")
        self.assertEqual(1, len(dead), f"expected exactly one dead assertion, got {dead}")
        self.assertIn("assertEqual", dead[0][2])

    def test_negative_control_a_hash_inside_a_string_is_not_flagged(self):
        """The exact shape that fooled the naive grep, on a LIVE assertion.

        BARCHI-2 measured the original `grep -nE '#.*self\\.assert'` flagging
        test_badf_build_activation.py, where the `#` lives inside the string literal
        "## badf-build -> ACTIVE" and the assertion after it executes. A detector without
        this control would ship a false positive as its remedy -- which is how the first
        version of this rule reached the issue.
        """
        self.assertEqual([], find_dead_assertions(STRING_HASH, "synthetic"))

    def test_no_dead_assertions_anywhere_in_tests(self):
        """The class guard. Anti-vacuity: the corpus is asserted non-trivial first, so an
        empty or mis-globbed directory cannot pass this by examining nothing."""
        modules = sorted(TESTS_DIR.glob("test_*.py"))
        self.assertGreater(len(modules), 30, "the tests corpus is missing; this guard would pass vacuously")
        dead = []
        for path in modules:
            dead.extend(find_dead_assertions(path.read_text(encoding="utf-8"), path.name))
        self.assertEqual([], dead, "assertions that the parser never sees: " + "; ".join(
            f"{f}:{ln} {', '.join(names)}" for f, ln, names in dead))


if __name__ == "__main__":
    unittest.main()
