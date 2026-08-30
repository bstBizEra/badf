# Integration-test contract — an observed artifact, never a sentence

"Integration tests passed" is a claim. G08 `integration-test` evidence is an **observation**: something an
approved runtime executed against the exact composed tree, recorded with the fields docs/10 already
requires for test integrity.

## The binding (VER-I08, VER-I09)

```yaml
evidence_type: integration-test
work_package_id: WP-2026-NNNN
target:
  source_revision: <sha>
  expected_content_tree: <tree>          # the composed identity — tests run on the composition, not the branch tip
execution:
  runtime: <approved runtime identity: CI job / badf_compose.py / declared verifier>
  command: python3 -m unittest discover -s tests -p 'test_*.py'
  working_directory: <path in the composed checkout>
  environment: {os: …, python: …, container_digest: …}
  toolchain: {name: …, version: …}
  fixtures_epoch: <data/fixture epoch or digest>
  seed: <seed, or null with a reason>
  started_at: …
  finished_at: …
  exit_code: 0
  tests: {total: 84, passed: 84, failed: 0, skipped: 0, quarantined: 0}
  output_artifact: work/<WP>/evidence/G08/integration-test.txt
  output_digest: sha256:…
outcome: PASS                            # the evidence core enum: PASS · FAIL · BLOCKED · NOT_RUN · NOT_APPLICABLE
non_coverage:
  - surface: <what the suite does not exercise>
    reason: …
    impact: …
```

`producer.type` is `controller` or `service` — the runtime that ran it. An `agent` producer on an
integration-test object is a proposal (PROPOSED), not evidence (`references/runtime-observation.md`).

## Quarantine and flakes

Quarantined or flaky tests carry owner, reason, expiry and compensating control (docs/10). A re-run is
recorded as a second execution with its own artifact; **never re-run until green and erase the failure**.
The first failing execution stays in the evidence set as `outcome: FAIL` with the re-run referencing it.

## Where the suite comes from

The integration obligations are the G06 `test-plan`'s (the seams `badf-build` built against). A missing
obligation is a `TEST_PLAN_DEFECT` routed upstream, not a test the verifier improvises and then credits.
