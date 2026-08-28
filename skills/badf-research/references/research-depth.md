# Research depth

Status: frozen contract v0.2 (`WP-2026-0041`). Depth is the bounded cost, coverage and challenge level for a research run. The schema carries the same `D0`–`D5` codes.

Type is *what* the run investigates. Depth is *how far* it may go. Depth is fixed during framing and may not be raised silently because a higher depth expands cost, source breadth and potentially tool usage.

| Code | Depth | Typical use |
| :--- | :--- | :--- |
| `D0` | `LOOKUP` | one bounded factual lookup |
| `D1` | `SCAN` | quick engineering investigation with explicit non-coverage |
| `D2` | `STANDARD` | multiple sources, claim assessment and comparison where applicable |
| `D3` | `DEEP` | broader triangulation and parallel evidence collection |
| `D4` | `ADVERSARIAL` | deep research plus mandatory independent challenge |
| `D5` | `EXPERIMENTAL` | controlled experiments plus mandatory independent challenge |

## Depth controls

- The framing record must name the depth before material collection.
- Raising depth requires an explicit recorded amendment within the originating demand/authority boundary; never hide expansion as “more research”.
- Lower depth may not be used to bypass a challenge trigger.
- `D4` and `D5` require the framework's existing independent council challenge.
- `R06` requires challenge regardless of depth.
- `D5` experiments must remain bounded and disposable unless a later decision and work package separately authorize adoption.
- Stop conditions remain binding at every depth. Depth does not authorize indefinite collection.
