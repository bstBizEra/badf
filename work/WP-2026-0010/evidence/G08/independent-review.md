# Independent review — fix/conflict-protocol-vocabulary-audit (99fc259 over ace1e57)

principal: g08-independent-reviewer · type: agent · blind to author reasoning · read-only at two SHAs

## Verdicts by dimension
| dimension | verdict | evidence (new revision) |
|---|---|---|
| 1 correctness of the claim | MAJOR | heading L108 and sentence L131 both say eight and agree; but a blank line at L118 terminates the GFM table, so the RENDERED page shows six rows. The count is right in source and wrong on the page. Pre-existing; inside scope. |
| 2 token cross-membership | NONE | mechanical count over L112-L120: exactly 3 tokens in >1 set. REJECTED x4, APPROVED x2, HUMAN_REQUIRED x2. Base falsely claimed APPROVE_WITH_CONDITIONS in two sets (it is in one); change removes it. Every assertion at new revision is true. |
| 3 collateral | MINOR | L187 changes `C5 -> REJECTED` to `C5 -> conflict REJECTED`: a compliance edit applying the doc's own "always name the set" rule. Meaning preserved; not covered by a "count fix" description. |
| 4 cross-document drift | MAJOR | DELIVERY_LIFECYCLE.md:123 still says "three verdict vocabularies"; TWO_PLANE_DECISION_MODEL.md:92 says "three shared tokens across six sets" (measured: two). Both now contradicted. |
| 5 non-coverage | declared | did not read PR/commit body (independence); did not run tests (none reference this doc); rows 4 and 6 have no external source to verify against; rendering checked with markdown-it-py not cmark-gfm. |

## OVERALL = APPROVE_WITH_CONDITIONS
- C1 delete L118 so the rendered table carries the eight rows the heading claims
- C2 correct DELIVERY_LIFECYCLE.md:123 and TWO_PLANE_DECISION_MODEL.md:92, or file one issue referenced from the PR before merge
- C3 PR description and squash title disclose the L187 edit and its impact level (C0 by effect)

non-blocking, to issues: ninth unlisted vocabulary at L79-80 (ballot.schema.json decisions); DECISION_AUTHORITY.md mis-cited at L116-117; "seventh" at L129 has no referent; "not three" at L133 is a changelog remark in normative prose; FIT-HDG-EAB.md:93 erratum; no test guards the count.
