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

BADF doctrine, preserved:

```text
same command + same hypothesis + same input
≠
new attempt
```

A repeat without a changed hypothesis, input, implementation or diagnostic does not consume a permitted
engineering attempt — and does not earn one either. Attempt, time or cost exhaustion yields `BLOCKED`
with the ledger and evidence so far; never an autonomous extension of the budget.
