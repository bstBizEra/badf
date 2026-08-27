# Operations, Resilience, and Learning

Status: **NORMATIVE**

## Operational acceptance

Before G13, define service owner, SLI/SLO/error budget, on-call/escalation, dashboards and alerts, dependency health, capacity, cost guardrails, backups, restore and disaster-recovery objectives, runbooks, maintenance, support, security monitoring, and stabilization window.

## Incident loop

`DETECT -> TRIAGE -> CONTAIN -> RECOVER -> VERIFY -> COMMUNICATE -> LEARN`

Preserve timeline and evidence. Prefer restoration of safe service over speculative root-cause changes during active response. Track customer/data impact and regulatory notification obligations. Test recovery and close corrective actions through work packages.

## Learning loop

1. collect defect, incident, review, delivery, and runtime signals;
2. distinguish one-off event from reusable pattern;
3. reproduce and validate the pattern;
4. propose a test, skill, memory, tool, or policy change;
5. review for overfitting and unintended constraints;
6. deploy in shadow mode and measure;
7. ratify, version, monitor, or revoke.

Agents may propose self-improvements but may not activate changes to their own authority, gates, or safety controls without independent review and required human ratification.

## Closure

G14 reconciles PRD outcomes and production KPIs, records accepted residual risk and debt, closes temporary access/exceptions, seals the evidence index, updates runbooks/knowledge, and assigns follow-up work. Closure is reversible if later evidence invalidates a claim.

