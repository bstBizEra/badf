# External Methodology Sources for `badf-prd`

Research baseline: **2026-08-27**. These are methodology references only. No third-party executable or source text is vendored by this skill.

## GitHub Spec Kit

Repository: `https://github.com/github/spec-kit`

Patterns adapted conceptually: specification before implementation; explicit clarification before planning; checklist-driven completeness; cross-artifact analysis for contradictions/omissions; deterministic artifact progression rather than one free-form prompt.

BADF difference: Spec Kit workflow output is capability evidence. BADF work packages, evidence binding, gate dossiers, and authority remain outside the skill.

## Platform Product Skills

Repository: `https://github.com/linyindong/platform-product-skills`

Patterns adapted conceptually: platform/product PRD construction, scope checking, PRD review as a distinct activity, and workflow/flow modeling where product behavior needs clarification.

BADF difference: `badf-prd` normalizes product content into the G01 contract and refuses to treat review completion as approval.

## Product on Purpose — PM Skills

Repository: `https://github.com/Product-On-Purpose/pm-skills`

Patterns adapted conceptually: predictable PRD structure; problem and why-now framing; measurable metrics; scope, requirements, risks, and dependencies as explicit sections; standards-compliant Agent Skill packaging.

BADF difference: G01 requires BADF-native provenance, acceptance, challenge, and product-approval evidence.

## Matt Pocock — Grilling / Challenge Pattern

Repository: `https://github.com/mattpocock/skills`

Patterns adapted conceptually: stress-test decisions through a decision tree; establish discoverable facts from environment/evidence first; focus operator questions on genuine decisions, trade-offs, and ambiguity.

BADF difference: challenge findings are structured evidence and never confer authority.

## Adoption rule

External sources remain `REFERENCE`/`ADAPT` inputs. Any future vendoring or execution of external scripts requires separate provenance, license, security, dependency, and skill-admission review under `docs/07-skills-governance.md` and `docs/09-security-supply-chain.md`.
