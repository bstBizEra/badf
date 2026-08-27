# Evidence and Provenance

Status: **NORMATIVE**

## Evidence object

Evidence must answer: what claim, produced by whom/what, from which inputs, using which toolchain and policy, against which source/target/environment, when, with what output, and with what integrity digest.

Use `schemas/evidence.schema.json`. Required bindings include work package, gate, claim, evidence type, producer, source revision, target, toolchain identity, command/operation, timestamps, outcome, artifact URI/path, and SHA-256 digest.

For composed changes also record target base, source head, merge base, merge method, expected result tree, ordered-prefix position, and test-set epoch.

## Evidence classes

- `AUTHORITY`: assignment, approval, or delegation receipt.
- `REQUIREMENT`: PRD, acceptance, traceability, design decision.
- `BUILD`: artifact/SBOM/provenance attestation.
- `TEST`: unit, integration, contract, E2E, UAT, performance, resilience.
- `SECURITY`: threat model, scan, review, penetration test, risk acceptance.
- `RELEASE`: change approval, artifact promotion, deployment record.
- `RUNTIME`: smoke, telemetry query, SLO/KPI window, incident/rollback.
- `LEARNING`: retrospective, pattern validation, memory/skill promotion.

## Integrity and freshness

- Prefer immutable IDs and content hashes.
- Capture stdout/stderr and exit status; sanitize secrets.
- Bind evidence to the exact source and target. Any material drift invalidates it.
- Record tool/version and policy/schema epoch.
- A link without retained content, digest, or stable identity is a pointer, not proof.
- Failed and blocked outcomes are evidence and must not be discarded.

## Gate dossier

A dossier is an index of evidence and decisions, not a copy-paste report. It must declare gate, work package, source/target, change class, artifacts, evidence objects, approvals, exceptions, risks, disposition, and timestamp. The validator checks structural completeness and digests; authorized reviewers judge substantive adequacy.

