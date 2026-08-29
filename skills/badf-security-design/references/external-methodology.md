# External methodology provenance

Status: **REFERENCE / ADAPT ONLY — no external executable vendored, no external skill or agent granted
authority.**

`badf-security-design` adapts external security methodologies into BADF domain contracts and normalized
evidence. The external projects are references, not BADF authority; any future vendoring or direct
execution requires a separate external-skill admission WP under `docs/07-skills-governance.md`.

## The disposition, frozen

```text
OWASP Secure Agent Playbook / OWASP AppSec Agent
        =
EXTERNAL SECURITY METHODOLOGY  →  ADAPT

NOT
        =
BADF gate · BADF authority · BADF lifecycle · BADF evidence schema
```

The useful shape is always:

```text
specialized procedure → structured observation → BADF normalization → BADF evidence
```

never:

```text
OWASP agent says PASS → G05 PASS
```

That must never happen.

## Dispositions

| Source | BADF ADAPTs | BADF does NOT adopt |
| :--- | :--- | :--- |
| OWASP Secure Agent Playbook | procedural decomposition; OWASP/ASVS/CWE/OpenCRE traceability; structured finding format; API / agent / MCP / LLM security taxonomies; explicit evidence | its plugin lifecycle as BADF lifecycle; its agent output as gate authority; a scanner result as security-approval; remediation authority |
| OWASP AppSec Agent | the threat-model workflow; repository/PR context extraction; adversarial challenge; false-positive challenge; the reviewer → adversary → fixer → verifier **separation** (one step never blesses its own fix) | its code reviewer / PR reviewer / PR adversary / FP adversary / code fixer / QA verifier as BADF authority (those are **assurance**, adapted later by `badf-security-assurance`) |

## Where each adapted piece lands

- The **design-time** taxonomies (API Top 10 categories, agent/MCP/LLM concerns, CWE/ASVS references)
  are adapted at G05 as *design* checklists and threat categories.
- The **attack-oriented execution** (is this BOLA actually exploitable? is this CVE reachable? does this
  secret leak?) is **assurance** and is adapted later by `badf-security-assurance` at G08/G09 — not here
  (SEC-I14).

## Admission posture

External methodologies grant no tool access, no execution permission, no gate authority and no runtime
dependency. `badf-security-design` composes their *ideas* into contracts; the canonical gate validates
the resulting evidence, and `security_authority` dispositions delivery. External capability can produce
evidence; it can never expand authority.
