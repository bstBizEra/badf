# G06 contract

`badf-implementation-plan` composes into the **existing G06** — **Implementation planning**, owner
`engineering_owner`, min `C1` — and changes **no** `lifecycle.json`. G06's required evidence, unchanged:

| Artifact | What it carries |
| :--- | :--- |
| `work-breakdown` | the Governed Work Package DAG (nodes + dependency edges, acyclic) |
| `test-plan` | acceptance → WP → test → evidence, per level |
| `release-plan` | candidate grouping, landing order, environment sequence |
| `rollback-plan` | trigger, scope, procedure, reversibility, stop conditions |

The gate already validates these (WP-0067: `check_work_breakdown` enforces schema, non-empty, unique ids,
resolvable dependencies and an **acyclic** graph). `badf-implementation-plan` **authors and reconciles**
the four; the canonical gate validates them and `engineering_owner` dispositions the dossier.

## No fifth artifact

There is **no** "implementation-plan" gate artifact. Adding one would duplicate what the four already
carry. The plan is the *composition* of the four, not a new evidence type (IMP-I17).
