# Execution budget

Autonomous execution is **bounded** (IMP-I11). Each WP carries an explicit budget so an agent knows where
the boundary is for *this* work, not merely that a global budget doctrine exists:

```yaml
execution_budget:
  max_attempts: 3
  max_elapsed_minutes: 120
  max_cost: <bounded-policy-value>
```

This converts BADF's global Engineering-Loop doctrine (max attempts; time/cost budget; root-cause mode
after repeated similar failures) into a **per-WP executable constraint**. A WP with no budget cannot be
handed to an autonomous executor — the stop point is undefined.
