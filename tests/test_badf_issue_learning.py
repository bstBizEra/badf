"""Resolved Issues become institutional learning (BADF-WP-0035, Issue #29).

The doctrine: "Every resolved Issue becomes potential institutional learning."
A demand that reached a terminal status (RESOLVED or REJECTED) must carry a
`learning` -- a docs/learnings/<slug>.md path that exists, or the literal
NONE_DECLARED. `badf_gate.py repo` refuses a terminal demand with neither.
Each test injects its defect into a backup-restored demand and re-signs, so
only the learning check decides.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

DEMANDS = gate.ROOT / "badf/demands"
GUARDED = sorted(DEMANDS.glob("*.json")) + [gate.ROOT / gate.LOCKFILE]


class IssueLearningTests(unittest.TestCase):
    def setUp(self):
        self.backup = tempfile.mkdtemp()
        for p in GUARDED:
            dst = Path(self.backup) / p.relative_to(gate.ROOT); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dst)

    def tearDown(self):
        for p in GUARDED:
            shutil.copy2(Path(self.backup) / p.relative_to(gate.ROOT), p)
        shutil.rmtree(self.backup, ignore_errors=True)

    def edit(self, demand_id, fn):
        p = DEMANDS / f"{demand_id}.json"; d = json.loads(p.read_text()); fn(d); p.write_text(json.dumps(d, indent=2) + "\n")
        gate.write_lock(gate.ROOT, gate.INTEGRITY_PATHS)   # re-signed: only the learning check may refuse

    def refused(self, needle):
        with self.assertRaisesRegex(gate.ValidationError, needle):
            gate.validate_repo()

    def test_clean_repo_passes(self):
        gate.validate_repo()

    def _terminal(self):
        """The demands this module's central assertion is about."""
        return [json.loads(p.read_text()) for p in sorted(DEMANDS.glob("*.json"))
                if json.loads(p.read_text())["status"] in gate.DEMAND_TERMINAL]

    def test_the_learning_check_is_not_vacuous_when_no_demand_is_terminal(self):
        """#234: every assertion below sits behind a `status in TERMINAL` filter, so a ledger
        with ZERO terminal demands passed while examining nothing -- "no terminal demands" was
        indistinguishable from "all terminal demands are correct".

        The floor is deliberately >= 1 and NOT pinned to today's count. #234 asks for a floor
        justified against the ledger rather than guessed, and any specific number is a guess
        about a moving population: it was 4 when the issue was filed, is 9 now (post-#224), and
        #220 would take it to ~88 in one landing. A pin would then fail for being RIGHT about
        an improvement. >= 1 is the exact property that was missing -- that the filter matched
        something -- and it is the only floor that stays true across #220.
        """
        terminal = self._terminal()
        self.assertGreaterEqual(
            len(terminal), 1,
            "no demand is terminal, so test_every_terminal_demand_carries_a_valid_learning "
            "would pass having asserted nothing; the learning discipline could have collapsed "
            "entirely and both this test and gate.verify_demand_learnings would stay green")

    def test_every_terminal_demand_carries_a_valid_learning(self):
        self.assertGreaterEqual(len(self._terminal()), 1, "filter matched nothing; see #234")
        for p in DEMANDS.glob("*.json"):
            d = json.loads(p.read_text())
            if d["status"] in ("RESOLVED", "REJECTED"):
                with self.subTest(demand=d["demand_id"]):
                    lv = d.get("learning")
                    self.assertTrue(isinstance(lv, str) and gate.LEARNING_FORM.match(lv), f"{d['demand_id']} has no learning")
                    if lv != "NONE_DECLARED":
                        self.assertTrue((gate.ROOT / lv).is_file(), lv)

    def test_a_resolved_demand_without_learning_is_refused(self):
        self.edit("BADF-DEM-0004", lambda d: d.pop("learning", None))
        self.refused("BADF-DEM-0004.*declares no learning")

    def test_a_rejected_demand_without_learning_is_refused(self):
        self.edit("BADF-DEM-0013", lambda d: d.pop("learning", None))
        self.refused("BADF-DEM-0013.*declares no learning")

    def test_none_declared_is_accepted(self):
        self.edit("BADF-DEM-0004", lambda d: d.update(learning="NONE_DECLARED"))
        gate.validate_repo()   # explicit "nothing learned" is a claim, not drift

    def test_a_learning_path_that_does_not_exist_is_refused(self):
        self.edit("BADF-DEM-0004", lambda d: d.update(learning="docs/learnings/no-such-file.md"))
        self.refused("BADF-DEM-0004.*does not exist")

    def test_a_malformed_learning_is_refused(self):
        self.edit("BADF-DEM-0004", lambda d: d.update(learning="see the wiki"))
        self.refused("BADF-DEM-0004.*malformed")

    def test_an_authorized_demand_needs_no_learning(self):
        # DEM-0021 (#27) is AUTHORIZED; removing any learning it lacks must not refuse
        self.edit("BADF-DEM-0021", lambda d: d.pop("learning", None))
        gate.validate_repo()

    def test_a_malformed_learning_on_a_non_terminal_demand_is_still_refused(self):
        self.edit("BADF-DEM-0021", lambda d: d.update(learning="whatever"))
        self.refused("BADF-DEM-0021.*malformed")


if __name__ == "__main__":
    unittest.main()
