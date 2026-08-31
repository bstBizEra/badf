# Admission ladder — badf-production-readiness

The skill's status is recorded in `badf/skill-registry.json`; this ladder is a pointer, not a second
status.

- `DESIGNED` — **WP-PRDY-A** (this freeze): thin router, PRDY-I01…I24, nine-stage workflow, sixteen
  references, registered C1 with no tools; no runtime, no schema, no lifecycle change, no gate change.
- `IMPLEMENTED` — **WP-PRDY-B**: typed `release-packet` and `operational-readiness` evidence schemas
  specializing `evidence.schema.json`; the readiness dossier as a typed artifact shaped like the G08
  verification matrix; the twelve-dimension evaluation and the bounded readiness vocabulary as typed
  objects. Extends the canonical gate; adds no second one.
- `VALIDATED` — **WP-PRDY-C**: deterministic G10 readiness controls in `badf_gate.py` — exact-candidate
  binding across all mandatory evidence, freshness refusal (no credit, not reduced credit),
  contradiction refusal (NOT_READY / INDETERMINATE, never the favorable claim), delta-driven
  mandatoriness, delta-invalidation on candidate mutation, and the authority-boundary refusal (no
  `PRODUCTION_AUTHORIZED` in any artifact this skill emits) — each failing-first and mutation-killed.
  **Lean mode disabled**: these are HARD INVARIANTS and are never traded for leanness.
- `SHADOWED` — **WP-PRDY-D**: shadow on real release material. BADF has shipped no production release,
  so this will likely be **representative rather than real**, and that limitation is declared in the
  shadow record rather than glossed — mirroring the WP-D pattern in `badf-solution-design`,
  `badf-security-design` and `badf-implementation-plan`. Injected defects across all twelve dimensions,
  measuring missed mandatory dimensions, false READY, contradiction handling and non-coverage quality.
- `APPROVED` / `ACTIVE` — **WP-PRDY-E**: the `release_authority` / operator admission decision, taken on
  WP-PRDY-D's evidence and recorded on its own issue; registry status flip only, digest unchanged.
  **No release, deployment or authorization authority is granted at any rung, including `ACTIVE`** —
  PRDY-I19…I22 hold throughout, which is the point of the capability rather than a restriction on it.
