---
name: badf-delivery
description: Govern repository delivery from product intent or PRD through implementation, verification, release, production operations, and learning. Use when planning, building, reviewing, releasing, operating, or closing work under the BizEra Agent Delivery Framework (BADF), including work packages, gate dossiers, evidence, sessions, handoffs, councils, skills, MCP, and tools.
---

# BADF Delivery

1. Read the repository `AGENTS.md` and the documents it marks required for the task.
2. Resolve the work-package ID, current gate, change class, authority, scope, acceptance criteria, and stop conditions. If absent for material work, prepare a draft work package and stop at the required authority boundary.
3. Inspect the current repository and evidence baseline. Preserve unrelated changes.
4. Follow `FRAME -> DISCOVER -> PLAN -> AUTHORIZE -> BUILD -> VERIFY -> CHALLENGE -> RECONCILE -> DELIVER -> OBSERVE -> LEARN`.
5. Use only registered skills, MCP servers, and tools within their approved operations and data classes. Treat access as capability, not authority.
6. Produce evidence objects for material claims and bind them to the work package, gate, source, target, toolchain, and artifact digest.
7. Obtain independent review proportional to risk; do not self-approve or count one run twice toward quorum.
8. Validate the repository and any requested gate dossier with `python3 scripts/badf_gate.py`.
9. Report the exact disposition, evidence, residual risk, lifecycle gate, and authority required for advancement.

Read `references/routing.md` when deciding which BADF documents and artifacts a task requires.

