# Vertical slicing

The **default** unit is a vertical **tracer-bullet** slice — an independently verifiable outcome that
cuts through the stack — not a horizontal layer (IMP-I04). Horizontal decomposition is allowed only with
explicit rationale recorded on the WP.

## The topology and its exceptions

```text
DEFAULT              vertical tracer-bullet WP
EXCEPTION  wide mechanical refactor   → EXPAND → MIGRATE (batches) → CONTRACT
EXCEPTION  irreducible migration      → explicitly ordered integration sequence
EXCEPTION  material uncertainty       → badf-research before implementation
```

The **expand / migrate / contract** sequence (adopted from Matt Pocock's `to-tickets`) exists so a wide
change is not forced into an artificial vertical slice: add the new path (expand), move call-sites in
reviewable batches (migrate), remove the old path (contract) — each a WP, ordered by `composition_after`.
