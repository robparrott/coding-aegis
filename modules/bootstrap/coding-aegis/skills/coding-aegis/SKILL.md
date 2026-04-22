---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages from the coding-aegis catalog. Trigger words — list packages, show package, install package, governance status.
---

# coding-aegis

Browse, install, and manage governance packages for coding agents.

## Command Dispatch

Match on the **first word** of the user input after `/coding-aegis`.

**CRITICAL**: The first word is consumed by this dispatch table. Do **NOT** pass it
as an argument to the script. Only the words/flags that follow the first word are
forwarded (e.g. `/coding-aegis list --catalog modules` → run `aegis-list.py --catalog modules`,
NOT `aegis-list.py list --catalog modules`).

| First word | Script | Required args | Extra args |
|------------|--------|---------------|------------|
| _(empty)_ | `aegis-list.py` | — | pass through |
| `list` | `aegis-list.py` | — | pass through |
| `show` | `aegis-show.py` | `<name>` (second word) | pass through |
| `install` | `aegis-install.py` | `<name> --scope <scope>` (see below) | pass through |
| `uninstall` | `aegis-uninstall.py` | `<name>` (second word) | pass through |
| `status` | `aegis-status.py` | — | pass through |
| `validate-install` | `aegis-validate.py` | `<name>` (second word) | pass through |
| `detect-tool` | `detect_tool.py` | — | pass through |
| anything else | print help text | — | — |

`{skill-dir}` is the directory containing this SKILL.md file.

### Help text

```
Usage:
  /coding-aegis list              List available packages by tier
  /coding-aegis show <package>    Show package details
  /coding-aegis install <package> Install a package into the current project
  /coding-aegis uninstall <package> Remove an installed package
  /coding-aegis status            Show installed packages and versions
  /coding-aegis validate-install <package> Verify a package's artifacts are correctly installed
  /coding-aegis detect-tool       Show which coding agent is active and why
```

## Execution — all commands except install

```bash
python3 "{skill-dir}/<script>" [args]
```

**Run the script immediately.** Do not read the script source, do not run
`--help`, do not list directories, do not verify the catalog path exists before
running. The dispatch table above provides everything needed — any pre-flight
calls are wasted round-trips.

Print stdout **exactly as-is** — no code fences, no reformatting, no
wrapping in ` ```text ``` ` blocks. The scripts already output markdown;
adding a code fence corrupts the formatting. If the script exits non-zero,
print stderr verbatim and stop. Do not improvise, retry, or interpret the
output.

## Execution — install

### Step 1: Resolve scope

Check whether the user's input already specifies a scope:

- Input contains "project scope" or "to project" (case-insensitive) → `--scope project`
- Input contains "user scope" or "to user" (case-insensitive) → `--scope user`

If no scope is specified, ask using AskUserQuestion:

```
Where should this package be installed?

1. Project — into this repository (governs this project, shared via source control)
2. User — into your home directory (governs all your projects)
```

### Step 2: Run the script

```bash
python3 "{skill-dir}/aegis-install.py" <name> --scope <project|user> [extra-args]
```

Include any extra args from the user's input (e.g. `--catalog modules`).
Print stdout verbatim. If the script exits non-zero, print stderr verbatim and stop.

## detect-tool output format

`detect_tool.py` outputs JSON. Format it as:

```
## Active tool: {tool}

Signals that fired:
- {signal_1}
- {signal_2}
```

If `signals` is empty:

```
## Active tool: {tool}

No signals fired — tool is unknown.
```

## Error handling

If any script exits non-zero, print stderr verbatim. Do not improvise,
infer paths, or attempt manual fallbacks.
