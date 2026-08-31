# The same-artifact rule

PRDY-I18. **The artifact authorized for production is the artifact that was verified.** No
per-environment rebuild substitution.

```text
verified artifact  ──digest──▶  the artifact G08/G09 evidence was observed against
authorized artifact ─digest──▶  the artifact release_authority authorizes
deployed artifact  ──digest──▶  the artifact G11 actually deploys

All three digests are the SAME value, or the chain is broken.
```

## Why a rebuild breaks the chain

A rebuild from the same source can differ: a floating dependency resolves differently, a base image
moved, a build timestamp or path is embedded, a toolchain patched. Every piece of evidence upstream was
observed against the *first* artifact. Rebuilding for production produces an artifact with no evidence
about it — and the substitution is invisible because the source revision is identical, which is exactly
what makes it dangerous. Source identity is a **proxy** for artifact identity; the two come apart
precisely when it matters.

## What is resolved

```text
artifact_digest      from the candidate binding (references/candidate-binding.md)
provenance/attestation  binding that artifact to that source revision and that build
sbom_digest          the bill of materials for that exact artifact
promotion record     evidence that the artifact was PROMOTED between environments, not rebuilt
```

A promotion record is the positive evidence; its absence is not neutral. Where the delta makes artifact
identity mandatory and no promotion record exists, the dimension is `NOT_READY` — "we rebuild per
environment and it has always been fine" is a description of a habit, not evidence about this release.

## Config is bound separately

The same artifact legitimately runs under different configuration per environment; that is why
`config_digest` is a separate binding (`references/candidate-binding.md`). The rule constrains the
*artifact*, not the configuration — but a config change is itself a candidate mutation that invalidates
the dossier (PRDY-I23).
