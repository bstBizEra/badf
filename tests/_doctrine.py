"""Section slicing for `docs/governance/GITHUB_CONTROL_PLANE.md`.

GOV-0121 / #279. Two admission sections carry **32 token assertions** scoped to the
section. Both slices ended the section at the next ``## `` heading, which made that
scope depend on **heading depth**: inserting any ``## `` inside a guarded section
truncated it, and the failure surfaced as a missing *token* -- sending the editor to
re-add prose that was already present. The doctrine file carries 104 ``## `` headings
and nothing told an editor which two are load-bearing.

A heading-depth rule cannot fix this: *any* ``## `` legitimately ends a section, so
"next section" and "heading inserted inside this one" are byte-identical structures.
The boundary is knowable, so it is **declared** rather than inferred -- each guarded
section ends at an explicit sentinel.

A sentinel is a markdown comment and an editor can delete one as easily as insert a
heading, which would relocate the same silent truncation. So a missing sentinel
**raises**, naming the coupling; it never degrades to "the rest of the file".
"""

END_TEMPLATE = "<!-- end: {key} -->"


class DoctrineSectionError(AssertionError):
    """Raised when a guarded section's boundary markers are absent or malformed."""


def end_marker(heading: str) -> str:
    """The sentinel that closes the section opened by ``heading``."""
    return END_TEMPLATE.format(key=heading.lstrip("#").strip())


def section(text: str, heading: str) -> str:
    """Return the guarded section opened by ``heading`` and closed by its sentinel.

    Never falls back to the rest of the file: a missing start or a missing, misplaced
    or duplicated end sentinel raises `DoctrineSectionError` naming the coupling.
    """
    marker = end_marker(heading)
    start = text.find(heading)
    if start < 0:
        raise DoctrineSectionError(
            f"doctrine section {heading!r} not found. This heading is load-bearing: "
            f"token assertions are scoped to it (GOV-0121 / #279)."
        )
    if text.count(marker) != 1:
        raise DoctrineSectionError(
            f"expected exactly one end sentinel {marker!r} in the doctrine file, "
            f"found {text.count(marker)}. This sentinel closes the section opened by "
            f"{heading!r}; the token assertions in tests/test_badf_git_activation.py and "
            f"tests/test_badf_build_activation.py are scoped by it. Removing it does NOT "
            f"widen the section -- it fails here, by design (GOV-0121 / #279)."
        )
    end = text.find(marker, start)
    if end < 0:
        raise DoctrineSectionError(
            f"end sentinel {marker!r} exists but precedes its own heading {heading!r}. "
            f"The sentinel must follow the section it closes (GOV-0121 / #279)."
        )
    return text[start:end]
