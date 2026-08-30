# Self-review vs independent review (BLD-I15)

The source methodologies invoke code review after implementation, per task and for the whole branch.
BADF keeps that discipline — and distinguishes what it is:

```text
BUILD REVIEW
=
author-side challenge

G08 INDEPENDENT REVIEW
=
independent assurance evidence
```

A reviewer dispatched by the same build controller may improve code quality, but does **not automatically**
satisfy G08 `independent-review` unless BADF's separation-of-duties contract proves genuine independence
(a different principal, not the author's delegate, with its own authority to refuse).

```text
self-review · task-review · branch-review
       ↓
G07 author verification evidence

NOT automatically

G08 independent-review
```
