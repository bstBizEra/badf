# IAM-security contract (secure and challenge — do not duplicate)

`badf-solution-design` already owns the **functional** authorization seam. `iam-security-design` **secures
and challenges** that contract; it **must not** recreate a second, contradictory IAM model (SEC-I06). Two
IAM models is the failure this contract exists to prevent.

## Ownership split

| Solution design owns (functional) | Security design owns (security) |
| :--- | :--- |
| who can perform business action X? | can this privilege be escalated / bypassed? |
| resource / action / scope | least privilege |
| authorization decision point | trust / security of the PDP / PEP |
| role / scoping semantics | separation of duties |
| default deny (`NO MATCH = DENY`) | bypass resistance |
| functional identity need | authentication assurance (incl. step-up / phishing-resistant MFA) |
| API authorization mapping | token / session / service-identity security |
| audit obligation exists | audit tamper-resistance and coverage |
| tenant scope | cross-tenant isolation |

## Shape

```yaml
authorization_ref: ACT-...     # the solution baseline tuple being secured (SEC-I06)
authentication_assurance: "..."   # e.g. step-up for privileged operations
least_privilege: "..."            # the minimal grant, and what is explicitly denied
bypass_resistance: [...]          # how the PDP/PEP cannot be sidestepped
separation_of_duties: "..."       # where required
isolation: "..."                  # cross-tenant / cross-principal isolation
audit_integrity: "..."            # tamper-resistance + coverage of the audit obligation
```

## Rules

- **Reference the canonical tuple (SEC-I06).** Every entry binds a solution `ACT-…`. Security design adds
  assurance and resistance properties; it does not invent new principals, resources, actions or scopes —
  those that are genuinely new are `REQUIREMENT_CHANGE_REQUIRED` back to solution/requirements.
- **Least privilege is explicit.** "Admin can do everything" is not a security design; the minimal grant
  and the explicit denials are stated.
- **Capability ≠ authority.** Being able to reach an endpoint is never permission to act on it; the PEP
  enforces the tuple, and its bypass resistance is designed, not assumed.
