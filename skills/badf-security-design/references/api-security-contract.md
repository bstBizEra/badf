# API-security contract (DESIGN, not review)

`api-security-design` is **design-time**: it specifies the security properties an API must be built with.
It is **not** the attack-oriented review that verifies whether those properties hold — that is assurance
(`badf-security-assurance`, G08/G09), adapted later from OWASP's API-security review workflow.

```text
DESIGN (here, G05)                         REVIEW / VERIFY (later, G08/G09)
authentication                             BOLA actually exploitable?
authorization (object ownership)           authentication bypass?
rate / resource controls                   mass assignment?
field-level exposure                       rate-limit bypass?
idempotency                                SSRF?
anti-automation                            unsafe downstream consumption?
input / output exposure                    shadow / undocumented API?
webhook trust                              …attack execution…
API inventory / version policy
```

## Shape (per protected operation)

```yaml
api_ref: API-...               # resolves to the solution baseline's API contract (SEC-I06)
authentication: "..."          # assurance level required
authorization_ref: ACT-...     # the solution IAM tuple this operation is bound to — referenced, not redefined
object_ownership: "..."        # how per-object ownership is enforced (anti-BOLA by design)
rate_controls: "..."
anti_automation: "..."
field_exposure: [...]          # request/response fields deliberately allowed; the rest denied
idempotency: "..."
webhook_trust: "..."           # if applicable
```

## Rules

- **Bind, don't redefine (SEC-I06).** Each operation references the solution baseline's `API-…` and
  `ACT-…`; api-security-design adds the *security properties*, it does not fork a second API/authz model.
- **Ownership by design.** Object-level authorization (the anti-BOLA property) is a design requirement per
  operation, not a review afterthought.
- **Design ≠ exploitability (SEC-I14).** This contract states what must be true; whether it *is* true in
  the build is proven by assurance, later.
