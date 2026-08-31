# `webapp-uat` — adapted for mechanics, rejected as the definition of acceptance

Confirmed absent from this repository (external reference only, not vendored, not a dependency).

## What is adapted

A Playwright-based E2E mechanic: scripted browser interaction, network/console capture, screenshot
diffing. These are execution-adapter concerns (`references/execution-adapters.md`) — useful as one
possible `browser` adapter implementation at a later rung.

## What is rejected

Treating "the scripted flow completed without error" as the definition of acceptance. That is exactly
UAT-I03 (technical E2E ≠ UAT): a Playwright run that completes cleanly proves the system did not crash;
it proves nothing about whether the observed behavior satisfies an approved business acceptance
criterion. `webapp-uat`-shaped tooling has no concept of a PRD, an acceptance criterion, or a human
acceptance layer — it is a technical verification tool, correctly scoped to G08/G09, not G10.

## Why this reference exists

To make the boundary explicit and falsifiable rather than implicit: a future contributor proposing to
adopt `webapp-uat` wholesale as `badf-uat`'s runtime is answered by this file, not by re-litigating the
distinction from scratch. Adopt its mechanics as one adapter among several; never adopt its definition
of done as this skill's definition of accepted.
