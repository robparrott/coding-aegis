# AD-10: Modular guidance file composition

**Status**: Accepted

## Context

Governance packages install rules, standards, and guidance into target repositories. A single monolithic AGENTS.md doesn't scale — it mixes org governance with project standards, makes ownership unclear, and creates update conflicts.

All four coding agent tools support a rules directory pattern with multiple files:

| Tool | Rules location | Scoping mechanism |
|------|---------------|------------------|
| Claude Code | `.claude/rules/*.md` | `paths:` YAML frontmatter |
| Cursor | `.cursor/rules/*.mdc` | YAML frontmatter (`alwaysApply`, `globs`) |
| Windsurf | `.windsurf/rules/*.md` | `trigger:` frontmatter |
| Copilot | `.github/instructions/*.instructions.md` | Glob-pattern frontmatter |

## Decision

### Install to tool-specific locations

Governance packages install one rule file per package into each detected tool's native rules directory. No tool-agnostic intermediary directory — files go directly where the tool expects them.

Example: the `git-workflow` rule from the `governance-core` package installs as:
- `.claude/rules/aegis--governance-core--git-workflow.md`
- `.cursor/rules/aegis--governance-core--git-workflow.mdc`
- `.windsurf/rules/aegis--governance-core--git-workflow.md`
- `.github/instructions/aegis--governance-core--git-workflow.instructions.md`

### Update AGENTS.md as documentation

AGENTS.md is updated to list installed governance rules and their locations. This avoids being "implicitly clever" — developers can see exactly what's installed and where by reading AGENTS.md.

```markdown
## Installed Governance Rules

| Rule | Package | Tier | Locations |
|------|---------|------|-----------|
| git-workflow | governance-core | required | `.claude/rules/`, `.cursor/rules/` |
| error-handling | governance-core | required | `.claude/rules/`, `.cursor/rules/` |
| code-review | code-review | best-practices | `.claude/rules/`, `.cursor/rules/` |
```

### Mark ownership explicitly

Each governance-managed rule file includes a metadata table at the top, similar to SKILL.md YAML frontmatter. This is visible, not hidden — developers immediately know what they're looking at:

```markdown
---
package: governance-core
rule: git-workflow
version: 1.0.0
tier: required
managed-by: coding-aegis
---

# Git Workflow Standards

...
```

The frontmatter contains: package name, rule name, version, tier, and the managing tool. This is human-readable and machine-parseable for updates.

### Atomic updates per file

Updates target individual files, not AGENTS.md or bulk rewrites. When the governance repo updates the `git-workflow` rule:
1. Only `aegis--governance-core--git-workflow.*` files are replaced
2. Project-owned files in the same directories are untouched
3. AGENTS.md installed rules table is refreshed

### Ownership boundaries

| File pattern | Owner | Can edit? |
|-------------|-------|-----------|
| `aegis--*` in rules dirs | Governance (coding-aegis) | No — overwritten on update |
| Everything else in rules dirs | Project team | Yes — never touched by governance |
| AGENTS.md (installed rules section) | Governance (coding-aegis) | Generated section only |
| AGENTS.md (all other sections) | Project team | Yes |

The `aegis--` filename prefix is the ownership boundary. The skill only writes files with this prefix and only modifies the designated section of AGENTS.md.

## Consequences

- Clear separation: governance files are identifiable by prefix and frontmatter
- No magic: AGENTS.md documents what's installed and where
- Safe updates: atomic per-file replacement, project content untouched
- Multi-tool support: same content rendered to each tool's native location

## Open Question

How to handle repos used with multiple coding agent tools simultaneously. See [AD-11](AD-11-multi-tool-repos.md).

## Related Decisions

- [AD-1: Package-based catalog](AD-1-package-catalog.md) — packages are the unit of distribution
- [AD-2: Canonical format](AD-2-canonical-format.md) — authored once, rendered per tool
- [AD-9: AGENTS.md as source of truth](AD-9-agents-md-source-of-truth.md) — AGENTS.md is the root entry point
