# Advanced Engineering Loop

Status: **NORMATIVE**

## Loop

1. **FRAME** — resolve work package, goal, gate, acceptance, constraints, risks, and authority.
2. **DISCOVER** — inspect current code, policies, history, dependencies, runtime facts, and prior evidence.
3. **PLAN** — decompose into reversible steps; define tests, evidence, rollback, and stop conditions.
4. **AUTHORIZE** — confirm the planned mutations and tools are within granted scope.
5. **BUILD** — make the smallest coherent change; preserve unrelated work.
6. **VERIFY** — run targeted checks, then the broader required suite on the actual composed result.
7. **CHALLENGE** — obtain independent security, architecture, quality, operations, and product lenses proportional to risk.
8. **RECONCILE** — compare findings and evidence with acceptance criteria; resolve contradictions and drift.
9. **DELIVER** — produce the review/release packet and an explicit disposition.
10. **OBSERVE** — verify runtime technical, security, and business behavior after deployment.
11. **LEARN** — promote validated patterns; update memory, skills, tests, and policy through governed work.

## Autonomous-loop controls

- Set a maximum attempt count and time/cost budget before execution.
- Each retry must change a hypothesis, input, implementation, or diagnostic—not merely repeat.
- Stop immediately for authority conflict, credential exposure, unexpected destructive scope, policy bypass, evidence corruption, or production instability.
- After two materially similar failures, switch to root-cause diagnosis.
- After the retry budget, emit a blocked handoff with reproduction and next decision required.
- Autonomous execution may prepare decisions; it may not assume reserved authority.

## Composition discipline

When several branches or agents contribute, maintain an ordered change set. Recompute the merge base and expected result tree after every upstream movement. Tests and approvals bind to the composed tree digest. Source-head success alone does not establish integration safety.

## Definition of done

Done is conjunctive: accepted behavior, required quality, secured design, verified composed change, updated documentation/contracts, deployability, observability, rollback, evidence completeness, and authority-compliant disposition.

