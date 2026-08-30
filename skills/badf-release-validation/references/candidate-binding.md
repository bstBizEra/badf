# candidate-binding.md — bind the exact G08-verified candidate, raise the bar

G09 **inherits G08's strongest binding controls and raises the bar**. G08 asks: *is the
engineered change internally coherent and correct on the composed result?* G09 asks: *does
that **exact** composed candidate withstand independent risk-based validation under
representative conditions?* (**VAL-I17**). The second question is only meaningful if every
class provably tested the **same** artifact G08 verified — so binding is the first control,
not a footnote. See [g09-contract.md](g09-contract.md) for the surrounding contract.

## What every G09 artifact binds (VAL-I01)

Each runtime observation, finding, threshold result and normalized evidence type binds the
identity of the candidate it examined. The five components are mandatory and immutable:

- **source revision** — the reviewed, merged VCS commit that produced the candidate.
- **composed content tree** — the exact composed result (post-merge tree), not a branch tip.
- **build artifact digest(s)** — content digests of the built artifacts under test.
- **configuration / environment identity** — config set + environment the candidate ran in
  (paired with the runtime provenance of **VAL-I07**).
- **validation policy epoch** — the thresholds/routing-policy version in force, so a result
  cannot be reinterpreted under a later policy.

```yaml
# bound candidate identity — replicated on every G09 artifact (illustrative)
candidate_binding:
  source_revision:      "a1b2c3d4e5f6…"          # reviewed + merged commit
  composed_content_tree:"tree:9f8e7d…"           # exact post-merge composed result
  build_artifact_digests:
    - "sha256:1122…app-image"
    - "sha256:3344…migration-bundle"
  config_environment_identity: "cfg:release-cand-14 @ env:staging-repl-2"
  validation_policy_epoch: "vpol-2026.08"        # thresholds + routing policy version
```

## One candidate, or REFUSE

Every mandatory class must bind **byte-identical** components. Binding is compared across
classes before the dossier composes.

```
if any REQUIRED class bound a different {revision | tree | digest | config | policy_epoch}:
        →  MIXED_CANDIDATE_EVIDENCE
        →  REFUSE   (candidate_identity_consistent = false; G09_PASS impossible)
```

`MIXED_CANDIDATE_EVIDENCE` is a **refusal, not a downgrade**. It cannot be waived by an
agent, averaged away, or resolved by re-labelling the newer run — the classes must re-bind
the same candidate and re-observe. This upholds the conjunctive dossier's leading term
`candidate_identity_consistent` (see [g09-contract.md](g09-contract.md)); a security run on
digest A and a performance run on digest B never compose into one G09 verdict.

## Why G09 binding is stricter than G08's

- **Runtime, not just static.** G08 verification can reason over the tree; G09 evidence comes
  from **approved observed execution** (**VAL-I04**), so the *environment* the candidate ran
  in is part of the bound identity (**VAL-I07**) and its deviations are declared (**VAL-I08**).
- **Multi-class, so drift multiplies.** Four independent classes running on possibly-different
  environments make silent candidate drift the default failure mode; explicit binding + the
  MIXED_CANDIDATE_EVIDENCE refusal is what prevents it.
- **Policy-pinned.** The **validation policy epoch** freezes the thresholds a result is judged
  against, complementing "thresholds pre-exist outcomes" (**VAL-I06**) — results cannot be
  retro-graded under a friendlier policy.

## Agent-authored bindings are draft until validated

An agent may *assert* which candidate it tested, but that assertion is **draft** until the
deterministic runtime confirms the bound identity (**VAL-I05**). Binding a candidate is a
verified fact about what executed, never a self-reported label. Routing that selects the
classes to bind is covered in [routing.md](routing.md); keeping each class's binding its own
(not copied) is enforced in [class-independence.md](class-independence.md).
