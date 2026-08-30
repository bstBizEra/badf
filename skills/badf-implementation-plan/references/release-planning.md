# Release planning

The `release-plan` defines how the executed WPs reach an environment:

```text
candidate grouping        which WPs land together
landing order             composition_after, realized by badf-git
migration order           schema/data migrations before dependents
feature flags             where a landed change stays dark until enabled
environment sequence      dev → … (per the org's promotion policy)
release unit              the atomic thing that ships
observability checkpoints what is watched after landing
```

The plan **declares** the release shape; `badf-git` realizes the landing and composition, and only a valid
**release authority** (for high-impact releases) permits the release itself. A merged commit is not a
release; a release tag is not a deployment (the Git-plane doctrine).
