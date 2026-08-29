# Privacy contract

`privacy-analysis` normalizes into the G05 **privacy-assessment** artifact. It is a *design* obligation:
what personal/sensitive data the intended system processes, why, and how it is protected across its
lifecycle — not a scan of a running system.

## Shape

```yaml
data_flow_ref: DF-...         # resolves to an architecture/solution data flow (SEC-I07)
data:
  classification: PII         # PII | SENSITIVE-PII | FINANCIAL | HEALTH | CREDENTIAL | NONE
  elements: [...]
purpose: "..."                # why it is processed (lawful-basis surface)
collection: "..."             # how/where it enters
protection:
  in_transit: [...]
  at_rest: [...]
  access_control_refs: [ACT-...]   # ties to the solution IAM contract (SEC-I06)
retention: "..."              # how long, and the clock
disclosure: [...]             # who/what it is shared with, incl. third parties/sub-processors
deletion: "..."               # deletion/erasure treatment
```

## Rules

- **Flow completeness (SEC-I07).** Every material personal/sensitive-data processing resolves to a
  **declared data flow** in the baseline. Data that appears in a control but in no flow is a seam defect.
- **Lifecycle completeness (SEC-I08).** Sensitive data has classification, purpose, protection
  (transit + rest), retention and deletion treatment. A field with no lifecycle is unfinished.
- **Access control is referenced, not recreated (SEC-I06).** Privacy binds to the solution baseline's
  authorization contracts (`ACT-…`) rather than defining a parallel access model.
- **Non-coverage explicit (SEC-I11).** A data domain not analyzed (e.g. a third-party sub-processor out of
  scope this WP) is named, not silently omitted.
