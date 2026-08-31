# Exact candidate binding

PRDY-I02, PRDY-I18, PRDY-I23. All mandatory readiness evidence resolves to the exact immutable release
candidate, or to an explicitly declared compatible baseline.

```text
source_digest         the exact source revision
composed_tree_digest  the tree that would land / did land (never a two-way diff prediction)
artifact_digest       the built artifact — the one that will reach production (PRDY-I18)
sbom_digest           the bill of materials for that artifact
provenance_digest     build attestation binding artifact to source
config_digest         the configuration the candidate runs under
migration_digest      the migration set this release carries
```

## Compatible baseline, declared not assumed

Some evidence legitimately predates the candidate (a G05 security design, an architecture record). Such
evidence may be credited only when its compatibility with this candidate is **explicitly declared** with
a stated basis — never inferred from "nothing relevant changed". The release delta
(`references/release-delta.md`) is what makes that declaration checkable.

## Mutation invalidates the dossier (PRDY-I23)

Any material change to the candidate, its configuration, its migrations or its release-owned artifacts
invalidates the readiness dossier. The dossier is not amended in place to match the new candidate — it
is superseded, and a fresh dossier is assembled against the new binding. A readiness claim that outlives
the candidate it measured is a claim about a build nobody is shipping.
