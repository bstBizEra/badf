# AI-agent-security contract (conditional, first-class)

`ai-agent-security-design` is **conditional**. For a non-agentic application it is
`NOT_APPLICABLE_WITH_REASON`. For BADF itself or any agentic project it routes **automatically** and is
first-class — because BADF's own doctrine is `CAPABILITY ≠ AUTHORITY`, and an agentic system is exactly
where that line is easiest to lose.

## Design concerns

```text
Agent identity                 Prompt / trust boundaries          Human authorization points
Agent authority                Untrusted-context handling         Side-effect isolation
Tool capability                Memory provenance                  Output trust
MCP capability                 Secret visibility                  Model / provider trust
Filesystem / network scope     Data exfiltration paths            Agent-to-agent delegation
                               Recursive-delegation limits
```

## Shape

```yaml
agent_ref: AGENT-...
capabilities:                  # explicitly scoped (SEC-I10)
  tools: [...]
  mcp: [...]
  filesystem_scope: [...]
  network_scope: [...]
trust_boundaries:
  untrusted_context_handling: "..."   # prompt-injection / untrusted-input containment
  memory_provenance: "..."
  secret_visibility: "..."
authority:
  human_authorization_points: [...]   # where a human gate is mandatory (capability ≠ authority)
  delegation: "..."                   # agent-to-agent, with recursive-delegation limits
  side_effect_isolation: "..."
exfiltration_paths: [...]      # identified and controlled
provenance:
  model_provider_trust: "..."
```

## Rules

- **Least privilege (SEC-I10).** Every agent/tool/MCP/filesystem/network capability is **explicitly
  scoped**. An unscoped capability is a finding.
- **Capability ≠ authority.** A model being able to call a tool never implies permission to use it; the
  human authorization points and side-effect isolation make the difference enforceable, not implied.
- **Untrusted context is contained.** Prompt/trust boundaries, memory provenance and secret visibility are
  designed so untrusted input cannot escalate into authority or exfiltrate data.
- **Delegation is bounded.** Agent-to-agent delegation carries explicit recursive-delegation limits;
  unbounded delegation is refused by design.
- This maps to OWASP's agent / MCP / LLM / multi-agent coverage as **reference** methodology
  (`references/external-methodology.md`) — adapted, never adopted as authority.
