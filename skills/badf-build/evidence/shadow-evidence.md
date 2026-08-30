# Shadow evidence (`BADF-WP-0101`, Issue #197 / GOV-0084)

**What is real and what is only declared — first sentence, as the contract requires.** Every case below is
real BADF history — the program's own builds, judged by the tools it built — recomputed from the object
store by `tests/test_badf_build_shadow.py` on every run; the controls history could **not** exercise
(C3, C4, C6, C7 — nothing on the ledger ever declared the fields they judge) are listed under non-coverage,
not implied to have passed.

`badf-build` shadows on the one corpus BADF has: **67 landed work packages carrying a G07 self-dossier**
(WP-2026-0011 … WP-2026-0100), measured at `8f3d805`. It is recorded once, in
`examples/build-shadow-evidence.json`, and re-derived on every CI run and inside every composed tree.

## Measurement

| Case class | Real history | What the contract had to represent | Outcome |
| :--- | :--- | :--- | :--- |
| `request-digest-bound` (67) | every evidence object every landed dossier indexes | BLD-B / BLD-I16: a request cannot point at nothing — each artifact's digest recomputes at the landed tree | **67/67 `BOUND`**, 0 mismatches |
| `authority-replayed` (67) | each work package's demand as recorded on `main` | C1 / BLD-I03: `AUTHORIZED` by a **human** | **67/67 `AUTHORIZED_HUMAN`** |
| `typed-binding-recomputed` (3) | every dossier produced by the BLD-B producer (WP-2026-0098, WP-2026-0099, WP-2026-0100 — the last is VER-A's, produced under the same producer) | BLD-I02 / C2: the bound content tree equals the landed content tree | **3/3 `MATCH`** |
| `fresh-verification-replayed` (67) | each dossier's unit-test outcome against its composition record | C5 / BLD-I09: a `PASS` needs the composed-tree run | 55 `NOT_RUN_DEFERRED`, 10 `NOT_RUN_DEFERRED_WITH_RECORD`, 2 `PASS_WITH_RECORD`, **0 `PASS_WITHOUT_RECORD`** |
| `dossier-not-on-ledger` (1) | WP-2026-0010 — a G07 dossier from before the ledger's identity window | the ledger is the landing authority; a dossier it cannot place is declared, not counted | `NOT_LANDED` (declared) |
| runner citations (3 runs) | CI runs 33301968905, 33319882660, 33325111196 (PRs #190, #193, #196) | BLD-A…C on real infrastructure: detached checkout, `repo` PASS validating typed dossiers, composed-tree verification | detached · `repo` PASS · `BADF COMPOSE PASS` |

**Result: no contract gap surfaced under real conditions.** 67 builds, every request digest-bound,
every demand human-authorized, every typed binding exact, and no unit-test `PASS` ever claimed without the
composed-tree run behind it — history already obeyed the controls the gate now enforces.

## Non-coverage (named, not implied)

- **C3 scope containment** — no landed work package declared `expected_surfaces`; the planned-vs-actual
  comparison and the `discovery_allowance` path are proven by `tests/test_badf_build_controls.py` and
  `test_badf_build_evidence.py` on scratch fixtures only.
- **C4 red before green / explicit exception** — no landed work package declared `test_obligations`; red
  observations exist on the ledger only from WP-2026-0098 on (`failing-first.txt`), and no `tdd_exception`
  was ever declared. Scratch-proven only.
- **C6 budget and stop** — one build ledger existed at measurement (WP-2026-0098), with no `RETRY` and no
  `STOP` event; exhaustion and stop dominance are scratch-proven only.
- **C7 delegation subset** — no `build/session.json` on the ledger carries `delegations`; scratch-proven only.
- **WP-2026-0010** — its G07 dossier predates the ledger's identity window and cannot be placed on a landing.
- **Runner-side controls on a real build controller** — no agent has yet executed a Work Package through
  `badf-build`'s workflow (CLAIM → … → HANDOFF); the shadow judges the *evidence* BADF's self-dossiers
  produced, not a controller's run. The first real project (or the first build executed under the
  contract) is where C3/C4/C6/C7 meet real conditions.

## Why the root is `SHADOWED`, not `ACTIVE`

`badf-build` is a declarative router whose implementation is the typed G07 evidence producer and the
seven controls in `badf_gate.py` (BLD-B, BLD-C) and their failing-first and mutation suites; its shadow is
this record. Advancing the family is the **operator's admission decision** — pre-authorized for the ladder
on #188, still taken on evidence at **BLD-E** — and the admission must carry the non-coverage above
verbatim: `ACTIVE` will mean "admitted on sixty-five self-builds, with four controls proven only on
scratch", not more. Nothing in this shadow affects a gate: no registry status change beyond `SHADOWED`,
no lifecycle change, no new control.
