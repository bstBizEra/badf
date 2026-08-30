# Independence — an execution-level contract, not a different prompt in the same conversation

"Independent" is decided by fields that can be checked, not by a role banner.
A banner is not authorization: under BADF's shared identity any execution can type any banner (`AGENTS.md`, comment
signatures: *labels, not authorization*), so authorship is established structurally or it is carried as a
deviation — never assumed from the text.

## The fields (VER-I04, VER-I05, VER-I06, VER-I19)

```yaml
independence:
  reviewer_run_id: <this review execution>
  author_run_id: <the build execution that produced the candidate>
  same_execution: false                          # reviewer_run_id != author_run_id
  sealed_input_digest: sha256:...                # equal across every seat of the same review
  prior_findings_visible: false                  # no other pass's findings were supplied
  author_reasoning_visible: false                # no hidden author reasoning, plan chatter or self-review was supplied
  cross_pass_communication_before_ballot: false  # no seat spoke to another before its ballot was persisted
  target_digest_equal: true
  conflicts_of_interest: []
```

For a review pass to count as independent, **all** of the following hold: a different execution AND a
sealed common target AND no prior reviewer findings supplied AND no author's hidden reasoning supplied AND
no cross-pass communication before the ballot is persisted. Preferably also `reviewer_identity !=
builder_identity`; see the deviation below for when that cannot be met.

## Council review — docs/03 referenced, not restated

For C2/C3 changes the council protocol of `docs/03-authority-and-agent-councils.md` governs verbatim:
the chair defines the exact question, artifact digest, options, mandatory lenses and quorum; members
receive the same sealed inputs and work independently; each ballot records identity/role, artifact digest,
verdict, findings, evidence, confidence, assumptions and non-coverage; **ballots are persisted before
synthesis**; the chair checks independence, quorum, conflicts of interest and digest equality; synthesis
preserves minority risks and unresolved contradictions; the authorized decision-maker accepts, rejects,
conditions or escalates. **The same person or model run cannot count twice toward quorum** (VER-I19).

```yaml
council:
  sealed_input_digest: sha256:...
  ballot_ids: [BALLOT-..., BALLOT-..., BALLOT-...]
  quorum_met: true
```

The synthesizer cannot invent ballots: every `ballot_id` resolves to a persisted ballot whose
`sealed_input_digest` equals the council's. The precedent is the research council (`RSR-003`): the gate
already refuses a researcher balloting on their own record and a duplicate reviewer identity — the same
refusals apply here at VER-C.

## The deviation BADF carries today — recorded, not hidden

BADF runs its own repository under a **single collaborator**. The account-level `reviewer ≠ author` cannot
be met for BADF's own Work Packages, and the self-dossier already records this as an **OPEN condition**
("an independent reviewer distinct from the author has not recorded an approval") rather than hiding it.
This contract keeps that discipline: independence is satisfied at the execution level by the fields above;
the account-level gap is carried as the condition until a distinct human `independent_reviewer` records an
approval or a decision record accepts the deviation. What is never acceptable is satisfying the condition
with a banner.
