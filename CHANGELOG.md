# Changelog

All notable changes to the BADF framework are recorded here, in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) order, newest first.

> **This is the repository's first `CHANGELOG.md`.** It was created under SARCHI's condition
> C3 on [#265](https://github.com/bstBizEra/badf/issues/265), which required that a change
> able to refuse a **new** record be recorded where a record author will find it. The
> repository had no changelog convention and no version file, so this file establishes one —
> deliberately, and as a decision that can be redirected rather than a side effect of a patch.
> BADF versions capabilities through the activation ladder
> (`DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → RATIFIED → ACTIVE`), not through SemVer,
> so entries are grouped by landing rather than by release number.

## Unreleased

### Changed

- **`check_schema` now enforces `minLength` on strings and `minItems` on arrays**
  ([#265](https://github.com/bstBizEra/badf/issues/265) Rung A, `WP-2026-0138`).
  These keywords were declared **377** and **48** times across the corpus and enforced
  nowhere; the walker previously implemented exactly seven keywords. **422 of the 425
  declaration sites become live** — the remaining 3 sit inside `anyOf`, for which the walker
  still has no branch.

  **What this means if you are writing a record:** a field declared `minLength: 1` will now
  refuse `""`, and an array declared `minItems: 1` will now refuse `[]`. **No record that had
  already landed is affected** — the replay at `main@310a660` swept 694 records and found
  **0** newly refused, with 292 refused identically before and after.

  **What it does not do:** `minLength` is a **length** bound, not a non-emptiness bound. It
  refuses `""` and admits `"   "` and `" GHOST"`. The code controls that use `.strip()` are
  therefore *strictly stronger* and are retained; the degenerate-content class
  ([#293](https://github.com/bstBizEra/badf/issues/293)) is **not** closed by this change.

### Notes

- 19 existing tests asserted a code control's message for a probe the schema now refuses
  first. 8 were re-pointed at the degenerate form only their control catches; the other 11
  have controls that are bare list-truthiness, where `minItems: 1` is exactly equivalent and
  nothing stronger exists to re-point at. Those are recorded in-file as **shadowed**, with the
  control retained and its disposition deferred.
