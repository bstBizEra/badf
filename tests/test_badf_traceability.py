"""BADF-MAIN-001: a PR body must name its Work Package and the Issue it
closes. Before BADF-WP-0016, 23 of 23 non-merge commits on main referenced
no Issue and the repository had never had one. This check is the first
link of Issue -> WP -> branch -> PR -> main, made deterministic.
"""
import subprocess
import sys
import unittest

import scripts.badf_gate as gate
sys.path.insert(0, str(gate.ROOT / "scripts"))
import check_pr_traceability as tr  # noqa: E402


class TraceabilityTests(unittest.TestCase):
    def test_both_present_passes(self):
        self.assertEqual(tr.check("Work-Package: BADF-WP-0016\nCloses #19\n"), [])

    def test_legacy_wp_form_accepted(self):
        self.assertEqual(tr.check("Work-Package: WP-2026-0010\nFixes #3\n"), [])

    def test_missing_closes_is_named(self):
        p = tr.check("Work-Package: BADF-WP-0016\n")
        self.assertEqual(len(p), 1); self.assertIn("Closes #N", p[0])

    def test_missing_wp_is_named(self):
        p = tr.check("Closes #19\n")
        self.assertEqual(len(p), 1); self.assertIn("Work-Package", p[0])

    def test_malformed_wp_is_refused(self):
        self.assertTrue(any("Work-Package" in x for x in tr.check("Work-Package: WP-16\nCloses #19\n")))

    def test_closes_must_be_its_own_line(self):
        """A 'Closes #N' buried mid-sentence is prose, not a declaration."""
        self.assertTrue(any("Closes" in x for x in tr.check("Work-Package: BADF-WP-0016\nsee Closes #19 later\n")))

    def test_empty_body_names_both(self):
        self.assertEqual(len(tr.check("")), 2)

    def test_cli_exit_codes(self):
        for body, want in (("Work-Package: BADF-WP-0016\nCloses #19\n", 0), ("", 1)):
            r = subprocess.run([sys.executable, "scripts/check_pr_traceability.py"], input=body,
                               cwd=str(gate.ROOT), capture_output=True, text=True)
            self.assertEqual(r.returncode, want, r.stdout + r.stderr)
            self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
