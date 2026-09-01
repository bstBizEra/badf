"""badf_id_sweep -- the id-allocation sweep, mechanized (GOV-0098 / #227, WP-2026-0118;
comment surface + readability report added by #282 / WP-2026-0128).

Reads surface DUMP FILES from --from-dir and reports, per id family, what is CLAIMED
(with the source surface named), what is merely MENTIONED in prose, what the COMMENT
surface shows (the session's actual binding-claim mechanism), the declared sentinel
exclusions, and the next-free candidate -- then names, per run, which surfaces it
read and which it could not, and what remains blind to every surface.

Deterministic and offline by design: this repository's CI has neither network nor
credentials, and a sweep that silently degrades when `gh` fails would report clean
scans it never performed. The dumps are produced by the operator/seat (one-liners in
GITHUB_CONTROL_PLANE.md, section "The id-allocation protocol"):

  ledger.txt    ls work/ ; ls badf/demands/            (claim-shaped, required)
  branches.txt  git ls-remote --heads origin           (claim-shaped, required)
  pr_files.txt  gh api repos/<r>/pulls/<N>/files ...   (claim-shaped, required)
  bodies.txt    gh issue/pr bodies, concatenated       (prose: MENTIONS, required)
  comments.txt  gh api repos/<r>/issues/{n}/comments   (OPTIONAL -- but the claim
                + PR comments, concatenated             mechanism lives here)

Properties held as structure, not convention (#227 + #282 field spec):
- MENTIONS and COMMENT ids are never folded into next-free. Prose may CARRY a binding
  claim -- which is exactly why a comment id at or above the computed next-free emits
  a named WARNING ("read it; the published claim is binding") instead of silently
  vanishing (four allocation incidents in one session) or polluting max() (#199).
- The SURFACES header reports every surface as READ (with id count) or NOT PROVIDED,
  every run: an unread surface stated is a caution; omitted, a false clean.
- Sentinels are excluded from next-free and warnings, and DECLARED in the output.
- POSITIVE CONTROL before any negative: the sweep refuses to report unless it can see
  ids known to be present on main forever.
- Every report ends with the NON-COVERAGE trailer: unpushed worktrees and independent
  clones are invisible to every surface here; the published issue claim is the
  binding mechanism and this sweep only bounds the risk.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FAMILIES = {
    "WP-2026": re.compile(r"\bWP-2026-(\d{4})\b"),
    "BADF-DEM": re.compile(r"\bBADF-DEM-(\d{4})\b"),
    "GOV": re.compile(r"\bGOV-(\d{4})\b"),
}
# 9999 is the sanctioned synthetic sentinel (GOV-0085); 0997-0999 are test fixtures
# named in #199 as the same latent class. 0900 is deliberately NOT here: unverified.
SENTINELS = ("0997", "0998", "0999", "9999")
CLAIM_SURFACES = ("ledger", "branches", "pr_files")
PROSE_SURFACES = ("bodies",)
OPTIONAL_SURFACES = ("comments",)
# Present on main since 2026-08-30; if a scan cannot see these, it cannot see.
ANCHORS = (("WP-2026", "0110"), ("BADF-DEM", "0097"), ("GOV", "0097"))
TRAILER = ("NON-COVERAGE: unpushed worktrees and independent clones are invisible to every "
           "surface above; ask the seats, then PUBLISH the claim on an issue before binding. "
           "The published claim is the binding mechanism -- this sweep only bounds the risk.")


def scan(surfaces: dict[str, str]) -> dict[str, dict[str, object]]:
    """Per family: claimed {num: source}, mentions {num}, comments {num} from the dumps."""
    report: dict[str, dict[str, object]] = {}
    for fam, rx in FAMILIES.items():
        claimed: dict[str, str] = {}
        mentions: set[str] = set()
        comments: set[str] = set()
        for name in CLAIM_SURFACES:
            for num in rx.findall(surfaces.get(name, "")):
                claimed.setdefault(num, name)
        for name in PROSE_SURFACES:
            for num in rx.findall(surfaces.get(name, "")):
                if num not in claimed:
                    mentions.add(num)
        for num in rx.findall(surfaces.get("comments", "")):
            comments.add(num)
        report[fam] = {"claimed": claimed, "mentions": mentions, "comments": comments}
    return report


def next_free(claimed: dict[str, str]) -> str:
    """Highest non-sentinel claim + 1, skipping sentinels. Claim-shaped surfaces only."""
    live = [int(n) for n in claimed if n not in SENTINELS]
    n = (max(live) + 1) if live else 1
    while f"{n:04d}" in SENTINELS:
        n += 1
    return f"{n:04d}"


def positive_control(report: dict[str, dict[str, object]]) -> list[str]:
    """The anchors the scan must be able to see (claimed or mentioned) before any
    negative is trusted."""
    missing = []
    for fam, num in ANCHORS:
        entry = report[fam]
        if num not in entry["claimed"] and num not in entry["mentions"]:
            missing.append(f"{fam}-{num}")
    return missing


def render(report: dict[str, dict[str, object]], readability: dict[str, str]) -> str:
    lines = ["BADF ID SWEEP (surfaces: " + ", ".join(CLAIM_SURFACES + PROSE_SURFACES + OPTIONAL_SURFACES) + ")"]
    lines.append("SURFACES:")
    for name in CLAIM_SURFACES + PROSE_SURFACES + OPTIONAL_SURFACES:
        lines.append(f"  {name}: {readability[name]}")
    lines.append("POSITIVE CONTROL: PASS (anchors visible: "
                 + ", ".join(f"{f}-{n}" for f, n in ANCHORS) + ")")
    for fam, entry in report.items():
        claimed: dict[str, str] = entry["claimed"]  # type: ignore[assignment]
        mentions: set[str] = entry["mentions"]  # type: ignore[assignment]
        comments: set[str] = entry["comments"]  # type: ignore[assignment]
        lines.append(f"== {fam} ==")
        if fam == "GOV":
            # GOV has no file-backed claim surface: numbers live in titles and prose.
            observed = sorted(set(claimed) | mentions | comments)
            lines.append("OBSERVED USES (prose-derived; GOV has no file-backed claim surface"
                         " -- READ BEFORE BINDING): "
                         + (", ".join(f"GOV-{n}" for n in observed) or "none"))
            continue
        lines.append("CLAIMED: " + (", ".join(f"{fam}-{n} ({src})" for n, src in sorted(claimed.items())) or "none"))
        lines.append("SENTINELS EXCLUDED: " + " ".join(SENTINELS))
        nf = next_free(claimed)
        lines.append(f"NEXT FREE (claim-shaped surfaces only): {fam}-{nf}")
        lines.append("MENTIONS (prose may carry a binding claim -- READ BEFORE BINDING): "
                     + (", ".join(f"{fam}-{n}" for n in sorted(mentions)) or "none"))
        # #282: a comment id at or above next-free is a probable BINDING claim the
        # claim-shaped surfaces cannot see -- warn by name, never fold into max().
        hot = sorted(n for n in comments if n not in SENTINELS and int(n) >= int(nf))
        for n in hot:
            lines.append(f"WARNING: comment surface shows {fam}-{n} at/above next-free "
                         f"{fam}-{nf} -- read it; the published claim is binding")
    lines.append(TRAILER)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from-dir", required=True, type=Path,
                    help="directory holding ledger.txt, branches.txt, pr_files.txt, "
                         "bodies.txt and optionally comments.txt")
    args = ap.parse_args(argv)
    surfaces: dict[str, str] = {}
    readability: dict[str, str] = {}
    for name in CLAIM_SURFACES + PROSE_SURFACES:
        p = args.from_dir / f"{name}.txt"
        if not p.is_file():
            print(f"BADF ID SWEEP FAIL: missing surface dump {p.name}; a sweep that skips a "
                  f"surface silently is the class this tool exists to close", file=sys.stderr)
            return 1
        surfaces[name] = p.read_text(encoding="utf-8", errors="replace")
    for name in OPTIONAL_SURFACES:
        p = args.from_dir / f"{name}.txt"
        if p.is_file():
            surfaces[name] = p.read_text(encoding="utf-8", errors="replace")
            readability[name] = "PENDING"
        else:
            surfaces[name] = ""
            readability[name] = "NOT PROVIDED (the claim mechanism lives here -- provide it or ask the seats)"
    report = scan(surfaces)
    for name in CLAIM_SURFACES + PROSE_SURFACES + OPTIONAL_SURFACES:
        if readability.get(name, "PENDING") == "PENDING" or name not in readability:
            count = sum(len(rx.findall(surfaces.get(name, ""))) for rx in FAMILIES.values())
            readability[name] = f"READ ({count} id occurrence(s))"
    missing = positive_control(report)
    if missing:
        print("BADF ID SWEEP FAIL: POSITIVE CONTROL failed -- known-present anchors invisible: "
              + ", ".join(missing) + "; an empty scan and a clean scan are identical, so no "
              "allocation advice is offered from a scan that cannot see")
        return 1
    print(render(report, readability))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
