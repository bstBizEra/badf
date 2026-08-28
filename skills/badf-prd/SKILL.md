---
name: badf-prd
description: Define, review, challenge, and prepare G01 evidence for a BADF Product Requirements Document. Use when creating or assessing product definition, PRD completeness, scope, product outcomes/KPIs, acceptance criteria, assumptions/constraints, stakeholders, initial RAID, or a product-owner approval. Do not use for G02 requirement decomposition, architecture, implementation, release, or to decide a gate.
---

# BADF PRD

This skill prepares the three G01 evidence artifacts for an independent BADF `G01` decision. It has **no gate authority** and no validator of its own: the gate opens the artifacts (`docs/01-lifecycle-gates.md`, *G01 evidence contract*).

1. **FRAME** — Read repository `AGENTS.md`, resolve the active work package, confirm `G01`, product owner, source inputs, change/data class, and authority boundary. Stop if material work has no active authority.
2. **DISCOVER** — Inspect existing product intent, PRD, decisions, research, user evidence, metrics, constraints, dependencies, and prior G01 evidence. Prefer established facts over asking the user to restate discoverable information.
3. **DEFINE** — Build the product definition from `templates/prd.json` using `references/g01-contract.md`: identity, overview, problem, target users, value proposition, vision, objectives, scope, capabilities, differentiation, success metrics, stakeholders, assumptions, constraints, RAID, legal/regulatory/data. Record the author.
4. **CLARIFY** — Resolve factual gaps from evidence first. Identify assumptions explicitly. Ask for product choices only when they are genuinely unresolved decisions.
5. **CHALLENGE** — Stress-test material decisions independently: problem validity, target users, value, why-now, scope boundaries, success metrics, acceptance, dependencies, constraints, material risks. Unresolved decisions stay visible; they do not become placeholders.
6. **COMPLETE** — Each objective maps to declared KPI ids; in-scope and out-of-scope do not overlap; acceptance criteria (`templates/acceptance-criteria.json`) are testable and reference objectives; no field carries a placeholder.
7. **VALIDATE** — Assemble the G01 dossier with the three evidence records and run `python3 scripts/badf_gate.py dossier <dossier>`. Exit 0 is the only pass; a refusal names the defect.
8. **EVIDENCE** — The product-owner approval (`templates/product-approval.json`) is a human act bound by digest to the exact PRD bytes; the PRD author must not produce it.
9. **DELIVER** — Report the gate's verdict and the unresolved items. Never emit an approval or a gate outcome as this skill's own decision.

Read `references/g01-contract.md` for the field contract and `references/source-patterns.md` for adapted external methodology (salvaged from PR #44, `e3cfde1`).
