# Test Guide

## Running Tests

TBD — no test tooling implemented yet.

## Verification Plan

1. **Claude Code bootstrap**: `/plugin marketplace add` + `/plugin install` installs the skill successfully
2. **Cursor bootstrap**: Admin imports repo into Team Marketplace; user one-click installs; `.mdc` rule loads in Cursor
3. **Catalog validation**: All `pkg.yaml` valid, artifact paths resolve
4. **Renderer test**: Render a package for Cursor — produces valid `.mdc` output
5. **Self-check**: This repo's own configs are consistent with governance patterns
6. **Quickstart test**: Each quickstart produces a buildable/lintable scaffold
7. **External package test**: External package pointer installs correctly, fetches content from GitHub repo at pinned ref
