# quality-validation — the oracle lives outside the agent (VAL-I04)

`quality-validation` is a **class-aggregator**, not one test and not "the QA agent's verdict on
the app". It normalizes many risk-routed functional and non-functional quality methods into the
single `quality-validation` evidence type the G09 lifecycle already names. The DESIGNED contract
adds no new lifecycle type, script or schema — it composes what exists (VAL-I20).

## What it aggregates — routed by risk, never "run all QA" (VAL-I02)

```text
E2E journeys (Playwright / Cypress)     accessibility (WCAG, keyboard, screen-reader)
exploratory / session-based             DB + migration validation (up/down, integrity)
cross-browser / cross-device            visual regression
AI evals (task success, safety)         payment + email delivery flows
```

The router marks each method `REQUIRED / NOT_APPLICABLE / DEFERRED_WITH_REASON` from surfaces,
NFRs and change class. An agent cannot silently drop a required method.

## The central rule — the oracle is outside the agent

An agent may **attempt** a journey. It may never **grade** it. Success is established by a
deterministic oracle that exists independently of the agent's narration (VAL-I04):

```text
agent attempts "the checkout journey"        DRAFT   (VAL-I05)
        ↓ deterministic oracle observes
order_id row exists                          ┐
payment sandbox reports success              │  OBSERVED  →  quality-validation
inventory mutation matches expectation       │             evidence
no forbidden error / console-error state     ┘
```

Forbidden, always:

```text
agent: "the checkout looked successful → PASS"     ✗ self-grade, no oracle
screenshot the agent narrates as correct → PASS    ✗ narration ≠ observation
LLM eval of its own transcript → PASS              ✗ author grades author
```

This bites hardest for **agentic browser testing**: a browser agent that drives the UI is a
*scenario executor*, not the oracle. Its click-stream is a draft; the order row, the sandbox
webhook, the DB mutation and the absence of a forbidden state are the oracle. No agent both
performs and scores the same journey.

## Oracles are concrete, not vibes

```text
functional      a row / status / event in a system the agent does not author
accessibility   axe / pa11y rule outcomes + AT-observable state, not "reads fine"
DB / migration  row counts, constraints, checksum of migrated data vs expected
visual          pixel / DOM diff vs an approved baseline digest
AI eval         a scored rubric run by a separate grader against a frozen key
```

## Thresholds, provenance, non-coverage

- Acceptance thresholds (pass rate, a11y level, visual tolerance, eval score) are **bound
  before** results are interpreted (VAL-I06). A green run under a threshold invented after the
  fact earns no credit.
- Every run binds environment identity, browser/toolchain, fixtures and observation time
  (VAL-I07). `staging PASS ≠ production proven` is declared as deviation, not assumed (VAL-I08).
- Every quality run names the surfaces it did **not** exercise (VAL-I15) — the untested journey
  is named and owned, never forgotten.
- A failed observation stays in the evidence set; rerun-until-green cannot erase it (VAL-I16). A
  second run is a second artifact that references the first.

## What quality-validation is not

`quality-validation` is not `security-validation`, `performance-test` or `resilience-test`
(VAL-I13): an E2E run that happens to be fast is not a performance budget, and a journey that
survived a slow backend is not a resilience experiment. And no set of green quality classes
grants release authority — that is G10 (VAL-I18), decided by release_authority, not here.
