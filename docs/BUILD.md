# Build Guide

## Tech Stack

TBD — no tooling implemented yet. The following are planned capabilities:

- **CLI/Tooling**: Language and framework TBD
- **Templates**: Template engine for tool adaptation rendering
- **Content parsing**: YAML parsing
- **CI**: GitHub Actions (GitLab CI abstractable later)
- **Git operations**: Abstracted to support `gh` and `glab`
- **Package format**: Markdown + YAML (`pkg.yaml` manifest)

## Setup

TBD — no tooling implemented yet.

## CLI Commands

TBD — no tooling implemented yet. Planned commands:

- **validate** — Validate catalog structure (all pkg.yaml valid, artifact paths resolve)
- **list** — List packages by tier
- **render** — Render a package for a specific tool
- **promote** — Move a package between tiers (creates PR)

## Package Authoring

See [Package Format Specification](architecture/package-format.md) for the full `pkg.yaml` schema and artifact types.

1. Create a directory under the appropriate tier in `pkgs/`
2. Add a `pkg.yaml` manifest
3. Add artifacts (skills, agents, rules, MCP configs)
4. Validate structure (tooling TBD)
5. Submit a PR
