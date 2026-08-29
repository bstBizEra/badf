# Accessibility-design contract

Accessibility is a **behavior contract bound to interaction states**, not a checklist appended to a
finished screen (SOL-I09). Composes into **G03** evidence (accessibility). Target: **WCAG 2.2 AA**.

## Binds to behavior

For each interaction state a UX flow defines:

```text
interaction → keyboard behavior → focus behavior → semantic announcement → error behavior → state-change notification
```

## Output contract

- **keyboard** — every operable element reachable and operable by keyboard; no keyboard trap;
- **focus** — visible, ordered, and managed across state changes and route changes;
- **semantics** — correct roles/names/values; state exposed to assistive technology, not by color alone;
- **errors** — a failure is announced programmatically and has a recovery path (ties SOL-I08 ↔ SOL-I09);
- **state changes** — dynamic changes are announced to assistive technology;
- **assistive-technology behavior** — the expected screen-reader / AT experience per state.

## Seams it must satisfy

- **SOL-I09** — accessibility binds each interaction state (not a per-screen afterthought).
- **SOL-I08** — an error surfaced accessibly still needs a UX recovery state; a state conveyed only by
  color (the refund example) fails both.

WCAG 2.2 AA is the floor; the contract names the *behavior*, which the specialist adapter designs and the
canonical gate's G03 `accessibility` evidence validates.
