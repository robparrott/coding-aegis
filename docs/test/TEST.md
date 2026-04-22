# Test Guide

This is the single authoritative reference for testing the coding-aegis skill install lifecycle. It covers the test plan, phase definitions, pass criteria, mechanics, and running instructions. Tool-specific setup, invocation, and caveats are in the per-tool detail files.

---

## Purpose

Validate the coding-aegis skill install lifecycle across agentic coding tools. Tests exercise the **actual user journey** — install the coding-aegis skill, then use it through the tool's agent to manage packages. No test bypasses the skill.

---

## Current Status (2026-04-22)

### pytest integration suite

Run all tools at once:

```bash
pytest tests/integration/ -v
```

All tools have exactly 10 tests. Tools without a marketplace validate the SKILL.md bootstrap mechanism in phase 2 instead.

| Tool | Test file | Tests | Result | Notes |
|------|-----------|-------|--------|-------|
| Claude Code | `test_claude.py` | 10 | **10/10 passing** | — |
| Codex | `test_codex.py` | 10 | **10/10 passing** | Requires push to GitHub first; phase 6 uses `danger-full-access` sandbox |
| Cursor | `test_cursor.py` | 10 | **10/10 passing** | Requires macOS quarantine fix after `brew install cursor-cli`; see [test-cursor.md §12](test-cursor.md) |
| OpenCode | `test_opencode.py` | 10 | **10/10 passing** | Phase 2 validates SKILL.md bootstrap mechanism |
| Gemini | `test_gemini.py` | 10 | **10/10 passing (paid tier); quota-skip on free tier** | Phase 2 validates SKILL.md bootstrap. Free-tier quota exhausts phases 4b–6; those steps call `pytest.skip`. |
| Copilot | `test_copilot.py` | 10 | **10/10 passing** | All phases validated 2026-04-22. No env var signal — path:.github only. Steps take 30–40s (Copilot LLM latency); UX budget warnings are expected. |

---

## Coding Tools

Each tool has a detail file covering CLI invocation, install mechanisms, tool detection, teardown, and caveats.

| Tool | Detail file | pytest | Tests | Status |
|------|------------|--------|-------|--------|
| Claude Code | [test-claude.md](test-claude.md) | `tests/integration/test_claude.py` | 10 | **10/10 passing** |
| Codex | [test-codex.md](test-codex.md) | `tests/integration/test_codex.py` | 10 | **10/10 passing** — phase 6 uses `danger-full-access` to allow skill dir removal |
| Cursor | [test-cursor.md](test-cursor.md) | `tests/integration/test_cursor.py` | 10 | **10/10 passing** — `cursor-agent 2026.04.16` working after macOS quarantine fix |
| OpenCode | [test-opencode.md](test-opencode.md) | `tests/integration/test_opencode.py` | 10 | **10/10 passing** |
| Gemini | [test-gemini.md](test-gemini.md) | `tests/integration/test_gemini.py` | 10 | **10/10 passing (paid tier)** — phases 4b–6 quota-skip on free tier; quota exhaustion calls `pytest.skip`, not `pytest.fail`. |
| Copilot | [test-copilot.md](test-copilot.md) | `tests/integration/test_copilot.py` | 10 | **10/10 passing** — all phases validated 2026-04-22. Steps take 30–40s (Copilot LLM latency); UX budget warnings are expected and not a defect. |

Each tool must have an equivalent install/uninstall lifecycle. This may vary depending on tool capabilities, but the testing scheme and consistency must be reflected in the test script for each tool.

---

## Test Phases

Every tool's pytest class implements exactly these 10 phases. Tools without a marketplace (Gemini, OpenCode) have phase 2 as an explicit `pytest.skip` stub — the omission is documented, not silent.

| Phase | Name | What it tests |
|-------|------|--------------|
| 1 | auth | Tool CLI is present, authenticated, and responds |
| 2 | plugin_manifest | Marketplace manifest file exists and lists `coding-aegis`; skip with reason if tool has no marketplace |
| 3 | skill_files_present / skill_discoverable | coding-aegis skill is installed and its key files are accessible |
| 4a | detect_tool_direct | `detect_tool.py` run directly (outside the agent) returns the correct tool name and at least one signal |
| 4b | detect_tool_skill | `/coding-aegis detect-tool` via the agent returns the correct tool name |
| 4c | list | `/coding-aegis list --catalog modules` returns helloworld |
| 4d | show | `/coding-aegis show helloworld --catalog modules` returns name, tier, version |
| 5 | install_helloworld | `/coding-aegis install helloworld` writes rule and skill files; verified by `aegis-validate.py` (see below) |
| 5b | helloworld_responds | `/helloworld` skill responds with `Hello, World` |
| 6 | uninstall_helloworld | `/coding-aegis uninstall helloworld` removes all installed files cleanly |

The skill is the product. Every agent-mediated test goes through it.

Almost every task initiated by the skill should complete in less than 10 seconds. Beyond that the user experience is a problem. The time for completion is part of the success criteria — steps that take a long time are not a success, even if completed.

### Principle: exercise the real user journey

Prompts must invoke the tool's **built-in mechanisms** — never instruct the agent to bypass them. For example, Codex has a built-in `$skill-installer` skill for installing skills from GitHub. The test prompt says "Use the skill-installer to install a skill from GitHub repo X, path Y" and lets the agent invoke `$skill-installer` naturally. It does NOT call `install-skill-from-github.py` directly or copy files manually.

Similarly, phases 4–5 prompts should reference the skill by name ("Use the coding-aegis skill to list packages") rather than providing implementation details about internal scripts or directory paths.

### Phase 5 verification: validate-install

After the agent runs `/coding-aegis install helloworld`, the test verifies the result by calling `aegis-validate.py` directly (no agent round-trip):

```python
v = subprocess.run(
    [sys.executable, str(VALIDATE_SCRIPT), "helloworld",
     "--catalog", str(REPO_ROOT / "modules"), "--tool", "<tool>"],
    capture_output=True, text=True,
    cwd=str(journey["test_dir"]),
)
assert v.returncode == 0, f"validate-install failed:\n{v.stdout}\n{v.stderr}"
```

`aegis-validate.py` checks each artifact declared in `pkg.yaml`:
- **rule/agent on codex/opencode**: AGENTS.md contains `aegis:begin package=helloworld` section
- **rule/agent on other tools**: `rules/aegis--helloworld--<stem>.md` exists with `managed-by: coding-aegis` frontmatter
- **skill**: `<scope>/skills/helloworld/SKILL.md` exists

This centralises verification logic in the skill itself rather than duplicating it across five test files.

### Install mechanism preference (phase 3)

| Preference | Mechanism | When to use |
|-----------|-----------|-------------|
| **1st** | Marketplace/registry | Tool has a plugin/skill marketplace (Claude) |
| **2nd** | Built-in skill installer | Tool has an agent-mediated install mechanism (Codex `$skill-installer`) |
| **3rd** | CLI skill management | Tool has a skills CLI (Gemini `skills install`) |
| **4th** | Local file copy | Tool has NO install mechanism — last resort |

---

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
| | 5.2–5.4 | Artifacts verified | `aegis-validate.py helloworld --tool <tool>` exits 0; checks rule file (or AGENTS.md section), frontmatter, and skill dir |
| | 5.5 | helloworld skill responds | Invoking `$helloworld` / `/helloworld` returns `Hello, World` |
| **6. Uninstall helloworld Package** | 6.1 | `uninstall helloworld` skill command | No errors in output |
| | 6.2 | Installed files removed | Rule file and skill directory absent |
| **7. Full Cleanup** | 7.1 | Uninstall coding-aegis skill | CLI or file removal succeeds |
| | 7.2 | Skill no longer discoverable | Name absent from tool's skill/plugin list |
| | 7.3 | Remove marketplace/registry | CLI or file removal succeeds |
| | 7.4 | Marketplace no longer registered | Name absent from tool's marketplace list (or manifest directory absent) |
| | 7.5 | Remove test directory | `rm -rf $TEST_DIR` |
| | 7.6 | Test directory gone | `assert not test_dir.exists()` |

**Phase 3.1 — detection invocation method**: Tools whose skill is installed under a tool-specific path segment (`.claude/`, `.codex/`, `.gemini/`) use a direct bash invocation of `detect_tool.py` — no agent needed, the `path:` signal fires from `__file__`. Exception: Gemini installs to `.gemini/skills/coding-aegis/` but the `GEMINI_CLI=1` env var is only set inside a live agent subprocess, so detect_tool.py run directly returns UNKNOWN. Phase 4b (agent-mediated) confirms the tool name. See the tool's detail file for the specific path and expected signal.

**Phase 5.1 — headless install**: The install command's interactive scope picker (`AskUserQuestion`) cannot be used in headless mode. Include "to Project scope" in the prompt so the agent can complete the install without waiting for input.

**Phase 7 — teardown ordering**: Run all assertions (7.2, 7.4, 7.6) before the corresponding removal steps. Never remove the test directory before asserting that earlier cleanup steps succeeded — a failing assertion inside a deleted directory produces no output.

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
pytest tests/unit/ -v
```

### Useful flags

| Goal | pytest flag |
|------|-------------|
| Stop at first failure | `-x` |
| Re-run only last-failed | `--lf` |
| Stream agent output (disable capture) | `-s` |
| JUnit XML report (for CI) | `--junit-xml=test-report.xml` |
| Full output on failure | `--tb=long` |

---

## Prerequisites by Tool

| Tool | Binary | Auth | Notes |
|------|--------|------|-------|
| Claude Code | `claude` | `claude /login` | — |
| Codex | `codex` | `codex auth login` | Changes must be pushed to GitHub first — Codex `$skill-installer` installs from GitHub, not local paths. See [test-codex.md](test-codex.md). |
| Gemini | `gemini` | Google account | **Deferred** — free-tier quota exhausts frequently, making tests unreliable for day-to-day dev. See [test-gemini.md](test-gemini.md). |
| Cursor | `cursor-agent` | Cursor account | After `brew install cursor-cli`, run `xattr -rd com.apple.quarantine $(brew --prefix)/Caskroom/cursor-cli/<version>/` to clear macOS quarantine. See [test-cursor.md §12](test-cursor.md). |
| OpenCode | `opencode` | Provider API key | `opencode run` requires `git init` in the working directory. |
| Copilot | `copilot` | `COPILOT_GITHUB_TOKEN` or `GH_TOKEN` | From `github/copilot-cli`. No env var injected into subprocesses — path:.github signal only. Catalog commands use natural language prompts (slash-command syntax with `--catalog` flag causes binary-not-found error). |

---

## Testing Mechanics

### Timing

Any test step that takes over 10 seconds should be regarded as a bug. Do not increase the test step timeout beyond 15 seconds to work around issues, since that very likely means the agent is not well guided and flailing.

All timeouts are capped at 30 seconds. A timeout is always a bug, never a tuning knob. If a step times out, fix the root cause — wrong paths, missing files, bad tool detection — do not raise the timeout.

### Prompts are ALWAYS delivered via stdin

Every prompt to an agent is set as `input=` and passed to `subprocess.run`. Never pass prompts as positional arguments or flag values.

```python
result = run_cli(
    ["claude", "-p", "--strict-mcp-config", ...],
    prompt="You have the coding-aegis skill loaded. Execute its list command.",
    cwd=test_dir,
)
```

### Non-prompt CLI calls

Tool management commands (marketplace add, plugin install, skills link) do NOT use `prompt=`. Arguments go directly to `run_cli`:

```python
result = run_cli(
    ["claude", "plugin", "marketplace", "add", str(repo_root)],
    cwd=test_dir,
)
```

For tool-specific flags, sandbox modes, and invocation patterns see each tool's detail file.

### Debug workflow

```bash
# Stop at first failure, stream all output
pytest tests/integration/test_codex.py -v -x -s

# Re-run only last-failed tests
pytest tests/integration/ --lf

# Full output on failure
pytest tests/integration/test_codex.py -v --tb=long 2>&1 | tee /tmp/aegis-test.log
```

`pytest -x` is the standard debugging mode. Never run a slow LLM test in a tight loop — each wasted phase costs real API quota.

### Test Package

`helloworld` from `modules/optional/helloworld/`:
- 1 rule + 1 skill (both artifact types)
- In the real catalog (available after push for remote tests)
- No side effects
- Predictable content for assertions

### Quota error handling (Gemini)

Quota exhaustion calls `pytest.skip` (not `pytest.fail`) — quota exhaustion is an infrastructure constraint, not a code defect. Skipping communicates this clearly in the report.

```python
QUOTA_PATTERNS = re.compile(
    r"quota|rate.limit|RESOURCE_EXHAUSTED|429|too many requests|limit exceeded|try again later",
    re.IGNORECASE
)

def assert_no_quota_error(result, tool="agent"):
    if QUOTA_PATTERNS.search(result.output):
        pytest.skip(f"{tool} API quota exhausted — skipping remaining tests")
```

### The user journey contract is inviolable

**NEVER substitute a direct file copy, manual script execution, or any other shortcut for the tool's proper install mechanism.** A test that bypasses the install mechanism does not validate the user journey — it validates nothing useful and creates false confidence. Worse, it hides real failures that will surface in production.

If a tool's install mechanism cannot be exercised (e.g. network unavailable, tool not installed), the correct action is to **skip the test and note it explicitly** — not to substitute a workaround. A skipped test with a clear explanation is always preferable to a test that breaks the user journey contract.

---

## Coverage Matrix

| Phase | Claude | Codex | Gemini | Cursor | OpenCode | Copilot |
|-------|--------|-------|--------|--------|----------|---------|
| 1 Environment & Tool Validation | done | done | done (deferred) | done | done | done |
| 2 Marketplace / Registry Setup | done | N/A | N/A | N/A | N/A | N/A |
| 3 Install coding-aegis Skill | done | done | done (deferred) | done | done | done |
| 4 Validate coding-aegis Skill | done | done | done (deferred) | done | done | done |
| 5 Install helloworld Package | done | done | done (deferred) | done | done | done |
| 6 Uninstall helloworld Package | done | done | done (deferred) | done | done | done |
| 7 Full Cleanup | done | done | done (deferred) | done | done | done |
| Unit tests | done (27) | — | — | — | — | — |

---

## Policy

**All tests must be run before closing any task.** Do not limit testing to scripts directly touched by a change — a regression anywhere in the suite is a failure. If a test cannot be run (tool not installed, binary broken, changes not pushed), note it explicitly and get user agreement before closing.
