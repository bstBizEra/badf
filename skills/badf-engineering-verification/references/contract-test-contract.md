# Contract-test contract — many surfaces, one outcome vocabulary

`contract-test` does not mean "HTTP API". It means: for every surface this change touches that some
other party depends on, is the observed behavior conformant with the declared contract?

## Surfaces (route by what changed)

```text
API contract              request/response shape, status semantics, versioning
event contract            topic, payload schema, ordering/idempotency guarantees
schema compatibility      forward/backward compatibility of a data or message schema
database migration        reversibility, data-preserving, rollback contract
CLI contract              flags, exit codes, output shape
config contract           keys, defaults, validation
plugin / tool contract    the interface a host expects
MCP contract              tool/resource declarations an MCP host expects
agent / tool capability   the capability contract an agent or tool registry declares
```

Each applicable surface yields its own observation; a surface not applicable to the change is declared
`NOT_APPLICABLE` **in the dossier's `non_coverage`** — which `check_non_coverage` already enforces: an
undeclared non-applicability is a missing test, not a non-coverage.

## Results — mapped onto the evidence outcome enum, no fifth vocabulary (VER-I14)

The contract result is a *reason*; the evidence `outcome` is the enum BADF already has.

| Contract result | `outcome` | Meaning |
| :--- | :--- | :--- |
| `CONFORMANT` | `PASS` | observed behavior matches the declared contract on the composed tree |
| `NONCONFORMANT` | `FAIL` | an observed deviation, bound to a finding of kind `contract` |
| `INDETERMINATE` | `BLOCKED` | the behavior could not be observed or the contract is ambiguous; the gate is held, the surface is named |
| `NOT_APPLICABLE` | `NOT_APPLICABLE` | the surface is not touched; declared in dossier `non_coverage` with reason and owner |

`INDETERMINATE` is never serialized as a pass. It mirrors the architecture-assurance doctrine
(`INDETERMINATE ≠ PASS`) and the research doctrine (`INCONCLUSIVE` is preserved, not rounded).

## The binding

```yaml
evidence_type: contract-test
surface: api-contract
contract_ref: <the declared contract: api-contract artifact, schema digest, ADR>
target: {source_revision: …, expected_content_tree: …}
execution: {runtime: …, command: …, environment: …, toolchain: …, started_at: …, finished_at: …, exit_code: …, output_digest: …}
result: CONFORMANT
outcome: PASS
non_coverage: []
```

A contract test whose `contract_ref` does not resolve is `INDETERMINATE`: a test against an unstated
contract measures nothing.
