# Supply-chain contract (DESIGN, not SCA)

`supply-chain-design` normalizes into the G05 **supply-chain-plan** artifact. It is **policy and
obligation design** — what the supply chain must guarantee — **not** the actual dependency scan. The scan
(SCA: real dependency graph, real CVEs, reachability, SBOM validation, malicious-package detection) is
**assurance** at G09, adapted later from OWASP's `sca-audit`, never a G05 design subskill (SEC-I09/I14).

```text
G05 — supply-chain DESIGN (here)          G09 — supply-chain ASSURANCE (later)
allowed registries                        actual dependency graph
dependency admission policy               actual CVEs
version / pinning policy                  reachability
provenance requirements                   actual SBOM
SBOM obligation                           signature validation
signing / attestation                     provenance validation
package admission                         malicious-package detection
secret-handling / distribution design     license / policy violations
base-image policy
update / vulnerability SLA
third-party trust policy
```

## Shape

```yaml
allowed_registries: [...]
dependency_admission_policy: "..."
version_policy: "..."          # pinning / range rules
provenance_requirements: [...]
sbom_obligation: "..."
signing_attestation: "..."
secret_distribution: "..."     # design of how secrets reach components (not the secrets)
update_policy: "..."
vulnerability_sla: "..."
base_image_policy: "..."       # if applicable
```

## Rules

- **Obligation, not observation (SEC-I09).** Each material third-party component carries an admission /
  provenance / update *obligation*. Whether a specific installed version has a CVE is assurance's job,
  later.
- **Secret handling is designed, never embedded.** The plan designs how secrets are distributed and
  scoped; it contains no secret material.
- **Design ≠ scan (SEC-I14).** A green SCA later does not retroactively become G05 evidence; a supply-chain
  plan here does not establish the built dependency graph is clean.
