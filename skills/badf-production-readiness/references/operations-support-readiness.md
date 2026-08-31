# Operations and support ownership — a service with no owner is not ready

PRDY-I16, PRDY-I17.

## Operations ownership (PRDY-I16)

**A mandatory production service cannot be `READY` without an identified accountable service/on-call
owner.** Not a team name that resolves to nobody at 3am; an ownership record that answers who is
paged, from which rotation, with what escalation when they do not answer.

```text
service owner       accountable for the service's continued operation
on-call rotation    who is reachable, and when
runbook             what they do — bound to the observability response actions (PRDY-I15)
escalation path     who is reached when the first owner does not respond
```

An unowned service does not fail at release; it fails the first time it degrades, and the failure mode
is that nothing happens. That is why ownership is a readiness dimension rather than an operational
detail settled later — "later" is after the incident.

## Support ownership (PRDY-I17)

**Customer/user-impacting releases identify support and escalation ownership.** The delta
(`references/release-delta.md`) determines whether a release is user-impacting; where it is:

```text
support ownership      who receives and triages user reports about this change
change communication   who tells users the change is happening, and when
escalation             how a support signal reaches the engineering owner above
```

## Why these two are one reference

Operations ownership answers "who is paged when the system tells us"; support ownership answers "who
acts when a *user* tells us". They are the same escalation graph entered from two directions, and they
must terminate at the same accountable owner or the release has two disconnected response paths. Split
across two documents, each would define an escalation the other did not know about. Consolidated per
the Lean minimality ladder — a genuinely inseparable concern, not a dropped one.

## Ownership is resolved, not assigned

This skill resolves the ownership records that exist. It does not assign owners, create rotations, or
nominate an escalation path — that is an operational decision by the owning organization (PRDY-I01).
Its output where ownership is absent is `NOT_READY` naming the unowned service.
