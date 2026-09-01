# Identity attribution — what the record can and cannot establish

**Status:** the structural half is NOT implemented. This document specifies it, codifies the
interim convention, and states precisely what remains unverifiable until an operator
provisions the identities. **It does not discharge M1 EC2; it prepares it.**

## 1. The measured baseline

Every landing on this repository, measured at `main@d82b6685`:

```
#290  merged_by bstBizEra   user bstBizEra
#297  merged_by bstBizEra   user bstBizEra
#298  merged_by bstBizEra   user bstBizEra
```

All seats share one account, so **`merged_by` is constant across every act and discriminates
nothing.** An audit can verify every gate, verdict, SHA and content tree of a landing and
cannot verify a single executor.

This is strictly worse than the comment half. `AGENTS.md` already rules that banners and
`<!-- agent: … -->` trailers are self-asserted text and must never gate a decision — a
banner is *prose a reader can discount*. A merge is an **action whose actor field is
uniformly and silently wrong**: it names an account that did technically perform it, so
nothing signals that the answer is uninformative.

**Consequence, stated plainly:** a compliant configuration (author ≠ merger, operator
delegation held) and a non-compliant one (a seat merging its own work with no delegation)
produce **byte-identical artifacts**.

## 2. The identity contract

**Minimum viable split — ONE structural identity, not per-seat.**

| | |
| :--- | :--- |
| **Identity** | `bst-sa-agent[bot]` (GitHub App or machine account) |
| **Used for** | delegated merge acts only — the acts where "who did this, under what authority" is currently unanswerable |
| **May hold** | a token scoped to merge PRs on this repository, nothing else |
| **May not hold** | repository administration, secrets access, force-push, branch-protection changes |
| **Custody** | operator-held; no seat receives it, reads it, or stores it |

**Per-seat identities are deferred, deliberately** — the Lean ladder's rung ⑤ before ⑥. One
identity answers *"was this act performed under a delegation, or by an author on their own
work?"*, which is the question the record cannot answer today. Five identities would answer
*"which seat"* — a question no incident has yet required. Deferred, not rejected: the trigger
is a concrete case where per-seat attribution would have changed a decision.

### The delta — what becomes verifiable

Stated as a difference rather than a capability list, because the value is only in the change:

| Question | Today | After |
| :--- | :--- | :--- |
| Did a human or an agent execute this merge? | **unanswerable** | `merged_by` discriminates |
| Was this a delegated act or an author merging their own work? | **unanswerable** | discriminable when the author is a seat and the merger is the bot |
| Which seat executed it? | unanswerable | **still unanswerable** (single identity) |
| Did the delegation actually exist? | unanswerable | **still unanswerable** (see §5) |

## 3. The interim norm — codifying an observed convention

The executor of any merge posts a comment at merge time naming its seat and the delegation it
acted under. **This is already practised**, not proposed — measured across every landing since
it was adopted:

```
#290  1 executor statement    #297  1    #298  1
```

**Its honesty framing is part of the norm and must travel with it:**

- **Self-asserted.** The comment is text under the same shared account as every other comment.
- **Unverifiable from outside.** No reader can confirm the delegation existed.
- **Falsifiable in one direction only.** Its *absence* is checkable; its *presence* proves nothing.

It converts "no artifact" into "a claim a reader can challenge" — which is exactly what the
banner regime already provides for comments, and no more. **A reader who mistakes this for
verification has been misled by the record, not by the seat.**

## 4. Operator runbook — every step `HUMAN_REQUIRED`

None of these is performable by a seat. Account-plane work with credential handling is not a
seat's act under the authority matrix, and this is a boundary rather than a preference.

1. **HUMAN_REQUIRED** — create the `bst-sa-agent` GitHub App (or machine account) under the
   `bstBizEra` organisation.
2. **HUMAN_REQUIRED** — grant it exactly one permission on `bstBizEra/badf`: pull requests,
   write. Verify no administration, contents-write, or secrets scope is attached.
3. **HUMAN_REQUIRED** — install it on `bstBizEra/badf` only.
4. **HUMAN_REQUIRED** — store its token where the operator's own credentials live. No seat
   receives it; no seat-facing config references it.
5. **HUMAN_REQUIRED** — perform one merge through it and confirm `merged_by` reads the bot.
   *This is the acceptance test: until one landing shows a discriminating `merged_by`, the
   split is specified and not proven.*
6. Then, and only then, the ratcheted guard becomes writable (§6).

## 5. What remains unverifiable after this lands

Enumerated so that nobody reads this document as closing EC2:

1. **The delegation itself.** A bot merge proves an act was routed through the delegated path;
   it does not prove an operator authorised *that* act. Channel-bound authorization (AET-I13)
   is a separate control.
2. **Which seat acted.** One identity by design; per-seat attribution is deferred.
3. **Comment authorship.** Unchanged — banners stay self-asserted. This document addresses the
   *merge* half only.
4. **History.** `merged_by` on every existing landing stays as measured. The record is not
   rewritten; the doctrine explains the epoch.

### The adversarial case

The criteria above are satisfiable by a configuration that changes **nothing**: provision the
bot, then **distribute its token to all five seats**. Every criterion passes — a structural
identity exists, `merged_by` is no longer the human account, the runbook was followed — and
attribution is exactly as unverifiable as today, because one shared credential across five
actors is the same defect wearing a new name.

**Refused by §2's custody row**, which is therefore the load-bearing line of this document and
not an administrative detail: *operator-held; no seat receives it, reads it, or stores it.* A
reviewer checking this work should check custody first and the rest afterwards.

## 6. The follow-on, named rather than stubbed

Once a landing demonstrates a discriminating `merged_by`, a ratcheted guard can require that
delegated merges after a declared threshold carry the structural actor — grandfathering
current history as measured-not-rewritten, in the same shape as the surface and seat ratchets.
**It cannot be written before the identity exists**, because it would have nothing to assert
against and would pass vacuously — a guard whose subject is absent is indistinguishable from a
guard that works.
