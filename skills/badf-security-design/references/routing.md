# Routing

The root skill routes each security concern to the specialist that owns it, and selects **only** the
specialists the work needs. External methodologies (OWASP) are **REFERENCE / ADAPT**, never BADF
authority:

```text
external methodology = REFERENCE / ADAPT     (not:  external agent output = BADF authority)
```

## Signal → specialist

| Signal | Specialist (design contract) |
| :--- | :--- |
| asset, entry point, attack path, trust-boundary crossing | `threat-model` |
| a derived security control that must become a requirement | `security-requirements` (cross-cutting) |
| personal / sensitive data, purpose, retention, disclosure | `privacy-analysis` |
| adversarial *business* behavior (replay, abuse of a legitimate flow) | `abuse-case-analysis` |
| endpoint auth, object ownership, anti-automation, field exposure | `api-security-design` |
| authentication assurance, least privilege, bypass resistance, isolation | `iam-security-design` |
| dependency admission, provenance, SBOM, signing, secret distribution | `supply-chain-design` |
| agent identity/authority, tool/MCP capability, prompt trust, delegation | `ai-agent-security-design` **[conditional]** |
| architecture boundary / topology / trust decision | **`badf-architecture`** (the spine, not a specialist) |
| detailed functional IAM/API/data behavior | **`badf-solution-design`** (the solution baseline, consumed) |
| uncertainty requiring evidence | **`badf-research`** |
| verifying an implementation (SAST/SCA/secrets/IaC/code review) | future **`badf-security-assurance`** (G08/G09) — **not here** |

## Routing rules

- Route the minimum: an unneeded specialist is scope, not thoroughness. A specialist that does not apply
  is recorded `NOT_APPLICABLE_WITH_REASON`, not silently dropped (SEC-I11).
- `ai-agent-security-design` is **conditional**: for a non-agentic application it is
  `NOT_APPLICABLE_WITH_REASON`; for BADF itself or any agentic project it routes automatically and is
  first-class.
- A signal that names an architectural boundary/interface/owner routes to `badf-architecture`, not to a
  security specialist — security design details and constrains interfaces, it does not invent them (SEC-I05).
- A signal about detailed *functional* authorization routes to the **solution baseline**; security design
  **secures and challenges** it (least privilege, bypass resistance), it does not recreate it (SEC-I06).
- An assurance signal (scan a repo, find a CVE, review a PR, verify a fix) routes to the future
  `badf-security-assurance`, never to this skill (SEC-I14).
- No specialist is **activated** at contract-freeze — routing names who *would* own each concern;
  specialist activation is a later WP.
