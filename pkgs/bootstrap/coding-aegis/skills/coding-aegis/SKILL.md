---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages from the coding-aegis catalog. Trigger words — list packages, show package, install package, governance status.
---

# coding-aegis

Browse, install, and manage governance packages for coding agents. This skill provides
four commands: `list`, `show`, `install`, and `status`.

## CLI Helper

This skill includes a Python CLI helper (`aegis-catalog.py`) in the same directory as
this SKILL.md file. Use it via the Bash tool for catalog operations instead of manual
Glob/Read/parse cycles:

```
python3 "{skill-dir}/aegis-catalog.py" <subcommand> [args]
```

Where `{skill-dir}` is the directory containing this SKILL.md file. Resolve it from
the skill file path. The helper outputs JSON to stdout — parse it and format the
response using the Output Format sections below.

### Available subcommands

| Subcommand | Purpose |
|------------|---------|
| `resolve-catalog [--from PATH]` | Locate the `pkgs/` catalog directory |
| `list [--catalog PATH]` | List all packages by tier |
| `show <name> [--catalog PATH]` | Full package details + README |
| `install-prep <name> [--catalog PATH]` | Prepare install artifacts with frontmatter |
| `status [--catalog PATH] [--scope PATH...]` | Installed packages and version status |

If `--catalog` is omitted, the helper resolves it from the current working directory.

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

1. Run: `python3 "{skill-dir}/aegis-catalog.py" list`
2. Parse the JSON response. It contains `tiers`, each with a `packages` array.
3. Format the output using the template below.

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

Sort packages alphabetically within each tier. If a tier has no packages, print "(none)".

## show

Display full details for a single package.

### Steps

1. Run: `python3 "{skill-dir}/aegis-catalog.py" show <name>`
2. If the JSON contains `"error"`, print the error message and stop.
3. Format the output using the template below.

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
| 1 | rule | rules/example-rule.md |
| 2 | skill | skills/example/SKILL.md |

### README

{readme contents, or "(No README)"}
```

## install

Install a package's artifacts into the target project or user configuration.

> **Note**: This skill currently supports **Claude Code only** (per AD-8).

### Step 1 — Resolve and prepare

1. Detect the active tool: if running in Codex, use `--tool codex`. If running
   in Cursor, use `--tool cursor`. Otherwise default to `--tool claude`.
   Detection: Codex sets `CODEX_HOME` env var; Cursor has `.cursor/` directory.
2. Run: `python3 "{skill-dir}/aegis-catalog.py" install-prep <name> --tool <tool>`
3. If the JSON contains `"error"`, print the error and stop.
4. The response contains `name`, `version`, `tier`, `tool`, `scope_base`, and
   an `artifacts` array. Each artifact has: `type`, `target_subdir`,
   `target_filename`, `content`, and optionally `base_path`.
5. If the artifacts array is empty, warn and stop.

### Step 2 — Scope picker

Use the `scope_base` from the install-prep JSON (e.g. `.claude` for Claude, `.claude` for Codex rules).

Present the user with a choice using AskUserQuestion:

```
Where should this package be installed?

1. Project — `{scope_base}/` in the current repo (governs this project, shared via source control)
2. User — `~/{scope_base}/` in your home directory (governs all your projects)
```

Map the response to a base path:

| Scope | Base path |
|-------|-----------|
| Project | `{CWD}/{scope_base}/` |
| User | `~/{scope_base}/` |

### Step 3 — Batch write all files

For each artifact from Step 1, compute the full target path:
- If the artifact has a `base_path` field, use: `{base_path}/{target_subdir}/{target_filename}`
- Otherwise use: `{scope-base}/{target_subdir}/{target_filename}`

where `scope-base` comes from the scope picker (Step 2) or from the `scope_base` field in the JSON.

Write all files using Bash with `mkdir -p` and `cat > file << 'AEGIS_EOF' ... AEGIS_EOF`.
The Write tool cannot write to `.claude/` paths (hardcoded sensitive-path protection),
so Bash is required. Create parent directories first, then write all files in a single
Bash call to minimize tool invocations.

### Step 4 — Update AGENTS.md (Project scope only)

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

### Step 5 — Confirm

Print a summary:

```
## Installed: {name} v{version} ({tier})

| # | Type | Installed to |
|---|------|-------------|
| 1 | rule | .claude/rules/aegis--example--example-rule.md |
| 2 | skill | .claude/skills/example/SKILL.md |
```

If AGENTS.md was updated, add: "AGENTS.md updated with installed governance rules table."

**Important**: After installing skills, remind the user: "Restart Claude Code to load newly installed skills."

## status

Show all coding-aegis-managed packages and their version status.

### Steps

1. Run: `python3 "{skill-dir}/aegis-catalog.py" status`
2. Parse the JSON response. It contains `scopes`, each with a `packages` array.
3. Format the output using the template below.

### Output format

```
## coding-aegis status

### Project (.claude/)

| Package | Version | Tier | Artifacts | Status |
|---------|---------|------|-----------|--------|
| example | 1.0.0 | required | 2 rules, 1 skill | current |

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

If a file write fails, report the path and suggest checking permissions.
Do not silently continue — stop and inform the user.

### Tool usage

Use the Write tool for all file creation. It creates parent directories automatically.
Do not use Bash for `mkdir` or any file operations during install — this avoids
unnecessary permission prompts.

## Cross-tool Support

This skill currently supports **Claude Code only** (per AD-8). Cross-tool adaptation
rules — file extension mapping, frontmatter injection, path routing per tool — are
documented in `references/install-rules.md` within this skill directory.

That reference file is not loaded during normal Claude Code operation. It exists as
forward investment for when Cursor, Windsurf, and Copilot support is added. When that
work begins, the install command will detect the active tool and apply the adaptation
rules from the reference file automatically.
