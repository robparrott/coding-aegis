---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages from the coding-aegis catalog. Trigger words — list packages, show package, install package, governance status.
---

# coding-aegis

Browse, install, and manage governance packages for coding agents. This skill provides
four commands: `list`, `show`, `install`, and `status`.

## Before You Begin: Detect the Active Tool

**Always run tool detection first**, before any other step. This determines install paths,
scope defaults, and which tool-specific logic to apply.

```bash
python3 "{skill-dir}/detect_tool.py"
```

Output:

```json
{
  "tool": "claude",
  "signals": ["env:CLAUDECODE=1"]
}
```

The `tool` field is the active agent: `claude` | `codex` | `cursor` | `gemini` | `windsurf` | `copilot`.
The `signals` list records what fired — include it in any error reports or debug output.

Use the detected tool for all subsequent path and scope decisions. Do not guess or
hardcode a tool name. If detection returns an unexpected tool, report it to the user
before proceeding.

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
| `uninstall-prep <name> [--scope PATH]` | Find installed artifacts to remove |
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
| `uninstall <name>` | Run **uninstall** for `<name>` |
| `status` | Run **status** |
| `detect-tool` | Run **detect-tool** |
| anything else | Print help text |

### Help text

```
Usage:
  /coding-aegis list              List available packages by tier
  /coding-aegis show <package>    Show package details
  /coding-aegis install <package> Install a package into the current project
  /coding-aegis uninstall <package> Remove an installed package
  /coding-aegis status            Show installed packages and versions
  /coding-aegis detect-tool       Show which coding agent is active and why
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

### Step 1 — Choose scope

First check whether the user's input already specifies a scope:

- If the input contains "project scope" or "to project" (case-insensitive) → use `--scope project`, skip the picker
- If the input contains "user scope" or "to user" (case-insensitive) → use `--scope user`, skip the picker

If no scope is specified in the input, ask using AskUserQuestion:

```
Where should this package be installed?

1. Project — into this repository (governs this project, shared via source control)
2. User — into your home directory (governs all your projects)
```

Map the choice to a `--scope` flag:

| Choice | Flag |
|--------|------|
| Project | `--scope project` |
| User | `--scope user` |

### Step 2 — Prepare install artifacts

Run:

```
python3 "{skill-dir}/aegis-catalog.py" install-prep <name> --scope <project|user>
```

**If the command exits non-zero or the JSON contains `"error"`: print the exact error
output verbatim, stop immediately, and do not attempt any further steps.** Do not
improvise, infer paths, or construct artifacts manually.
If `artifacts` is empty, warn and stop.

The response contains:
- `tool` — the detected active agent
- `scope` — `project` or `user`
- `scope_base` — absolute base path for rules and non-skill artifacts
- `artifacts` — array of files to write; each entry has `install_path` (the complete absolute destination path), `content`, and `type`

### Step 3 — Batch write all files

For each artifact, write `content` to `install_path`. Use `mkdir -p` to create parent directories. Issue all writes in a single Bash call:

```bash
mkdir -p "$(dirname '{install_path_1}')" && cat > '{install_path_1}' << 'AEGIS_EOF'
{content_1}
AEGIS_EOF
mkdir -p "$(dirname '{install_path_2}')" && cat > '{install_path_2}' << 'AEGIS_EOF'
{content_2}
AEGIS_EOF
```

**Do not recompute or adjust the paths.** Write exactly to the `install_path` values from the JSON — they already account for tool-specific layout (e.g. Codex skills go to `.agents/skills/`, not `.claude/skills/`).

### Step 4 — Update AGENTS.md (Claude Code, Project scope only)

Skip for all tools except Claude Code. Skip for User scope. Skip if AGENTS.md does not exist in CWD.

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

   Populate the table by scanning `{scope_base}/rules/aegis--*`. Read each file's
   frontmatter for package, rule, version, and tier.

### Step 5 — Confirm

Print a summary:

```
## Installed: {name} v{version} ({tier})

Tool: {tool}

| # | Type | Installed to |
|---|------|-------------|
| 1 | rule | .claude/rules/aegis--example--example-rule.md |
| 2 | skill | .agents/skills/example/SKILL.md |
```

If AGENTS.md was updated (Claude Code only), add: "AGENTS.md updated with installed governance rules table."

**Important**: After installing skills, remind the user: "Restart Claude Code (or your active tool) to load newly installed skills."

## uninstall

Remove an installed package's artifacts from the target project or user configuration.

### Step 1 — Find installed artifacts

1. Run: `python3 "{skill-dir}/aegis-catalog.py" uninstall-prep <name>`
   The script auto-detects the active tool and scans for artifacts managed by the package.
2. If the JSON contains `"error"`, print the error and stop.
3. The response contains `files_to_remove` (individual files) and `dirs_to_remove` (skill directories).

### Step 2 — Remove artifacts

Use Bash to delete all files and directories listed in the JSON:

```bash
rm -f <file1> <file2> ...
rm -rf <dir1> <dir2> ...
```

Issue all removals in a single Bash call.

### Step 3 — Update AGENTS.md (Project scope only)

If AGENTS.md exists and contains `## Installed Governance Rules`, rebuild the table
by scanning remaining `aegis--*` files (same as install Step 4). If no governance
files remain, remove the section entirely.

### Step 4 — Confirm

Print a summary:

```
## Uninstalled: {name}

Removed:
- {file_or_dir_1}
- {file_or_dir_2}
```

**Important**: After removing skills, remind the user: "Restart Claude Code to unload removed skills."

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

## detect-tool

Report which coding agent is active and which signals triggered the detection. Useful
as a diagnostic when installs or path resolution behave unexpectedly.

### Steps

1. Run: `python3 "{skill-dir}/detect_tool.py"`
2. Parse the JSON response. It contains `tool` (string) and `signals` (array of strings).
3. Format the output using the template below.

### Output format

```
## Active tool: {tool}

Signals that fired:
- {signal_1}
- {signal_2}
```

If `signals` is empty, print:

```
## Active tool: {tool}

No signals fired — defaulted to claude. If this is unexpected, check that the skill
is installed to the correct tool's skill directory.
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
