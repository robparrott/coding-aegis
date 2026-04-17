# AD-14: Cross-tool artifact model

**Status**: Accepted

## Decision

Establish a canonical mapping of coding-aegis concepts to the native artifact locations and capabilities of each supported tool. All design docs, installation logic, and renderer implementations must use this mapping as the single source of truth.

## Cross-tool artifact matrix

| Concept | Claude Code | Codex | OpenCode | Cursor | Windsurf | Copilot |
|---------|-------------|-------|----------|--------|----------|---------|
| **Always-on guidance** | `CLAUDE.md`, `AGENTS.md` | `AGENTS.md` | `AGENTS.md` | `AGENTS.md`, `.cursor/rules/*.mdc` (`alwaysApply: true`) | `AGENTS.md`, `.windsurf/rules/*.md` | `.github/copilot-instructions.md` |
| **File-scoped rules** | `.claude/rules/*.md` (`globs:`) | _(none — use AGENTS.md)_ | _(none — use AGENTS.md)_ | `.cursor/rules/*.mdc` (`globs:`) | `.windsurf/rules/*.md` (`globs:`) | `.github/instructions/*.instructions.md` (`applyTo:`) |
| **coding-aegis rule delivery** | `.claude/rules/aegis--{pkg}--{rule}.md` | `AGENTS.md` `aegis:begin/end` section | `AGENTS.md` `aegis:begin/end` section | `.cursor/rules/aegis--{pkg}--{rule}.mdc` | `.windsurf/rules/aegis--{pkg}--{rule}.md` | _(TBD)_ |
| **Invocable skills** | `.claude/skills/{name}/SKILL.md` | `.agents/skills/{name}/SKILL.md` | `.opencode/skills/{name}/SKILL.md` | `.cursor/skills/{name}/SKILL.md` | `.agents/skills/{name}/SKILL.md` | Not supported |
| **Custom agents** | `.claude/agents/{name}/AGENT.md` | N/A | N/A | Background agents (built-in) | Cascade (built-in) | Agent mode (built-in) |
| **MCP config** | `.mcp.json` (project), `~/.claude.json` (user) | N/A | N/A | `.mcp.json` (project), `~/.cursor/mcp.json` (user) | `.mcp.json` (project), `~/.codeium/windsurf/mcp_config.json` (user) | Not supported |
| **Plugin system** | `.claude-plugin/` marketplace | `.codex-plugin/` manifest | _(none)_ | `.cursor-plugin/` marketplace | Not supported | GitHub Marketplace |

## Frontmatter format comparison

| Feature | Claude Code | Codex / OpenCode | Cursor | Windsurf | Copilot |
|---------|-------------|------------------|--------|----------|---------|
| **Format** | YAML frontmatter in `.md` | AGENTS.md sections (no frontmatter) | YAML frontmatter in `.mdc` | YAML frontmatter in `.md` | YAML frontmatter in `.md` |
| **Always-on** | Implicit (all `CLAUDE.md` files) | Implicit (`AGENTS.md` always read) | `alwaysApply: true` | Implicit (all rule files) | Implicit (instructions file) |
| **File scoping** | `globs: "*.ts"` | N/A — no file-scoped rules | `globs: "*.ts"` | `globs: "*.ts"` | `applyTo: "*.ts"` |
| **Description** | `description:` | N/A | `description:` | `description:` | N/A |

## Scope levels per tool

| Scope | Claude Code | Codex | OpenCode | Cursor | Windsurf | Copilot |
|-------|-------------|-------|----------|--------|----------|---------|
| **Project** | `{repo}/.claude/` | `{repo}/.agents/` | `{repo}/.opencode/` | `{repo}/.cursor/` | `{repo}/.windsurf/` | `{repo}/.github/` |
| **User** | `~/.claude/` | N/A | `~/.config/opencode/` | `~/.cursor/` | `~/.codeium/windsurf/` | VS Code settings |
| **Team** | N/A | N/A | N/A | Cursor Team Marketplace | N/A | GitHub org-level |

> **Note**: Claude Code supports a local settings override via `.claude/settings.local.json`, but does not discover skills, rules, or agents from a `.claude.local/` directory. The two supported installation scopes for artifacts are Project and User.

## Agent Skills standard

The [Agent Skills](https://agentskills.io) open standard defines a portable `SKILL.md` format. Adoption status:

- **Claude Code**: Native support via `.claude/skills/{name}/SKILL.md`
- **Codex**: Supports `.agents/skills/{name}/SKILL.md`
- **OpenCode**: Supports `.opencode/skills/{name}/SKILL.md`
- **Cursor**: Native support via `.cursor/skills/{name}/SKILL.md` and `.agents/skills/{name}/SKILL.md`
- **Windsurf**: Supports `.agents/skills/{name}/SKILL.md`
- **Copilot**: Not supported

## Known bugs and limitations

- **Claude Code `paths:` bug**: The `paths:` frontmatter key is documented but not yet functional. Use `globs:` as a workaround.
- **Cursor Remote Rules**: Remote rules via URL have known reliability issues with auto-refresh. Symlink-based local installation is more reliable (see AD-13).
- **Windsurf rules scoping**: Windsurf does not support `alwaysApply`; all rule files in `.windsurf/rules/` are always active.
- **Copilot instructions**: Limited to a single `.github/copilot-instructions.md` for global guidance; file-scoped instructions via `.github/instructions/` are newer and less widely adopted.

## Rationale

Previous design docs (SKILL.md artifacts table, AD-4, AD-5) incorrectly showed `—` for Cursor skills, but Cursor natively supports the SKILL.md format. This ADR corrects the model and serves as the canonical reference for all downstream docs and implementation.

## References

- [AD-4: Dual marketplace registration](AD-4-dual-marketplace.md)
- [AD-5: Installation targets](AD-5-installation-targets.md)
- [AD-9: AGENTS.md as source of truth](AD-9-agents-md-source-of-truth.md)
- [AD-10: Modular guidance files](AD-10-modular-guidance-files.md)
- [AD-13: Cursor remote distribution](AD-13-cursor-remote-distribution.md)
