---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages from the coding-aegis catalog. Trigger words — list packages, show package, install package, governance status.
---

# coding-aegis

Browse, install, and manage governance packages for coding agents.

## Command Dispatch

Parse the user input after `/coding-aegis` and route to the matching script.

| Input | Script | Args |
|-------|--------|------|
| _(empty)_ | `aegis-list.py` | — (also print help below) |
| `list` | `aegis-list.py` | — |
| `show <name>` | `aegis-show.py` | `<name>` |
| `install <name>` | `aegis-install.py` | `<name> --scope <scope>` (see below) |
| `uninstall <name>` | `aegis-uninstall.py` | `<name>` |
| `status` | `aegis-status.py` | — |
| `detect-tool` | `detect_tool.py` | — |
| anything else | print help text | — |

`{skill-dir}` is the directory containing this SKILL.md file.

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

## Execution — all commands except install

```bash
python3 "{skill-dir}/<script>" [args]
```

Print stdout verbatim. If the script exits non-zero, print stderr verbatim
and stop. Do not improvise, retry, or interpret the output — just print it.

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
python3 "{skill-dir}/aegis-install.py" <name> --scope <project|user>
```

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

No signals fired — defaulted to claude.
```

## Error handling

If any script exits non-zero, print stderr verbatim. Do not improvise,
infer paths, or attempt manual fallbacks.
