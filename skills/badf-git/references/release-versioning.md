# Release and Versioning Contract

This reference defines design guidance for BADF Git release refs. It does not grant release authority and does not create a release automation mechanism.

## Release identity

A BADF release must bind:

- an authorized, verified `main` revision;
- the immutable artifact/result identity produced from that revision;
- version/tag identity;
- SBOM/provenance/change/release evidence required by `docs/11-release-production.md`;
- release authority and disposition;
- promotion/deployment records where applicable.

```text
MERGED != RELEASED
TAG_EXISTS != RELEASE_AUTHORIZED
RELEASED != PRODUCTION_VERIFIED
```

## Tag families

BADF already has historical baseline tags in the form:

```text
BADF-BASELINE-X.Y.Z
```

Preserve those historical identities. Do not rewrite them merely to fit a newer convention.

For future product/framework releases, the recommended release-tag convention is:

```text
vX.Y.Z
```

Example:

```text
v1.2.3
```

A later governance decision may refine this convention. This skill does not rename or mutate existing tags.

## SemVer decision contract

Semantic versioning is a governed release decision based on the public/operational contract of BADF, not a mechanical reading of commit prefixes.

### MAJOR

Use a major version when an authorized release intentionally introduces a breaking change to a supported BADF contract, for example:

- incompatible lifecycle/gate semantics;
- incompatible schema or artifact contract without a compatible migration path;
- breaking authority/CLI/interface behavior;
- incompatible skill/runtime contract promised to consumers;
- required migration that makes prior integration/automation assumptions invalid.

### MINOR

Use a minor version for backward-compatible capability growth, for example:

- new optional gate/capability/skill behavior that preserves existing supported contracts;
- additive schema/interface fields with compatible handling;
- new supported workflow/command whose addition does not break existing consumers.

### PATCH

Use a patch version for backward-compatible correction/hardening, for example:

- defect fixes;
- stricter implementation that enforces an already-ratified contract without changing the supported interface;
- documentation/evidence corrections required to make existing behavior accurate;
- security hardening that preserves the supported contract.

The release authority decides the actual version after evidence. A `feat:` or `fix:` commit prefix is advisory metadata at most.

## Version source of truth

A release version must be defined by an explicit release record/decision or approved version source. Do not derive the authoritative version from:

- branch name alone;
- PR title alone;
- Conventional Commit prefix alone;
- a tag that an unauthorized actor can create;
- an agent's confidence or interpretation.

## Release-from-main rule

Normal BADF release refs are created only from an authorized, verified `main` revision.

Why:

- `main` is the protected integration ledger;
- composed-result checks/reconciliation already establish the integrated content identity;
- releasing from arbitrary topic heads bypasses the integration contract;
- a release should be reproducible from the same versioned source state.

Exception requires explicit release/governance authority and is outside this skill's default contract.

## Immutable release refs

Once published as an immutable release/baseline identity:

- do not move the tag to another commit;
- do not delete/recreate the same version to hide a faulty release;
- do not reuse a version number for different content;
- corrections produce a new release/version or an explicit revocation/supersession record.

If an immutable release is bad, rollback/revert through governed release/change control; preserve the historical identity.

## Tag authenticity and provenance

Release policy should make tag/release provenance independently verifiable through platform identity, signatures/attestations or equivalent controls appropriate to the environment.

Historical baseline tags that lack newer provenance controls remain historical facts. Do not rewrite them retroactively; record the provenance limitation and apply stronger controls to future release refs.

## Same-artifact promotion

A release artifact is built/identified once and promoted through environments by immutable digest. Do not rebuild separately per environment and call the outputs the same release merely because the version string matches.

The Git release binding must make it possible to answer:

- which source result produced this artifact?
- which artifact digest is being promoted?
- which release/version names that digest?
- which authority approved the promotion?

## Release candidate posture

A release candidate can be represented by evidence/records without creating a permanent lifecycle branch.

Avoid permanent `release`, `staging`, `alpha`, or `beta` branches as state machines. If temporary release-candidate refs are ever needed, they remain short-lived controlled refs with explicit purpose and must not replace BADF gate/release records.

## Hotfix posture

BADF does not require the classic Git Flow `hotfix/*` model.

Urgent production correction still follows:

```text
incident/demand
  → bounded work package
  → short-lived change branch/worktree
  → verify/compose/challenge
  → protected integration to current main
  → authorized release/promotion
  → runtime verification
```

Urgency may change approval timing through ratified emergency policy, but does not justify silent protected-history rewrite or release-tag reuse.

## Release evidence

In addition to general evidence, record where applicable:

```yaml
release_binding:
  version: vX.Y.Z
  tag_ref: refs/tags/vX.Y.Z
  source_ref: refs/heads/main
  source_revision: <main-commit-sha>
  source_result_tree: <tree-sha>
  artifact_digest: sha256:<digest>
  sbom_ref: <immutable-ref>
  provenance_ref: <immutable-ref>
  change_ticket: <id>
  release_authority: <principal/receipt>
  release_record: <id>
```

Fields defer to the canonical BADF release/evidence schemas when they exist; this design contract does not create a competing schema.

## Release stop conditions

Do not create or mutate a release ref when:

- source is not a verified authorized `main` revision;
- release authority is missing;
- artifact identity/digest is missing or rebuilt inconsistently;
- required release packet evidence is incomplete;
- version identity collides with different content;
- the requested action would move/delete/reuse an immutable tag;
- required rollback/operational readiness is absent;
- protected/main composition has not been reconciled.

Return `BLOCKED` or `HUMAN_REQUIRED` as appropriate.

## Relationship to baseline tags

`BADF-BASELINE-X.Y.Z` and `vX.Y.Z` can coexist:

- baseline tags preserve historical governance baseline identities;
- `vX.Y.Z` is the recommended forward release convention;
- neither should be rewritten to collapse the distinction;
- documentation/release records should state what each tag means.

A future cleanup/migration may add aliases or documentation, but must preserve immutable historical references.
