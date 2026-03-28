---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages from the coding-aegis catalog.
---

# coding-aegis

Browse, install, and manage governance packages for coding agents.

## Usage

```
/coding-aegis list                  # List available packages by tier
/coding-aegis show <package>        # Show package details
/coding-aegis install <package>     # Install a package into the current project
/coding-aegis status                # Show installed packages and versions
```

## Catalog

Packages are organized by tier:

| Tier | Purpose | Listed in priority order |
|------|---------|--------------------------|
| **required** | Non-negotiable governance — auto-installed | 1st |
| **best-practices** | Recommended defaults — opt-out with justification | 2nd |
| **optional** | Available on demand — opt-in | 3rd |
| **goodies** | Community and experimental | 4th |

The catalog lives at `pkgs/` in the [coding-aegis](https://github.com/coding-aegis/coding-aegis) repository. Each package contains a `pkg.yaml` manifest describing its artifacts (skills, agents, rules, MCP configs).

## Installation

Packages install artifacts to tool-native locations:

| Artifact | Claude Code | Cursor | Windsurf | Copilot |
|----------|-------------|--------|----------|---------|
| skill | `.claude/skills/{name}/` | — | — | — |
| agent | `.claude/agents/` | — | — | — |
| rule | `.claude/rules/` | `.cursor/rules/` | `.windsurf/rules/` | `.github/instructions/` |
| mcp | `.mcp.json` | `.mcp.json` | `.mcp.json` | — |

Rules installed by coding-aegis are prefixed `aegis--` to distinguish governance-managed files from project-owned files.

## Scope

Packages can be installed to:
- **Project** — governs a single repository
- **User** — applies across all repositories for the current user
- **Local** — applies to you in this repository only

The install command presents a scope picker.
