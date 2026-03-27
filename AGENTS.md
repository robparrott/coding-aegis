# AGENTS.md

This file provides guidance to coding agents when working with code in this repository. Refer to README.md for the business purpose and project overview.

You are parsimonious and only implement when required. You avoid AI slop. You create tests before implementing, and do not commit and or complete tasks until tests pass and code is committed.

DO NOT START implementation until tasks are reviewed and approved by the user. 

## Planning

Use beads (`bd`) to do planning, task tracking and dependency management. Run `bd onboard` for more information. Every task should have a spec file created to define the contract or behavior for the work. When wrapping up a task, use `bd` to export the planning 

## Repository Layout Standard

This layout is a common standard for all repositories in our organization.

- **README.md** — Human-readable project description with links to documentation and key directories.
- **AGENTS.md** — Coding agent guidance (this file). Cross-tool: applies to Claude Code, Cursor, Windsurf, Copilot.
- **docs/** — Markdown-based documentation.
- **docs/backlog/** — Storage for task management. When not using `bd` this will be one file per task, written as markdown. Each task file has a description, status, and dependency list. Update once a task is complete. When using `bd` this will contain periodic extracts from the beads database for human consumption.
- **docs/architecture/** — Architecture decision records (ADRs) and specification files.
- **docs/BUILD.md** — How to build this project.
- **docs/TEST.md** — How to run various tests.

## Tool-Specific Configs

Each coding agent tool has its own configuration file for tool-specific behavior. AGENTS.md covers cross-cutting guidance; these files handle tool-native concerns:

- **Claude Code**: `CLAUDE.md` shim (`@AGENTS.md` import) — created at runtime by the coding-aegis skill, not checked in
- **Cursor**: `.cursor/rules/governance.mdc`
- **Windsurf**: `.windsurf/rules/governance.md`
- **Copilot**: `.github/copilot-instructions.md`

AGENTS.md is the single source of truth. Tool-specific files either import it (Claude Code) or contain rendered content from it (Cursor, Windsurf, Copilot). When modifying coding agent guidance, update AGENTS.md — tool-specific files are derived.

## Package Authoring Rules

- `pkg.yaml` must have: `name` (lowercase/hyphens, unique across catalog), `version` (semver), `description`, `author`, `artifacts` list
- Artifact types: `skill`, `agent`, `rule`, `mcp`, `plugin`
- Skills follow the [Agent Skills Specification](https://agentskills.io/specification): SKILL.md with YAML frontmatter (`name` 1-64 chars lowercase/hyphens, `description` 1-1024 chars)
- Tier is determined by directory location under `pkgs/` — never specified in `pkg.yaml`
- Claude Code layout is the canonical format. Use `tools/{cursor,windsurf,copilot}/` override directories only when automatic adaptation fails.
- `source` is an optional field for external package references — points to a GitHub repo (`type`, `repo`, `ref`, optional `path`). External packages must not have local artifact directories (`skills/`, `agents/`, `rules/`, `mcp/`). `source.ref` should be an immutable tag or SHA.

## Key References

- `docs/backlog/` — task tracking and planning
- `docs/architecture/` — ADRs and architecture decisions (AD-1 through AD-12)
- `docs/BUILD.md` — Build, install, and CLI commands
- `docs/TEST.md` — Test execution guidance
- `pkgs/` — The package catalog, organized by tier

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
