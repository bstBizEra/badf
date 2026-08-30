# Evidence normalization — PROPOSED / OBSERVED / CANONICAL, on the mechanics BADF already has

Three artifact states name a distinction G08 cannot do without. They are **artifact** states — not the
`AGENTS.md` §10 memory labels (`OBSERVED / INFERRED / DECIDED / SUPERSEDED`), which classify recalled
context. The word `OBSERVED` is shared deliberately: in both vocabularies it means "produced by looking,
not by reasoning".

| State | Produced by | Lives | Becomes the next state through |
| :--- | :--- | :--- | :--- |
| **PROPOSED** | an agent (or a human) — a review draft, a finding, a test scenario, an expected behavior, a coverage hypothesis, a suspected regression | outside `work/<WP>/evidence/` (a draft file, a ballot before validation) | schema validation + target binding + provenance checks |
| **OBSERVED** | an approved runtime executing against the bound target — exit status, HTTP response, DB state, compiler error, contract diff, recomputed content tree | the runtime's artifact under `work/<WP>/evidence/G08/` | digest + provenance + relationship checks |
| **CANONICAL** | the gate's validation of a PROPOSED or OBSERVED artifact | indexed in the G08 dossier; signed in `badf/lockfile.json` | — (only CANONICAL evidence enters the dossier) |

## The checks that make an artifact CANONICAL

```text
schema validation        evidence.schema.json + the typed schema for its evidence_type (VER-B)
identity binding         work_package_id, gate, producer, reviewer/runtime run id
target digest binding    source_revision + expected_content_tree equal to the dossier's
provenance               command, environment, toolchain, timestamps, output digest (VER-I09)
relationship             findings cite locations in the bound diff; ballots cite the sealed digest; matrix rows resolve
non-coverage             present, or explicitly permitted empty
```

An artifact that fails any check stays PROPOSED or OBSERVED; it may be *referenced* by a canonical
artifact's non-coverage, never *counted*.

## Normalization is not laundering

Normalizing a review means validating its shape and bindings — not editing its content. A finding's
`severity`, `status`, and existence pass through normalization unchanged (VER-I12). Deduplication merges
identical findings and keeps every reporter; it does not choose a winner.

## The lockfile is the last word

Every canonical G08 object is a governance path signed in `badf/lockfile.json`; `badf_gate.py repo`
refuses a mismatch. Evidence that is not signed is not canonical, whatever its content says.
