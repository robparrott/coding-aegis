# AD-9: AGENTS.md as single source of truth

**Status**: Accepted

## Context

Multiple coding agent tools each have their own guidance file format:
- Claude Code: `CLAUDE.md`
- Cursor: `.cursor/rules/*.mdc`
- Windsurf: `.windsurf/rules/*.md`
- Copilot: `.github/copilot-instructions.md`

AGENTS.md is an open standard under the Linux Foundation's Agentic AI Foundation, supported by 60k+ projects and most coding agent tools. However, Claude Code does not natively read AGENTS.md — it reads `CLAUDE.md` and supports importing AGENTS.md via `@AGENTS.md` syntax.

## Decision

**AGENTS.md is the single source of truth for all coding agent guidance.** No tool-specific guidance file is checked into version control as a manually authored artifact.

Tool-specific files are created at runtime by the coding-aegis skill:

| Tool | File created | Mechanism |
|------|-------------|-----------|
| **Claude Code** | `CLAUDE.md` containing `@AGENTS.md` | Created by skill at runtime, not checked in |
| **Cursor** | `.cursor/rules/governance.mdc` | Rendered from AGENTS.md by the rendering pipeline |
| **Windsurf** | `.windsurf/rules/governance.md` | Rendered from AGENTS.md by the rendering pipeline |
| **Copilot** | `.github/copilot-instructions.md` | Rendered from AGENTS.md by the rendering pipeline |

## Rationale

- Avoids content drift between multiple files
- AGENTS.md aligns with the emerging industry standard
- Claude Code's `@import` mechanism bridges the gap without duplication
- Cursor, Windsurf, and Copilot don't support imports, so their files must contain rendered content — but this is generated, not hand-authored
- Tool-specific shims are the responsibility of the skill/tooling, not the package author

## Consequences

- Package authors write AGENTS.md (or content that populates it) — never tool-specific files directly
- The coding-aegis skill must detect which tool it's running in and create the appropriate shim
- `CLAUDE.md` should be in `.gitignore` for target repos (it's a generated artifact)
- This repo itself does not contain a `CLAUDE.md` — Claude Code users working on this repo rely on AGENTS.md being imported by their session context

## Related Decisions

- [AD-2: Claude Code conventions as canonical format](AD-2-canonical-format.md) — canonical for package content, not for the guidance file
- [AD-6: Equivalent behavior across tools](AD-6-equivalent-behavior.md) — all tools get the same content
