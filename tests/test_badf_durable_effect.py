"""AET-B-2 (#294, WP-2026-0132): the durable-effect record, red-first.

AET-I05 says an ambiguous state-changing operation is never blindly retried, and the
ledger's outcome vocabulary is a MEMBERSHIP check at both consumers -- never a state
machine. Probed on main before this WP: an effect recorded PREPARED -> COMMITTED ->
PREPARED -> COMMITTED is ADMITTED, and replay_run then reports it as one clean commit
with nothing unresolved. A durable external effect executed twice, invisible.

That is #290's defect one layer down -- a vocabulary constraining values but not
transitions -- so the remedy is inherited rather than re-derived: the rule lives at ONE
authoritative site that both the append path and the read/replay path consume, and the
proof is PER-CONSUMER mutation discrimination, because a batch run cannot distinguish a
shared refusal from two independent ones.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

EFFECT = "EFF-PROBE-1"
DIGEST = "sha256:" + "a" * 64


class _Ledger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wp = Path(self.tmp) / "WP-2026-9995"
        self.wp.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def append(self, outcome, effect_id=EFFECT, step="commit", digest=None):
        return gate.append_event(self.wp, step, outcome, "SARCHI", "agent",
                                 effect_id=effect_id,
                                 output_digest=digest if digest is not None else DIGEST)

    def authorize(self, effect_id=EFFECT):
        """The contract's second phase, recorded. Under the #294 ratchet a COMMITTED
        effect must carry this witness, so every legal fixture below performs it --
        the tests exercise the real four-phase protocol rather than a shortcut."""
        return self.append("AUTHORITY_CHECKED", effect_id=effect_id, step="authority")

    def append_raw(self, **over):
        """Write an event straight to the file, bypassing append_event, so the READ
        path is exercised on a chain the append path would have refused. Without this
        the two consumers cannot be told apart (the #290 site-discrimination lesson)."""
        events = []
        path = self.wp / gate.LEDGER_NAME
        if path.is_file():
            events = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        seq = len(events) + 1
        ev = {"event_id": f"EVT-{self.wp.name}-{seq:04d}", "workflow_id": self.wp.name,
              "sequence": seq, "step": "commit", "outcome": "PREPARED",
              "actor": {"id": "SARCHI", "type": "agent"},
              "recorded_at": "2026-09-01T00:00:00Z", "effect_id": EFFECT,
              "output_digest": DIGEST, "provenance": "RECORDED_AT_EVENT_TIME",
              "previous_event_hash": events[-1]["event_hash"] if events else gate.GENESIS_HASH}
        ev.update(over)
        ev["event_hash"] = gate._event_hash(ev)
        with path.open("a", encoding="utf-8") as h:
            h.write(json.dumps(ev, sort_keys=True, separators=(",", ":")) + "\n")
        return ev


class TerminalOutcomesAreTerminal(_Ledger):
    def test_a_committed_effect_cannot_be_re_prepared_on_the_append_path(self):
        """The probed hole: PREPARED -> COMMITTED -> PREPARED was admitted, which is a
        durable external effect being scheduled a second time."""
        self.append("PREPARED"); self.authorize(); self.append("COMMITTED")
        with self.assertRaises(gate.ValidationError) as cm:
            self.append("PREPARED")
        self.assertIn(EFFECT, str(cm.exception))
        self.assertIn("established", str(cm.exception).lower())

    def test_a_committed_effect_cannot_be_re_committed_on_the_append_path(self):
        self.append("PREPARED"); self.authorize(); self.append("COMMITTED")
        with self.assertRaises(gate.ValidationError) as cm:
            self.append("COMMITTED")
        self.assertIn("established", str(cm.exception).lower())

    def test_the_read_path_refuses_a_chain_the_append_path_would_have(self):
        """Per-consumer inheritance: a ledger written around append_event (edited by
        hand, restored from a backup, produced by an older writer) must still be
        refused when READ. assert on the read path specifically -- append is not
        the only way a ledger comes into being."""
        self.append_raw(outcome="PREPARED")
        self.append_raw(outcome="AUTHORITY_CHECKED")
        self.append_raw(outcome="COMMITTED")
        self.append_raw(outcome="PREPARED")     # the illegal transition, written raw
        with self.assertRaises(gate.ValidationError) as cm:
            gate.read_ledger(self.wp)
        self.assertIn("established", str(cm.exception).lower())

    def test_replay_does_not_report_a_twice_executed_effect_as_one_clean_commit(self):
        """The consequence the rule exists to prevent, asserted on the OUTPUT rather
        than on the refusal: replay_run reported committed=[EFF] / unresolved=[] over
        a double execution. With the chain refused, replay cannot report it at all."""
        self.append_raw(outcome="PREPARED")
        self.append_raw(outcome="AUTHORITY_CHECKED")
        self.append_raw(outcome="COMMITTED")
        self.append_raw(outcome="PREPARED")
        self.append_raw(outcome="COMMITTED")
        with self.assertRaises(gate.ValidationError):
            gate.replay_run(self.wp)

    def test_a_terminal_but_unestablished_outcome_may_still_be_prepared_again(self):
        """The distinction the ledger's OWN tests already encoded and my first rule
        overrode: PROVEN_ABSENT is TERMINAL but not ESTABLISHED -- proving an effect did
        not happen is proof it is safe to retry. A rule keyed on TERMINAL_OUTCOMES
        forbade a retry the protocol requires (test_proven_absent_effect_may_be_prepared
        _again). Terminal means this attempt concluded; established means the world
        changed."""
        self.append("PREPARED")
        self.append("OUTCOME_UNKNOWN")
        self.append("PROVEN_ABSENT")
        ev = self.append("PREPARED")
        self.assertEqual(ev["outcome"], "PREPARED")
        self.assertEqual(gate.plan_next_effect(self.wp, EFFECT), "PREPARE")

    def test_compensation_may_follow_an_established_effect(self):
        """Positive control on the allowed set: an effect that really happened may be
        recorded as undone or escalated -- a rule that sealed the effect entirely would
        make compensation unrecordable, which is worse than the hole it closes."""
        self.append("PREPARED"); self.authorize(); self.append("COMMITTED")
        # Vacuity guard: this test derives its cases from the constant under test, so an
        # empty set would make the loop pass like a full one -- the #290 enumeration-
        # vacuity class, reproduced in the instrument for the rule that inherits it.
        # Pin the members the protocol REQUIRES, then walk whatever the constant holds.
        self.assertLessEqual({"COMPENSATED", "MANUAL_REMEDIATION"}, gate.AFTER_ESTABLISHED_ALLOWED,
                             "an established effect must remain compensable and escalable")
        for allowed in sorted(gate.AFTER_ESTABLISHED_ALLOWED):
            with self.subTest(allowed=allowed):
                tmp = Path(tempfile.mkdtemp()); wp = tmp / "WP-2026-9995"; wp.mkdir()
                try:
                    gate.append_event(wp, "p", "PREPARED", "S", "agent", effect_id=EFFECT, output_digest=DIGEST)
                    gate.append_event(wp, "a", "AUTHORITY_CHECKED", "S", "agent", effect_id=EFFECT, output_digest=DIGEST)
                    gate.append_event(wp, "c", "COMMITTED", "S", "agent", effect_id=EFFECT, output_digest=DIGEST)
                    ev = gate.append_event(wp, "x", allowed, "S", "agent", effect_id=EFFECT, output_digest=DIGEST)
                    self.assertEqual(ev["outcome"], allowed)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_every_established_outcome_seals_re_execution_walking_the_declared_set(self):
        """The closed set walked WHOLE from the declared constant -- EFFECT_ESTABLISHED
        read live, so a member added later is covered without editing this test."""
        # Same vacuity guard as the sibling at the top of this class, applied here after
        # QA measured the gap (#298 review): reading the constant live covers members
        # ADDED later, and silently loses coverage for members REMOVED. Dropping
        # SKIPPED_ALREADY_COMMITTED -- the idempotency outcome itself -- survived the
        # whole module. Pin what the protocol requires, then walk whatever it holds.
        self.assertLessEqual({"COMMITTED", "SKIPPED_ALREADY_COMMITTED"}, gate.EFFECT_ESTABLISHED,
                             "an established effect must stay sealed against re-execution")
        for terminal in sorted(gate.EFFECT_ESTABLISHED):
            with self.subTest(terminal=terminal):
                tmp = Path(tempfile.mkdtemp()); wp = tmp / "WP-2026-9994"; wp.mkdir()
                try:
                    gate.append_event(wp, "commit", "PREPARED", "SARCHI", "agent",
                                      effect_id=EFFECT, output_digest=DIGEST)
                    gate.append_event(wp, "authority", "AUTHORITY_CHECKED", "SARCHI", "agent",
                                      effect_id=EFFECT, output_digest=DIGEST)
                    gate.append_event(wp, "commit", terminal, "SARCHI", "agent",
                                      effect_id=EFFECT, output_digest=DIGEST)
                    with self.assertRaises(gate.ValidationError):
                        gate.append_event(wp, "commit", "PREPARED", "SARCHI", "agent",
                                          effect_id=EFFECT, output_digest=DIGEST)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)

    def test_a_non_terminal_outcome_still_accepts_a_successor(self):
        """Positive control: the rule refuses transitions OUT OF terminal states only.
        OUTCOME_UNKNOWN is explicitly non-terminal (resume must reconcile it), so a
        successor after it stays legal -- a rule that refused everything would pass
        every test above while breaking the protocol."""
        self.append("PREPARED")
        self.authorize()
        self.append("OUTCOME_UNKNOWN")
        ev = self.append("COMMITTED")
        self.assertEqual(ev["outcome"], "COMMITTED")
        self.assertEqual(gate.replay_run(self.wp)["unresolved_effects"], [])

    def test_a_different_effect_is_unaffected_by_another_effects_terminal_state(self):
        """Positive control on the scoping: the rule is per-effect_id. A committed
        EFF-1 must not freeze the whole ledger."""
        self.append("PREPARED", effect_id="EFF-1"); self.authorize("EFF-1")
        self.append("COMMITTED", effect_id="EFF-1")
        ev = self.append("PREPARED", effect_id="EFF-2")
        self.assertEqual(ev["outcome"], "PREPARED")

    def test_events_without_an_effect_id_are_unaffected(self):
        """Positive control: workflow-step events carry no effect_id and must keep
        flowing -- the rule governs durable EFFECTS, not the run's own steps."""
        gate.append_event(self.wp, "plan", "OBSERVED", "SARCHI", "agent")
        gate.append_event(self.wp, "plan", "OBSERVED", "SARCHI", "agent")
        self.assertEqual(len(gate.read_ledger(self.wp)), 2)


class TheEventRecordIsClosed(_Ledger):
    def test_an_undeclared_key_on_a_ledger_event_is_refused(self):
        """Probed on main: an event carrying 'granted_authority' was ADMITTED --
        run-ledger-event.schema.json declares no additionalProperties. The walker
        DOES enforce additionalProperties (measured live on seats.schema.json in
        #290), so the declaration is load-bearing here, not decorative."""
        self.append("PREPARED")
        ev = dict(gate.read_ledger(self.wp)[0])
        ev["granted_authority"] = "unlimited"
        with self.assertRaises(gate.ValidationError):
            gate.check_schema("run-ledger-event", ev)

    def test_a_declared_event_still_validates(self):
        """Negative control for the closure: the real shape must stay admissible."""
        self.append("PREPARED")
        gate.check_schema("run-ledger-event", gate.read_ledger(self.wp)[0])


class TheAuthorityCheckIsWitnessed(_Ledger):
    """Gap 3: the contract's four phases are PREPARE -> AUTHORITY CHECK -> COMMIT ->
    RECONCILE, but no vocabulary recorded that the check RAN, and REJECTED is ambiguous
    about which phase rejected on whose authority. A phase that leaves no trace cannot
    be shown to have happened -- and it is invisible to any test that walks only the
    vocabulary that exists, which is why the adversarial clause was pointed here.

    Mandatory from this WP's own id forward, grandfathered below it, sentinels exempt --
    the surface/seat ratchet shape reused rather than a new mechanism invented.
    """
    def wp_at(self, wp_id):
        d = Path(self.tmp) / wp_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_committing_without_an_authority_check_is_refused_at_and_above_threshold(self):
        wp = self.wp_at("WP-2026-9995")
        gate.append_event(wp, "prepare", "PREPARED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        with self.assertRaises(gate.ValidationError) as cm:
            gate.append_event(wp, "commit", "COMMITTED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        msg = str(cm.exception)
        self.assertIn("authority", msg.lower())
        self.assertIn(EFFECT, msg)

    def test_an_authority_checked_event_admits_the_commit(self):
        """Positive control: the rule demands a witness, it does not forbid committing."""
        wp = self.wp_at("WP-2026-9995")
        gate.append_event(wp, "prepare", "PREPARED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        gate.append_event(wp, "authority", "AUTHORITY_CHECKED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        ev = gate.append_event(wp, "commit", "COMMITTED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        self.assertEqual(ev["outcome"], "COMMITTED")

    def test_the_witness_is_per_effect_not_per_run(self):
        """A check for one effect must not authorize a different one -- otherwise the
        witness is satisfied by something adjacent to the thing under test."""
        wp = self.wp_at("WP-2026-9995")
        gate.append_event(wp, "authority", "AUTHORITY_CHECKED", "SARCHI", "agent", effect_id="EFF-1", output_digest=DIGEST)
        with self.assertRaises(gate.ValidationError):
            gate.append_event(wp, "commit", "COMMITTED", "SARCHI", "agent", effect_id="EFF-2", output_digest=DIGEST)

    def test_a_grandfathered_work_package_is_not_refused(self):
        wp = self.wp_at("WP-2026-0100")
        gate.append_event(wp, "prepare", "PREPARED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        ev = gate.append_event(wp, "commit", "COMMITTED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        self.assertEqual(ev["outcome"], "COMMITTED")

    def test_the_sentinel_is_exempt(self):
        wp = self.wp_at("WP-2026-9999")
        gate.append_event(wp, "prepare", "PREPARED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        ev = gate.append_event(wp, "commit", "COMMITTED", "SARCHI", "agent", effect_id=EFFECT, output_digest=DIGEST)
        self.assertEqual(ev["outcome"], "COMMITTED")

    def test_the_read_path_inherits_the_witness_rule(self):
        """Per-consumer inheritance again: a chain written around append_event is
        refused when READ."""
        wp = self.wp_at("WP-2026-9995")
        self.wp = wp
        self.append_raw(outcome="PREPARED")
        self.append_raw(outcome="COMMITTED")
        with self.assertRaises(gate.ValidationError) as cm:
            gate.read_ledger(wp)
        self.assertIn("authority", str(cm.exception).lower())


class TheAdversarialCase(_Ledger):
    def test_a_sequence_outside_the_declared_table_is_refused_or_declared(self):
        """#270, pointed where a walk of the existing vocabulary is blind: a
        COMMITTED effect that later reports PROVEN_ABSENT is not in any table, is not
        obviously illegal (a reconciler might genuinely discover the effect absent),
        and is a contradiction the record must not simply absorb. Whichever way the
        rule falls it must be STATED -- refused here, because two terminal outcomes
        for one effect assert two different facts about the world."""
        self.append("PREPARED"); self.authorize(); self.append("COMMITTED")
        with self.assertRaises(gate.ValidationError) as cm:
            self.append("PROVEN_ABSENT")
        msg = str(cm.exception).lower()
        self.assertIn("established", msg)


if __name__ == "__main__":
    unittest.main()
