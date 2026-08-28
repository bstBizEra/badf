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


# A body that satisfies everything EXCEPT what a test removes, so each test
# isolates one failure (BADF-WP-0034 added the section requirement, so the
# trailer-isolation tests must carry the sections).
SECTIONS = "## What\nx\n\n## Verification\nx\n"
FULL = SECTIONS + "Work-Package: BADF-WP-0016\nCloses #19\n"


class TraceabilityTests(unittest.TestCase):
    def test_full_body_passes(self):
        self.assertEqual(tr.check(FULL), [])

    def test_legacy_wp_form_accepted(self):
        self.assertEqual(tr.check(SECTIONS + "Work-Package: WP-2026-0010\nFixes #3\n"), [])

    def test_missing_closes_is_named(self):
        p = tr.check(SECTIONS + "Work-Package: BADF-WP-0016\n")
        self.assertEqual(len(p), 1); self.assertIn("Closes #N", p[0])

    def test_missing_wp_is_named(self):
        p = tr.check(SECTIONS + "Closes #19\n")
        self.assertEqual(len(p), 1); self.assertIn("Work-Package", p[0])

    def test_malformed_wp_is_refused(self):
        self.assertTrue(any("Work-Package" in x for x in tr.check(SECTIONS + "Work-Package: WP-16\nCloses #19\n")))

    def test_closes_must_be_its_own_line(self):
        """A 'Closes #N' buried mid-sentence is prose, not a declaration."""
        self.assertTrue(any("Closes" in x for x in tr.check(SECTIONS + "Work-Package: BADF-WP-0016\nsee Closes #19 later\n")))

    def test_empty_body_names_everything(self):
        p = tr.check("")
        self.assertEqual(len(p), 4)   # WP, Closes, What, Verification

    def test_missing_a_required_section_is_named(self):
        p = tr.check("## What\nx\n\nWork-Package: BADF-WP-0016\nCloses #19\n")
        self.assertEqual(len(p), 1); self.assertIn("Verification", p[0])

    def test_a_section_must_be_a_heading_not_prose(self):
        body = "we did the Verification and What of it\nWork-Package: BADF-WP-0016\nCloses #19\n"
        self.assertEqual({x.split("`")[1] for x in tr.check(body)}, {"## What", "## Verification"})

    def test_pr_template_carries_the_required_sections_and_trailers(self):
        tmpl = (gate.ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        for name in tr.REQUIRED_SECTIONS:
            self.assertRegex(tmpl, rf"(?m)^##\s+{name}\b", f"PR template lacks the {name} heading the check requires")
        self.assertIn("Work-Package:", tmpl); self.assertIn("Closes #", tmpl)

    def test_issue_form_requests_the_problem_contract_sections(self):
        # Parse the labels deterministically -- PyYAML is not a project dependency
        # and is absent on the CI runner (this test errored there before the fix).
        import re as _re
        form = (gate.ROOT / ".github/ISSUE_TEMPLATE/demand.yml").read_text(encoding="utf-8")
        labels = set(_re.findall(r"(?m)^\s+label:\s*(.+?)\s*$", form))
        self.assertLessEqual({"Observed", "Expected", "Proposed work package"}, labels)
        cfg = (gate.ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        self.assertRegex(cfg, r"(?m)^blank_issues_enabled:\s*false\b", "a demand must use the form, not a blank issue")

    def test_cli_exit_codes(self):
        for body, want in ((FULL, 0), ("", 1)):
            r = subprocess.run([sys.executable, "scripts/check_pr_traceability.py"], input=body,
                               cwd=str(gate.ROOT), capture_output=True, text=True)
            self.assertEqual(r.returncode, want, r.stdout + r.stderr)
            self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
