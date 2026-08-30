# Evidence planning

Every **material claim** identifies the evidence required to prove it (IMP-I10). A WP's
`evidence_obligations` name the artifacts the Engineering Loop must produce — the same evidence types the
G07 self-dossier already assembles:

```yaml
evidence_obligations: [source-change, build, unit-test, documentation]
```

The plan does not produce the evidence (that is execution); it **declares which evidence is owed** so the
gate can check it exists and an authority can weigh it. A claim with no evidence obligation is an
assertion, not a governable outcome.
