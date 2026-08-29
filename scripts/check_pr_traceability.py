#!/usr/bin/env python3
"""BADF-MAIN-001 traceability: a PR body must name its Work Package and the
Issue it closes. Deterministic; reads the body from argv or stdin.

BADF-WP-0070 (badf-git GIT-B) froze ONE work-package identity with three
faces and one binding, and this check enforces it on every pull request:

  binding   the body trailer  `Work-Package: <machine id>`   (canonical only)
  label     the PR title      `<display label>: <concise outcome>`
  branch    the head ref      `wp/<machine id>-<slug>`

all three carrying the same NNNN. The machine id namespace is defined once in
badf_gate.py and imported here -- this file carries no literal of its own.
History is never rewritten: badf_gate.py keeps resolving historical
display-form trailers; only new PRs must bind the canonical form.

Exit 0  everything present, well-formed and consistent
Exit 1  refused -- prints exactly which, with the line to paste
Exit 2  usage -- --title and --head-ref are REQUIRED (CI passes them from the
        pull_request event); absence is an error, never a silent skip

This is the first link of the chain Issue -> WP -> branch -> PR -> main,
made checkable. Until BADF-WP-0016, zero commits on main referenced an
Issue; this check is what makes that number stop being zero.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from badf_gate import WP_DISPLAY, WP_NAMESPACE  # noqa: E402

_NS, _DL = re.escape(WP_NAMESPACE), re.escape(WP_DISPLAY)
WP = re.compile(rf"^Work-Package:\s*({_NS}[0-9]{{4}})\s*$", re.M)
WP_DISPLAY_TRAILER = re.compile(rf"^Work-Package:\s*{_DL}([0-9]{{4}})\s*$", re.M)
CLOSES = re.compile(r"^(Closes|Fixes|Resolves):?\s+#([0-9]+)\s*$", re.M | re.I)
TITLE = re.compile(rf"^{_DL}([0-9]{{4}}):\s+\S")
HEAD_REF = re.compile(rf"^wp/{_NS}([0-9]{{4}})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
# The PR body is the squash commit message on main -- the surface the next agent
# greps. `.github/pull_request_template.md` REQUESTS this shape; this check
# ENFORCES it, because `gh pr create --body-file` bypasses the web template
# (BADF-WP-0034, #27). A section heading is `## <Name>` on its own line.
REQUIRED_SECTIONS = ("What", "Verification")


def _section(name: str) -> "re.Pattern[str]":
    return re.compile(rf"^##\s+{name}\b", re.M | re.I)


def check(body: str) -> list[str]:
    """Body-only problems: the binding trailer, the Closes line, the sections."""
    problems = []
    if not WP.search(body):
        d = WP_DISPLAY_TRAILER.search(body)
        if d:
            problems.append(f"the Work-Package trailer must be the canonical machine id -- paste "
                            f"`Work-Package: {WP_NAMESPACE}{d.group(1)}` (found `{WP_DISPLAY}{d.group(1)}`; "
                            f"{WP_DISPLAY}NNNN is the display label for the PR title only -- BADF-WP-0070)")
        else:
            problems.append(f"missing `Work-Package: {WP_NAMESPACE}NNNN` line")
    if not CLOSES.search(body):
        problems.append("missing `Closes #N` line (every PR closes the Issue that demanded it)")
    for name in REQUIRED_SECTIONS:
        if not _section(name).search(body):
            problems.append(f"missing `## {name}` section (see .github/pull_request_template.md)")
    return problems


def check_identity(body: str, title: str, head_ref: str) -> list[str]:
    """Title and branch must carry the trailer's NNNN (BADF-WP-0070 / GIT-B)."""
    problems = []
    bound = WP.search(body)
    nnnn = bound.group(1)[len(WP_NAMESPACE):] if bound else None
    t = TITLE.match(title or "")
    if not t:
        want = f"{WP_DISPLAY}{nnnn or 'NNNN'}: <concise outcome>"
        problems.append(f"the PR title must start with the display label `{want}` (BADF-WP-0070), got {title!r}")
    elif nnnn and t.group(1) != nnnn:
        problems.append(f"the PR title label {WP_DISPLAY}{t.group(1)} does not match the trailer "
                        f"`Work-Package: {WP_NAMESPACE}{nnnn}` -- one NNNN across trailer, title and branch")
    h = HEAD_REF.match(head_ref or "")
    if not h:
        want = f"wp/{WP_NAMESPACE}{nnnn or 'NNNN'}-<slug>"
        problems.append(f"the head branch must be `{want}` (lowercase kebab slug; BADF-WP-0070), got {head_ref!r}")
    elif nnnn and h.group(1) != nnnn:
        problems.append(f"the head branch id {WP_NAMESPACE}{h.group(1)} does not match the trailer "
                        f"`Work-Package: {WP_NAMESPACE}{nnnn}` -- one NNNN across trailer, title and branch")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="BADF-MAIN-001 PR traceability + BADF-WP-0070 identity contract")
    ap.add_argument("body", nargs="?", help="the PR body; read from stdin when omitted")
    ap.add_argument("--title", required=True, help="the PR title (github.event.pull_request.title)")
    ap.add_argument("--head-ref", required=True, help="the PR head branch (github.event.pull_request.head.ref)")
    args = ap.parse_args(argv)
    body = args.body if args.body is not None else sys.stdin.read()
    problems = check(body) + check_identity(body, args.title, args.head_ref)
    if problems:
        print("BADF TRACEABILITY FAIL: " + "; ".join(problems), file=sys.stderr)
        return 1
    wp = WP.search(body).group(1); issue = CLOSES.search(body).group(2)
    print(f"BADF TRACEABILITY PASS: {wp} closes #{issue} on {args.head_ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
