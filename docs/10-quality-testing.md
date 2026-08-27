# Quality and Testing Strategy

Status: **NORMATIVE**

## Test layers

1. static analysis, formatting, type and policy checks;
2. unit and property tests for logic/invariants;
3. integration tests for components and infrastructure;
4. API/event/schema contract and compatibility tests;
5. data migration, rollback, reconciliation, and integrity tests;
6. end-to-end critical journeys and negative paths;
7. accessibility, localization, usability, and device/browser checks;
8. performance, capacity, soak, resilience, failover, and recovery tests;
9. security, privacy, abuse, and penetration tests;
10. UAT and business control reconciliation;
11. production smoke, canary, telemetry, and business KPI checks.

## Test integrity

Map requirements and risks to tests. Record environment, fixtures/data epoch, tool versions, seed, command, output, and digest. Quarantined/flaky tests require owner, reason, expiry, and compensating control. Rerun only under a documented flake policy; never rerun until green and erase failures.

## Coverage

Coverage is a diagnostic, not proof. Define thresholds by criticality and combine them with mutation testing, boundary cases, production risk, and defect history. Reviewers must report untested surfaces.

## Independence

The implementer may author tests; C2/C3 acceptance requires an independent challenge of relevant risks. Validation uses the exact candidate artifact or composed result and production-representative configuration.

