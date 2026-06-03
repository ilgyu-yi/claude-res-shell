"""Research-document adapter — parse a research document and run the strategic
guard on it (claude-res-shell SPEC §2.1/§2.3, §3).

The res-side analogue of the orchestrator's `fetch.py` and dir's `candidate.py`
(real artifact -> tested core): pull the `mode` / `code-read` frontmatter and the
`## Evidence` citations from a produced research document (SPEC §2.1 shape) into
`ResearchDocumentFacts`, then `check()` it (strategic_guard).

Frontmatter is parsed with a minimal line parser (no PyYAML dependency) — only the
few scalar keys the guard needs.

Python 3 stdlib only. See validation/README.md.
"""

from __future__ import annotations

import re
from typing import Optional

from strategic_guard import ResearchDocumentFacts, GuardResult, check


_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
_BOOL_TRUE = {"true", "yes", "on", "1"}
_BOOL_FALSE = {"false", "no", "off", "0"}


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER.search(text)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fm[key.strip().lower()] = val.strip().strip("'\"")
    return fm


def _as_bool(val: Optional[str], *, default: bool = False) -> bool:
    if val is None:
        return default
    v = val.strip().lower()
    if v in _BOOL_TRUE:
        return True
    if v in _BOOL_FALSE:
        return False
    return default


def extract_section(text: str, name: str) -> Optional[str]:
    """Body of a `## <name>` / `### <name>` section, or None (same convention as
    dir's candidate adapter)."""
    pat = re.compile(
        r"^#{2,3}\s+" + re.escape(name) + r"\s*$(.*?)(?=^#{1,3}\s|\Z)",
        re.I | re.M | re.S,
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(1).strip() or None


def _citations(evidence: Optional[str]) -> tuple[str, ...]:
    if not evidence:
        return ()
    cites = []
    for line in evidence.splitlines():
        s = line.strip()
        m = re.match(r"(?:[-*]|\d+\.)\s+(.*)", s)
        if m and m.group(1).strip():
            cites.append(m.group(1).strip())
    return tuple(cites)


def parse_document(text: str, footprint_paths: tuple[str, ...] = ()) -> ResearchDocumentFacts:
    """Parse a research document's frontmatter + Evidence into guard facts.

    `mode` and `code-read` come from frontmatter (SPEC §2.1); citations come from
    the `## Evidence` section (SPEC §2.3). `footprint_paths` (the notes/ files,
    SPEC §7.1) live on disk, not in the document, so they are supplied by the caller
    when a filesystem check is wanted; default empty.
    """
    fm = _parse_frontmatter(text)
    mode = (fm.get("mode") or "").lower()
    if mode not in ("strategic", "technical"):
        raise ValueError(f"document frontmatter `mode` must be strategic|technical, got {mode!r}")
    code_read = _as_bool(fm.get("code-read") or fm.get("code_read"), default=False)
    citations = _citations(extract_section(text, "Evidence"))
    return ResearchDocumentFacts(
        mode=mode,
        code_read=code_read,
        citations=citations,
        footprint_paths=footprint_paths,
    )


def check_document(text: str, footprint_paths: tuple[str, ...] = ()) -> GuardResult:
    """Parse + guard a research document in one step (SPEC §2.2/§3.2/D4)."""
    return check(parse_document(text, footprint_paths))


if __name__ == "__main__":
    clean = """---
doc-id: 2026-06-03-activation-benchmarks
mode: strategic
caller: dir
code-read: false
---
## Question
What activation rate is realistic?

## Evidence
- Vaswani et al. (2017). Attention Is All You Need. arXiv:1706.03762
- State of Onboarding 2025 — https://example.com/report.html (accessed 2026-06-03)
- owner/repo issue #47
"""
    leaky = """---
mode: strategic
code-read: false
---
## Evidence
- acme/widgets @ a1b2c3d server/handler.py:L10-L42
"""
    for label, doc in [("clean strategic", clean), ("leaky strategic", leaky)]:
        r = check_document(doc)
        print(f"[{label}] ok={r.ok}")
        for v in r.violations:
            print(f"   - {v}")
