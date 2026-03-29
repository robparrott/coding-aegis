# Cross-tool Install Adaptation Rules

> **Status**: Reference only. The coding-aegis skill currently supports Claude Code only (AD-8).
> This file documents the adaptation rules for when cross-tool install is implemented.

## Tool Detection

When running inside a coding agent, detect the active tool:

| Tool | Detection signal |
|------|-----------------|
| Claude Code | Default — if no other tool detected |
| Cursor | `.cursor/` directory exists at repo root, or `.cursorrc` present |
| Windsurf | `.windsurf/` directory exists at repo root |
| Copilot | `.github/copilot-instructions.md` exists |

For multi-tool repos (AD-11), install to all detected tools.

## File Extension Mapping

Source rules are authored as `.md`. Adapt extension per target tool:

| Source | Claude Code | Cursor | Windsurf | Copilot |
|--------|-------------|--------|----------|---------|
| `{rule}.md` | `aegis--{pkg}--{rule}.md` | `aegis--{pkg}--{rule}.mdc` | `aegis--{pkg}--{rule}.md` | `aegis--{pkg}--{rule}.instructions.md` |

## Path Routing

### Rules

| Tool | Target directory |
|------|-----------------|
| Claude Code | `.claude/rules/` |
| Cursor | `.cursor/rules/` |
| Windsurf | `.windsurf/rules/` |
| Copilot | `.github/instructions/` |

### Skills

| Tool | Target directory |
|------|-----------------|
| Claude Code | `.claude/skills/{name}/` |
| Cursor | `.cursor/skills/{name}/` |
| Windsurf | `.agents/skills/{name}/` |
| Copilot | Not supported |

### Agents

| Tool | Target directory |
|------|-----------------|
| Claude Code | `.claude/agents/` |
| Cursor | Not supported (background agents are built-in) |
| Windsurf | Not supported (Cascade is built-in) |
| Copilot | Not supported |

### MCP configs

| Tool | Project location | User location |
|------|-----------------|---------------|
| Claude Code | `.mcp.json` | `~/.claude.json` |
| Cursor | `.mcp.json` | `~/.cursor/mcp.json` |
| Windsurf | `.mcp.json` | `~/.codeium/windsurf/mcp_config.json` |
| Copilot | Not supported | Not supported |

## Frontmatter Adaptation

### Always-on rules (no `globs:` in source)

| Tool | Adaptation |
|------|-----------|
| Claude Code | No change — rules in `.claude/rules/` without `globs:` are always-on |
| Cursor | Inject `alwaysApply: true` into frontmatter |
| Windsurf | No change — all rules in `.windsurf/rules/` are always-on |
| Copilot | No change — instructions files are always-on by default |

### File-scoped rules (`globs:` present in source)

| Tool | Adaptation |
|------|-----------|
| Claude Code | Keep `globs:` as-is |
| Cursor | Keep `globs:` as-is (Cursor supports the same syntax) |
| Windsurf | Keep `globs:` as-is |
| Copilot | Translate `globs:` → `applyTo:` |

### Description field

All tools support `description:` in frontmatter. No translation needed.

## Override Directory

Before applying automatic adaptation, check for a `tools/{tool}/` override directory in the package:

```
{package}/
└── tools/
    ├── cursor/
    │   └── rules/
    │       └── my-rule.mdc       ← Use this instead of auto-adapted version
    └── copilot/
        └── rules/
            └── my-rule.instructions.md
```

If an override file exists for the target tool and artifact, use it verbatim instead of adapting the canonical source. This is the escape hatch for cases where automatic adaptation is insufficient (AD-15).

## Scope Mapping

| Scope | Claude Code | Cursor | Windsurf | Copilot |
|-------|-------------|--------|----------|---------|
| Project | `{repo}/.claude/` | `{repo}/.cursor/` | `{repo}/.windsurf/` | `{repo}/.github/` |
| User | `~/.claude/` | `~/.cursor/` | `~/.codeium/windsurf/` | VS Code settings |
| Local | `{repo}/.claude.local/` | N/A | N/A | N/A |

For tools that don't support a scope level, warn the user and skip.

## References

- [AD-6: Equivalent behavior across tools](../../../../../docs/architecture/AD-6-equivalent-behavior.md)
- [AD-14: Cross-tool artifact model](../../../../../docs/architecture/AD-14-cross-tool-artifact-model.md)
- [AD-15: Single-source adaptation](../../../../../docs/architecture/AD-15-single-source-install-adaptation.md)
