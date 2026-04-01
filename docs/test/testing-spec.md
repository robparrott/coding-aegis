# Testing Specification: Skill Setup Pipeline

## Purpose

Validate the coding-aegis skill install lifecycle across agentic coding tools. Tests exercise the **actual user journey** — install the coding-aegis skill, then use it through the tool's agent to manage packages. No test bypasses the skill.

## User Journey

This is the flow every test script validates, in order:

1. **Register the coding-aegis marketplace/registry** — add the catalog source so the tool can discover and install the skill. This validates the distribution mechanism itself.
2. **Install the coding-aegis skill from the marketplace** — use the tool's native install command to install the skill from the registered source. Marketplace-based install is **strongly preferred**. Fall back to local file copy ONLY if the tool has no marketplace or registry mechanism.
3. **Use the skill to list** packages in the catalog
4. **Use the skill to show** the helloworld package details
5. **Use the skill to install** the helloworld package into a test directory
6. **Verify** the installed files exist with correct naming and frontmatter
7. **Teardown** — remove helloworld, uninstall coding-aegis, remove marketplace, clean up

The skill is the product. Every agent-mediated test goes through it.

### Install mechanism preference (T1)

| Preference | Mechanism | When to use |
|-----------|-----------|-------------|
| **1st** | Marketplace/registry | Tool has a plugin/skill marketplace (Claude, Gemini) |
| **2nd** | Git-based install | Tool supports `install <git-url>` (Gemini, Codex via clone) |
| **3rd** | Local file copy | Tool has NO marketplace or registry (Codex `.agents/skills/`) |

Only Codex currently requires local file copy. Claude uses plugin marketplace. Gemini uses `skills link` (local) or `skills install` (remote). If a tool adds marketplace support later, its test MUST be updated to use it.

## CLI Invocation Standard

All test scripts use `lib-test-harness.sh`. These rules are non-negotiable.

### Prompts are ALWAYS delivered via stdin

Every prompt to an agent is set in `CLI_PROMPT` and piped to the command's stdin by the harness. Never pass prompts as positional arguments or flag values.

```bash
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its list command."
RUN_DIR="$TEST_DIR" run_cli "skill list" <tool> <flags-only>
```

### Tool invocation patterns

Every tool follows the same stdin pattern. The only differences are the binary name and flags.

| Tool | Agent invocation (receives prompt on stdin) | Non-agent invocation |
|------|---------------------------------------------|---------------------|
| Claude | `claude -p --allowedTools "..." $CLAUDE_FLAGS` | `claude plugin marketplace add ...` |
| Codex | `codex exec --ephemeral -s <sandbox> -o /dev/stdout` | `cp` to `.agents/skills/` |
| Gemini | `gemini_quiet -o text` | `gemini_quiet skills link ...` |

**Claude flags:**
- `--strict-mcp-config --mcp-config '{"mcpServers":{}}'` — disables MCP servers (prevents startup hangs)
- `--allowedTools "Bash,Read,Glob"` — read-only commands (list, show)
- `--allowedTools "Bash,Read,Write,Glob" --permission-mode dontAsk` — install (needs Write)

**Codex flags:**
- `--ephemeral` — no session persistence
- `-s read-only` — read-only commands; `-s workspace-write` — install
- `-o /dev/stdout` — captures output
- Requires `git init` in working directory

**Gemini flags:**
- `-o text` — plain text output
- `--yolo` — auto-approve tool use for all agent-mediated steps (T3-T5); without this, Gemini prompts for approval which hangs in headless mode
- `gemini_quiet` wrapper filters Homebrew keytar warnings

### Non-prompt CLI calls

Tool management commands (marketplace add, plugin install, skills link) do NOT use `CLI_PROMPT`. Arguments go directly to `run_cli`:

```bash
run_cli "marketplace add" claude plugin marketplace add "$REPO_ROOT"
```

## Test Harness (`tests/lib-test-harness.sh`)

All scripts source this. No script implements its own pass/fail, CLI wrappers, or output formatting.

| Function | Purpose |
|----------|---------|
| `run_cli <desc> <cmd...>` | Execute command. If `CLI_PROMPT` set, pipes via stdin and displays as `echo "prompt" \| cmd`. If `RUN_DIR` set, runs there. Timeouts register as FAIL. Wrapper names (`*_quiet`) are auto-resolved for display. Sets `$LAST_OUTPUT`, `$LAST_EXIT`. `CLI_PROMPT` and `RUN_DIR` reset after call. |
| `assert_contains <output> <pattern> <desc>` | Case-insensitive grep, pass/fail |
| `assert_not_contains <output> <pattern> <desc>` | Inverse |
| `assert_file_exists <path> <desc>` | File existence |
| `assert_file_contains <path> <pattern> <desc>` | Grep file content |
| `assert_no_quota_error <output> [tool]` | Detect quota/rate-limit errors; FAIL + abort if found |
| `pass <desc>` / `fail <desc>` | Counters + colored output |
| `print_results` | Final summary, exit 0/1 |
| `section <title>` / `test_header <title>` | Formatted headers |

| Variable | Default | Purpose |
|----------|---------|---------|
| `TIMEOUT` | 90 | Seconds before kill |
| `CLI_PROMPT` | empty | Stdin prompt; reset after `run_cli` |
| `RUN_DIR` | empty | Working directory; reset after `run_cli` |
| `LAST_OUTPUT` | — | Captured output |
| `LAST_EXIT` | — | Exit code |

## Test Sequence

### T0 — Prerequisites

| Step | Pass criteria |
|------|---------------|
| T0.1 Tool installed | `command -v <tool>` succeeds, version printed |
| T0.2 Tool authenticated | `CLI_PROMPT="Reply with exactly: AUTH_OK"` returns AUTH_OK |

### T1 — Register Marketplace / Registry

Add the coding-aegis catalog as a source the tool can install from.

| Step | Pass criteria |
|------|---------------|
| T1.1 Register source | CLI reports success |
| T1.2 Source visible in list | Marketplace/registry name visible |

| Tool | T1.1 | T1.2 |
|------|------|------|
| Claude | `claude plugin marketplace add <path>` | `claude plugin marketplace list` |
| Codex | Verify `install-skill-from-github.py` exists | Built-in installer present |
| Gemini | N/A (uses `skills link` directly — skip to T2) | N/A |

### T2 — Install coding-aegis Skill

Install the skill from the registered source (T1) or via the best available mechanism.

| Step | Pass criteria |
|------|---------------|
| T2.1 Install skill | CLI reports success or files present |
| T2.2 Skill discoverable | Name visible in tool's list/discovery |

| Tool | T2.1 | T2.2 |
|------|------|------|
| Claude | `claude plugin install coding-aegis@<mp>` | `claude plugin list` |
| Codex | `install-skill-from-github.py --repo --path --dest` | `assert_file_exists` |
| Gemini | `gemini skills link <path> --consent` | `gemini skills list` |

### T3 — Use Skill: List Packages

| Step | Pass criteria |
|------|---------------|
| T3.1 Agent lists packages | Output contains "helloworld" |

### T4 — Use Skill: Show Package

| Step | Pass criteria |
|------|---------------|
| T4.1 Agent shows helloworld | Output contains name, tier "optional", version "1.0.0" |

### T5 — Use Skill: Install Package

| Step | Pass criteria |
|------|---------------|
| T5.1 Agent installs helloworld | Agent reports install activity |

Prompt instructs agent to use Project scope without asking.

### T6 — Verify Installed Files

Filesystem checks, no agent.

| Step | Pass criteria |
|------|---------------|
| T6.1 Rule file exists | `aegis--helloworld--helloworld.md` present |
| T6.2 Rule frontmatter | `managed-by: coding-aegis`, `package: helloworld`, `tier: optional` |
| T6.3 Skill file exists | `skills/helloworld/SKILL.md` present |

### T7 — Teardown

| Step | Pass criteria |
|------|---------------|
| T7.1 Uninstall skill | CLI success or files removed |
| T7.2 Remove marketplace/registry | CLI success (skip for tools without marketplace) |
| T7.3 Remove test directory | Deleted |

## Test Package

`helloworld` from `pkgs/optional/helloworld/`:
- 1 rule + 1 skill (both artifact types)
- In the real catalog (available after push for remote tests)
- No side effects
- Predictable content for assertions

## Test Scripts

| Tool | Script |
|------|--------|
| Claude | `tests/test-claude-bootstrapped-skill-install.sh` |
| Codex | `tests/test-codex-skill-install.sh` |
| Gemini | `tests/test-gemini-skill-install.sh` |
| Cursor | `tests/test-cursor-skill-install.sh` (future) |
| Harness | `tests/lib-test-harness.sh` |
| Unit | `tests/test_aegis_catalog.py` |

## Coverage Matrix

| Test | Claude | Codex | Gemini | Cursor |
|------|--------|-------|--------|--------|
| T0 Prerequisites | done | done | done | TBD |
| T1 Register marketplace | done | N/A | N/A | TBD |
| T2 Install skill | done | done | done | TBD |
| T3 Skill: list | done | done | done | TBD |
| T4 Skill: show | done | done | done | TBD |
| T5 Skill: install | done | done | done | TBD |
| T6 Verify files | done | done | done | TBD |
| T7 Teardown | done | done | done | TBD |
| Unit tests | done (31) | — | — | — |

All test scripts conform to the T0-T7 sequence defined above.
