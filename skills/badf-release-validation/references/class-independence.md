# class-independence.md — VAL-I03 / VAL-I13, stronger than G08 reviewer independence

G08 independence means *a different reviewer looked*. G09 independence is **stronger**: each
validation class is its own investigation with its own falsifiable claim, its own way of
observing, and its own record — so a green in one risk domain cannot borrow credibility for
another. A validation class establishes evidence **only for its own risk domain**; **no class
impersonates another** (**VAL-I03**); **no result is copied into several evidence slots**
(**VAL-I13**). This is what makes the conjunctive dossier (see
[g09-contract.md](g09-contract.md)) meaningful rather than a re-labelled single run.

## Each class carries its own six

A validation class — quality, security, performance, resilience — owns all six, distinctly:

- **risk hypothesis** — the falsifiable claim about *this* risk domain it tries to break.
- **method** — how it attempts to disqualify the candidate in that domain.
- **oracle** — the success/failure authority **outside the agent** (**VAL-I04**).
- **execution identity** — who/what ran it, bound with environment provenance (**VAL-I07**).
- **runtime result** — the deterministic observation of what actually happened.
- **non-coverage** — the material surfaces in its domain it did **not** establish (**VAL-I15**).

```
                 own hypothesis · own method · own oracle
                 own identity   · own result · own non-coverage
   QUALITY ───────────────┐
   SECURITY ──────────────┤   shared infrastructure is fine…
   PERFORMANCE ───────────┤   …shared EVIDENCE is not (VAL-I13)
   RESILIENCE ────────────┘
```

## Shared infrastructure, never shared evidence

Classes **may** share a cluster, a fixture set, a data seed, a CI runner, even a single test
harness. What they may **not** share is a **result standing in two required evidence slots**.
The distinction: infrastructure is *how* an observation is produced; evidence is *which risk
domain that observation establishes*. One run answers exactly one class's risk hypothesis.

## Substitution — the failures VAL-I13 forbids

| Attempted substitution | Why it is invalid |
| :--- | :--- |
| a k6 **average-load** run counted as `resilience-test` | it is a `performance-test`; average load is not fault injection, no steady-state/blast-radius/abort hypothesis, no observed recovery (**VAL-I10** vs **VAL-I11/I12**) |
| **Semgrep-green** counted as `security-validation` complete | one static observation is not the class; it carries no runtime attack evidence and no non-coverage of the surfaces it never reached (**VAL-I09**, **VAL-I15**) |
| **performance PASS** implying **resilience PASS** | different risk hypothesis and oracle; performing well under load says nothing about recovery after a fault (**VAL-I11/I12**) |
| **quality E2E-green** counted as `security-validation` | E2E exercises intended behavior; security tests abuse cases — different hypothesis, different oracle (**VAL-I03**) |
| a `security-validation` run reused as `performance-test` | security oracle judges control efficacy, not an SLO/budget; no bound performance threshold (**VAL-I06/I10**) |

In each case the copied result would fill a slot whose risk domain it never investigated.
The router assigns one obligation per class (see [validation-obligations.md](validation-obligations.md));
independence is what keeps each obligation honestly its own.

## Why independence is load-bearing

- The dossier is **conjunctive** — every required class must independently satisfy. If one
  result could satisfy several slots, "3 of 4 → majority" would sneak back in through copying,
  and a security blocker could be papered over by a well-performing candidate (**VAL-I14**).
- **Blocking findings are preserved per class.** Because each class owns its own runtime
  result and non-coverage, a blocker in one domain cannot be normalized away by another's
  green (**VAL-I14/I16**).
- **Same candidate, separate observations.** Every class binds the exact candidate
  (**VAL-I01**, see [candidate-binding.md](candidate-binding.md)) yet observes it through its
  own oracle — shared identity, independent evidence. Agent-authored scenarios in any class
  stay **draft** until that class's runtime validates and binds them (**VAL-I05**).
