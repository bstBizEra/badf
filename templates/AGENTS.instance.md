# {{PROJECT_NAME}} Agent Operating Charter

This repository is governed by BADF (BizEra Agent Delivery Framework).
Framework: `{{FRAMEWORK_REPOSITORY}}` at `{{FRAMEWORK_REVISION}}`. This file is the
entrypoint; the control plane is `badf/`. Neither duplicates the framework's documents —
they are consumed by reference at the pinned revision.

| Question | Answer lives in |
| :--- | :--- |
| What project is this? | `badf/project.yaml` |
| Where is it in the lifecycle? | `badf/state.json` (derived; never edited by hand) |
| What proves what has happened? | `badf/evidence/` (`receipts/` first) |
| What work is authorised? | `badf/work/` — none until a work package is admitted |
| Who or what may act? | `badf/authority/` — absent until the authority instance exists; until then **no** authority is established here and every material action is refused |

Rules that bind here, from the framework's constitution:

- No material work without authority. No claim without evidence. No self-approval.
- Fail closed: unknown or false → deny. Credential possession never equals permission.
- Local instructions may **narrow** authority; they can never expand it.
- A run's output is measured by its side effects, never by its own account of itself.
- Discoveries become issues, not fixes.

Initialised by `badf init` for work package `{{WORK_PACKAGE}}`; receipt:
`{{RECEIPT}}`.
