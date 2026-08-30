# Runtime evidence — a claim earns no credit until a runtime observed it (VAL-I04)

The deepest rule of G09 is not a scanner or a load generator. It is a separation of powers:
**a validation agent decides what to investigate; a deterministic runtime establishes what actually
happened.** A claim receives **no validation credit** without an approved *observed* runtime execution
in which the claim is mechanically observable (VAL-I04). The runtime — never the agent — establishes
the observable facts.

## The rule

```text
agent scenario / finding / interpretation      DRAFT        (non-canonical, VAL-I05)
        ↓ threshold + oracle bound first (VAL-I06)
        ↓ approved runtime executes
observed result                                 OBSERVED     (runtime is the producer)
        ↓ candidate binding (VAL-I01) + environment provenance (VAL-I07) + digest
canonical G09 evidence                          BOUND
```

A result an agent *reports* — "I ran the suite, the login flow passed", "the scan is clean", "latency
looked fine" — is a claimed result. It stays **DRAFT** and non-canonical until a runtime validated it and
it was bound (VAL-I05). Credit attaches only when an approved runtime observed the execution and wrote the
artifact the evidence binds.

## Mechanically observable, or it is non-coverage

A claim earns credit only where the runtime can mechanically observe it. Establish success from a fact the
runtime reads — an `order_id` row exists, the sandbox returned success, an inventory mutation matches, no
forbidden state was reached — **never** from "it looked successful". A claim that no available runtime can
observe is not passed and not failed: it is **declared non-coverage** (VAL-I15), owned by
`quality_authority`.

## What every runtime result binds

Every observation carries its full provenance, so a second party can re-run it and expect the same fact
(this is the environment-provenance obligation, VAL-I07):

```yaml
runtime_result:
  candidate:        <exact bound candidate identity>     # VAL-I01
  environment:      <id + digest>                        # VAL-I07, see environment-fidelity.md
  config:           <resolved configuration digest>
  fixtures:         <seed data / dataset identity>
  toolchain:        <runner + version, scanner + ruleset version>
  seed:             <RNG / workload seed, where applicable>
  command:          <exact invocation>
  output:           <stdout/stderr, report artifact>
  digest:           <sha256 of the observation artifact>
```

An observation missing any of these is not a stronger claim — it is an **unreproducible** one.

## Producers observe; they never decide

Approved runtimes, load generators and scanners are **observation producers, never authority**. A green
Semgrep run is one security *observation*, not a `security-validation` verdict; a k6 run is a latency
*observation*, not a `performance-test` PASS. The producer of an *execution* is a deterministic runtime or
an approved service — **never the agent** for the execution itself. An agent may propose the run and
package the artifact; it may not be the producer of record for the observation, and no producer's output
is a gate decision. The oracle decides (see `thresholds-and-oracles.md`); `quality_authority` decides G09;
G09 does not decide release (VAL-I18).

## What runtime evidence is not

Runtime evidence is not a verdict. An OBSERVED artifact is a bound fact about the exact candidate under a
declared environment. Whether that fact satisfies its class is an **oracle** evaluation against a
**pre-bound threshold**; whether the G09 dossier passes is a conjunctive composition (see
`findings-and-disposition.md`). Observation establishes the *what happened*; it never grants the *what may
proceed*.
