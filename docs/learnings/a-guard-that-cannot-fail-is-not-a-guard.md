# A guard that cannot fail is not a guard

From `BADF-DEM-0087` / `0090` / `0092` / `0093` / `0095` — the `badf-engineering-verification`
ladder, Issues #195 / #200 / #204 / #207 / #214 (**RESOLVED**).

The G08 ladder shipped five rungs, each failing-first and mutation-killed, and its own controls
refused every defect injected at them. The defects that actually got through were of one kind, and
it was never the thing under test — it was the **check**:

- **Dead assertions.** Two `assertEqual([], entry["allowed_tools"])` calls were spliced into
  end-of-line comments by rung-flip edits (`stmt1;` replaced with `stmt  # comment`, leaving
  `stmt2; stmt3` after the `#`). Both suites stayed green — a dead assertion fails nothing. Found by
  BADF-QA/BADF-REV on PR #208, not by CI, which cannot distinguish an assertion that passes from one
  that does not run. A third site was filed as #210.
- **A masked exit code.** `git apply -3 patch | head -5` discarded a *total* apply failure: the
  pipeline's status is the last command's, so the chain "succeeded" against an unchanged tree.
- **A stale claim bound before the thing it claimed.** `badf_compose.py --record` was run before the
  content commit, so the composition record bound a tree that no longer existed by push time.
- **A pin that guards a different property than assumed.** `references/acceptance.md` is the one
  reference the contract test never content-asserted; the architecture family has a stale-status guard
  for exactly this file and this family does not (#216). It **is** integrity-locked — measured:
  `badf/lockfile.json` holds 1316 digests, 134 under `skills/`, 18 for this capability including
  `acceptance.md`, re-signed by this very PR — so the lockfile catches an *unrecorded* edit but cannot
  catch an *authorized* edit that introduces a stale claim. Two different guarantees; only one was in
  place.
- **A guard concentrated to a single point.** Each rung relaxed the previous rung's exact status
  assertion to a floor and moved exactness forward — correct, but it leaves exactly one exact pin
  alive; relaxing that one unpins status entirely (#218).
- **A watch that matched an adjacent thing.** A verdict monitor grepping for the reviewer's seat name
  fired on a *different* seat's comment that merely mentioned it.

- **A claim repeated without measuring it.** The first draft of *this file* asserted that `skills/` was
  absent from the lockfile — "0 of 27" — carried over from a peer's supporting premise and never run.
  BADF-REV measured it and it was false (1316 digests, 134 under `skills/`). An institutional learning
  about unverified checks came within one review of shipping an unverified claim.
- **A wrong-tree measurement producing a confident false negative about a guard.** BADF-REV's first
  attempt to reproduce the `verify_demand_learnings` red measured against `ce3c458`, where `DEM-0087` is
  still `AUTHORIZED` and correctly needs no learning — so the guard "did not fire", and the reviewer
  nearly filed that as a finding. Caught by printing the tree and the record's status before writing it
  up. The reviewer of this document is not exempt from its subject either: the count is six, not five.
- **A guard that is correct and never reached.** `verify_demand_learnings` is real, wired into `repo`,
  and has fired — yet, **measured on `8de88d5`, 87 of 91 demand records sat non-terminal with all 86
  issue-linked sources CLOSED**, so the requirement examined four records while green CI attested
  compliance over the rest. Nothing is broken; the precondition is simply never met (#220). *That count
  is pinned to a revision on purpose: it is a live number, it has already moved (89 of 93 by the time
  this file was reviewed), and an unqualified count in an extend-only directory would be this file
  committing the very defect it describes — a proxy standing in for a property. Caught by BADF-QA in
  review of this file.*
- **A check that flags working code.** BADF-REV's own acceptance criterion on #210 would have matched
  correct lines; their first AST-based replacement then produced a second false positive. Struck and
  corrected on the issue.
- **A silent fallback that manufactures a plausible wrong answer.** `d.get('files', d)` and
  `d['paths'] if isinstance(d.get('paths'), dict) else d` — two seats, same hour, same false zero, both
  while measuring the same ledger. The expected key was `digests`; neither lookup said so.

**Learned:** these are one defect class — *the check matched something adjacent to the thing it was
meant to check, could not fail at all, or guarded a different property than the one assumed*. Green is
not evidence that a guard ran; it is evidence that nothing which ran failed. The two are different
claims, and only the second is measured. The class extends to prose: a premise inherited from a
trusted peer is still an unmeasured claim until you run it yourself.

**Changed, concretely:**

- An anchor that appends a `#` comment must consume the **whole line**. To *detect* the failure, use the
  corrected criterion on #210 — AST-based, with string-literal masking and an asserted positive control —
  **not** a grep for `#` followed by `self.assert`. That grep is itself an instance of this defect class:
  it matches the `#` character wherever it occurs, including inside a string literal, so at `ce3c458` it
  fires on `tests/test_badf_build_activation.py:52`, where `text.find("## badf-build → ACTIVE")` precedes
  a live `self.assertGreater` in a module that passes 4/4. The character is a proxy; "this assertion does
  not execute" is the property.

  *This correction was caught by BADF-REV in review of this very file, which had listed that grep as a
  finding and then prescribed it as the remedy two paragraphs later. Recorded rather than quietly fixed:
  a document whose thesis is "the check matched a proxy" shipping the proxy-check as its cure is the most
  instructive failure in it.*
- A guard's exit status is read **unpiped** — capture to a file, then grep — because a pipe discards it.
- Bind order is fixed: content commit → `compose --record` → `self-dossier` → chore commit →
  re-compose must print `PASS` → only then push. Verify against the **pushed** tree, not the intended one.
- A verdict or state watch matches on the **author** plus the head plus the token, never on a name
  appearing anywhere in a body.
- Where exactness is *moved* rather than dropped (the floor pattern), something must assert that at
  least one exact pin still exists — #218.
- Before repeating a peer's structural claim — especially one that widens a finding — **run it**. Cite
  the measurement, not the source.

**The generalization, stated by BADF-REV and load-bearing here.** Every one of these was a check
pointed at a **proxy** for its property rather than at the property — a character (`#`), a name
(a seat's banner in any body), a dict key (`files`, `paths`), a line, a status field, a pipeline's
last exit code. A proxy can occur without the property holding, and the property can hold without the
proxy occurring; the guard cannot tell the difference, and neither can a green run. Two mitigations
would have caught all of them:

1. **Assert the property directly.** Not "the comment character is absent" but "the assertion executes";
   not "a name appears in a body" but "this author posted it about this head"; not "the key is present"
   but "the container holds the members I claim to be counting".
2. **Give every guard a positive control that has actually been seen to fail.** A guard never observed
   red is not evidence — it is an untested claim wearing a test's clothes. Every mutation battery in
   this ladder exists for that reason, and every defect above was in something that had no such control.

**Whose defects these were.** All four seats, in one evening — six instances, the last two found *during the review of this file*: the author's spliced assertions and
repeated unmeasured claim; BADF-QA's false zero and two struck premises; BADF-REV's #210 criterion and
its AST replacement; and the shared-ledger measurement both QA and the author got wrong independently.
No seat was exempt, and that is the finding — this is not a property of one agent's care but of the
shape itself. A record listing only its author's mistakes would be a confession; this one is a
description.

**Not changed:** none of this is mechanically enforced by the gate today, and #210 / #216 / #218 / #220
are the open proposals to make parts of it structural. Until they land, the discipline is the control —
and the reason the ladder's defects were caught at all is that independent seats measured the tree
instead of reading the diff. Every single one was found by measurement, none by CI: a green run is
evidence that nothing which ran failed, never that the intended check ran at all.
