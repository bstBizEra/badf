# UAT ≠ go-no-go ≠ deployment

UAT-I18, UAT-I19. Three separate acts, three separate owners, none of which this skill performs.

```text
G09  badf-release-validation   independent technical validation (quality/security/perf/resilience)
G10  badf-uat (this skill)     records business acceptance of the exact candidate — produces `uat` only
G10  badf-production-readiness produces `release-packet` + `operational-readiness` (the other two G10 types)
G10  release_authority (human) issues `go-no-go` — reserved, not delegable to any skill
G11  Deployment / Change Ctrl  executes the deployment the go-no-go authorized
```

## Why this line matters here specifically

A fully `ACCEPTED` UAT disposition is strong evidence, but it is not authorization. `badf-uat` finishing
green does not itself trigger `go-no-go`, and `go-no-go` finishing does not itself deploy anything
(G11 is a separate gate with its own owner and evidence). Collapsing any of these into the skill that
produced the evidence one step earlier is the exact failure mode BADF's gate-owner separation exists to
prevent — the same shape already enforced at the G08/G09 boundary in `badf-engineering-verification` and
`badf-release-validation`, extended here one gate further.
