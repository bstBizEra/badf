---
name: badf-security-design
description: Compose the pre-implementation security-design specialist contracts — threat model, security requirements, privacy, abuse cases, API/IAM/supply-chain security design, and (conditionally) AI-agent security — over the architecture and solution baselines, and normalize them into the existing G05 design evidence (threat-model, privacy-assessment, supply-chain-plan). Use when an architected, detailed solution (G04) must be modelled for abuse and given controls and security requirements before implementation. Do not use to verify an implementation, run a scanner, produce the G05 security-approval, accept residual risk, decide a gate, or invent architecture.
---

# BADF Security Design

`badf-security-design` is the **pre-implementation security composition and orchestration layer** for
G05. It consumes the architecture baseline (`badf-architecture`) and the solution baseline
(`badf-solution-design`), models how that intended system can be abused, derives controls and security
requirements, and **normalizes** its specialists' outputs into the **existing** G05 design evidence. It
is a router and constraint contract — **not** a scanner, a second gate, a security authority, or a
document-generation mega-skill.

Its live status is `badf/skill-registry.json`; this file defines the contract, not the status, and never
hardcodes a lifecycle status that can drift from the registry.

## Canonical principle

```text
Architecture declares the security-relevant structure (boundaries, trust, data flows, ownership).
Solution Design declares the detailed intended behavior (UX, API, IAM, data, audit).
Security Design models how that intended system can be abused, derives controls and security
    requirements, and packages normalized G05 evidence.
Security Assurance later determines whether the IMPLEMENTATION satisfies those obligations (G08/G09).
The canonical gate validates the evidence.
Only security authority may approve G05 or accept residual risk.
```

**Capability ≠ authority.** A component (or an agent, or a tool) being *able* to act never implies
*permission* to act. Security design's job is to make the difference explicit and defensible, not to
grant it.

## Design ≠ assurance (the hard scope line)

`badf-security-design` is **pre-implementation**. It reasons about a *design*, not a *build*. It does
**not** perform — and must not absorb — security **assurance/verification**:

```text
badf-security-design   (G05, PRE-implementation)   |   badf-security-assurance (future, G08/G09)
threat-model                                        |   security code review / SAST
security-requirements                               |   SCA / dependency CVE + reachability
privacy-analysis                                    |   secrets scanning
abuse-case-analysis                                 |   API/web/mobile attack-oriented review
api-security-design                                 |   IaC security review
iam-security-design                                 |   agent/MCP security audit
supply-chain-design                                 |   remediation verification
ai-agent-security-design [conditional]              |   security-validation (G09)
```

Absence of a design finding never establishes implementation security (SEC-I14). Assurance is a separate,
later capability that consumes the implementation; it is **out of scope here**.

## Boundary with badf-architecture and badf-solution-design

Security design **consumes**, it does not rediscover.

- **`badf-architecture`** owns boundaries, topology, trust transitions, data flows and ownership. Security
  design **may constrain** architecture but **must not silently invent or rewrite** an architectural
  boundary. When the architecture is insufficient for a required control:
  `ARCHITECTURE_CHANGE_REQUIRED → ADR / architecture revision → re-baseline → resume security design` (SEC-I05).
- **`badf-solution-design`** already owns the *functional* authorization seam
  (`principal · resource · action · scope · decision point · default deny · audit obligation`). Security
  design **challenges and secures** that contract — least privilege, bypass resistance, authentication
  assurance, separation of duties, cross-tenant isolation, audit tamper-resistance — it **does not
  recreate** a second, contradictory IAM model (SEC-I06). See `references/iam-security-contract.md`.

## Security requirements cannot silently expand scope

Security analysis often derives new requirements (e.g. "privileged operations require phishing-resistant
MFA"). The skill **may derive** them, but if a derived requirement materially changes product behavior or
scope it does **not** rewrite G02 in place:

```text
REQUIREMENT_CHANGE_REQUIRED → G02 requirements revision → solution/architecture reconciliation → resume G05
```

This preserves traceability; G05 never silently rewrites G02 (SEC-I04, and see `references/security-requirements.md`).

## Invariants (SEC-I01 … SEC-I15)

```text
SEC-I01  Exact baseline            every security conclusion binds the exact architecture and solution baselines it reasoned over
SEC-I02  Threat provenance         every material threat resolves to real assets, interfaces, data flows, trust boundaries or requirements
SEC-I03  Threat disposition        every material threat is controlled, explicitly deferred, blocked, or submitted for independent residual-risk acceptance
SEC-I04  Security traceability     a security requirement traces upstream to threat/requirement/NFR and downstream to a verification obligation; it cannot silently expand product scope
SEC-I05  Architecture fidelity     security design may constrain architecture but cannot silently invent or rewrite architectural boundaries (ARCHITECTURE_CHANGE_REQUIRED)
SEC-I06  Solution fidelity         security design challenges and secures the canonical IAM/API/data contracts; it cannot silently replace them with a second model
SEC-I07  Privacy flow completeness material personal/sensitive-data processing resolves to declared data flows
SEC-I08  Data protection           sensitive data has classification, purpose, protection and lifecycle (retention/deletion) treatment
SEC-I09  Supply-chain provenance   material third-party components carry admission / provenance / update obligations (design, not a scan)
SEC-I10  Agent least privilege     agent/tool/MCP capabilities are explicitly scoped when an agentic system exists (capability ≠ authority)
SEC-I11  Non-coverage declared     unobserved or unmodelled security surfaces are explicit; silence is not coverage
SEC-I12  Residual risk ≠ accepted  the skill may report residual risk but cannot self-accept it
SEC-I13  Approval separation       the skill cannot produce its own G05 security-approval; that is security_authority's, referencing exact digests
SEC-I14  Design ≠ verification     absence of a design finding does not establish implementation security (that is assurance, G08/G09)
SEC-I15  No second gate            no scripts/badf_security_design.py or competing validator; deterministic evidence semantics live in the canonical gate
```

See `references/threat-model-contract.md` for the machine-addressable threat shape, and the other
`references/*-contract.md` for each specialist's design surface.

## Lifecycle placement

`badf-security-design` composes into the **existing G05** — it adds **no** new gate and changes **no**
`lifecycle.json`. It normalizes its specialists into the three G05 **design** artifacts and leaves the
fourth to authority:

```text
G04 architecture + solution baseline → badf-security-design → { threat-model ; privacy-assessment ; supply-chain-plan }  (design evidence)
                                                              security-approval  ← produced by security_authority (NOT the skill)
```

See `references/g05-contract.md` and `references/normalization.md`.

## Workflow

`FRAME → INGEST → CLASSIFY → ROUTE → SPECIALIZE → RECONCILE → CHALLENGE → NORMALIZE → PACKAGE`

1. **FRAME** — scope the security design and its authority boundary; it is design, not assurance.
2. **INGEST** — the architecture baseline + ADRs + trust boundaries + data flows, the solution baseline
   (UX/API/IAM/data/audit), G02 requirements + NFRs. Bind their exact digests (SEC-I01).
3. **CLASSIFY** — data classification, agentic-vs-not, regulatory surface; decide which specialists apply
   (and record `NOT_APPLICABLE_WITH_REASON` for those that do not, e.g. `ai-agent-security-design` for a
   non-agentic app).
4. **ROUTE** — select only the specialists the work needs (`references/routing.md`); external
   methodologies (OWASP) are **REFERENCE / ADAPT**, never BADF authority.
5. **SPECIALIZE** — each specialist produces its domain contract (threat-model, security-requirements,
   privacy, abuse-case, api-security, iam-security, supply-chain, ai-agent-security).
6. **RECONCILE** — against the architecture and solution baselines (SEC-I05/I06); a boundary the baseline
   lacks raises `ARCHITECTURE_CHANGE_REQUIRED`; a security requirement that changes scope raises
   `REQUIREMENT_CHANGE_REQUIRED` — neither is patched silently.
7. **CHALLENGE** — adversarial and false-positive review; every material threat gets a disposition
   (SEC-I03); residual risk is reported, never self-accepted (SEC-I12).
8. **NORMALIZE** — fold specialist outputs into the three G05 design artifacts
   (`references/normalization.md`); declare non-coverage explicitly (SEC-I11).
9. **PACKAGE** — emit the G05 design evidence; the gate validates it, and **security_authority** produces
   `security-approval` and any residual-risk acceptance (SEC-I13). Never emit a gate outcome or an
   approval as this skill's own decision.

Read `references/acceptance.md` for the admission controls and the WP-SEC-A…E ladder, and
`references/external-methodology.md` for the OWASP methodology dispositions (reference-only). This skill
has **no authority of its own**: it composes and constrains; the canonical gate validates and
security_authority decides.
