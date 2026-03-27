# AGENTS.md

This file provides guidance to coding agents when working with code in this repository. Refer to README.md for the business purpose and project overview.

You are parsimonious and only implement when required. You avoid AI slop. You create specs and tests before implementing, and do not complete tasks until tests pass and code is committed and pushed.

DO NOT START implementation until tasks are reviewed and approved by the user. 

## Planning

Use beads (`bd`) to do planning, task tracking and dependency management. Run `bd onboard` for more information. Every task should have a spec file created to define the contract or behavior for the work. After completing each task and before committing, run `scripts/sync-backlog.sh` to export the current beads state to `docs/backlog/`.

When a design decision is made, create an architecture decision record to document the decision and why it was made.

## Repository Layout Standard

This layout is a common standard for all repositories in our organization.

- **README.md** — Human-readable project description with links to documentation and key directories.
- **AGENTS.md** — Coding agent guidance (this file). Cross-tool: applies to Claude Code, Cursor, Windsurf, Copilot.
- **docs/** — Markdown-based documentation.
- **docs/backlog/** — Auto-generated snapshot of the beads database. Do not edit manually. Run `scripts/sync-backlog.sh` before committing to keep in sync.
- **docs/architecture/** — Architecture decision records (ADRs) and specification files.
- **docs/build/BUILD.md** — How to build this project.
- **docs/test/TEST.md** — How to run various tests.
- **pkgs/** — The package catalog, organized by tier (`required`, `best-practices`, `optional`, `goodies`, `bootstrap`).
- **.claude-plugin/** — Claude Code plugin marketplace manifest. Required at repo root by Claude Code's plugin discovery. See [AD-4](docs/architecture/AD-4-dual-marketplace.md).
- **.cursor-plugin/** — Cursor Team Marketplace manifest. Required at repo root by Cursor's plugin discovery. See [AD-4](docs/architecture/AD-4-dual-marketplace.md).

## This Repo vs. Target Repos

This repository is a **package catalog and authoring environment**. AGENTS.md governs coding agents working on this codebase. No tool-specific config files (`.cursor/rules/`, `.windsurf/rules/`, `.github/copilot-instructions.md`) exist here — they are not needed for authoring.

When packages from this catalog are installed into a **target repository**, the coding-aegis skill generates tool-specific configs there at runtime. See [AD-9](docs/architecture/AD-9-agents-md-source-of-truth.md) for the rendering strategy and [AD-10](docs/architecture/AD-10-modular-guidance-files.md) for how installed rules are composed.

## Package Authoring Rules

When authoring or modifying packages under `pkgs/`, follow the [Package Format Specification](docs/architecture/package-format.md).
