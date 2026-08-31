# Diagnostics supplement the oracle; they never replace it

UAT-I06, UAT-I10. The business oracle is the scenario's `expected_business_outcome` — a human-readable
statement of what the business approved. Console errors, network traces, accessibility scans and i18n
checks are diagnostic signal collected *alongside* an execution; they explain a failure, they do not
define acceptance.

```text
Business oracle   "the customer sees their order confirmed with the correct total"   ← authoritative
Diagnostics       zero console errors, response time, WCAG pass, correct locale       ← supplementary
```

A scenario can PASS its business oracle while diagnostics show a non-blocking issue (logged, not fatal
to acceptance) — and a scenario can technically render with zero console errors while failing the
business oracle. The two are recorded separately (`diagnostics_ref` on the observation, per
`references/execution-adapters.md`) and never merged into one verdict. Confusing "the page loaded
cleanly" with "the business accepted this" is exactly the technical-E2E-≠-UAT distinction this skill
exists to enforce (UAT-I03).
