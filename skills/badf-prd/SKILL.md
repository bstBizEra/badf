---
name: badf-prd
description: Define, review, challenge, and prepare evidence for a BADF Gate G01 Product Requirements Document baseline. Use when creating or assessing product definition, PRD completeness, scope, product outcomes/KPIs, acceptance criteria, assumptions/constraints, stakeholders, initial RAID, or a PRD baseline request. Do not use for G02 requirement decomposition, architecture, implementation, release, or to issue PRD_BASELINED.
---

# BADF PRD

This skill prepares a PRD candidate for an independent BADF `G01` decision. It has **no gate authority**.

1. **FRAME** — Read repository `AGENTS.md`, resolve the active work package, confirm `G01`, product owner, source inputs, change/data class, and authority boundary. Stop mutation if material work has no active authority.
2. **DISCOVER** — Inspect existing product intent, PRD, decisions, research, user evidence, metrics, constraints, dependencies, and prior G01 evidence. Prefer established facts over asking the user to restate discoverable information.
3. **DEFINE** — Build the product definition and PRD using `references/g01-contract.md`: identity, overview, problem, target users, value proposition, vision, objectives, scope, capabilities, differentiation, success metrics, stakeholders, assumptions, constraints, RAID, legal/regulatory/data considerations, and acceptance criteria.
4. **CLARIFY** — Resolve factual gaps from evidence first. Identify assumptions explicitly. Ask for product choices only when they are genuinely unresolved decisions and cannot be established from approved sources.
5. **CHALLENGE** — Stress-test material decisions independently. Walk the decision tree for problem validity, target users, value, why-now, scope boundaries, success metrics, acceptance, dependencies, constraints, and material risks. Record findings with severity, evidence, and `RESOLVED`, `ACCEPTED_AS_RISK`, or `BLOCKING`; record unresolved decisions separately.
6. **COMPLETE** — Check that each product objective maps to measurable KPI IDs, in-scope and out-of-scope do not overlap, acceptance criteria are testable, and no required G01 field is represented by a placeholder or silent omission.
7. **VALIDATE** — Materialize the candidate from `templates/prd-baseline.json` and run `python3 scripts/badf_prd.py validate <path>`. Treat exit `2` as invalid evidence and exit `3` as `REWORK_REQUIRED`.
8. **EVIDENCE** — Bind claims and approval references using `docs/05-evidence-and-provenance.md`. A product-owner approval is independent evidence; the PRD author must not manufacture it.
9. **DELIVER** — Report only `ELIGIBLE_FOR_G01_REVIEW`, `REWORK_REQUIRED`, or `BLOCKED`, plus evidence and unresolved items. Never emit `PRD_BASELINED`, `PASS`, or an approval as this skill's own decision.

Read `references/g01-contract.md` for the canonical field and state contract. Read `references/source-patterns.md` when adapting external methodology.
