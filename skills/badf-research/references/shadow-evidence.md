# Shadow evidence (`BADF-WP-0055`, Issue #101)

Before `APPROVED`/`ACTIVE`, the `badf-research` contract is run retrospectively on **real historical
BADF cases**, framed as if the answer were unknown, and measured: would the contract have surfaced the
correct uncertainty, evidence, contradiction and decision boundary? This is stronger than the synthetic
examples because the cases actually happened and their outcomes are known independently.

Three shadow records, each a distinct research type exercising a distinct part of the contract, all
gate-valid under the 26 controls:

| Record | Type | Real case | What the contract had to represent | Outcome |
| :--- | :--- | :--- | :--- | :--- |
| `research-record-shadow-control15.json` | R02 (repository-investigation) | The control-15 mistracking this session — was it enforced or only documented? | A repository investigation binding a claim to `scripts/badf_gate.py` at a pinned revision (`e7ea929`), control 3 baseline resolution | Faithful. A blind R02 finds the `# 15:` check in code → `RESEARCH_SUFFICIENT`, correcting the doc. Confidence **MODERATE** (1 primary, reproducible), derived not asserted. |
| `research-record-shadow-composed-red.json` | R03 (root-cause) | WP-0019 turned `main` red at `30186c5` after a green PR | Hypothesis elimination bound to a commit; the `BRANCH_GREEN != MERGE_SAFE` mechanism | Faithful. One hypothesis retained (pre-merge ledger), one eliminated (flake) → root cause. Confidence **VERY_HIGH** (2 primary, reproducible, 0 contradictions). |
| `research-record-shadow-ci-parity.json` | R10 (fact-verification) | Does a green local run prove a green CI run? (#57 PyYAML) | A **FALSIFIED** inferred claim with a **preserved contradiction** (controls 21 + 8) | Faithful. The claim is `FALSIFIED` by a primary contradicting CI outcome; the contradiction is recorded, not buried. Confidence **VERY_LOW** (0 supporting primary). |

## Measurement

The contract represented all three cases without distortion: the derived confidence matched each
evidence basis (control 9), the repository baselines resolved (control 3), the falsification carried
its contradiction (controls 21, 8), every finding was grounded (control 22), and each sufficient
disposition rested on synthesised findings (control 26) while granting no implementation authority
(RSR-I01). **No contract gap surfaced under real conditions** in these three cases.

This is the `SHADOWED` evidence. It does not itself advance the family's registry status — that is the
operator's admission decision (`DESIGNED -> IMPLEMENTED -> VALIDATED -> SHADOWED -> APPROVED -> ACTIVE`),
now backed by shadow data rather than synthetic examples alone.
