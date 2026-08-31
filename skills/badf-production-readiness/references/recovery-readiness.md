# Recovery — backup ≠ restore

PRDY-I11, PRDY-I12.

## The distinction the invariant exists for (PRDY-I12)

A backup artifact establishes that data was written somewhere. It establishes nothing about whether it
can be read back, whether it is complete, whether the restore path works under the conditions that would
require it, or how long a restore takes. Backup is an artifact; recoverability is an observed property.
Only the second is readiness evidence.

```text
Claim                                          Establishes recoverability?
---------------------------------------------  ---------------------------
"backups are configured"                       no
"a backup artifact exists, dated <t>"          no
"the backup passes an integrity check"         no — integrity ≠ restorability
"a restore was performed and verified at <t>"  yes, for the conditions observed
```

## Recovery observations where applicable (PRDY-I11)

Resilience claims include **actual recovery observations** — a restore executed, a failover exercised,
a degraded mode entered and exited — not a plan describing one. Where a recovery observation is
genuinely impractical for this release, that is declared non-coverage with a reason, not a dimension
quietly marked `READY` on the strength of the plan.

## RPO and RTO are bound, not aspirational

```text
RPO   the maximum data loss the release is designed to tolerate — and the loss the OBSERVED restore showed
RTO   the maximum time to recover — and the time the OBSERVED restore took
```

A declared RPO/RTO with no observation against it is a target. A dossier that reports the target as
though it were a measurement is the proxy-for-property error in its operational form: the number is
real, it is just not a measurement of this system.
