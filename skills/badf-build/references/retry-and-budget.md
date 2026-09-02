# Retry and budget — retries must add information (BLD-I11, BLD-I12)

The build does not "keep trying until it works". It inherits the BADF Engineering Loop and the Work
Package's `execution_budget`:

```text
attempt 1
   ↓ failure
change hypothesis
   ↓
attempt 2
   ↓ materially similar failure
ROOT_CAUSE_MODE
   ↓
attempt 3
   ↓ budget exhausted
BLOCKED HANDOFF
```

> **The `1 / 2 / 3` above is an ILLUSTRATION, not a threshold.** It shows the *shape* — each attempt
> changes a hypothesis, a materially similar failure enters `ROOT_CAUSE_MODE`, exhaustion hands off
> `BLOCKED` — using three attempts because a diagram needs a number. **Three is not the limit.**
>
> **The normative value is the Work Package's `execution_budget.max_attempts`**, which the schema
> requires (`schemas/work-package.schema.json`, `execution_budget.required: ["max_attempts"]`) and the
> gate enforces: a build whose retries exceed it is refused, and *a recorded `STOP` dominates the
> count* (`badf_gate.py:1794-1803`). The parallel control for work-breakdown tasks refuses a budget
> that is not a positive integer — IMP-C3 / IMP-I11, `badf_gate.py:1653-1658`.
>
> So a Work Package declaring `max_attempts: 5` gets five, and one declaring `2` gets two. **Reading
> `3` off this diagram would under-run the first and over-run the second.**

BADF doctrine, preserved:

```text
same command + same hypothesis + same input
≠
new attempt
```

A repeat without a changed hypothesis, input, implementation or diagnostic does not consume a permitted
engineering attempt — and does not earn one either. Attempt, time or cost exhaustion yields `BLOCKED`
with the ledger and evidence so far; never an autonomous extension of the budget.
