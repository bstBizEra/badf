# Acceptance and admission

The capability's **live status is `badf/skill-registry.json`** (`DESIGNED` at `BADF-WP-0078` / WP-SEC-A)
— this document defines the contract, not the status, so it never hardcodes a status line that can drift
from the registry. Progression follows `docs/07-skills-governance.md`.

## Controlled admission ladder

The same pattern that carried `badf-research`, `badf-architecture` and `badf-solution-design` — freeze the
contract first, prove it later, in separate WPs. **Do not build every specialist in the first PR.**

| WP | Outcome | Status |
| :--- | :--- | :--- |
| WP-SEC-A | root `SKILL.md` + references: G05 mapping, routing, specialist boundaries, architecture/solution-design interfaces, threat/control/risk model, normalization contract, OWASP dispositions, SEC-I01…I15, admission criteria | `DESIGNED` |
| WP-SEC-B | the `security-composition` matrix schema + the `security` gate command with structural controls (no-empty · SEC-C01 unique · SEC-C02 provenance · SEC-C03 controlled-has-control · SEC-I12 residual-risk-not-accepted by schema); see `traceability.md` | `IMPLEMENTED` |
| **WP-SEC-C** | matrix-internal cross-artifact **seam** controls: SEC-C04 (a `controlled` threat is verified, SEC-I04 downstream) + SEC-C05 (residual-risk ↔ disposition coherence, SEC-I12); external-artifact seams (full SEC-I04 bidirectional, SEC-I01 baseline binding, semantic resolution) deferred | `VALIDATED` |
| WP-SEC-D | historical / representative security-design shadow calibration | `SHADOWED` |
| WP-SEC-E | independent admission | `ACTIVE` |

## WP-SEC-A boundaries (no scope creep)

- **No runtime, no second validator** — no `scripts/badf_security_design.py` (SEC-I15); `badf_gate.py` is
  the sole gate authority.
- **No schema, no lifecycle change** — G05 required_evidence and its gate rules are unchanged;
  security-design normalizes into the **existing** G05 design artifacts.
- **No scanner, no assurance** — code review / SAST / SCA / secrets / IaC / API-review / remediation are
  **out of scope**; they are a future `badf-security-assurance` at G08/G09 (SEC-I14).
- **No self-approval** — the skill does not produce `security-approval` or accept residual risk; those are
  `security_authority`'s (SEC-I12/I13).
- **No specialist activation** — routing names who would own each concern; the specialist adapters are not
  admitted here. `ai-agent-security-design` is conditional and `NOT_APPLICABLE_WITH_REASON` for non-agentic
  work.
- **Architecture + solution spines respected** — security design consumes the baselines and raises
  `ARCHITECTURE_CHANGE_REQUIRED` / `REQUIREMENT_CHANGE_REQUIRED` rather than rewriting them.

## Admission

- `DESIGNED`: the contract exists as this `SKILL.md` + references and is registered. **Met (WP-SEC-A).**
- `IMPLEMENTED` … `ACTIVE`: earned by the later WPs above, each through the full loop; a seam becomes a
  deterministic control only when a failing-first probe warrants it, never by precedent.
