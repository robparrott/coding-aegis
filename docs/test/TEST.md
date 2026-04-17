# Test Guide

## Overview

Tests validate the coding-aegis skill install lifecycle across agentic coding tools. Every test follows the 7-phase user journey defined in [testing-spec.md](testing-spec.md). Tool-specific setup, invocation, and caveats are in the per-tool detail files.

## Current Status (2026-04-17)

### pytest integration suite

Run all tools at once:

```bash
pytest tests/integration/ -v
```

All tools have exactly 10 tests. Tools without a marketplace have phase 2 as an explicit skip.

| Tool | Test file | Tests | Result | Notes |
|------|-----------|-------|--------|-------|
| Claude Code | `test_claude.py` | 10 | **10/10 passing** | — |
| Codex | `test_codex.py` | 10 | **10/10 passing** | Requires push to GitHub first |
| Gemini | `test_gemini.py` | 10 | **4 pass / 6 skip** | Quota exhaustion → skip (not failure); model: `gemini-3-flash-preview` |
| Cursor | `test_cursor.py` | 10 | **10/10 passing** | `cursor-agent 2026.04.16` working after macOS quarantine fix; see [test-cursor.md §12](test-cursor.md) |
| OpenCode | `test_opencode.py` | 10 | **9 pass / 1 skip** | Phase 2 skip (no marketplace) |

### Bash harness (legacy)

| Script | Tool | Status |
|--------|------|--------|
| `tests/test-claude-bootstrapped-skill-install.sh` | Claude Code | passing |
| `tests/test-codex-skill-install.sh` | Codex | passing |
| `tests/test-gemini-skill-install.sh` | Gemini | passing (quota-dependent) |

---

## Running the Tests

### Full pytest suite (recommended)

```bash
pytest tests/integration/ -v
```

Requires all tools installed. Tests that cannot find their CLI binary skip automatically.

### Single tool

```bash
pytest tests/integration/test_claude.py -v
pytest tests/integration/test_codex.py -v
pytest tests/integration/test_gemini.py -v
pytest tests/integration/test_cursor.py -v
pytest tests/integration/test_opencode.py -v
```

### Unit tests

```bash
pytest tests/test_aegis_catalog.py -v
```

---

## Prerequisites by Tool

| Tool | Binary | Auth | Notes |
|------|--------|------|-------|
| Claude Code | `claude` | `claude /login` | — |
| Codex | `codex` | `codex auth login` | Changes must be pushed to GitHub first — Codex `$skill-installer` installs from GitHub, not local paths. See [test-codex.md](test-codex.md). |
| Gemini | `gemini` | Google account | Free-tier quota exhausts quickly; skips convert to `pytest.skip`, not failures. |
| Cursor | `cursor-agent` | Cursor account | After `brew install cursor-cli`, run `xattr -rd com.apple.quarantine $(brew --prefix)/Caskroom/cursor-cli/<version>/` to clear macOS quarantine. See [test-cursor.md §12](test-cursor.md). |
| OpenCode | `opencode` | Provider API key | `opencode run` requires `git init` in the working directory. |

---

## Per-Tool Detail Files

| Tool | Detail file |
|------|-------------|
| Claude Code | [test-claude.md](test-claude.md) |
| Codex | [test-codex.md](test-codex.md) |
| Gemini | [test-gemini.md](test-gemini.md) |
| Cursor | [test-cursor.md](test-cursor.md) |
| OpenCode | [test-opencode.md](test-opencode.md) |

---

## Policy

**All tests must be run before closing any task.** Do not limit testing to scripts directly touched by a change — a regression anywhere in the suite is a failure. If a test cannot be run (tool not installed, binary broken, changes not pushed), note it explicitly and get user agreement before closing.

See [testing-spec.md](testing-spec.md) for the full test plan, phase definitions, pass criteria, and the user journey contract.
