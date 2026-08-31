# Environment and data fidelity — representative context, declared provenance

UAT-I08. A scenario executed against an environment or dataset that does not represent the business
context it claims to validate produces an observation, not evidence of acceptance.

## Required declarations per execution

```text
environment_id      which environment the scenario ran in (staging / uat / representative-prod-mirror)
permissions_profile  which role/permission set the actor operated under, matching actor_role
business_rules_epoch which configuration/rule-set version was in force
test_data_provenance where the data came from (synthetic-representative / anonymized-prod-sample / fixture)
test_data_epoch      when that data was captured or generated
```

A scenario executed under an undeclared or non-representative environment is not silently accepted as
PASS — it is flagged as an environment-fidelity defect (`references/defect-classification.md`,
`ENVIRONMENT_DEFECT`), and the disposition records the gap rather than absorbing it into the result.
