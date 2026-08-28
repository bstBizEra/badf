#!/usr/bin/env python3
"""BADF-MAIN-001 traceability: a PR body must name its Work Package and the
Issue it closes. Deterministic; reads the body from argv or stdin.

Exit 0  both present and well-formed
Exit 1  missing or malformed -- prints exactly which

This is the first link of the chain Issue -> WP -> branch -> PR -> main,
made checkable. Until BADF-WP-0016, zero commits on main referenced an
Issue; this check is what makes that number stop being zero.
"""
import re
import sys

WP = re.compile(r"^Work-Package:\s*(BADF-WP-[0-9]{4}|WP-2026-[0-9]{4})\s*$", re.M)
CLOSES = re.compile(r"^(Closes|Fixes|Resolves):?\s+#([0-9]+)\s*$", re.M | re.I)

# The PR body is the squash commit message on main -- the surface the next agent
# greps. `.github/pull_request_template.md` REQUESTS this shape; this check
# ENFORCES it, because `gh pr create --body-file` bypasses the web template
# (BADF-WP-0034, #27). A section heading is `## <Name>` on its own line.
REQUIRED_SECTIONS = ("What", "Verification")


def _section(name: str) -> "re.Pattern[str]":
    return re.compile(rf"^##\s+{name}\b", re.M | re.I)


def check(body: str) -> list[str]:
    problems = []
    if not WP.search(body):
        problems.append("missing `Work-Package: BADF-WP-NNNN` line")
    if not CLOSES.search(body):
        problems.append("missing `Closes #N` line (every PR closes the Issue that demanded it)")
    for name in REQUIRED_SECTIONS:
        if not _section(name).search(body):
            problems.append(f"missing `## {name}` section (see .github/pull_request_template.md)")
    return problems


def main() -> int:
    body = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    problems = check(body)
    if problems:
        print("BADF TRACEABILITY FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    wp = WP.search(body).group(1); issue = CLOSES.search(body).group(2)
    print(f"BADF TRACEABILITY PASS: {wp} closes #{issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
