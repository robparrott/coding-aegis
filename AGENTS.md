# AGENTS.md

This file provides guidance to coding agents when working with code in this repository. Refer to README.md for the business purpose and project overview.

You are parsimonious and only implement when required. You avoid AI slop. You create specs and tests before implementing, and do not complete tasks until tests pass and code is committed and pushed.

DO NOT START implementation until tasks are reviewed and approved by the user. 

## Planning

Use beads (`bd`) to do planning, task tracking and dependency management. Run `bd onboard` for more information. Every task should have a spec file created to define the contract or behavior for the work. When wrapping up a task, use `bd` to export the planning 

When a design decision is made, create an architecture decision record to document the decision and why it was made.

## Repository Layout Standard

This layout is a common standard for all repositories in our organization.

- **README.md** — Human-readable project description with links to documentation and key directories.
- **AGENTS.md** — Coding agent guidance (this file). Cross-tool: applies to Claude Code, Cursor, Windsurf, Copilot.
- **docs/** — Markdown-based documentation.
- **docs/backlog/** — Storage for task management. When not using `bd` this will be one file per task, written as markdown. Each task file has a description, status, and dependency list. Update once a task is complete. When using `bd` this will contain periodic extracts from the beads database for human consumption.
- **docs/architecture/** — Architecture decision records (ADRs) and specification files.
- **docs/build/BUILD.md** — How to build this project.
- **docs/test/TEST.md** — How to run various tests.
- **pkgs/** — The package catalog, organized by tier (`required`, `best-practices`, `optional`, `goodies`, `bootstrap`).

## Tool-Specific Configs

Each coding agent tool has its own configuration file for tool-specific behavior. AGENTS.md covers cross-cutting guidance; these files handle tool-native concerns:

- **Claude Code**: `CLAUDE.md` shim (`@AGENTS.md` import) — created at runtime by the coding-aegis skill, not checked in
- **Cursor**: `.cursor/rules/governance.mdc`
- **Windsurf**: `.windsurf/rules/governance.md`
- **Copilot**: `.github/copilot-instructions.md`

AGENTS.md is the single source of truth. Tool-specific files either import it (Claude Code) or contain rendered content from it (Cursor, Windsurf, Copilot). When modifying coding agent guidance, update AGENTS.md — tool-specific files are derived.

## Package Authoring Rules

When authoring or modifying packages under `pkgs/`, follow the [Package Format Specification](docs/architecture/package-format.md).
