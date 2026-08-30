# G08 contract — what engineering verification proves

G08 ("Engineering verification") requires four evidence types in `badf/lifecycle.json`:
`independent-review`, `integration-test`, `contract-test`, `composed-tree-test`. Owner role:
`quality_authority`. Minimum change class C1. Exit criteria: review blockers resolved · integration
and contract checks pass · composed result verified · non-coverage declared.

`badf-engineering-verification` normalizes its work into **exactly those four** — it does not invent
another gate, another evidence type, or a second validator (VER-I20). Deterministic G08 semantics live in
`badf_gate.py`; today the gate validates G08 objects only against the generic `evidence.schema.json` and
enforces "non-coverage declared" through `check_non_coverage`. Later rungs *extend* that path — typed
schemas at VER-B, controls at VER-C — and never compete with it.

## The boundary this contract sits on

```text
G07 — Build complete:            source-change · build · unit-test · documentation
G08 — Engineering verification:  independent-review · integration-test · contract-test · composed-tree-test
G09 — Independent validation:    quality-validation · security-validation · performance-test · resilience-test
```

`badf-build` proves what it built. G08 independently challenges what changed and observes what the
composed result does. G09 validates, risk-based and independently, whether the candidate withstands
quality, security, performance and resilience thresholds. The gate evaluates. Authority permits.

## What the four evidence types must bind (VER-I01, VER-I09)

| Evidence | Plane | Binds |
| :--- | :--- | :--- |
| `independent-review` | Reviewer | WP · sealed-input digest · candidate `source_revision` · `expected_content_tree` · lens · reviewer run identity · findings (canonical) · non-coverage · completion (`inspected_complete_diff`) · verdict from docs/03's council set |
| `integration-test` | Verifier | WP · composed content tree · command · working directory · environment/toolchain identity · fixtures/data epoch · seed · started_at · completed_at · exit code · counts · output digest · non-coverage |
| `contract-test` | Verifier | WP · surface class · contract baseline ref · observed behavior ref · result mapped onto `outcome` · non-coverage |
| `composed-tree-test` | Verifier | WP · `target_base_sha` · candidate · recorded `expected_content_tree` · recomputed content tree · suite pattern · result · staleness verdict |

Bindings that do not name the exact composed tree are not G08 evidence; they are notes.

## What a verified change proves — and does not

```text
G08 APPROVED proves only:
  "an independent reviewer challenged this exact change and reported no unresolved blocker,
   and an approved runtime observed the declared integration, contract and composed-tree checks
   passing on the exact composed tree, with the unobserved surfaces declared."

It does not mean:
  "correct"                      (no findings ≠ correctness — VER-I10)
  "fully covered"                (passing tests ≠ coverage; coverage is a diagnostic — docs/10)
  "validated"                    (that is G09 — VER-I16)
  "approved to merge"            (that is integration authority via badf-git)
  "approved to release"          (that is G10/G11)
```

Verification evidence cannot self-authorize the transition (VER-I18). The quality authority decides.
