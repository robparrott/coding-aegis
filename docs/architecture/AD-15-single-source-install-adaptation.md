# AD-15: Single-source artifacts with install-time adaptation

**Status**: Accepted

## Context

Packages contain rules, skills, and MCP configs as canonical source files. Different coding agent tools require minor variations in these files:

- File extension (`.md` vs `.mdc` vs `.instructions.md`)
- Frontmatter keys (`alwaysApply: true` for Cursor, `applyTo:` for Copilot)
- Installation paths (`.claude/rules/` vs `.cursor/rules/` vs `.windsurf/rules/`)

An earlier approach placed tool-specific copies in a `tools/` override directory within each package. This creates duplication and content drift — exactly the problem coding-aegis exists to prevent.

## Decision

Wherever possible, we strongly prefer a single canonical copy of each artifact, with the coding-aegis skill adapting to the target tool at install time. Package authors should not need to maintain tool-specific variants for routine format differences.

When adaptation is not feasible or possible — for example, when a tool requires fundamentally different content or structure that cannot be mechanically derived — tool-specific overrides in the `tools/` directory are acceptable.

### Install-time adaptations performed by the skill

| Adaptation | Example |
|-----------|---------|
| **File rename** | `my-rule.md` → `aegis--my-rule.mdc` (Cursor), `aegis--my-rule.instructions.md` (Copilot) |
| **Frontmatter injection** | Add `alwaysApply: true` for Cursor always-on rules |
| **Frontmatter translation** | `globs:` → `applyTo:` for Copilot |
| **Path routing** | Same file installed to `.claude/rules/`, `.cursor/rules/`, `.windsurf/rules/`, or `.github/instructions/` depending on target tool |

## Package Author Guidance

- Write each rule once, in canonical `.md` format
- Use `globs:` for file-scoped rules (the skill translates to tool-native equivalents)
- Avoid adding tool-specific frontmatter (`alwaysApply`, `applyTo`, etc.) — the skill handles this
- Use the `tools/` override directory only when the canonical artifact genuinely cannot serve a particular tool

## Skill Responsibilities

- Detect which tool is running (Claude Code, Cursor, Windsurf, Copilot)
- Apply file extension, frontmatter, and path adaptations at install time
- Check for `tools/{tool}/` overrides and prefer them when present
- On uninstall, remove exactly the files it created

## Rationale

- Reduces content duplication and drift across tool variants
- Lowers package authoring burden — authors write once, install everywhere
- Centralizes routine adaptation logic in the skill where it can be tested and updated
- Aligns with AD-9 ("tool-specific shims are the responsibility of the skill/tooling, not the package author") and AD-6 (equivalent behavior across tools)
- Preserves an escape hatch for genuine tool-specific needs

## Consequences

- The `tools/` override directory in the package format spec should be documented as an escape hatch, not standard practice
- Existing packages with `tools/` overrides for routine format differences should be cleaned up
- The skill's install command needs adaptation logic before cross-tool install works end-to-end

## References

- [AD-6: Equivalent behavior across tools](AD-6-equivalent-behavior.md)
- [AD-9: AGENTS.md as single source of truth](AD-9-agents-md-source-of-truth.md)
- [AD-14: Cross-tool artifact model](AD-14-cross-tool-artifact-model.md)
