# Test planning

Every acceptance claim has a **verification obligation** (IMP-I09). The `test-plan` aggregates the per-WP
obligations into the chain:

```text
AC → WP → test → evidence
```

across levels: `unit`, `contract`, `integration`, `security`, `migration`, `performance`, `composed-tree`.

```yaml
test_obligations:
  - id: TEST-031, claim: AC-021, level: integration
  - id: TEST-032, claim: AC-022, level: unit
```

A WP whose acceptance criterion has no test obligation is an incomplete plan — "green" cannot be defined,
so the WP cannot be safely executed.
