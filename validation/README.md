# validation/ — res strategic-mode guard (Tier-2 unit)

Defense-in-depth check that a **strategic** research document contains no code,
operationalizing claude-res-shell [SPEC.md](../SPEC.md) §2.2 / §3.2 / decision D4 and the
§10 open item "Strategic-mode verification check".

## Why this exists (and what really guarantees no-code)

The **primary** guarantee that a strategic invocation reads no source code is **tool
absence at launch** (SPEC §3.2, §7.3): in strategic mode res has *no* code-reading
capability, so it cannot read code even if it tried. This module does **not** replace that
— it is **defense-in-depth on the produced output**: given a research document's mode flags
and its citation/footprint references, it asserts a strategic document declares
`code-read: false` and cites no codebase path or code line reference. It catches
misconfiguration and contract drift; it is not the enforcement boundary itself.

## What it is

- `strategic_guard.py`
  - `looks_like_code_reference(ref) -> bool` — heuristic detector for the code-citation
    forms SPEC §2.3 reserves for *technical* documents: `org/repo @ <commit>`, file paths
    with code extensions, `:L<n>` line refs, and VCS `blob/raw` URLs to code. Plain web
    URLs, papers, `MISSION §…`, and `owner/repo issue #N` are **allowed** (not flagged).
  - `ResearchDocumentFacts(mode, code_read, citations, footprint_paths)` — the minimal
    facts inspected (a subset of the SPEC §2.1 frontmatter + the reference list). The guard
    never needs the Findings prose.
  - `check(doc) -> GuardResult(ok, violations)` — fail-closed. strategic: `code-read` must
    be false and no reference may be code. technical: code allowed; only checks internal
    consistency (code cited ⇒ `code-read` should be true).

## Document adapter (`document.py`)

`document.py` is the res-side analogue of the orchestrator's `fetch.py` and dir's
`candidate.py` (real artifact → tested core). It parses a produced research document's
frontmatter (`mode`, `code-read`) and `## Evidence` citations (SPEC §2.1/§2.3) into
`ResearchDocumentFacts`, then runs the guard:

- `parse_document(text, footprint_paths=())` → `ResearchDocumentFacts` (minimal frontmatter
  parser, no PyYAML).
- `check_document(text, footprint_paths=())` → `GuardResult` in one step.

```sh
cd validation && python3 document.py    # demo: clean strategic doc + leaky strategic doc
```

## Verify

```sh
python3 -m unittest discover -s validation -p 'test_*.py'   # from repo root — 30 tests
cd validation && python3 -m unittest test_strategic_guard -v   # guard (20)
cd validation && python3 -m unittest test_document -v          # document adapter (10)
cd validation && python3 strategic_guard.py                    # guard demo
```

`test_strategic_guard.py` (20) pins the heuristic (flags repo@commit / code paths / line
refs / VCS blob-to-code; allows papers / web / pdf / md / planning-tier refs), the strategic
contract (clean passes; code citation / `code-read: true` / code footprint fails; violations
accumulate), the technical contract, and validation. `test_document.py` (10) pins
frontmatter + Evidence parsing and a parse→guard end-to-end path.

## Known limitations (heuristic boundary)

- It is a **heuristic on text**, not a sandbox. A code reference disguised as prose, or a
  shortened/obfuscated URL to code, can slip past. That is acceptable because the real
  guarantee is tool-absence (above); this guard is a second line.
- Extension/URL heuristics may need tuning per real corpora; `CODE_EXTENSIONS` and the VCS
  blob patterns are the tuning points.

## Notes

- **Language is a provisional Tier-2 choice** (Python 3 stdlib), matching the orchestrator's
  `routing/` unit for consistency and zero-dependency offline testing. Reversible.
- This unit validates a document's *facts*; parsing a real document's frontmatter +
  Evidence section into `ResearchDocumentFacts` is a thin adapter left for when the res
  document producer exists (SPEC §2, §5).
