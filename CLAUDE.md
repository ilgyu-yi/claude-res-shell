# claude-res-shell — Operating Norms

Operating manual for working in this repo, read by Claude Code at session start.
Authoritative design: [SPEC.md](SPEC.md). Direction: [MISSION.md](MISSION.md). res is the
research tier of the orchestrated claude-*-shell system.

## Status

**[SPEC.md](SPEC.md) is the source of truth** for design — where this file or the README
disagree with SPEC, SPEC wins. The prior Korean multi-project framework
(`/new-project`…`/report`) is superseded (SPEC §9 D2). This is a **spec-first** project: do
not implement a unit until its SPEC section is complete; if implementation reveals the spec
is wrong, fix the spec first. Engineering process follows **claude-eng-shell discipline**
(see the bottom of this file): Issue → branch → PR (`Closes #N`) → merge.

## Core norms

### 1. res is a subroutine — called, never initiating
res is invoked with a **research request** and returns a **research document** to its
caller (SPEC §4). It has **no outgoing edges**: never files Issues, never mutates a
caller's artifacts, never triggers a stage transition, never calls dir/eng/orchestrator
(SPEC §1). Its only output is the document at the request's `output_location`.

### 2. res makes no decisions
A research document presents findings + cited evidence + caller-relevant **implications**
and **stops short of deciding** (no recommendation, no selection, no go/no-go). The caller
exercises judgment. SPEC §2.1 (the "Implications for the caller (non-deciding)" section).

### 3. Mode is fixed by the caller and never mixed
`caller = dir` ⟹ **strategic** (no source code, ever). `caller = eng` ⟹ **technical**
(may read the authorized codebase) or strategic. The mode is read once at entry and is
immutable for the whole invocation (SPEC §3). A strategic call that turns out to need code
**does not escalate** — it returns the limitation and lets the caller re-issue to eng.

### 4. Strategic mode reads no code — guaranteed by tooling
In a strategic invocation, code-reading capability is **absent**, not merely discouraged
(SPEC §3.2, §7.3). A strategic document asserts `code-read: false` and cites no code. When
working by hand before the implementation ships, honor this as if enforced: in a strategic
task, do not read any source tree, diff, or test output; cite only planning-tier and
external sources.

### 5. Method: broad → narrow, four-element dispatch, effort scaling
Survey the landscape before deep-reading (SPEC §5.1). Every subagent dispatch states
objective / output format / tools (mode-gated — no code tools in strategic) / boundary
(SPEC §5.2). Scale effort by tier (quick / comparison / broad, SPEC §5.3); record the tier
used and don't exceed it (or a request `budget`) without rationale.

### 6. Cite everything; absolute dates
Every non-trivial claim carries a citation (SPEC §2.3). Web sources get an absolute access
date (`YYYY-MM-DD`), never "last week". Code citations appear only in technical-mode
documents.

### 7. Output language
Research documents default to **English** (SPEC §9 D7). A request may opt into another
language via the `language` field (e.g. the prior Korean convention via `language: ko`),
but English is the default and all repo docs/specs are English.

## Engineering discipline (adopted from claude-eng-shell)

This repo follows claude-eng-shell's process:

- **Issue → branch → PR → merge.** File a typed Issue; branch
  `<gh-username>/<type>/<issue#>-<slug>`; open a PR that ends with `Closes #<N>` (or
  `Refs #<N>` for intermediate PRs); merge into `main` with a **merge commit** (no
  squash/rebase on the default branch).
- **Conventional commits.** `<type>(#<issue>)[!]: <subject>` (subject ≤ 72 codepoints).
  Types: `feat fix docs refactor perf` (issue # required) · `test style build ci chore
  revert` (issue # optional). Optional trailer `Co-Authored-By: Claude
  <noreply@anthropic.com>`.
- **Doc → Test → Code** phased commits where it applies (features); relaxed for
  fix/refactor/perf.
- **Changelog fragments.** Each PR with an observable change adds a one-line fragment
  `changelog_unreleased/<category>/<PR>.md` (`- … (#<PR>)`); pure-internal PRs use the
  `skip-changelog` label. Releases consolidate fragments into `CHANGELOG.md` + bump
  `VERSION`.

## Boundary

- Never modifies user-global state (`~/.zshrc`, global git config, `~/.claude/` outside the
  auto-memory tier).
- Never writes to a caller's artifacts or to sibling shells. **claude-eng-shell is a frozen
  external system** — never write to it.
- When res ships, the strategic invocation profile launches without code-reading tools; the
  technical profile adds them, scoped to the codebase eng authorizes (SPEC §7.3).
