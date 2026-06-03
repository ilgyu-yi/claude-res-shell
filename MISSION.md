# MISSION — claude-res-shell

claude-res-shell is the **research tier** of an orchestrated Claude Code shell system. It is
an **on-demand research subroutine**: a caller shell (claude-dir-shell or claude-eng-shell)
hands it a research question, res runs a bounded research task, and returns a **research
document** used as evidence for the caller's judgment.

## The load-bearing idea

res's **mode is fixed by its caller** and is immutable for the whole invocation. A `dir`
call is **strategic** — res reads **no source code**; all evidence is planning-tier or
external. An `eng` call may be **technical** — res may read the codebase eng authorizes. One
invocation is one mode, never mixed. This is the property that lets the planning tier ground
its commitments in real research while staying code-independent, and it is enforced by the
**absence** of code-reading tools in a strategic invocation, not by convention. See
[SPEC.md](SPEC.md) §3.

## Shared principle — context narrowing

res shares the system's load-bearing principle (origin:
[claude-eng-shell MISSION](https://github.com/ilgyu-yi/claude-eng-shell/blob/main/MISSION.md)
"The mechanism"; system statement in claude-orch-shell MISSION): **output quality is bounded
by the size and relevance of working context** — keep the active context small and relevant
(narrowing + selective injection), with **artifacts, not conversations, as the durable
memory**. Every research call is judged against it.

res embodies it by returning a **document — a distilled verdict, not a transcript** (one per
call), by **mode-gating its context surface** (a strategic invocation carries *no code tools
at all*, so the code context is structurally absent), and by going **broad→narrow** (survey
the landscape before deep-reading). Each call is a **bounded, single-mode subroutine**, not
an accumulating session — which is exactly why the prior long-running multi-project framing
was dropped (SPEC §9 D2).

## What it does

- **Answers a research question** with a bounded, effort-scaled investigation (broad→narrow).
- **Returns a research document** — findings + cited evidence + caller-relevant implications,
  stopping short of any decision. res makes no decisions and has no outgoing edges.
- **Guarantees the mode contract** — a strategic document declares `code-read: false` and
  cites no code; a technical document may cite the authorized codebase.

## Success looks like

- **The mode boundary holds.** No strategic document ever contains code-derived content; the
  guarantee is structural (tool absence), with a defense-in-depth output check.
- **Documents are evidence, not decisions.** Every document presents and stops; the caller
  exercises judgment.
- **Grounding is real.** Findings are cited (papers, web with absolute dates, planning-tier
  artifacts; code only in technical mode), broad→narrow, effort-scaled.

## Out of scope

- **Not a workflow stage** — res is called on demand; it never initiates or routes.
- **Not a decision-maker** — it produces evidence, never a recommendation/selection/go-no-go.
- **Not a standalone multi-project app** — the prior `/new-project`…`/report` framing is
  superseded (SPEC §9 D2).

---

*Authoritative design: [SPEC.md](SPEC.md).*
