# coding-aegis

Coding agent governance repository — the central catalog and distribution point for coding agent packages across the engineering organization.

## Problem

Engineering organizations adopting AI coding agents (Claude Code, Cursor, Windsurf, GitHub Copilot) need a centralized way to distribute and enforce coding standards, skills, MCP configurations, and governance policies across repositories. Without this, each repo independently configures its tools, leading to inconsistency, duplicated effort, and no mechanism for org-wide governance.

## Solution

This repository is the catalog and distribution point for coding agent packages — authored by different teams, curated via PR, organized by governance tier. Packages are authored in Claude Code conventions as the [canonical format](docs/architecture/AD-2-canonical-format.md) and adapted to other tools via renderers. Packages can also reference external GitHub repos via [registry pointers](docs/architecture/AD-12-external-package-references.md), keeping content in the source team's repo while the catalog provides curation and tier gating.

## Architecture

Packages are the unit of distribution, organized by [tier](docs/architecture/tier-system.md) in the `pkgs/` directory following a yum/rpm repository model. Tier = directory location; promotion is a directory move via PR.

| Tier | Enforcement | Behavior |
|------|-------------|----------|
| `required` | Strict — CI validates | Auto-installed, cannot opt out |
| `best-practices` | Recommended | Installed by default, opt-out with justification |
| `optional` | Opt-in | Listed in catalog, not installed by default |
| `goodies` | None | Available for browsing |

The [coding-aegis skill](docs/architecture/coding-aegis.md) is the primary interface — it browses the catalog, installs packages, checks status, and manages governance. It uses a [two-layer architecture](docs/architecture/AD-3-two-layer-skill.md): a minimal bootstrap mechanism per tool, and a rich skill that provides the full experience.

All tools receive equivalent governance via [AGENTS.md as the single source of truth](docs/architecture/AD-9-agents-md-source-of-truth.md), with [modular rule files](docs/architecture/AD-10-modular-guidance-files.md) installed per-package into each tool's native rules directory.

## Assumptions

- **Hosting**: Private GitHub repository accessible to all engineering team members
- **Claude Code**: Team has access to Claude Code with plugin support
- **Cursor**: Organization has a Cursor Teams plan (enables Team Marketplace)
- **Windsurf / Copilot**: TBD — bootstrap mechanisms to be designed later
- **GitHub Enterprise App**: Required for Cursor private repo access

## Documentation

### Specifications
- [Package format](docs/architecture/package-format.md) — pkg.yaml schema, artifact types, package layout
- [Tier system](docs/architecture/tier-system.md) — Governance tiers and promotion model
- [Repository structure](docs/architecture/repository-structure.md) — Full directory layout
- [coding-aegis skill](docs/architecture/coding-aegis.md) — Skill capabilities and interaction model

### Architecture Decisions
- [AD-1: Package-based catalog](docs/architecture/AD-1-package-catalog.md)
- [AD-2: Claude Code as canonical format](docs/architecture/AD-2-canonical-format.md)
- [AD-3: Two-layer skill architecture](docs/architecture/AD-3-two-layer-skill.md)
- [AD-4: Dual marketplace registration](docs/architecture/AD-4-dual-marketplace.md)
- [AD-5: Two installation targets](docs/architecture/AD-5-installation-targets.md)
- [AD-6: Equivalent behavior across tools](docs/architecture/AD-6-equivalent-behavior.md)
- [AD-7: No dependency resolution](docs/architecture/AD-7-no-dependency-resolution.md)
- [AD-8: Claude Code first](docs/architecture/AD-8-claude-code-first.md)
- [AD-9: AGENTS.md as source of truth](docs/architecture/AD-9-agents-md-source-of-truth.md)
- [AD-10: Modular guidance files](docs/architecture/AD-10-modular-guidance-files.md)
- [AD-11: Multi-tool repository support](docs/architecture/AD-11-multi-tool-repos.md) *(open question)*
- [AD-12: External package references](docs/architecture/AD-12-external-package-references.md)

### Guides
- [Build guide](docs/build/BUILD.md) — How to build, install, and use the CLI
- [Test guide](docs/test/TEST.md) — How to run tests and verify the system
- [AGENTS.md](AGENTS.md) — Coding agent guidance for contributors
- [Backlog](docs/backlog/) — Implementation phases and task tracking

## Key Directories

- `pkgs/` — The package catalog, organized by tier
- `quickstarts/` — Project scaffolding packages
- `docs/architecture/` — ADRs and specifications
- `docs/backlog/` — Phase planning and task tracking
