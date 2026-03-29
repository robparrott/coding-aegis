---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages from the coding-aegis catalog. Trigger words — list packages, show package, install package, governance status.
---

# coding-aegis

Browse, install, and manage governance packages for coding agents. This skill provides
four commands: `list`, `show`, `install`, and `status`.

## Catalog Resolution

Before executing any command, locate the package catalog:

1. Use Glob to search for `pkgs/required` starting from the current working directory.
2. If found, the catalog root is the `pkgs/` directory containing it.
3. If not found in CWD, check whether this skill file's path contains `pkgs/bootstrap/coding-aegis/`. If so, walk up from the skill file's location to reach `pkgs/`.
4. If the catalog still cannot be found, print the error from the Error Handling section and stop.

Store the resolved `pkgs/` path — all commands below reference it.

### Tier directories

Scan in this fixed order. Never reorder.

| Order | Directory | Purpose |
|-------|-----------|---------|
| 1 | `required/` | Non-negotiable governance |
| 2 | `best-practices/` | Recommended defaults |
| 3 | `optional/` | Available on demand |
| 4 | `goodies/` | Community and experimental |

The `bootstrap/` directory is internal infrastructure. Exclude it from all listings and searches.

## Command Dispatch

Parse the user input after `/coding-aegis`. Route to the matching section below.

| Input | Action |
|-------|--------|
| _(empty)_ | Print help text, then run **list** |
| `list` | Run **list** |
| `show <name>` | Run **show** for `<name>` |
| `install <name>` | Run **install** for `<name>` |
| `status` | Run **status** |
| anything else | Print help text |

### Help text

```
Usage:
  /coding-aegis list              List available packages by tier
  /coding-aegis show <package>    Show package details
  /coding-aegis install <package> Install a package into the current project
  /coding-aegis status            Show installed packages and versions
```

## list

Display all available packages grouped by tier.

### Steps

1. For each tier directory in order (`required`, `best-practices`, `optional`, `goodies`):
   a. Use Glob: `{catalog}/\{tier\}/*/pkg.yaml`
   b. For each match, Read the `pkg.yaml`. Extract `name`, `version`, `description`.
   c. Count artifacts by type from the `artifacts` list. Format as comma-separated
      summary: "2 rules, 1 skill" or "1 skill". Use this type order: rules, skills, agents, mcp.
2. Print one table per tier. If a tier has no packages, print the tier heading with "(none)".

### Output format

```
## coding-aegis catalog

### required
(none)

### best-practices
(none)

### optional
| Package | Version | Artifacts | Description |
|---------|---------|-----------|-------------|
| fancy-beads | 0.1.0 | 1 skill | Issue tracking with beads... |

### goodies
| Package | Version | Artifacts | Description |
|---------|---------|-----------|-------------|
| ascii-hello | 0.1.0 | 1 skill | Generate ASCII art from... |
| pirate-speak | 0.1.0 | 2 rules, 1 skill | Arrr! Pirate-themed... |
```

Sort packages alphabetically within each tier.

## show

Display full details for a single package.

### Steps

1. Search all four tier directories for a subdirectory matching the package name.
   Use Glob: `{catalog}/*/\{name\}/pkg.yaml`
2. If no match, print: "Package '{name}' not found in the catalog." and stop.
3. Read the matched `pkg.yaml`. Determine the tier from the path (the directory between
   `pkgs/` and the package name).
4. Check for `README.md` in the package directory. Read it if present.
5. Print the details.

### Output format

```
## {name}

| Field | Value |
|-------|-------|
| Name | {name} |
| Version | {version} |
| Tier | {tier} |
| Author | {author} |
| Description | {description} |

### Artifacts

| # | Type | Path |
|---|------|------|
| 1 | rule | rules/pirate-speak.md |
| 2 | rule | rules/pirate-readme.md |
| 3 | skill | skills/pirate-speak/SKILL.md |

### README

{README.md contents, or "(No README)"}
```

## install

Install a package's artifacts into the target project or user configuration.

> **Note**: This skill currently supports **Claude Code only** (per AD-8).

### Step 1 — Resolve the package

1. Find the package in the catalog (same lookup as `show`).
2. Read `pkg.yaml`. Extract `name`, `version`, `artifacts`.
3. Determine tier from directory path.
4. Store the full package directory path for reading source files.
5. If the package has no artifacts, warn and stop.

### Step 2 — Scope picker

Present the user with a choice using AskUserQuestion:

```
Where should this package be installed?

1. Project — `.claude/` in the current repo (governs this project, shared via source control)
2. User — `~/.claude/` in your home directory (governs all your projects)
```

Map the response to a base path:

| Scope | Base path |
|-------|-----------|
| Project | `{CWD}/.claude/` |
| User | `~/.claude/` |

### Step 3 — Install rules

For each artifact where `type: rule`:

1. Read the source file from the package directory.
2. Extract the rule basename: filename without extension.
   Example: `rules/pirate-speak.md` → basename `pirate-speak`.
3. Build the managed-by frontmatter block:

   ```yaml
   ---
   package: {package-name}
   rule: {rule-basename}
   version: {package-version}
   tier: {tier}
   managed-by: coding-aegis
   ---
   ```

4. If the source file has existing YAML frontmatter (between `---` delimiters):
   - Parse both the source frontmatter and the managed-by keys.
   - Merge them. Managed-by keys (`package`, `rule`, `version`, `tier`, `managed-by`)
     take precedence. All other source keys (e.g., `description`, `globs`) are preserved.
   - Reconstruct the combined frontmatter block followed by the body content.
5. If the source file has no frontmatter, prepend the managed-by block.
6. Compute the target filename: `aegis--{package-name}--{rule-basename}.md`
7. Ensure the target directory exists: `mkdir -p {base-path}/rules/`
8. Write the file to `{base-path}/rules/{target-filename}`.

### Step 4 — Install skills

For each artifact where `type: skill`:

1. Determine the skill name from the artifact path.
   Example: `skills/pirate-speak/SKILL.md` → skill name `pirate-speak`.
2. Glob for all files in the source skill directory: `{pkg-dir}/skills/{skill-name}/**/*`
3. For each file found:
   a. Read the source file.
   b. Compute the relative path within the skill directory.
   c. Ensure the target directory exists: `mkdir -p {base-path}/skills/{skill-name}/{subdir}`
   d. Write the file to `{base-path}/skills/{skill-name}/{relative-path}`.
4. Skills are copied verbatim — no frontmatter injection. The SKILL.md frontmatter
   already has `name` and `description` per the Agent Skills standard.

### Step 5 — Install agents

For each artifact where `type: agent`:

1. Read the source agent file.
2. Extract the basename without extension.
3. Build managed-by frontmatter (same schema as rules, with `rule:` key omitted).
4. Merge frontmatter as in Step 3.
5. Write to `{base-path}/agents/aegis--{package-name}--{agent-basename}.md`.

### Step 6 — Install MCP configs

For each artifact where `type: mcp`:

1. Read the source `servers.json` from the package.
2. Determine the target config file:
   - Project scope: `{CWD}/.mcp.json`
   - User scope: `~/.claude.json`
3. If the target file exists, read it and parse as JSON.
4. Merge each server entry from the package into the `mcpServers` object.
   Do not overwrite existing entries with the same key.
5. Write the updated JSON file.

### Step 7 — Update AGENTS.md (Project scope only)

Skip this step for User scope. Skip if AGENTS.md does not exist in CWD.

1. Read AGENTS.md.
2. Look for the heading `## Installed Governance Rules`.
3. If found: replace everything from that heading to the next `##` heading (or EOF).
4. If not found: append the section at the end of the file.
5. Build the section content:

   ```markdown
   ## Installed Governance Rules

   <!-- managed by coding-aegis — do not edit manually -->

   | Rule | Package | Version | Tier | File |
   |------|---------|---------|------|------|
   | {rule} | {package} | {version} | {tier} | `{relative-path}` |
   ```

   Populate the table by scanning `{CWD}/.claude/rules/aegis--*`. Read each file's
   frontmatter for package, rule, version, and tier.

### Step 8 — Confirm

Print a summary:

```
## Installed: {name} v{version} ({tier})

| # | Type | Installed to |
|---|------|-------------|
| 1 | rule | .claude/rules/aegis--pirate-speak--pirate-speak.md |
| 2 | rule | .claude/rules/aegis--pirate-speak--pirate-readme.md |
| 3 | skill | .claude/skills/pirate-speak/SKILL.md |
```

If AGENTS.md was updated, add: "AGENTS.md updated with installed governance rules table."

**Important**: After installing skills, remind the user: "Restart Claude Code to load newly installed skills."

## status

Show all coding-aegis-managed packages and their version status.

### Steps

1. Define scopes to scan:

   | Scope | Path |
   |-------|------|
   | Project | `{CWD}/.claude/` |
   | User | `~/.claude/` |

2. For each scope:
   a. Glob: `{path}/rules/aegis--*`
   b. Glob: `{path}/agents/aegis--*`
   c. Glob: `{path}/skills/*/SKILL.md`

3. For each `aegis--*` file found:
   a. Read the file. Parse YAML frontmatter.
   b. Extract `package`, `version`, `tier`, `managed-by`.
   c. Skip files where `managed-by` is not `coding-aegis`.
   d. Record the artifact: package name, version, type (rule or agent), tier.

4. For each skill SKILL.md found:
   a. Read frontmatter. Extract `name`.
   b. Cross-reference: search the catalog for a package containing a skill artifact
      whose path matches this skill name.
   c. If matched, include it under that package. Otherwise skip — it is not governance-managed.

5. Group artifacts by package name within each scope.
   Build the artifact summary per package (e.g., "2 rules, 1 skill").

6. Version comparison:
   a. For each installed package, search the catalog for a matching `pkg.yaml`.
   b. Read the catalog version.
   c. Compare: if equal → `current`; if catalog is newer → `outdated`; if not in catalog → `unknown`.

### Output format

```
## coding-aegis status

### Project (.claude/)

| Package | Version | Tier | Artifacts | Status |
|---------|---------|------|-----------|--------|
| pirate-speak | 0.1.0 | goodies | 2 rules, 1 skill | current |

### User (~/.claude/)
(none)
```

If no governance-managed files found in any scope:

```
No coding-aegis packages installed. Run `/coding-aegis list` to browse the catalog.
```

## Constants and Naming

### Filename prefix

All governance-managed rule and agent files use the `aegis--` prefix.
This is the ownership boundary. The skill only creates, reads, updates, and deletes
files with this prefix. Files without the prefix are project-owned and never touched.

### Rule filename formula

```
aegis--{package-name}--{rule-basename}.md
```

- `{package-name}`: the `name` field from `pkg.yaml`
- `{rule-basename}`: source filename without extension

Example: `pirate-speak.md` from the `pirate-speak` package →
`aegis--pirate-speak--pirate-speak.md`

### Agent filename formula

```
aegis--{package-name}--{agent-basename}.md
```

### Managed-by frontmatter schema

```yaml
---
package: <string>           # Package name from pkg.yaml
rule: <string>              # Rule basename (rules only, omit for agents)
version: <string>           # Package version at time of install
tier: <string>              # required | best-practices | optional | goodies
managed-by: coding-aegis    # Ownership marker — always this literal value
---
```

Source frontmatter keys (`description`, `globs`, etc.) are preserved alongside
managed-by keys. Managed-by keys take precedence on conflict.

### Tier processing order

Always: `required` → `best-practices` → `optional` → `goodies`.
Never include `bootstrap`.

## Error Handling

### Catalog not found

```
Error: Could not locate the coding-aegis package catalog.
Ensure you are running this skill from within a coding-aegis repository clone,
or that the `pkgs/` directory is accessible from the current working directory.
```

### Package not found

```
Error: Package '{name}' not found in the catalog.
Run `/coding-aegis list` to see available packages.
```

### No artifacts

```
Warning: Package '{name}' has no artifacts to install.
```

### Write errors

If `mkdir -p` or file write fails, report the path and suggest checking permissions.
Do not silently continue — stop and inform the user.

### Directory creation

Always create target directories before writing files. Use `mkdir -p` via Bash
for `rules/`, `skills/`, and `agents/` directories under the chosen scope.

## Cross-tool Support

This skill currently supports **Claude Code only** (per AD-8). Cross-tool adaptation
rules — file extension mapping, frontmatter injection, path routing per tool — are
documented in `references/install-rules.md` within this skill directory.

That reference file is not loaded during normal Claude Code operation. It exists as
forward investment for when Cursor, Windsurf, and Copilot support is added. When that
work begins, the install command will detect the active tool and apply the adaptation
rules from the reference file automatically.
