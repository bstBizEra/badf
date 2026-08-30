# Runtime observation — a claimed result is a claim; an observed result is evidence (VER-I08)

The deepest idea adapted from `qa-tester` is not a browser driver. It is the separation:
**agents author drafts; a deterministic runtime validates, registers, executes and reports canonical
artifacts** — and the runtime never calls a model.

## The rule

```text
agent test proposal          PROPOSED
        ↓ schema validation
        ↓ runtime execution
observed result              OBSERVED
        ↓ digest + provenance + target binding
canonical G08 evidence       CANONICAL
```

A test result that an agent *reports* ("I ran the suite, 84 passed") is a claimed result. It receives no
verification credit. Credit attaches only when an approved runtime observed the execution and wrote the
artifact — exit code, output, digest, timestamps, environment — that the evidence object binds.

## Who may produce OBSERVED evidence

The evidence core's `producer.type` enum is `human · agent · service · controller`. For the Verifier
plane:

- `controller` — a deterministic BADF tool (`badf_compose.py`, a `badf_gate.py` subcommand) or a CI job
  under the repository's workflow;
- `service` — an approved external runner recorded in `badf/tool-registry.json`;
- **never `agent`** for the execution itself. An agent may *propose* the run (the command, the
  scenario, the expected behavior) and may *package* the runtime's artifact; it may not be the producer of
  record for the observation.

A `human` producer is admissible for a manual reproduction only when the artifact carries the same
bindings and the human is not the author.

## Recording runs — the ledger BADF already has

Verification run events (`START · OBSERVE · RETRY · STOP · PACKAGE`) are recorded as
`run-ledger-event` records — the hash-chained ledger the build already writes under `work/<WP>/build/`
(`schemas/run-ledger-event.schema.json`). At VER-B the verification ledger lives beside it under
`work/<WP>/verification/`; it is recovery and evidence, never a verdict source.

## Safety bounds

Runtimes execute inside the environment the Work Package permits (`permissions`, `allowed_tools`), on
the composed checkout, with no credentials beyond the run's need. A runtime that would need production
data or a production endpoint is a G09 concern, declared as non-coverage here.
