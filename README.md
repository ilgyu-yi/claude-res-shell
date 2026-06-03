# claude-res-shell

The **research tier** of an orchestrated [Claude Code](https://docs.claude.com/claude-code)
shell system. res-shell is an **on-demand research subroutine**: another shell
([claude-dir-shell](https://github.com/ilgyu-yi/claude-dir-shell) or
[claude-eng-shell](https://github.com/ilgyu-yi/claude-eng-shell)) **calls** it with a
research question, res runs a bounded research task, and **returns a research document**
used as **evidence** for the caller's judgment. res makes no decisions and has no outgoing
edges.

See [SPEC.md](SPEC.md) for the authoritative design (a fresh 2026-06-03 English rewrite).
The earlier Korean docs and the `/new-project`…`/report` multi-project workflow are
superseded and retained in git history only.

## The core idea

```
dir-shell ──research request (strategic)──► res-shell ──research document──► dir-shell
eng-shell ──research request (technical)──► res-shell ──research document──► eng-shell
```

- **Called, never initiating.** res returns a document and stops; it never files
  artifacts, never decides, never triggers anything downstream.
- **Mode is fixed by the caller.** A `dir` call is **strategic** — res reads **no source
  code**; all evidence is planning-tier or external. An `eng` call may be **technical** —
  res may read the codebase eng authorizes. One invocation is one mode, start to finish;
  modes never mix. This is what lets dir stay code-independent while still grounding its
  Initiatives in real research. SPEC §3.
- **Document as evidence, not decision.** The document presents findings + cited evidence +
  caller-relevant implications, and stops short of recommending. The caller judges. SPEC §2.

## Status

Specification complete; tooling in progress. The repo carries the authoritative SPEC,
README/MISSION/CLAUDE, a strategic-baseline `.claude/settings.json`, and the `validation/`
tooling (the strategic-mode guard + research-document adapter). The request/response handler
is not yet implemented. The prior `/new-project`…`/report` multi-project workflow is
superseded (SPEC §9 D2) and not part of this repo.

## Design basis (salvaged mechanics)

- **broad → narrow** exploration — survey the landscape before deep-reading, to avoid
  dead ends. SPEC §5.1.
- **Subagent four-element dispatch** — objective / output format / tools (mode-gated) /
  boundary. SPEC §5.2.
- **Effort scaling** — quick / comparison / broad tiers. SPEC §5.3.

Reference: [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)
