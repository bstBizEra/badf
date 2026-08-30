"""Post-merge reconciliation (BADF-WP-0019, Issue #26).

WP-2026-0018 landed on main as c510516 with a record that said IN_PROGRESS.
main is PR-only, so a record cannot know its own squash SHA before it lands
and nothing could update it after. Landing is a fact of the git ledger, so
the gate DERIVES it -- first-parent history of origin/main, commit bodies
carrying the record's Work-Package line -- corroborates every claim a record
makes, names silence as LANDED_UNRECONCILED, and refuses to open a new work
package while a landed one is unreconciled. Every test runs the real gate in
a scratch clone whose origin/main is the real authorized ledger.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

WP18, WP19, WP10 = "WP-2026-0018", "WP-2026-0019", "WP-2026-0010"
LANDED_18 = "c510516"   # squash of PR #23; body carries "Work-Package: BADF-WP-0018"
NOT_18 = "0871417"      # merge commit of PR #18 on main; body carries no such line


class LedgerScratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "badf"
        self.base = seed_clone(self.root, carry_working_state=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}
        # Baseline: the tree's work packages equal the ledger's, so each test
        # adds exactly what it asserts on (the working tree may carry a new WP).
        on_ledger = set(self.git("ls-tree", "-r", "--name-only", f"origin/{gate.DEFAULT_BRANCH}", "--", "work/").splitlines())
        for rec in list((self.root / "work").glob("WP-*/work-package.json")):
            if rec.relative_to(self.root).as_posix() not in on_ledger:
                shutil.rmtree(rec.parent)
        # The design guarantees that right after EVERY merge origin/main carries one
        # LANDED_UNRECONCILED record: the one that just landed. The first version of
        # this fixture assumed a debt-free ledger and was red on main from the very
        # merge that shipped it (30186c5, run 33091002713) -- BRANCH_GREEN != MERGE_SAFE.
        # Normalise: corroborate every carried record the ledger shows landed, using
        # an INDEPENDENT parse so the gate's parser is cross-checked, never trusted.
        for wp, sha in self.ledger().items():
            rec = self.record(wp)
            if rec.is_file() and not (json.loads(rec.read_text()).get("external_target") or {}).get("landed_as"):
                self.set_record(wp, status="CLOSED", landed_as=sha, landing_not_on_ledger=None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), *a], capture_output=True, text=True, check=True).stdout.strip()

    def ledger(self):
        """Independent derivation, deliberately unlike the gate's: WP id -> OLDEST
        first-parent origin/main commit whose body carries its Work-Package line."""
        out = {}
        log = self.git("log", "--first-parent", "--reverse", "--format=%H%n%B%n@@END@@", f"origin/{gate.DEFAULT_BRANCH}")
        for chunk in log.split("@@END@@"):
            lines = chunk.strip().splitlines()
            if not lines:
                continue
            sha, body = lines[0].strip(), "\n".join(lines[1:])
            for m in re.finditer(r"^Work-Package:\s*(?:BADF-WP-|WP-2026-)(\d{4})\s*$", body, re.M):
                out.setdefault(f"WP-2026-{m.group(1)}", sha)   # --reverse: first seen is oldest
        return out

    def record(self, wp):
        return self.root / "work" / wp / "work-package.json"

    def set_record(self, wp, **fields):
        p = self.record(wp); w = json.loads(p.read_text())
        if "landed_as" in fields:
            et = dict(w.get("external_target", {})); v = fields.pop("landed_as")
            et.pop("landed_as", None)
            if v is not None:
                et["landed_as"] = v
            w["external_target"] = et
        for k, v in fields.items():
            if v is None:
                w.pop(k, None)
            else:
                w[k] = v
        p.write_text(json.dumps(w, indent=2) + "\n")

    def new_record(self, wp):
        w = json.loads(self.record(WP18).read_text())
        w["id"] = wp; w["status"] = "IN_PROGRESS"; w.pop("landing_not_on_ledger", None)
        w["external_target"] = {k: v for k, v in w.get("external_target", {}).items() if k != "landed_as"}
        d = self.root / "work" / wp; d.mkdir()
        (d / "work-package.json").write_text(json.dumps(w, indent=2) + "\n")

    def lock(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env,
                       capture_output=True, check=True)

    def raw(self, *args, **env_over):
        env = dict(self.env); env.update(env_over)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", *args], cwd=self.root, env=env,
                              capture_output=True, text=True)

    def cmd(self, *args, **env_over):
        self.lock()   # every fixture edit is re-signed: only the rule under test decides
        return self.raw(*args, **env_over)


class LedgerRulesTests(LedgerScratch):

    def test_landed_but_silent_record_is_reported_not_hidden(self):
        self.set_record(WP18, status="IN_PROGRESS", landed_as=None)
        r = self.cmd("repo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("LANDED_UNRECONCILED", r.stdout)
        self.assertIn(WP18, r.stdout)

    def test_corroborated_claim_passes_with_nothing_to_report(self):
        self.set_record(WP18, status="CLOSED", landed_as=self.git("rev-parse", LANDED_18))
        r = self.cmd("repo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("LANDED_UNRECONCILED", r.stdout)

    def test_claimed_landing_not_on_the_ledger_is_refused(self):
        self.git("checkout", "-q", "-b", "side")
        (self.root / "side.txt").write_text("x\n"); self.git("add", "side.txt")
        self.git("commit", "-qm", "side\n\nWork-Package: BADF-WP-0018")
        self.set_record(WP18, status="CLOSED", landed_as=self.git("rev-parse", "HEAD"))
        r = self.cmd("repo")
        self.assertNotEqual(r.returncode, 0, "a landing that is not on origin/main was accepted")
        self.assertIn("not on the ledger", r.stderr)

    def test_claimed_landing_whose_commit_lacks_the_line_is_refused(self):
        self.set_record(WP18, status="CLOSED", landed_as=self.git("rev-parse", NOT_18))
        r = self.cmd("repo")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not carry", r.stderr)

    def test_claimed_landing_with_open_status_is_refused(self):
        self.set_record(WP18, status="IN_PROGRESS", landed_as=self.git("rev-parse", LANDED_18))
        r = self.cmd("repo")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("must be CLOSED", r.stderr)

    def test_closed_without_a_corroborated_landing_needs_a_stated_reason(self):
        self.set_record(WP18, status="CLOSED", landed_as=self.git("rev-parse", LANDED_18))   # keep 18 clean
        # WP-2026-9999: a sentinel the sequential ledger can never allocate (0099 was used until BADF-WP-0099 landed and collided).
        self.new_record("WP-2026-9999")
        self.set_record("WP-2026-9999", status="CLOSED", landing_not_on_ledger=None)
        r = self.cmd("repo")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("landing_not_on_ledger", r.stderr)
        self.set_record("WP-2026-9999", landing_not_on_ledger="withdrawn before any PR was opened")
        r = self.cmd("repo")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_landing_not_on_ledger_is_refused_when_the_ledger_shows_a_landing(self):
        self.set_record(WP18, status="CLOSED", landed_as=None, landing_not_on_ledger="withdrawn")
        r = self.cmd("repo")
        self.assertNotEqual(r.returncode, 0, "a false 'not on ledger' statement was accepted")
        self.assertIn("ledger shows", r.stderr)

    def test_new_record_while_a_landed_one_is_unreconciled_is_refused(self):
        self.set_record(WP18, status="IN_PROGRESS", landed_as=None)
        self.new_record("WP-2026-9999")
        r = self.cmd("repo")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("before opening a new one", r.stderr)
        self.assertIn(WP18, r.stderr)

    def test_new_record_after_reconciliation_is_admitted(self):
        self.set_record(WP18, status="CLOSED", landed_as=self.git("rev-parse", LANDED_18))
        self.new_record("WP-2026-9999")
        r = self.cmd("repo")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unreachable_ledger_is_refused_not_skipped(self):
        """`repo` cannot show this refusal: the monotonic guard needs origin/main
        too and runs first, so the ledger's own refusal is shadowed there.
        `reconcile` does not run the monotonic guard -- it is the CLI path on
        which the ledger must refuse by itself rather than proceed on nothing."""
        self.set_record(WP18, status="IN_PROGRESS", landed_as=None)
        self.git("remote", "remove", "origin")
        r = self.cmd("reconcile", WP18)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ledger cannot be established", r.stderr)
        self.assertEqual(json.loads(self.record(WP18).read_text())["status"], "IN_PROGRESS", "reconcile wrote on an unestablished ledger")


class ReconcileTests(LedgerScratch):

    def test_reconcile_writes_the_corroborated_claim(self):
        self.set_record(WP18, status="IN_PROGRESS", landed_as=None)
        r = self.cmd("reconcile", WP18)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        w = json.loads(self.record(WP18).read_text())
        self.assertEqual(w["status"], "CLOSED")
        self.assertEqual(w["external_target"]["landed_as"], self.git("rev-parse", LANDED_18))
        r = self.raw("repo")   # reconcile re-signed; nothing left to report
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("LANDED_UNRECONCILED", r.stdout)

    def test_reconcile_accepts_the_badf_wp_form(self):
        self.set_record(WP18, status="IN_PROGRESS", landed_as=None)
        r = self.cmd("reconcile", "BADF-WP-0018")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_reconcile_refuses_a_wp_the_ledger_does_not_show(self):
        self.new_record("WP-2026-9999")
        r = self.cmd("reconcile", "WP-2026-9999")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("has not landed", r.stderr)

    def test_reconcile_refuses_a_foreign_wp(self):
        r = self.cmd("reconcile", WP10)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not this repository", r.stderr)

    def test_reconcile_refuses_an_already_reconciled_wp(self):
        self.set_record(WP18, status="CLOSED", landed_as=self.git("rev-parse", LANDED_18))
        r = self.cmd("reconcile", WP18)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already", r.stderr)

    def test_reconcile_writes_the_record_and_the_lockfile_and_nothing_else(self):
        self.set_record(WP18, status="IN_PROGRESS", landed_as=None); self.lock()
        snap = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        r = self.raw("reconcile", WP18)
        self.assertEqual(r.returncode, 0, r.stderr)
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        changed = {p.relative_to(self.root).as_posix() for p in set(snap) | set(after) if snap.get(p) != after.get(p)}
        self.assertEqual(changed, {f"work/{WP18}/work-package.json", "badf/lockfile.json"})


if __name__ == "__main__":
    unittest.main()
