# Execution adapters — browser, API, manual, hybrid; observation only

UAT-I02, UAT-I09. An adapter executes a scenario and reports an observation. It never classifies the
observation as "accepted" — that is the disposition step (`references/acceptance-disposition.md`), and
it is never automatic.

```text
Adapter        Observes
browser        rendered UI behavior against the scenario's expected business outcome
api            request/response behavior against the scenario's expected business outcome
manual         a human executor's recorded observation, same scenario contract
hybrid         a scenario split across adapters (e.g. API setup + browser verification)
```

## Registration state at WP-UAT-A

**No adapter is registered as a subskill at this rung.** Registering `browser-uat` / `api-uat` /
similar concrete adapters before the contract they implement is frozen is the over-engineering risk this
WP explicitly refuses (see issue #239's Stage-Gate note). This reference fixes the adapter *contract*
(inputs: scenario + environment; output: an observation record) so a later WP can register concrete
adapters against it without renegotiating the shape.

## Adapter output shape (frozen now, implemented later)

```json
{
  "scenario_id": "UAT-SCN-...",
  "adapter": "browser | api | manual | hybrid",
  "observed_outcome": "what was actually observed, business-readable",
  "result": "PASS | FAIL | BLOCKED | NOT_EXECUTED",
  "diagnostics_ref": "optional pointer to console/network/a11y/i18n output (references/diagnostics-vs-oracle.md)",
  "executed_by": "adapter identity or human executor identity",
  "executed_at": "timestamp"
}
```
