# Evidence packaging — the four G07 types, and the build ledger

## PACKAGE — exactly four types, richer bindings (BLD-I16)

`source-change` binds WP, base SHA, head SHA, changed paths, change digest, the expected-surface
comparison and unexpected-surface list, producer and toolchain. `build` captures command, working
directory, environment/toolchain identity, started_at, completed_at, exit code, artifact refs, artifact
digests and non-coverage. `unit-test` binds test obligation, acceptance criterion, seam, red evidence
where required, green evidence, command, result, test count, failure count and coverage scope.
`documentation` answers: what changed, what contract changed, what operator/developer behavior changed,
what docs required update, what was NOT updated and why.

The types stay the four in `badf/lifecycle.json`; their schemas are BLD-B; the producer remains the
canonical gate's self-dossier path, extended — never a second producer (BLD-I18).

## The build ledger (recovery and evidence, never authority)

A persistent ledger prevents context compaction from redispatching finished work:

```text
work/WP-.../
├── work-package.json
├── build/
│   ├── session.json
│   ├── progress.jsonl
│   ├── decisions.jsonl
│   └── evidence/
```

(or BADF's session infrastructure where its storage contract fits.) Every material execution transition is
recorded:

```text
START · BASELINE · RED · GREEN · VERIFY · RETRY · STOP · RESUME · HANDOFF
```

The ledger is recovery and evidence. It is not authority: nothing in it permits a transition.
