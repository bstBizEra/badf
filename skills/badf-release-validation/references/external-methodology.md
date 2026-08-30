# external-methodology.md — adapt the method, never the authority

Status: **REFERENCE / ADAPT ONLY — no external executable vendored, no external tool granted
authority.**

`badf-release-validation` draws validation *method* from external sources and puts every
resulting artifact back inside BADF's candidate-binding, evidence, identity, and authority
envelope. The one rule that governs all of them: **adapt evidence and check patterns, never
decision authority.** An external skill's "GO" is not a BADF gate verdict. Vendoring or
executing any source requires a separate external-skill admission WP under skills
governance.

## Disposition table

| Source | Disposition | ADAPT | REJECT / do not import |
| :--- | :--- | :--- | :--- |
| `petrkindlmann/qa-skills` | ADAPT taxonomy + procedures | risk routing, E2E, accessibility, DB/migration, release-evidence patterns, chaos | its lifecycle/authority — its `release-readiness` is a **G10** go/no-go, never G09 |
| Grafana `k6` skills | ADAPT deeply (performance) | SLO-backed thresholds, workload classes, load-generator monitoring, immutable run investigation | any run interpreted as PASS without a bound budget (**VAL-I10**) |
| OWASP Secure Agent Playbook | ADAPT as **primary** security family | threat-driven validation, attack-oriented checks, control verification | a scanner's "clean" as risk acceptance (**VAL-I09**) |
| Individual scanners / test tools | Adapter / observation producer | raw runtime observations bound to a candidate | any tool ruling treated as a BADF authority decision |

### qa-skills — the boundary trap

`qa-skills` supplies the richest validation-method taxonomy: risk routing, E2E, exploratory,
accessibility, DB/migration, release-evidence, chaos. Adopt its check catalog and evidence
patterns freely. But its own `release-readiness` skill emits a **release go/no-go** — that is
**G10 authority** (`release_authority`), not G09. Importing its taxonomy while importing its
decision authority would collapse **VAL-I18** on day one. Adapt the checks; leave the verdict
at G10.

### k6 — performance without conformance drift

k6 is adapted as the performance methodology: workload families (smoke / average / stress /
spike / soak / breakpoint), SLO-backed thresholds bound *before* the run (**VAL-I06**),
load-generator health monitoring, and immutable-run investigation. A metric without a bound
SLO is a measurement, not a `performance-test` PASS (**VAL-I10**).

### OWASP Secure Agent Playbook — primary security family

The OWASP playbook is the primary security methodology for `security-validation`. Scanners
(Semgrep, dependency audit, DAST) are **observation producers** underneath it, never
authority. A security validator cannot waive or accept its own discovered residual risk
(**VAL-I09**); a single green scan is one observation, not `security-validation` complete.

## External → BADF gate placement

Where a given external testing discipline lands in the BADF lifecycle — so nothing is
imported into the wrong gate:

```text
test strategy / test planning ..................... G06
unit testing ...................................... G07
API / contract / integration engineering ......... G08
exploratory · E2E · accessibility ·
  cross-browser · data validation ................ G09  (quality-validation)
security testing .................................. G09  (security-validation)
performance · load · stress · soak ................ G09  (performance-test)
chaos · fault injection · recovery ................ G09  (resilience-test)
release-readiness ................................. G10  — NOT G09
testing-in-production · synthetic-monitoring ...... G12 / G13
quality postmortem · production→test learning ..... G14
```

The four G09 rows are exactly the four evidence types this capability composes. Everything
above G09 (unit, integration, contract) is earlier-gate engineering; everything below
(release-readiness, production monitoring, postmortem learning) is later-gate authority.

## The frozen rule

```text
"qa-skills says GO"        ≠  BADF G10 authorization
an external scanner "clean" ≠  security-validation PASS
an external run "under budget" ≠ performance-test PASS without a bound SLO
```

Adapt the method, the taxonomy, the check patterns, and the evidence shapes. **Never adapt
the decision authority.** A G09 result stays G09 evidence; `quality_authority` decides G09
PASS, and G10 alone owns release readiness (**VAL-I18**). See
[g08-g09-g10-boundary.md](g08-g09-g10-boundary.md).
