# C4 contract

C4 (c4model.com) is abstraction-first and notation-independent: it prescribes a small set of nested abstractions (System Context → Container → Component → Code) and is deliberate that Context and Container diagrams are normally sufficient, while Component and Code views are created only when they add value. BADF adopts C4 as a **view system**, not as the architecture store.

## Levels and when they are required

```text
Level 1 — System Context     required by default
Level 2 — Container          required by default
Level 3 — Component          optional; only for complex/high-risk containers where the decomposition adds assurance value
Level 4 — Code               generated on demand only; not manually curated unless risk justifies its lifecycle cost
```

## Views project the baseline

Every C4 element, relationship and boundary must already exist in the canonical architecture baseline (`architecture-model.md`). A C4 view element absent from the baseline is refused (ARCH-I02). Mermaid, Structurizr and any other notation are interchangeable renderings; none of them is the source of truth.

## Why the baseline, not the diagram

C4 conveys structure and communication well, but a diagram alone does not encode the trust-boundary, NFR-allocation, operability and compliance semantics BADF needs. Those live in the baseline and its sibling G04 artifacts; the diagram is a projection for humans. Storing intent only as a diagram would make architecture visible but neither governable nor evolvable.
