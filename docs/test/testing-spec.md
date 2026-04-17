# Testing Specification: Skill Setup Pipeline

## Purpose

Validate the coding-aegis skill install lifecycle across agentic coding tools. Tests exercise the **actual user journey** — install the coding-aegis skill, then use it through the tool's agent to manage packages. No test bypasses the skill.

## Coding Tools

Each tool has a detail file covering CLI invocation, install mechanisms, tool detection, teardown, and caveats.

All tools have exactly 10 tests. Tools without a marketplace (Gemini, OpenCode) have phase 2 as an explicit skip stub rather than a silent omission.

| Tool | Detail file | pytest | Tests | Status |
|------|------------|--------|-------|--------|
| Claude Code | [test-claude.md](test-claude.md) | `tests/integration/test_claude.py` | 10 | **10/10 passing** |
| Codex | [test-codex.md](test-codex.md) | `tests/integration/test_codex.py` | 10 | **10/10 passing** |
| Gemini | [test-gemini.md](test-gemini.md) | `tests/integration/test_gemini.py` | 10 | **4 pass / 6 skip** (quota exhausted; not failures) |
| Cursor | [test-cursor.md](test-cursor.md) | `tests/integration/test_cursor.py` | 10 | **10/10 skip** — `cursor-agent 2026.04.16` binary broken (`wpi.14`); was 10/10 on `2026.03.30` |
| OpenCode | [test-opencode.md](test-opencode.md) | `tests/integration/test_opencode.py` | 10 | **9 pass / 1 skip** (phase 2 not applicable) |
| Windsurf | TBD | TBD | — | not started |

Each tool must have an equivalent install/uninstall lifecycle. This may vary depending on tool capabilities, but the testing scheme and consistency must be reflected in the test script for each tool.

## Test Phases

Every tool's pytest class implements exactly these 10 phases. Tools without a marketplace (Gemini, OpenCode) have phase 2 as an explicit `pytest.skip` stub — the omission is documented, not silent.

| Phase | Name | What it tests |
|-------|------|--------------|
| 1 | auth | Tool CLI is present, authenticated, and responds |
| 2 | plugin_manifest | Marketplace manifest file exists and lists `coding-aegis`; skip with reason if tool has no marketplace |
| 3 | skill_files_present / skill_discoverable | coding-aegis skill is installed and its key files are accessible |
| 4a | detect_tool_direct | `detect_tool.py` run directly (outside the agent) returns the correct tool name and at least one signal |
| 4b | detect_tool_skill | `/coding-aegis detect-tool` via the agent returns the correct tool name |
| 4c | list | `/coding-aegis list --catalog pkgs` returns helloworld |
| 4d | show | `/coding-aegis show helloworld --catalog pkgs` returns name, tier, version |
| 5 | install_helloworld | `/coding-aegis install helloworld` writes rule and skill files; asserts file contents |
| 5b | helloworld_responds | `/helloworld` skill responds with `Hello, World` |
| 6 | uninstall_helloworld | `/coding-aegis uninstall helloworld` removes all installed files cleanly |

The skill is the product. Every agent-mediated test goes through it. 

Almost every task initiated by the skill should complete in less than 10 seconds. Beyond that the user experience is a problem. The time for completion is part of the success criteria ... steps that take a long time are not a success, even if completed.

### Principle: exercise the real user journey

Prompts must invoke the tool's **built-in mechanisms** — never instruct the agent to bypass them. For example, Codex has a built-in `$skill-installer` skill for installing skills from GitHub. The test prompt says "Use the skill-installer to install a skill from GitHub repo X, path Y" and lets the agent invoke `$skill-installer` naturally. It does NOT call `install-skill-from-github.py` directly or copy files manually.

Similarly, phases 4–5 prompts should reference the skill by name ("Use the coding-aegis skill to list packages") rather than providing implementation details about internal scripts or directory paths.

### Install mechanism preference (phase 3)

| Preference | Mechanism | When to use |
|-----------|-----------|-------------|
| **1st** | Marketplace/registry | Tool has a plugin/skill marketplace (Claude) |
| **2nd** | Built-in skill installer | Tool has an agent-mediated install mechanism (Codex `$skill-installer`) |
| **3rd** | CLI skill management | Tool has a skills CLI (Gemini `skills link`) |
| **4th** | Local file copy | Tool has NO install mechanism — last resort |

## Test Plan

| Phase | Step | Description | Pass criteria |
|-------|------|-------------|---------------|
| **1. Environment & Tool Validation** | 1.1 | Tool installed | `command -v <tool>` succeeds; version printed |
| | 1.2 | Tool authenticated | Prompt `Reply with exactly: AUTH_OK` returns `AUTH_OK` |
| | 1.3 | Working directory initialized | `git init` (or equivalent) succeeds in `$TEST_DIR` |
| **2. Marketplace / Registry Setup** | 2.1 | Register coding-aegis source | CLI reports success |
| | 2.2 | Source visible | Marketplace/registry name appears in tool's list |
| **3. Install coding-aegis Skill** | 3.1 | Install skill via native mechanism | CLI reports success or expected files present |
| | 3.2 | Skill discoverable | Name visible in tool's skill/plugin list |
| | 3.3 | `detect_tool.py` present | File exists at installed path |
| **4. Validate coding-aegis Skill** | 4.1 | Tool detected correctly | `detect_tool.py` returns correct `tool` value and non-empty `signals` |
| | 4.2 | `detect-tool` skill command | Skill output contains tool name and at least one signal |
| | 4.3 | `list` skill command | Output contains `helloworld` |
| | 4.4 | `show` skill command | Output contains name, tier `optional`, version `1.0.0` |
| **5. Install helloworld Package** | 5.1 | `install helloworld` skill command | Agent reports install activity |
| | 5.2 | Rule file present | `aegis--helloworld--helloworld.md` exists at expected path |
| | 5.3 | Rule frontmatter correct | Contains `managed-by: coding-aegis`, `package: helloworld`, `tier: optional` |
| | 5.4 | Skill file present | `skills/helloworld/SKILL.md` exists |
| | 5.5 | helloworld skill responds | Invoking `$helloworld` / `/helloworld` returns `Hello, World` |
| **6. Uninstall helloworld Package** | 6.1 | `uninstall helloworld` skill command | No errors in output |
| | 6.2 | Installed files removed | Rule file and skill directory absent |
| **7. Full Cleanup** | 7.1 | Uninstall coding-aegis skill | CLI or file removal succeeds |
| | 7.2 | Skill no longer discoverable | Name absent from tool's skill/plugin list |
| | 7.3 | Remove marketplace/registry | CLI or file removal succeeds |
| | 7.4 | Marketplace no longer registered | Name absent from tool's marketplace list (or manifest directory absent) |
| | 7.5 | Remove test directory | `rm -rf $TEST_DIR` |
| | 7.6 | Test directory gone | `assert_dir_not_exists $TEST_DIR` |

**Phase 3.1 — detection invocation method**: Tools whose skill is installed under a tool-specific path segment (`.claude/`, `.codex/`) use a direct bash invocation of `detect_tool.py` — no agent needed, the `path:` signal fires from `__file__`. Tools where the skill is linked to a local path with no tool-specific segment (Gemini via `skills link`) require an agent-mediated invocation so the tool's env var (`GEMINI_CLI=1`) is present. See the tool's detail file for the specific path and expected signal.

**Phase 5.1 — headless install**: The install command's interactive scope picker (`AskUserQuestion`) cannot be used in headless mode. Include "to Project scope" in the prompt so the agent can complete the install without waiting for input.

**Phase 7 — teardown ordering**: Run all assertions (7.2, 7.4, 7.6) before the corresponding removal steps. Never remove the test directory before asserting that earlier cleanup steps succeeded — a failing assertion inside a deleted directory produces no output.

## Testing Mechanics

All test scripts use `lib-test-harness.sh`. These rules are non-negotiable.

### Timing

Any test step that takes over 10 seconds should be regarded as a bug. Do not increase the test step timeout beyond 15 seconds to work around issues, since that very likely means the agent is not well guided and flailing.

### Prompts are ALWAYS delivered via stdin

Every prompt to an agent is set in `CLI_PROMPT` and piped to the command's stdin by the harness. Never pass prompts as positional arguments or flag values.

```bash
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its list command."
RUN_DIR="$TEST_DIR" run_cli "skill list" <tool> <flags-only>
```

### Non-prompt CLI calls

Tool management commands (marketplace add, plugin install, skills link) do NOT use `CLI_PROMPT`. Arguments go directly to `run_cli`:

```bash
run_cli "marketplace add" claude plugin marketplace add "$REPO_ROOT"
```

For tool-specific flags, sandbox modes, and invocation patterns see each tool's detail file.

### Test Harness (`tests/lib-test-harness.sh`)

All scripts source this. No script implements its own pass/fail, CLI wrappers, or output formatting.

| Function | Purpose |
|----------|---------|
| `run_cli <desc> <cmd...>` | Execute command. If `CLI_PROMPT` set, pipes via stdin and displays as `echo "prompt" \| cmd`. If `RUN_DIR` set, runs there. Timeouts register as FAIL. Wrapper names (`*_quiet`) are auto-resolved for display. Sets `$LAST_OUTPUT`, `$LAST_EXIT`. `CLI_PROMPT` and `RUN_DIR` reset after call. |
| `assert_contains <output> <pattern> <desc>` | Case-insensitive grep, pass/fail |
| `assert_not_contains <output> <pattern> <desc>` | Inverse |
| `assert_file_exists <path> <desc>` | File existence |
| `assert_file_contains <path> <pattern> <desc>` | Grep file content |
| `assert_file_not_exists <path> <desc>` | File absence (for teardown) |
| `assert_dir_not_exists <path> <desc>` | Directory absence (for teardown) |
| `assert_no_quota_error <output> [tool]` | Detect quota/rate-limit errors; FAIL + abort if found |
| `assert_json_value <json> <field> <expected> <desc>` | Parse JSON, assert a top-level field equals expected string |
| `assert_json_nonempty_array <json> <field> <desc>` | Parse JSON, assert a top-level array field has at least one element |
| `pass <desc>` / `fail <desc>` | Counters + colored output |
| `print_results` | Final summary, exit 0/1 |
| `section <title>` / `test_header <title>` | Formatted headers |

**Timeout policy: all timeouts are capped at 30 seconds. A timeout is always a bug, never a tuning knob. If a step times out, fix the root cause — wrong paths, missing files, bad tool detection — do not raise the timeout.**

| Variable | Default | Purpose |
|----------|---------|---------|
| `TIMEOUT` | 30 | Default seconds before kill |
| `TIMEOUT_LONG` | 30 | Extended timeout (kept at 30 — see policy above) |
| `CLI_PROMPT` | empty | Stdin prompt; reset after `run_cli` |
| `CLI_TIMEOUT` | empty | Per-call timeout override; reset after `run_cli` |
| `RUN_DIR` | empty | Working directory; reset after `run_cli` |
| `LAST_OUTPUT` | — | Captured output |
| `LAST_EXIT` | — | Exit code |
| `AEGIS_TEST_FAIL_FAST` | unset | Set to `1` to stop at the first `fail()` and run cleanup immediately. Use when debugging to avoid burning time and API quota on subsequent phases. |
| `AEGIS_TEST_LOG` | unset | Set to a file path to capture all output. Screen output is teed to the file; additionally, the **full** `LAST_OUTPUT` from every `run_cli` call is appended untruncated (bypassing the 50-line screen limit). Useful for post-mortem review of long agent interactions. |

### Debug workflow

When a test fails and you need to diagnose it:

```bash
# Stop at first failure, log everything to a file
AEGIS_TEST_FAIL_FAST=1 AEGIS_TEST_LOG=/tmp/aegis-test.log \
  tests/test-codex-skill-install.sh

# Review the full agent output for the failing step
grep -A 200 "FULL OUTPUT: skill install" /tmp/aegis-test.log
```

`AEGIS_TEST_FAIL_FAST=1` is the standard debugging mode. Never run a slow LLM test in a tight loop without it — each wasted phase costs real API quota.

### Test Package

`helloworld` from `pkgs/optional/helloworld/`:
- 1 rule + 1 skill (both artifact types)
- In the real catalog (available after push for remote tests)
- No side effects
- Predictable content for assertions

### Test Scripts

| Tool | Script |
|------|--------|
| Claude | `tests/test-claude-bootstrapped-skill-install.sh` |
| Codex | `tests/test-codex-skill-install.sh` |
| Gemini | `tests/test-gemini-skill-install.sh` |
| Cursor | `tests/test-cursor-skill-install.sh` (future) |
| Harness | `tests/lib-test-harness.sh` |
| Unit | `tests/test_aegis_catalog.py` |

**All scripts must be run before closing any task.** Do not limit testing to scripts directly touched by a change — a regression anywhere in the suite is a failure. If a script cannot be run (e.g. tool not installed), note it explicitly and get user agreement before closing.

### The user journey contract is inviolable

**NEVER substitute a direct file copy, manual script execution, or any other shortcut for the tool's proper install mechanism.** A test that bypasses the install mechanism does not validate the user journey — it validates nothing useful and creates false confidence. Worse, it hides real failures that will surface in production.

If a tool's install mechanism cannot be exercised (e.g. network unavailable, tool not installed), the correct action is to **skip the test and note it explicitly** — not to substitute a workaround. A skipped test with a clear explanation is always preferable to a test that breaks the user journey contract.

## Coverage Matrix

| Phase | Claude | Codex | Gemini | Cursor |
|-------|--------|-------|--------|--------|
| 1 Environment & Tool Validation | done | done | done | TBD |
| 2 Marketplace / Registry Setup | done | N/A | N/A | TBD |
| 3 Install coding-aegis Skill | done | done | done | TBD |
| 4 Validate coding-aegis Skill | done | done | done | TBD |
| 5 Install helloworld Package | done | done | done | TBD |
| 6 Uninstall helloworld Package | done | done | done | TBD |
| 7 Full Cleanup | done | done | done | TBD |
| Unit tests | done (31) | — | — | — |

All test scripts conform to the 7-phase test plan defined above.
