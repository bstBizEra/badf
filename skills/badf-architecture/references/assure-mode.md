# ASSURE mode

Determine whether an implementation, PR, branch, composed tree or running system still conforms to declared architectural intent. **Read-only unless mutation is separately demanded and authorized** (ARCH-I12).

## Workflow

```text
BASELINE → OBSERVE → MODEL_ACTUAL → COMPARE → FITNESS → ADR_CHECK → NFR_CHECK → CHALLENGE → REPORT
```

## Baseline binding (ARCH-I01, ARCH-I09)

Every run establishes, as immutable evidence: `architecture_baseline_digest`, `architecture_baseline_revision`, `observed_repository`, `observed_revision`, `observation_time`, `ADR_set`, `fitness_spec_set`. Never compare against "latest", "current architecture" or "what the repo seems to intend" without resolving those phrases to a pinned revision. `NO BASELINE ≠ COMPLIANT` (ARCH-I07): a missing baseline yields observations, never compliance.

## Structural assurance

- **Dependency direction** — rules derive from the declared architecture style, not universal assumptions (e.g. `domain → infrastructure` forbidden, `adapter → domain` allowed).
- **Cycles** — across modules, components, and package/build dependencies; report the complete cycle.
- **Boundary violations** — importing another module's internals, bypassing a public API, direct cross-context DB access, shared tables across ownership boundaries, dependency on a forbidden layer, hidden coupling via shared utilities.
- **Public-surface leakage** — boundaries are crossed only through their declared public contracts.

## ADR compliance

For each active ADR: affected elements → observable implementation rules → actual implementation. Result is `CONFORMANT`, `NONCONFORMANT`, `INDETERMINATE`, `SUPERSEDED`, or `NOT_OBSERVABLE`. `INDETERMINATE` never converts to PASS. Intentional implementation drift with no corresponding ADR/baseline update is still drift.

## Drift (DECLARED vs OBSERVED)

Categories: `ELEMENT_DRIFT`, `DEPENDENCY_DRIFT`, `BOUNDARY_DRIFT`, `TOPOLOGY_DRIFT`, `DATA_OWNERSHIP_DRIFT`, `INTERFACE_DRIFT`, `TRUST_BOUNDARY_DRIFT`, `ADR_DRIFT`, `NFR_DRIFT`, `OPERABILITY_DRIFT`. Drift is not automatically a defect; it may be `UNAUTHORIZED_DRIFT`, `DOCUMENTATION_LAG`, `APPROVED_EVOLUTION_NOT_BASELINED`, `EXPECTED_VARIANCE` or `UNKNOWN` — but only independent evidence/authority may classify evolution as approved (ARCH-I08).

## Finding contract

Every material finding carries: `finding_id`, `kind`, `severity`, `baseline_ref`, `observed_ref`, `affected_elements[]`, `evidence_locations[]`, `expected`, `observed`, `impact`, `failure_scenario`, `recommendation_direction`, `status`, `non_coverage[]`. Evidence points to concrete files, lines, manifests, dependency edges, API versions or runtime evidence. Do not manufacture a failure scenario solely to raise severity.

## Non-coverage

Every run states what it did not inspect (e.g. runtime network policy not observed, production topology unavailable, generated-client edges excluded, dynamic plugin loading not statically resolvable). No non-coverage declaration means the result is incomplete.
