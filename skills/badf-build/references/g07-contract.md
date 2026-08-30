# G07 contract — what a build proves

G07 ("Build complete") requires four evidence types in `badf/lifecycle.json`: `source-change`, `build`,
`unit-test`, `documentation`. `badf-build` normalizes its execution into **exactly those** — it does not
invent another gate, another evidence type, or a second validator (BLD-I18). Deterministic G07 semantics
live in `badf_gate.py`; today the self-dossier already produces the four objects for BADF's own Work
Packages, and later rungs *extend* that producer rather than compete with it.

## The boundary this contract sits on

```text
G06 — Implementation planning:   work-breakdown · test-plan · release-plan · rollback-plan
G07 — Build complete:            source-change · build · unit-test · documentation
G08 — Engineering verification:  independent-review · integration-test · contract-test · composed-tree-test
```

`badf-implementation-plan` decides how authorized work is decomposed. `badf-build` performs the
authorized mutation. G08 independently verifies the result. `badf-git` governs repository
topology and integration. The gate evaluates evidence. Authority permits the transition.

## What the four evidence types must bind (BLD-I16)

| Evidence | Binds |
| :--- | :--- |
| `source-change` | WP · base SHA · head SHA · changed paths · change digest · expected-surface comparison · unexpected-surface list · producer · toolchain |
| `build` | command · working directory · environment/toolchain identity · started_at · completed_at · exit code · artifact refs · artifact digests · non-coverage |
| `unit-test` | test obligation · acceptance criterion · seam · red evidence where required · green evidence · command · result · test count · failure count · coverage scope |
| `documentation` | what changed · what contract changed · what operator/developer behavior changed · what docs required update · what was NOT updated and why |

Key rule for `source-change`: a changed path outside the authorized expected surface is a **stop /
re-authorize** event at build time — not a fact reported afterwards (see `scope-containment.md`).

## What a successful build proves — and does not

```text
A successful build proves only:
  "the authorized change was built and author-verified."

It does not mean:
  "independently verified"   (that is G08)
  "approved to merge"        (that is integration authority via badf-git)
  "approved to release"      (that is G10/G11)
  "safe for production"      (that is G12/G13)
```

Completion of implementation grants no push, merge or release authority (BLD-I17).
