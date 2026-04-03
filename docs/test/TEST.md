# Test Guide

## Overview

Tests validate the coding-aegis skill install lifecycle across agentic coding tools. Every test follows the 7-phase plan defined in [testing-spec.md](testing-spec.md). Tool-specific setup and caveats are in the per-tool detail files.

| Script | Tool | Detail file |
|--------|------|-------------|
| `tests/test-claude-bootstrapped-skill-install.sh` | Claude Code | [test-claude.md](test-claude.md) |
| `tests/test-codex-skill-install.sh` | Codex | [test-codex.md](test-codex.md) |
| `tests/test-gemini-skill-install.sh` | Gemini | [test-gemini.md](test-gemini.md) |
| `tests/test-cursor-skill-install.sh` | Cursor | [test-cursor.md](test-cursor.md) (future) |
| `tests/test_aegis_catalog.py` | Unit (Python) | — |

All integration scripts source `tests/lib-test-harness.sh` for assertions, output formatting, and timeouts.

## Running the Tests

### Unit tests

```bash
python3 -m pytest tests/test_aegis_catalog.py -v
```

### Claude Code integration test

Requires: `claude` installed and authenticated.

```bash
tests/test-claude-bootstrapped-skill-install.sh
```

### Gemini integration test

Requires: `gemini` installed and authenticated.

```bash
tests/test-gemini-skill-install.sh
```

### Codex integration test

Requires: `codex` installed and authenticated. **Changes must be pushed to GitHub first** — the Codex `$skill-installer` only installs from GitHub, not from local paths. See [test-codex.md](test-codex.md) for the two-phase testing requirement.

```bash
git push
tests/test-codex-skill-install.sh
```

## Policy

**All scripts must be run before closing any task.** Do not limit testing to scripts directly touched by a change — a regression anywhere in the suite is a failure. If a script cannot be run (e.g. tool not installed, changes not pushed), note it explicitly and get user agreement before closing.

See [testing-spec.md](testing-spec.md) for the full test plan, phase definitions, pass criteria, and the user journey contract.
