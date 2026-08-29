# API-design contract — DESIGN + ASSURE

The API specialist runs in **two modes**, mirroring the successful `badf-architecture` DESIGN/ASSURE
pattern — without turning solution design into another architectural assurance system. Composes into
**G04** detailed evidence (coherent with `api-contract`).

## API DESIGN — produce the contract

- **operations / resources / events** — each traced to a `REQ`/G03 need (SOL-I01) and to a UX action (SOL-I03);
- **schemas** — request/response, agreeing with the data model (SOL-I07);
- **error model** — every material failure has a code and a UX recovery state (SOL-I08);
- **pagination, idempotency, authentication, authorization** — each operation's protection resolves the authorization tuple (SOL-I04);
- **versioning / compatibility** posture.

## API ASSURE — compare candidate against baseline

Compare a candidate contract to the baseline and produce **assurance evidence, not authority**. Checks:

```text
breaking changes · removed operations · required-field additions · enum narrowing · type changes
response-code changes · pagination contract · idempotency changes · authentication changes
authorization changes · versioning · deprecation window
```

A breaking change is **explicitly identified and dispositioned** (SOL-I11) — never silent. ASSURE emits
evidence; the canonical gate validates it and an authority decides. There is no second validator (SOL-I12).

## Seams it must satisfy

- **SOL-I03** UX↔API · **SOL-I04** API↔authorization · **SOL-I07** API↔data · **SOL-I08** UX↔error · **SOL-I11** compatibility.
