"""res strategic-mode guard — defense-in-depth check that a strategic document
contains no code (claude-res-shell SPEC §2.2, §3.2, D4; §10 "Strategic-mode
verification check").

The PRIMARY guarantee that a strategic invocation reads no source code is
*tool absence* at launch (SPEC §3.2, §7.3): res simply has no code-reading
capability in strategic mode. This module is **defense-in-depth on the output**:
given a produced research document's mode + its citations/footprint, it asserts a
`strategic` document declares `code-read: false` and cites no codebase path or
code line reference. It is heuristic by nature (see limitations below) and
fail-closed: any violation -> not ok.

Web sources (http/https URLs) are ALLOWED in strategic mode (SPEC §2.2) and are
not flagged, except for obvious VCS "blob/raw" links pointing at code.

No third-party dependencies; Python 3 stdlib only. See validation/README.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# Source-code file extensions that, on a non-URL path, signal a codebase reference.
# Deliberately excludes doc/data/web extensions (.md, .txt, .pdf, .html, .csv, .json…)
# which legitimately appear in strategic citations.
CODE_EXTENSIONS = frozenset({
    "py", "js", "ts", "tsx", "jsx", "go", "rs", "java", "kt", "kts", "c", "cc",
    "cpp", "cxx", "h", "hpp", "hh", "rb", "sh", "bash", "zsh", "swift", "scala",
    "php", "cs", "m", "mm", "lua", "pl", "r", "jl", "ex", "exs", "erl", "clj",
    "vue", "svelte", "sql",
})

# `:L12` or `:L12-34` or `:L12-L34` — a code line reference (SPEC §2.3).
_LINE_REF = re.compile(r":L\d+(?:-L?\d+)?\b")
# A `#L12` anchor as used by VCS web blob links.
_HASH_LINE = re.compile(r"#L\d+\b")
# `org/repo @ <commit>` — a code citation per SPEC §2.3 (repo at a commit/tag).
_REPO_AT_COMMIT = re.compile(r"\b[\w.\-]+/[\w.\-]+\s*@\s*[0-9a-f]{7,40}\b", re.I)
# A bare token ending in a code extension (e.g. `src/server.py`, `pkg/main.go:L4`).
_CODE_PATH = re.compile(
    r"(?<![\w./])[\w./\-]+\.(" + "|".join(sorted(CODE_EXTENSIONS)) + r")\b", re.I
)
# VCS web blob/raw links (github/gitlab/bitbucket style) pointing at a file.
_VCS_BLOB = re.compile(r"/(?:blob|raw|-/blob|-/raw|src)/", re.I)


def _is_url(ref: str) -> bool:
    return ref.strip().lower().startswith(("http://", "https://"))


def looks_like_code_reference(ref: str) -> bool:
    """Heuristic: does this citation/footprint token reference a codebase / code?

    Returns True for repo@commit code citations, file paths with code extensions,
    and code line references — i.e. the forms SPEC §2.3 reserves for *technical*
    documents. Plain web URLs are allowed (False) UNLESS they are an obvious VCS
    blob/raw link to a code file or carry a `#L<n>` line anchor.
    """
    s = ref.strip()
    if not s:
        return False

    if _is_url(s):
        # Web sources are allowed in strategic mode — except blob/raw VCS links to code.
        if _VCS_BLOB.search(s) and (_CODE_PATH.search(s) or _HASH_LINE.search(s)):
            return True
        return False

    # Non-URL references:
    if _LINE_REF.search(s):
        return True
    if _REPO_AT_COMMIT.search(s):
        return True
    if _CODE_PATH.search(s):
        return True
    return False


@dataclass(frozen=True)
class ResearchDocumentFacts:
    """The minimal facts the guard inspects (a subset of the SPEC §2.1 frontmatter
    plus the document's citation/footprint references). The guard never needs the
    Findings prose — only the mode flags and the reference list."""

    mode: str                      # "strategic" | "technical"
    code_read: bool                # the frontmatter `code-read` field
    citations: tuple[str, ...] = ()      # Evidence entries (SPEC §2.3)
    footprint_paths: tuple[str, ...] = ()  # files in the invocation's notes/ (SPEC §7.1)

    def __post_init__(self) -> None:
        if self.mode not in ("strategic", "technical"):
            raise ValueError(f"mode must be 'strategic' or 'technical', got {self.mode!r}")


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    violations: tuple[str, ...] = ()


def check(doc: ResearchDocumentFacts) -> GuardResult:
    """Validate a research document against its mode's contract (fail-closed).

    strategic: `code-read` must be false AND no citation/footprint may be a code
    reference (SPEC §2.2). technical: code is allowed; we only check internal
    consistency (if code is cited, `code-read` should be true).
    """
    violations: list[str] = []

    if doc.mode == "strategic":
        if doc.code_read:
            violations.append("strategic document declares `code-read: true` (must be false)")
        for c in doc.citations:
            if looks_like_code_reference(c):
                violations.append(f"strategic document cites a code reference: {c!r}")
        for p in doc.footprint_paths:
            if looks_like_code_reference(p):
                violations.append(f"strategic invocation footprint contains a code path: {p!r}")
    else:  # technical
        cites_code = any(looks_like_code_reference(c) for c in doc.citations)
        if cites_code and not doc.code_read:
            violations.append("technical document cites code but declares `code-read: false`")

    return GuardResult(ok=not violations, violations=tuple(violations))


if __name__ == "__main__":
    samples = [
        ResearchDocumentFacts(
            "strategic", code_read=False,
            citations=(
                "Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762",
                "State of AI Report 2025 — https://example.com/report.html (accessed 2026-06-03)",
                "owner/repo issue #47",
                "MISSION §Success looks like",
            ),
        ),
        ResearchDocumentFacts(
            "strategic", code_read=False,
            citations=("acme/widgets @ a1b2c3d server/handler.py:L10-L42",),
        ),
        ResearchDocumentFacts("strategic", code_read=True, citations=()),
        ResearchDocumentFacts(
            "technical", code_read=True,
            citations=("acme/widgets @ a1b2c3d server/handler.py:L10-L42",),
        ),
    ]
    for i, s in enumerate(samples, 1):
        r = check(s)
        print(f"[{i}] mode={s.mode} ok={r.ok}")
        for v in r.violations:
            print(f"     - {v}")
