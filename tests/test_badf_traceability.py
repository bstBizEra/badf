"""BADF-MAIN-001: a PR body must name its Work Package and the Issue it
closes. Before BADF-WP-0016, 23 of 23 non-merge commits on main referenced
no Issue and the repository had never had one. This check is the first
link of Issue -> WP -> branch -> PR -> main, made deterministic.

BADF-WP-0070 (GIT-B, the badf-git identity contract) froze ONE identity with
three faces and one binding: the machine id `WP-2026-NNNN` (WP-2026- is a
fixed ledger namespace constant, defined once in badf_gate.py), the display
label `BADF-WP-NNNN` permitted only in the PR title / squash subject, and the
branch `wp/WP-2026-NNNN-<slug>` -- all three carrying one NNNN, bound by the
body trailer `Work-Package: WP-2026-NNNN`. Before it, title, branch and
trailer could each name a different work package and CI stayed green; the
check accepted either trailer form and looked at neither title nor branch.
"""
import re
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
FULL = SECTIONS + "Work-Package: WP-2026-0016\nCloses #19\n"
TITLE = "BADF-WP-0016: main is PR-only"
HEAD = "wp/WP-2026-0016-pr-only"


def cli(body: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "scripts/check_pr_traceability.py", *args], input=body,
                          cwd=str(gate.ROOT), capture_output=True, text=True)


class TraceabilityTests(unittest.TestCase):
    def test_full_body_passes(self):
        self.assertEqual(tr.check(FULL), [])

    def test_missing_closes_is_named(self):
        p = tr.check(SECTIONS + "Work-Package: WP-2026-0016\n")
        self.assertEqual(len(p), 1); self.assertIn("Closes #N", p[0])

    def test_missing_wp_is_named(self):
        p = tr.check(SECTIONS + "Closes #19\n")
        self.assertEqual(len(p), 1); self.assertIn("Work-Package", p[0])

    def test_malformed_wp_is_refused(self):
        self.assertTrue(any("Work-Package" in x for x in tr.check(SECTIONS + "Work-Package: WP-16\nCloses #19\n")))

    def test_closes_must_be_its_own_line(self):
        """A 'Closes #N' buried mid-sentence is prose, not a declaration."""
        self.assertTrue(any("Closes" in x for x in tr.check(SECTIONS + "Work-Package: WP-2026-0016\nsee Closes #19 later\n")))

    def test_empty_body_names_everything(self):
        p = tr.check("")
        self.assertEqual(len(p), 4)   # WP, Closes, What, Verification

    def test_missing_a_required_section_is_named(self):
        p = tr.check("## What\nx\n\nWork-Package: WP-2026-0016\nCloses #19\n")
        self.assertEqual(len(p), 1); self.assertIn("Verification", p[0])

    def test_a_section_must_be_a_heading_not_prose(self):
        body = "we did the Verification and What of it\nWork-Package: WP-2026-0016\nCloses #19\n"
        self.assertEqual({x.split("`")[1] for x in tr.check(body)}, {"## What", "## Verification"})

    def test_pr_template_carries_the_required_sections_and_trailers(self):
        tmpl = (gate.ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        for name in tr.REQUIRED_SECTIONS:
            self.assertRegex(tmpl, rf"(?m)^##\s+{name}\b", f"PR template lacks the {name} heading the check requires")
        self.assertIn("Work-Package:", tmpl); self.assertIn("Closes #", tmpl)

    def test_issue_form_requests_the_problem_contract_sections(self):
        # Parse the labels deterministically -- PyYAML is not a project dependency
        # and is absent on the CI runner (this test errored there before the fix).
        form = (gate.ROOT / ".github/ISSUE_TEMPLATE/demand.yml").read_text(encoding="utf-8")
        labels = set(re.findall(r"(?m)^\s+label:\s*(.+?)\s*$", form))
        self.assertLessEqual({"Observed", "Expected", "Proposed work package"}, labels)
        cfg = (gate.ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8")
        self.assertRegex(cfg, r"(?m)^blank_issues_enabled:\s*false\b", "a demand must use the form, not a blank issue")

    def test_cli_exit_codes(self):
        for body, want in ((FULL, 0), ("", 1)):
            r = cli(body, "--title", TITLE, "--head-ref", HEAD)
            self.assertEqual(r.returncode, want, r.stdout + r.stderr)
            self.assertNotIn("Traceback", r.stderr)


class IdentityContractTests(unittest.TestCase):
    """BADF-WP-0070 / GIT-B: one NNNN across trailer, title and branch."""

    # -- the binding: the trailer is the canonical machine id --------------------
    def test_canonical_trailer_title_and_branch_pass(self):
        r = cli(FULL, "--title", TITLE, "--head-ref", HEAD)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("BADF TRACEABILITY PASS: WP-2026-0016 closes #19 on wp/WP-2026-0016-pr-only", r.stdout)

    def test_display_form_trailer_is_refused_with_canonical_fix(self):
        """Retires test_legacy_wp_form_accepted (BADF-WP-0016..0069 accepted either
        form). The display label is for titles; the trailer is the binding."""
        p = tr.check(SECTIONS + "Work-Package: BADF-WP-0016\nCloses #19\n")
        self.assertEqual(len(p), 1, p)
        self.assertIn("Work-Package: WP-2026-0016", p[0])   # the exact line to paste

    # -- the display label: title ----------------------------------------------
    def test_title_without_display_label_is_refused(self):
        p = tr.check_identity(FULL, "enforce the identity contract", HEAD)
        self.assertEqual(len(p), 1, p); self.assertIn("BADF-WP-0016:", p[0])

    def test_title_label_must_match_trailer_id(self):
        p = tr.check_identity(FULL, "BADF-WP-0017: something else", HEAD)
        self.assertEqual(len(p), 1, p)
        self.assertIn("BADF-WP-0017", p[0]); self.assertIn("WP-2026-0016", p[0])

    # -- the branch ---------------------------------------------------------------
    def test_branch_outside_wp_namespace_is_refused(self):
        for head in ("feat/identity", "feature/BADF-WP-0016-x", "fix/BADF-BUG-0001-x", "chore/x", "gov/BADF-WP-0016-x", "main"):
            with self.subTest(head=head):
                p = tr.check_identity(FULL, TITLE, head)
                self.assertEqual(len(p), 1, p); self.assertIn("wp/WP-2026-0016-", p[0])

    def test_branch_with_display_id_is_refused(self):
        p = tr.check_identity(FULL, TITLE, "wp/BADF-WP-0016-pr-only")
        self.assertEqual(len(p), 1, p); self.assertIn("wp/WP-2026-0016-", p[0])

    def test_branch_id_must_match_trailer_id(self):
        p = tr.check_identity(FULL, TITLE, "wp/WP-2026-0017-pr-only")
        self.assertEqual(len(p), 1, p)
        self.assertIn("WP-2026-0017", p[0]); self.assertIn("WP-2026-0016", p[0])

    def test_branch_slug_must_be_lowercase_kebab(self):
        for bad in ("wp/WP-2026-0016-PR_Only", "wp/WP-2026-0016-", "wp/WP-2026-0016", "wp/WP-2026-0016--x", "wp/WP-2026-0016-x/y"):
            with self.subTest(head=bad):
                self.assertEqual(len(tr.check_identity(FULL, TITLE, bad)), 1, bad)
        self.assertEqual(tr.check_identity(FULL, TITLE, "wp/WP-2026-0016-identity-contract-2"), [])

    def test_missing_title_or_head_ref_is_a_usage_error_not_a_pass(self):
        for args in ((), ("--title", TITLE), ("--head-ref", HEAD)):
            with self.subTest(args=args):
                r = cli(FULL, *args)
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertNotIn("PASS", r.stdout)
                self.assertNotIn("Traceback", r.stderr)

    # -- one namespace constant, defined once --------------------------------------
    def test_namespace_constant_is_defined_once_and_shared(self):
        gate_src = (gate.ROOT / "scripts/badf_gate.py").read_text(encoding="utf-8")
        self.assertEqual(gate_src.count('WP_NAMESPACE = "WP-2026-"'), 1)
        self.assertEqual(gate_src.count('"WP-2026-'), 1, "badf_gate.py must build every id from WP_NAMESPACE, not repeat the literal")
        for name in ("badf_compose.py", "check_pr_traceability.py"):
            src = (gate.ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertNotIn("WP-2026-", src, f"{name} carries its own namespace literal")
            self.assertIn("WP_NAMESPACE", src, f"{name} does not share the constant")
        self.assertEqual(tr.WP_NAMESPACE, gate.WP_NAMESPACE)
        import badf_compose as compose  # noqa: E402  (import-safe: docstring, imports, constants, defs)
        self.assertEqual(compose.WP_NAMESPACE, gate.WP_NAMESPACE)

    # -- history is not rewritten ---------------------------------------------------
    def test_ledger_still_resolves_historical_display_form_trailers(self):
        landings = gate.ledger_landings()
        self.assertIn("WP-2026-0016", landings)   # 12f5056 carries `Work-Package: BADF-WP-0016`
        self.assertGreaterEqual(len(landings), 50)
        self.assertTrue(all(re.fullmatch(rf"{re.escape(gate.WP_NAMESPACE)}[0-9]{{4}}", k) for k in landings))

    # -- doctrine moves with the contract ------------------------------------------
    def test_control_plane_and_template_name_the_canonical_forms(self):
        plane = (gate.ROOT / "docs/governance/GITHUB_CONTROL_PLANE.md").read_text(encoding="utf-8")
        self.assertIn("wp/WP-2026-NNNN-<slug>", plane)
        self.assertNotIn("wp/BADF-WP-NNNN", plane)
        tmpl = (gate.ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
        self.assertIn("Work-Package: WP-2026-NNNN", tmpl)
        self.assertNotIn("Work-Package: BADF-WP-NNNN", tmpl)

    def test_branch_pr_contract_declares_enforcement_live_from_this_wp(self):
        text = (gate.ROOT / "skills/badf-git/references/branch-pr-contract.md").read_text(encoding="utf-8")
        self.assertNotIn("branch-name enforcement is deferred", text)
        self.assertIn("WP-2026-0070", text)
        self.assertIn("wp/WP-2026-NNNN-<slug>", text)


if __name__ == "__main__":
    unittest.main()
