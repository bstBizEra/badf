"""Mandate section 6: a delivery must leave a replayable record of its run.

Measured before this existed: WP-2026-0010, BADF's first non-BADF delivery,
left a digest-bound RESULT (dossier + evidence) and NO record of the RUN.
A second session could not tell which steps happened, in what order, which
were retried (the diff artifact was rebuilt twice), or -- had the session
died after evidence and before the dossier -- what remained to do. The run
lived in a chat transcript.

The minimum durable artifact is a run LEDGER, not a workflow engine: an
append-only event history per work package, each event bound to the step,
its outcome, and the artifact digest it produced. Replay reconstructs
state from the ledger; it must never re-execute an effect whose receipt is
already recorded.

Ported from secb_pf's EVENT_ENVELOPE / EFFECT_REQUEST / replay standard,
not invented. Written to FAIL before the ledger existed.
"""
import json
import unittest

import scripts.badf_gate as gate

WP = gate.ROOT / "work/WP-2026-0010"


class RunLedgerExistsTests(unittest.TestCase):
    def test_wp_0010_has_a_run_ledger(self):
        ledger = WP / "run-ledger.jsonl"
        self.assertTrue(ledger.is_file(), "WP-2026-0010 records a result but no run")

    def test_ledger_is_append_only_events_bound_to_steps_and_digests(self):
        events = [json.loads(l) for l in (WP / "run-ledger.jsonl").read_text().splitlines() if l.strip()]
        self.assertGreater(len(events), 0)
        for e in events:
            for f in ("event_id", "workflow_id", "sequence", "step", "outcome", "recorded_at", "actor"):
                self.assertIn(f, e, f"event lacks {f}")
        seqs = [e["sequence"] for e in events]
        self.assertEqual(seqs, sorted(seqs), "sequence must be monotonic")
        self.assertEqual(len(seqs), len(set(seqs)), "sequence must be unique")

    def test_every_evidence_artifact_has_a_producing_event(self):
        """The result must be explained by the run: each artifact digest in the
        dossier's evidence appears as the output of some ledger event."""
        events = [json.loads(l) for l in (WP / "run-ledger.jsonl").read_text().splitlines() if l.strip()]
        produced = {e.get("output_digest") for e in events if e.get("output_digest")}
        for ev in (WP / "evidence/G07").glob("*.json"):
            digest = json.loads(ev.read_text())["digest"]
            self.assertIn(digest, produced, f"{ev.name}'s artifact {digest[:19]} has no producing event")

    def test_replay_reconstructs_state_without_reexecuting_effects(self):
        """gate.replay_run() returns the reconstructed state and the set of
        committed effects. Calling it twice must be pure: same state, no new
        events appended, no receipts re-issued."""
        before = (WP / "run-ledger.jsonl").read_bytes()
        s1 = gate.replay_run(WP)
        s2 = gate.replay_run(WP)
        self.assertEqual(s1, s2)
        self.assertEqual((WP / "run-ledger.jsonl").read_bytes(), before, "replay appended to the ledger")
        self.assertIn("committed_effects", s1)
        self.assertIn("current_step", s1)

    def test_a_committed_effect_is_not_reexecuted_on_resume(self):
        """Resume with a ledger that already records an effect's receipt:
        the effect must be SKIPPED, and the skip itself recorded."""
        state = gate.replay_run(WP)
        already = state["committed_effects"]
        self.assertGreater(len(already), 0)
        decision = gate.plan_next_effect(WP, list(already)[0])
        self.assertEqual(decision, "SKIP_ALREADY_COMMITTED")


if __name__ == "__main__":
    unittest.main()


class LedgerTamperTests(unittest.TestCase):
    """The chain, not the line, is the control. Every in-place edit must be
    refused -- including one that recomputes its own hash, because that
    breaks the NEXT event's previous_event_hash. And OUTCOME_UNKNOWN is never
    terminal: resume must reconcile it before scheduling anything."""

    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.mkdtemp()
        self.wp = __import__("pathlib").Path(self.tmp) / "WP-2026-0010"
        shutil.copytree(WP, self.wp)
        self.ledger = self.wp / gate.LEDGER_NAME
        self.orig = self.ledger.read_text()

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmp, ignore_errors=True)

    def mutate(self, fn):
        lines = self.orig.splitlines(); fn(lines)
        self.ledger.write_text("\n".join(lines) + "\n")

    def rewrite(self, lines, i, **fields):
        e = json.loads(lines[i]); e.update(fields)
        lines[i] = json.dumps(e, sort_keys=True, separators=(",", ":"))

    def test_rewritten_outcome_is_refused(self):
        self.mutate(lambda L: self.rewrite(L, 3, outcome="COMMITTED"))
        with self.assertRaisesRegex(gate.ValidationError, "event_hash does not match"):
            gate.read_ledger(self.wp)

    def test_swapped_digest_is_refused(self):
        self.mutate(lambda L: self.rewrite(L, 4, output_digest="sha256:" + "f" * 64))
        with self.assertRaisesRegex(gate.ValidationError, "event_hash does not match"):
            gate.read_ledger(self.wp)

    def test_deleted_event_is_refused(self):
        self.mutate(lambda L: L.__delitem__(3))
        with self.assertRaisesRegex(gate.ValidationError, "breaks the run"):
            gate.read_ledger(self.wp)

    def test_reordered_events_are_refused(self):
        def swap(L): L[5], L[6] = L[6], L[5]
        self.mutate(swap)
        with self.assertRaisesRegex(gate.ValidationError, "breaks the run"):
            gate.read_ledger(self.wp)

    def test_rewrite_with_recomputed_own_hash_breaks_the_chain(self):
        def f(L):
            e = json.loads(L[3]); e["outcome"] = "COMMITTED"; e["event_hash"] = gate._event_hash(e)
            L[3] = json.dumps(e, sort_keys=True, separators=(",", ":"))
        self.mutate(f)
        with self.assertRaisesRegex(gate.ValidationError, "hash chain broken"):
            gate.read_ledger(self.wp)

    def test_append_onto_tampered_ledger_is_refused_not_laundered(self):
        self.mutate(lambda L: self.rewrite(L, 3, outcome="COMMITTED"))
        with self.assertRaisesRegex(gate.ValidationError, "event_hash does not match"):
            gate.append_event(self.wp, "x", "OBSERVED", "t", "agent")

    # --- OUTCOME_UNKNOWN is never terminal ---------------------------------
    def test_unknown_outcome_must_be_reconciled_before_resume(self):
        gate.append_event(self.wp, "push-release", "OUTCOME_UNKNOWN", "t", "agent", effect_id="release-1")
        self.assertEqual(gate.plan_next_effect(self.wp, "release-1"), "RECONCILE_FIRST")
        self.assertIn("release-1", gate.replay_run(self.wp)["unresolved_effects"])

    def test_reconciled_effect_becomes_committed_and_is_then_skipped(self):
        gate.append_event(self.wp, "push-release", "OUTCOME_UNKNOWN", "t", "agent", effect_id="release-1")
        gate.append_event(self.wp, "push-release", "COMMITTED", "t", "agent", effect_id="release-1",
                          output_digest="sha256:" + "a" * 64, note="reconciliation found the effect")
        self.assertEqual(gate.plan_next_effect(self.wp, "release-1"), "SKIP_ALREADY_COMMITTED")
        self.assertEqual(gate.replay_run(self.wp)["unresolved_effects"], [])

    def test_proven_absent_effect_may_be_prepared_again(self):
        gate.append_event(self.wp, "push-release", "OUTCOME_UNKNOWN", "t", "agent", effect_id="release-1")
        gate.append_event(self.wp, "push-release", "PROVEN_ABSENT", "t", "agent", effect_id="release-1",
                          note="reconciliation proved absence")
        self.assertEqual(gate.plan_next_effect(self.wp, "release-1"), "PREPARE")

    def test_invalid_outcome_is_refused_on_append(self):
        with self.assertRaisesRegex(gate.ValidationError, "invalid outcome"):
            gate.append_event(self.wp, "x", "DONE", "t", "agent")

    def test_invalid_actor_type_is_refused_on_append(self):
        with self.assertRaisesRegex(gate.ValidationError, "invalid actor type"):
            gate.append_event(self.wp, "x", "OBSERVED", "t", "robot")
