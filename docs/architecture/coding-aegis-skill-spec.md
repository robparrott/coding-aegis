# coding-aegis Skill Behavior Specification

**Status**: Draft — defines the contract for the coding-aegis skill implementation.

## Overview

The coding-aegis skill is the primary interface for browsing, installing, and managing governance packages from the coding-aegis catalog. It runs as a Claude Code skill invoked via `/coding-aegis`.

## Commands

### `list` (also default when no args)

**Input**: `/coding-aegis` or `/coding-aegis list`
**Output**: Table of packages grouped by tier.

#### Behavior

1. Resolve catalog root: locate the `pkgs/` directory (4 dirs up from skill base directory).
2. Scan tier directories in fixed order: `required`, `best-practices`, `optional`, `goodies`.
3. Skip `bootstrap/` — it is internal infrastructure.
4. For each tier, Glob for `pkgs/{tier}/*/pkg.yaml`.
5. Read each `pkg.yaml`. Extract `name`, `version`, `description`; count `artifacts` by type.
6. Display a table per tier. Empty tiers show "(none)".

#### Output format

```
## coding-aegis catalog

### required
(none)

### optional
| Package | Version | Artifacts | Description |
|---------|---------|-----------|-------------|
| fancy-beads | 0.1.0 | 1 skill | Issue tracking with beads... |
```

#### Artifact summary

Count by type, comma-separated: "2 rules, 1 skill".

---

### `show <package>`

**Input**: `/coding-aegis show pirate-speak`
**Output**: Full package details including README.

#### Behavior

1. Glob for `pkgs/*/{name}/pkg.yaml` across all tier dirs.
2. If not found → error: "Package '{name}' not found in the catalog."
3. Read `pkg.yaml`. Determine tier from path segment.
4. Check for `README.md` in package directory.
5. Display: metadata table, artifacts table, README content.

#### Output format

```
## pirate-speak

| Field | Value |
|-------|-------|
| Name | pirate-speak |
| Version | 0.1.0 |
| Tier | goodies |
| Author | platform-team |

### Artifacts
| # | Type | Path |
|---|------|------|
| 1 | rule | rules/pirate-speak.md |

### README
[README.md contents or "(No README)"]
```

---

### `install <package>`

**Input**: `/coding-aegis install pirate-speak`
**Output**: Installed files summary.

#### Behavior

1. **Resolve**: Find package in catalog, read `pkg.yaml`, determine tier.
2. **Scope picker**: Ask user — Project (`.claude/`), User (`~/.claude/`), Local (`.claude.local/`).
3. **Install rules**: For each `type: rule` artifact:
   - Read source file.
   - Construct managed-by frontmatter: `package`, `rule`, `version`, `tier`, `managed-by: coding-aegis`.
   - Merge with any existing source frontmatter (managed-by keys take precedence).
   - Write to `{scope}/rules/aegis--{package}--{rule-basename}.md`.
4. **Install skills**: For each `type: skill` artifact:
   - Determine skill name from path.
   - Copy SKILL.md and all sibling files to `{scope}/skills/{skill-name}/`.
   - No frontmatter injection — skills are copied as-is.
5. **Install agents**: For each `type: agent` artifact:
   - Add managed-by frontmatter.
   - Write to `{scope}/agents/aegis--{package}--{agent-basename}.md`.
6. **Install MCP**: For each `type: mcp` artifact:
   - Merge server definitions into target `.mcp.json` or `~/.claude.json`.
7. **Update AGENTS.md** (Project scope only):
   - Find or create `## Installed Governance Rules` section.
   - Build table by scanning all `aegis--*` files in `.claude/rules/`.
   - Replace section content. Do not touch other sections.
   - Skip if AGENTS.md does not exist.
8. **Confirm**: Print summary table of installed files.

#### Frontmatter schema

```yaml
---
package: <string>
rule: <string>
version: <string>
tier: required | best-practices | optional | goodies
managed-by: coding-aegis
---
```

#### Filename formula

```
aegis--{package-name}--{rule-basename}.md
```

---

### `status`

**Input**: `/coding-aegis status`
**Output**: Installed packages with version comparison.

#### Behavior

1. Scan three scopes: Project (`.claude/`), Local (`.claude.local/`), User (`~/.claude/`).
2. For each scope:
   - Glob for `{scope}/rules/aegis--*`.
   - Glob for `{scope}/skills/*/SKILL.md`.
   - Glob for `{scope}/agents/aegis--*`.
3. For `aegis--*` files: parse YAML frontmatter for `package`, `version`, `tier`, `managed-by`.
4. For skills: cross-reference skill name with catalog packages.
5. Group by scope, then by package.
6. Compare installed version with catalog version. Mark as `current`, `outdated`, or `unknown`.

#### Output format

```
## coding-aegis status

### Project (.claude/)
| Package | Version | Tier | Artifacts | Status |
|---------|---------|------|-----------|--------|
| pirate-speak | 0.1.0 | goodies | 2 rules, 1 skill | current |

### Local (.claude.local/)
(none)

### User (~/.claude/)
(none)
```

If no governance-managed files found: "No coding-aegis packages installed."

---

## Ownership Boundaries

| Pattern | Owner | Editable? |
|---------|-------|-----------|
| `aegis--*` in rules/agents dirs | coding-aegis | No — overwritten on update |
| Everything else in rules/agents | Project team | Yes — never touched |
| AGENTS.md `## Installed Governance Rules` | coding-aegis | Generated section only |
| AGENTS.md all other sections | Project team | Yes |

## Error Cases

| Condition | Message |
|-----------|---------|
| Catalog not found | "Could not locate the coding-aegis package catalog." |
| Package not found | "Package '{name}' not found in the catalog." |
| Empty artifacts | "Warning: Package '{name}' has no artifacts to install." |
| Write failure | "Error: Could not write to {path}. Check permissions." |

## Design References

- [AD-5: Installation targets](AD-5-installation-targets.md)
- [AD-8: Claude Code first](AD-8-claude-code-first.md)
- [AD-10: Modular guidance files](AD-10-modular-guidance-files.md)
- [AD-14: Cross-tool artifact model](AD-14-cross-tool-artifact-model.md)
- [AD-15: Single-source adaptation](AD-15-single-source-install-adaptation.md)
