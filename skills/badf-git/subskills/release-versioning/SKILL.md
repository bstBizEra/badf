---
name: release-versioning
description: Decide and bind a BADF release the way the release contract requires -- the version is a governed SemVer decision by the release authority, the binding is written with `badf_gate.py git-release-record` before the tag is created, the tag is annotated and created only from a verified main revision, and `badf_gate.py git-release-check` proves the pair is annotated, on main, record-bound and unmoved. Use when preparing, recording or verifying a release or baseline ref. Do not use to create, move, delete or sign a tag on the tool's behalf, to derive a version from a commit prefix, or to grant release authority.
---

# release-versioning

A subskill of `badf-git` (`../../SKILL.md`) for the RELEASE stage and the release contract
(`../../references/release-versioning.md`). Its admission status is recorded in
`badf/skill-registry.json`; this file defines behaviour and hardcodes no lifecycle status.

**The invariants:** `MERGED != RELEASED` · **`TAG_EXISTS != RELEASE_AUTHORIZED`** ·
`RELEASED != PRODUCTION_VERIFIED`. A tag is a name anyone with push rights can create; a
*release* is a record the release authority binds to an authorized, verified `main` revision.
Once published, a release ref is **immutable** — never moved, deleted, recreated or reused.

## Two tag families

| Ref | Meaning |
| --- | --- |
| `BADF-BASELINE-X.Y.Z` | a historical governance baseline; preserved as it is (the first, `BADF-BASELINE-1.0.0`, is unsigned — recorded as a provenance limitation, never rewritten) |
| `vX.Y.Z` | the forward release convention for BADF as a framework |

## The SemVer decision (the release authority's checklist, never a commit-prefix inference)

- **MAJOR** — an intentional breaking change to a supported BADF contract: incompatible lifecycle/gate
  semantics, an incompatible schema or artifact contract without a migration path, breaking
  authority/CLI behaviour, a required migration that invalidates prior integration assumptions.
- **MINOR** — an additive, backward-compatible gate, capability, skill, subcommand or feature.
- **PATCH** — a backward-compatible correction or hardening.
- Pure working documentation usually releases nothing. When in doubt, the lower tier.

## The sequence: record → tag → check

```text
1. the release authority decides the version (above) at a verified first-parent commit of main
2. python3 scripts/badf_gate.py git-release-record vX.Y.Z      # writes badf/releases/vX.Y.Z.json, HUMAN_REQUIRED
3. commit the record (lockfile re-signed) -- it lands through the normal PR loop
4. the release authority creates the tag:  git tag -a vX.Y.Z -m "…" <that commit>   (or gh release, from the same commit)
5. python3 scripts/badf_gate.py git-release-check vX.Y.Z       # RELEASE_BOUND, or BLOCKED naming why
```

`git-release-record` binds an **existing** tag to its own commit (recording a historical or just-created
ref) or, when no tag exists yet, HEAD — a request. It never runs `git tag`. It refuses a commit off
`main`'s first-parent history, a version already recorded for different content, and any form other
than `vX.Y.Z` / `BADF-BASELINE-X.Y.Z`.

`git-release-check` refuses: a missing or **lightweight** tag; a tag off `main`'s first-parent
history; a tag with no record (`TAG_EXISTS != RELEASE_AUTHORIZED`); a record for a different
revision — the tag **moved**; a version or result tree that differs; a provenance statement the
tag object contradicts. `badf_gate.py repo` enforces the same immutability for every recorded
release ref that exists locally.

## A bad release

is superseded or revoked by a **new** record and version — never by moving or deleting the tag. The
rollback is a governed forward change (`git-recovery`, `pull-request-integration`).

## Boundaries

- Tag creation, signing, GitHub releases, tag rulesets: the release authority's and the platform's;
  this subskill records and verifies, it never mutates a ref.
- SBOM / attestation / deployment records are G10–G13 evidence (`docs/11`), not bound here.
