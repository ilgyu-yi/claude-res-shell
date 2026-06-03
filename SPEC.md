# SPEC — claude-res-shell

Canonical specification for **claude-res-shell**, the **research tier** of the orchestrated
shell system. res-shell is an **on-demand research subroutine**: it is *called* by another
shell (dir or eng), runs a bounded research task, and **returns a research document** used
as **evidence** for the caller's judgment. res makes no decisions and has no outgoing edges.

- **Status**: Specification phase, fresh rewrite (English). 2026-06-03.
- **Authority**: This SPEC is the source of truth for res-shell *design*. State/progress
  lives in claude-orch-shell's `WORK_LOG.md`. Where this SPEC and the earlier Korean
  res-shell docs (README, CLAUDE.md, the `/new-project`…`/report` workflow) disagree,
  **this SPEC wins**; the earlier docs are retained in git history only and are
  non-authoritative (working brief §2.5).
- **Scope**: res's role and invariants (§1), the research-document artifact + per-mode
  contract (§2), the mode mechanism (§3), the call interface (§4), how a document is
  produced internally (§5), the dir↔res / eng↔res contracts (§6), substrate (§7),
  capabilities/subagents (§8), decision record (§9), open items (§10).

> **Reading order.** §1 (role + invariants) → §2 (the document artifact) → §3 (modes) →
> §4 (call interface) → §6 (caller contracts). §2–§4 and §6 are the interfaces dir, eng,
> and claude-orch-shell depend on; treat them as frozen once accepted. The dir-side of the
> dir↔res contract is in **dir SPEC §6** and this SPEC mirrors it.

---

## 1. Role and invariants

res-shell sits to the side of the dir→eng pipeline, not in it:

```
   dir-shell ──research request (strategic)──► res-shell ──research document──► dir-shell
   eng-shell ──research request (technical)──► res-shell ──research document──► eng-shell
```

**Invariants (never violated):**

1. **res is always called; it never initiates.** It has **no outgoing edges**: it never
   calls dir, eng, or claude-orch-shell; never files Issues; never mutates a caller's
   artifacts; never triggers a stage transition. Its sole output is a document handed back
   to the caller.
2. **res makes no decisions.** A research document presents findings + evidence +
   caller-relevant implications and **stops short of deciding**. Whether and how the
   evidence changes anything is the caller's judgment, not res's.
3. **res's mode is fixed by its caller** (§3) and is **one mode for the whole invocation**.
   A single research call never mixes modes. A `strategic` call reads no source code; a
   `technical` call may.
4. **res is invisible to claude-orch-shell.** Research calls are **stage-internal
   subroutines** of dir's or eng's work (dir SPEC §6, §14 D11; claude-orch-shell SPEC). The
   claude-orch-shell neither sees nor routes them.

Conceptually, res is a **pure function**: `research(request) → document`. Same request →
equivalent document; no side effects outside writing that document to the agreed location.

What res is **not**: not a decision-maker, not a workflow stage, not a multi-project
planning workspace (the prior framing), not an author of Initiatives/Directives. It is a
evidence producer invoked on demand.

---

## 2. The research-document artifact

The research document is res-shell's sole output. It is written to the `output_location`
the caller supplied (§4) and its location is returned to the caller.

### 2.1 Shape

YAML frontmatter + markdown body:

```yaml
---
doc-id: 2026-06-03-activation-rate-benchmarks
mode: strategic | technical          # fixed at invocation (§3); never both
caller: dir | eng                    # who requested it
question: "<the research question, verbatim from the request>"
created-at: 2026-06-03T14:10:00Z
effort: quick | comparison | broad   # the effort tier actually used (§5.3)
sources-count: 12
code-read: false | true              # MUST be false in strategic mode (§3.2)
language: en                         # output language (default en; §9 D7)
---

## Question
<the question restated, plus any sub-questions res decomposed it into>

## Scope & method
<what was searched/read, the effort tier, the broad→narrow path taken, and explicit
 boundaries: what was deliberately NOT investigated and why>

## Findings
<the substantive answer, organized by sub-question or theme. Each non-trivial claim is
 attributed to a source in §Evidence.>

## Evidence
<numbered citations (§2.3). In strategic mode: planning-tier artifacts, web sources,
 literature, market/industry data — NEVER source code. In technical mode: may additionally
 cite code (files, symbols, commits, test/measurement results).>

## Confidence & limitations
<per-finding or overall confidence; what would change the conclusion; gaps; conflicting
 sources and how they were weighed>

## Implications for the caller (non-deciding)
<how this evidence bears on the caller's question — framed as "if X then this suggests Y",
 NOT "you should do Z". res presents; the caller decides. This section MUST NOT contain a
 recommendation, a selection, or a go/no-go.>
```

### 2.2 Per-mode contract

The body shape is identical across modes; the **contract on `Evidence` and `code-read`
differs**, and this difference is the whole point of modes:

- **strategic** (caller = dir): `code-read: false`. The `Evidence` section cites **only**
  planning-tier artifacts (MISSION, Issues, milestones), external/web sources, published
  literature, and market/industry data. **No source code, no diffs, no test output, no
  file paths into a codebase.** This is what makes the document safe for dir to fold into
  an Initiative without violating dir's code-independence (dir SPEC §6.3, D5). A strategic
  document is, by contract, evaluable and citable by someone who has never read code.
- **technical** (caller = eng): `code-read` may be `true`. The `Evidence` section may
  additionally cite code — specific files, symbols, commits, and measured/observed results
  from the codebase eng named — alongside external sources. Suitable as evidence for eng's
  code-level judgment.

A document's `mode` is authoritative: a `strategic` document **guarantees** no code was
read; a consumer (or a Tier-2 verification check, §10) can assert that no codebase path
appears in a strategic document's citations.

### 2.3 Citation conventions (both modes)

- **Paper**: `Author(s) (year). Title. Venue/arXiv-ID.`
- **Repo (technical mode only)**: `org/repo @ <commit-or-tag>` and, for a specific claim,
  `path/to/file.ext:Lstart-Lend` or a named symbol.
- **Web**: `Title — URL (accessed YYYY-MM-DD)`. Always an **absolute** access date; never
  "last week".
- **Planning-tier artifact**: `MISSION §<section>` / `<owner/repo> issue #N` / milestone name.

Every non-trivial claim in `Findings` carries a citation. Uncited assertion is a defect.

---

## 3. The mode mechanism

Mode is the load-bearing safety property of res: it is what lets dir stay code-independent
while still grounding Initiatives in real research, and what lets eng get code-aware
research when it needs it — without either caller having to police res by hand.

### 3.1 Mode is fixed by the caller, at entry

`caller` and `mode` are both fields of the request (§4.1), but they are **not independent**:
`mode` is **constrained to the value(s) its `caller` is permitted**, and res **validates**
the pair at entry — rejecting any request whose `mode` is not permitted for its `caller`.

- `caller = dir` ⟹ the **only** permitted `mode` is `strategic`. dir cannot request
  `technical`; a `dir` request with `mode: technical` is **rejected** (§4.1). (In this
  sense mode is "fixed by caller identity" — for dir there is exactly one legal value.)
- `caller = eng` ⟹ permitted `mode` is `technical` (default) or `strategic` for a purely
  planning-tier question — but never the reverse for dir (§3.3).
- **Trust source of `caller`.** `caller` is established by the **invoking context** (which
  shell launched res, §4.3) — it is a trusted property of the invocation, not a
  self-declared claim res must take on faith. res treats `caller` as authoritative and
  validates `mode` against it; it does not attempt to re-derive caller identity from the
  question or context.
- The validated `mode` is read **once, at invocation start**, and is immutable for the
  remainder of the call. There is no API to change mode mid-run.

### 3.2 Code-access is gated by mode

Mode determines res's available toolset for the invocation:

| Capability | strategic | technical |
|---|---|---|
| Web search / fetch | ✅ | ✅ |
| Read planning-tier artifacts (via the caller's provided context) | ✅ | ✅ |
| Read source code of a named codebase (Read/Grep/Glob over a repo; clone; run/measure) | ❌ **disabled** | ✅ (scoped to the codebase eng names) |
| File Issues / mutate caller artifacts / trigger transitions | ❌ | ❌ |

In **strategic** mode the code-reading capability is **not available to res at all** — it
is not a guideline res chooses to follow but a capability absent from the invocation
(enforced at the tooling/permission layer; §7.3, §10). This is the guarantee behind
`code-read: false`.

### 3.3 One invocation never mixes modes

- A single `research(request)` call is **one mode start to finish**. res cannot escalate
  from strategic to technical mid-run (the capability simply isn't present) and does not
  silently downgrade.
- If, mid-strategic-call, res discovers the question can **only** be answered by reading
  code, it does **not** switch modes. It returns the document with that finding stated
  under `Confidence & limitations` ("this question requires code-level investigation;
  out of scope for a strategic research call") and lets the caller decide whether to
  re-issue the question to eng (which would call res in technical mode). dir, by contract
  (dir SPEC §6.1), reframes such a question as planning-tier or defers it to eng.
- To get both a strategic and a technical perspective, a caller issues **two separate
  invocations**, each single-mode. They never blend inside one document.

---

## 4. The call interface

### 4.1 Request (input)

A research request is a structured brief (the contract dir issues per dir SPEC §6.2; eng
issues the analogous brief):

| Field | Required | Meaning |
|---|---|---|
| `question` | yes | The research question. |
| `caller` | yes | `dir` \| `eng`. Established by the **invoking context** (§4.3), trusted; not self-declared prose (§3.1). |
| `mode` | yes | `strategic` \| `technical`. **Constrained by `caller`** and **validated** against it (§3.1): dir⟹`strategic` only; eng⟹`technical`\|`strategic`. A request whose `mode` is not permitted for its `caller` is rejected. |
| `context` | yes | Caller-supplied context. **strategic**: planning-tier only (MISSION excerpts, Issue/Initiative text) — no code, no codebase paths. **technical**: may include the codebase address/path eng authorizes res to read. |
| `output_location` | yes | Path where res writes the research document and (in res's own substrate) any supporting notes. |
| `effort` | no | Hint: `quick` \| `comparison` \| `broad` (§5.3). res may adjust with rationale. |
| `language` | no | Output language for the document. Default `en`. |
| `deadline`/`budget` | no | Optional bound on tool calls / subagents (caps §5.3 scaling). |

res **validates** the request at entry and **fails closed** on any violation — it does not
silently repair a malformed request:

1. `mode` must be permitted for `caller` (§3.1: dir⟹`strategic` only; eng⟹`technical`|
   `strategic`). An impermissible pair is **rejected** (the call never starts).
2. In `strategic` mode, `context` must contain **no codebase path or code excerpt**. If it
   does, the request is **rejected** with an error naming the offending path — **not**
   silently stripped. (Fail-closed: a strategic call that smuggles in code access is a
   contract violation by the caller; res surfaces it rather than proceeding on a guess. dir,
   by its own contract (dir SPEC §6.2), never supplies code paths, so a well-behaved dir
   call never trips this — the check guards against misconfiguration, not normal operation.)

### 4.2 Response (output)

- res writes the research document (§2) to `output_location` and **returns that location**
  (and a one-line summary) to the caller.
- That is the **entire** response. res does not act on the caller's artifacts, does not
  decide, does not initiate anything downstream (§1 invariants 1–2).
- The caller reads the document and exercises its own judgment (dir folds it into an
  Initiative as cited evidence per dir SPEC §6.3; eng uses it for code-level judgment).

### 4.3 Invocation mechanism (design level)

All local, no remotes. res is a component the caller invokes; the concrete mechanism
(separate Claude Code session/subprocess with the request as its brief, vs. an in-process
research subagent bundle) is a **Tier-2 implementation choice** and is recorded when built.
At the design level the contract is what matters: request in (§4.1) → document at
`output_location` (§4.2) → control returns to caller. The mode's tool-gating (§3.2) must
hold whatever the mechanism; strategic invocations must be launched with code-reading
capabilities absent (§7.3).

---

## 5. Producing a document (internal method)

How res turns a request into a well-grounded document. These are res's *internal*
mechanics (salvaged from the prior res-shell and reframed); they are not visible to the
caller, which sees only the request/response contract (§4).

### 5.1 Broad → narrow

Begin with short, wide queries to map the landscape (categories, candidates, key sources);
only then narrow to deep reads of the most promising sources. This avoids deep-reading
dead ends. (Prior `/survey` capability → the broad phase; §8.)

### 5.2 Subagent dispatch — four elements

When res fans work out to subagents, every dispatch states all four:
**Objective** (what to find), **Output format** (structure/length), **Tools/Sources**
(which tools — **constrained by mode**, §3.2), **Boundary** (what not to do, when to stop).
In strategic-mode dispatches, the Tools element must not include code-reading; this is how
the mode invariant propagates to subagents.

### 5.3 Effort scaling

| Effort tier | Subagents | Tool calls each | Use for |
|---|---|---|---|
| `quick` | 1 | 3–10 | a single fact / narrow lookup |
| `comparison` | 2–4 | 10–15 | contrast a few approaches/options |
| `broad` | 3–6 | 15–25 | landscape survey of an open area |

The request may hint `effort` (§4.1); res may adjust and records the tier actually used in
the document frontmatter and `Scope & method`. Exceeding a tier (or a request `budget`)
without rationale is a defect.

### 5.4 Synthesis

Cross-cut the gathered sources into the document (§2): agreements, conflicts (and how
weighed), gaps, and the caller-relevant implications — stopping short of a decision (§1
invariant 2). Every claim cited (§2.3).

---

## 6. Caller contracts

### 6.1 dir ↔ res (strategic)

Mirror of **dir SPEC §6**. dir issues `{question, mode: strategic, caller: dir, context:
planning-tier-only, output_location}`. res returns a strategic document (`code-read:
false`, no code in citations). dir cites it as Evidence in an Initiative and treats it as
evidence for dir's judgment, never a decision. The strategic contract (§2.2) is exactly
what preserves dir's code-independence: dir can fold the document in without ever touching
code, because res guarantees the document contains none.

### 6.2 eng ↔ res (technical, or strategic)

eng issues `{question, mode: technical, caller: eng, context: may include an authorized
codebase address, output_location}`. res returns a technical document that may cite code
from the named codebase plus external sources. eng may also issue a `strategic` request
for a purely planning-tier question; res then behaves exactly as in §6.1 (no code).
**This SPEC defines res's side of the eng↔res contract only.** eng-shell is a frozen
external system (working brief §2.1); res is designed to serve eng's request without
requiring any eng-shell change. If a future need would require eng to change, it is
recorded here as deferred — none identified this session.

### 6.3 Orchestrator

claude-orch-shell does **not** participate in res calls (§1 invariant 4; dir SPEC §14 D11).
res calls are internal to dir/eng stages. res exposes nothing to and requires nothing from
claude-orch-shell.

---

## 7. Substrate

### 7.1 Per-invocation workspace

Each invocation gets a working area under its `output_location` to hold the document and
the supporting notes that justify it (an audit trail of what was read):

```
<output_location>/
  <doc-id>.md                 # the returned research document (§2)
  notes/
    landscape-<date>.md       # broad-phase survey output (§5.1)
    <source-id>.md            # deep-read notes (paper / web / code per mode)
  request.json                # the validated request (§4.1) — provenance
```

Notes are retained as the audit trail so a caller (or future session) can see what evidence
the document rests on. This replaces the prior `projects/<name>/PLAN.md` multi-project
model — res no longer owns long-lived projects; it owns one document per call (§9 D2). The
caller, not res, decides where `output_location` lives (e.g., dir points it at the
workspace batch's `research/` dir, dir SPEC §7.1).

### 7.2 No code in strategic substrate

In a strategic invocation, `notes/` contains no code excerpts and `request.json`'s context
carries no codebase paths (§4.1 validation). The whole invocation footprint is
code-free — verifiable after the fact (§10).

### 7.3 Tool gating by mode

The invocation's permission set is selected by mode at launch (§3.2): strategic launches
**without** code-reading/repo tools; technical launches with them, scoped to the authorized
codebase. The current `.claude/settings.json` (web + file-ops over a research workspace) is
the strategic baseline; the technical profile adds scoped code-reading and is a Tier-2
deliverable. See §10.

---

## 8. Capabilities / subagents

res's existing skills are reframed as **internal capabilities used while producing a
document**, not user-facing project commands. Mode gates which are available:

| Capability (prior skill) | Role in producing a document | Modes |
|---|---|---|
| landscape-survey | The broad phase (§5.1): map categories/candidates, shortlist sources | both |
| paper-reader | Deep-read an external paper/article into a note | both |
| codebase-scout | Deep-read a named codebase (structure, entry points, modules) | **technical only** (§3.2) |
| synthesizer | Cross-cut notes into Findings/Evidence (§5.4) | both |
| report-builder | Assemble the final research document (§2) | both |
| idea-incubator | Decompose the question into sub-questions when the question is broad | both (internal only; res does not "incubate ideas" for a caller — the caller owns the question) |

`codebase-scout` being technical-only is a clean enforcement point: if a strategic
invocation ever reaches for it, the mode invariant has been violated and the call is
defective.

The prior **user-facing** commands (`/new-project`, `/incubate`, `/survey`, `/paper`,
`/codebase`, `/synthesize`, `/report`, `/capture`, `/triage`, `/status`, `/projects`) are
**dropped** as the primary interface — res is invoked via a request (§4), not driven as a
standalone multi-project app. Some may return as **debug/manual entry points** for running
res by hand against a hand-written request (a Tier-2 convenience), but they are not the
contract. Recorded in §9 D2 and §10.

---

## 9. Decision record

Settled choices + rationale. **[brief]** marks premises inherited from the working brief §3
(fixed unless proven to block the end goal, then revise-and-log per brief §2.4).

| # | Decision | Rationale |
|---|---|---|
| D1 **[brief]** | res is an **on-demand subroutine** with **no outgoing edges**, returning a **document used as evidence**, and **makes no decisions** (§1). | The brief fixes this shape. It keeps res composable (any caller) and keeps judgment with the caller. |
| D2 | **Drop the multi-project workflow** (`/new-project`…`/report`, `projects/<name>/PLAN.md`) as the interface; res produces **one document per call** with a per-invocation workspace (§7.1). The old skills become **internal capabilities** (§8). | The brief reframes res from a standalone research app into a callable producer. One-document-per-call matches `research(request)→document`. Salvage the *mechanics* (broad→narrow, 4-element dispatch, effort scaling, citations), drop the *project framing*. |
| D3 **[brief]** | **Mode is fixed by caller identity**, immutable per invocation, and **gates code access** (§3). dir⟹strategic (never code); eng⟹technical\|strategic. | The core safety property: it is what lets dir stay code-independent while still using real research, with no per-call policing. |
| D4 **[brief]** | A **strategic** document **guarantees `code-read: false`** and cites no code (§2.2); enforced by **absence of code-reading tools** in the invocation, not by convention (§3.2, §7.3). | A guarantee dir (and a verifier) can rely on. Tooling-level enforcement is stronger than a prompt instruction. |
| D5 **[brief]** | **One invocation never mixes modes** (§3.3); a strategic call that hits a code-only question returns the limitation rather than escalating. | The brief requires single-mode invocations. Escalation would silently break dir's code-independence; surfacing the limitation keeps the boundary clean and hands the decision back to the caller. |
| D6 **[brief]** | res is **invisible to claude-orch-shell** (§6.3); research calls are stage-internal. | claude-orch-shell is type-A metadata-only plumbing (dir SPEC §14 D11; claude-orch-shell SPEC); res calls are subroutines of dir/eng stages, not routed artifacts. |
| D7 | Research-document **output language defaults to English** with an optional `language` request field. | The brief mandates English for this work; callers are English. The prior Korean-output convention is retained only as an opt-in (`language: ko`), not the default. |
| D8 | **Invocation mechanism is a Tier-2 choice** (§4.3); the SPEC fixes the request/response **contract**, not the transport. | Lets the contract stabilize now (Tier 1) and claude-orch-shell spec depend on it, while the concrete launch mechanism is decided at implementation. |

---

## 10. Open items

- **Concrete invocation mechanism** (§4.3): separate session/subprocess vs in-process
  subagent bundle. Decide at Tier 2; whichever is chosen must preserve mode tool-gating.
- **Technical-mode permission profile** (§7.3): the scoped code-reading `settings.json`
  profile for technical invocations (the current settings are the strategic baseline).
- **Strategic-mode verification check**: ✅ **implemented** (defense-in-depth) in
  [`validation/`](validation/) — `check()` asserts a strategic document declares
  `code-read: false` and cites no codebase path / code line reference (operationalizes D4).
  20 offline tests. Note: the *primary* guarantee remains tool-absence at launch (§3.2,
  §7.3); this is a second line on the output. Still open: a thin adapter parsing a real
  document's frontmatter+Evidence into the guard's input once the producer exists.
- **Whether to keep any user-facing manual commands** (§8) as debug entry points for
  running res by hand against a written request.
- **Request schema format** (§4.1): JSON vs YAML vs CLI flags for `request.json`; pick at
  Tier 2 to match the invocation mechanism.
- **Effort defaults** when `effort` is omitted (currently res infers from the question;
  may want a stated default).
- **eng's request shape** (§6.2): eng is frozen/out of scope, so the eng-side request brief
  is unspecified here. A Tier-2 res implementation that must validate an eng request should
  first reverse-engineer eng's actual call shape (read-only) or document the **assumed** eng
  brief and validate against it — without requiring any eng-shell change.

---

*This SPEC is a fresh English rewrite (2026-06-03) superseding the prior Korean res-shell
docs and the `/new-project`…`/report` workflow where they conflict. State/progress:
claude-orch-shell `WORK_LOG.md`.*
