# QA Architect Proposal: pytest-based Integration Test Framework

**Date**: 2026-04-03
**Author**: QA Architect review
**Status**: Proposal — pending implementation
**Scope**: Replaces bash integration scripts with a Python/pytest framework for the 7-phase user journey tests. The bash scripts are retained as reference material.

---

## 1. Current Approach Critique

### What the bash approach gets right

The bash scripts are not frivolous. They correctly model an external-process integration test: every agent call goes through the real CLI, stdin piping is consistent, timeouts are enforced, and the shared harness prevents per-script divergence. The 7-phase structure maps cleanly to the spec. The `AEGIS_TEST_LOG` / `FAIL_FAST` controls are practical. This is not a bad starting point — it is a starting point that has hit the ceiling of what bash can cleanly express.

### Specific weaknesses

**Maintainability**

The harness is ~340 lines of bash. Each tool script adds 150–200 more. Logic that could be a parametrized Python function is copy-pasted: compare the three identical Phase 1 "tool authenticated" blocks. Adding a fourth tool (Cursor) means copying the entire file structure and manually syncing any harness change. There is no mechanism to express "these three scripts share Phase 4–5 assertions" without another sourced file, which adds another indirection layer without adding type safety or IDE support.

The `timeout` polyfill (lines 35–47 of `lib-test-harness.sh`) exists because macOS does not ship GNU `timeout`. This is a maintenance liability: it does not handle the same exit codes as GNU `timeout` on Linux CI, and the three exit-code checks (124, 142, 143) show this has already been patched reactively. Python's `subprocess.run(timeout=...)` raises `subprocess.TimeoutExpired` uniformly on all platforms.

**Debuggability**

When `assert_contains` fails, the output is: `FAIL: list — helloworld found — expected 'helloworld' not found`. There is no stack trace, no diff, no indication of which line in the script triggered it. To correlate a failure with the triggering code you must mentally map the description string back to the script line. pytest, by contrast, prints the exact file, line number, local variables at failure point, and the diff between expected and actual — without any extra tooling.

The `AEGIS_TEST_LOG` workaround (tee to file, then grep with line offsets) exists solely because bash has no structured output. A pytest run captures stdout per-test automatically and makes it accessible via `-s` or `--tb=long`.

**Assertions**

The assertion vocabulary is: `assert_contains` (regex grep), `assert_not_contains`, `assert_file_exists`, `assert_file_contains`, `assert_file_not_exists`, `assert_dir_not_exists`, `assert_json_value`, `assert_json_nonempty_array`. That is the entire set.

Missing that pytest provides natively:

- Equality with diff: `assert result["tier"] == "optional"` prints the full dict on failure, not just the mismatched field.
- Substring with context: `assert "helloworld" in output` shows the full `output` string on failure.
- Type checking: `assert isinstance(result, dict)` before accessing keys.
- Pytest approx for numeric comparisons (relevant for timing assertions).
- Custom assertion messages using `pytest.fail("message")` with structured data attached via `pytest.fail(..., pytrace=False)`.
- `assert_contains` uses case-insensitive grep — this is implicit and has already caused false passes (e.g., "ERROR" matching "no errors" check if the pattern is wrong). Explicit `in` is unambiguous.

**Portability**

`#!/usr/bin/env -S bash -l` requires GNU coreutils `env` with `-S`. macOS ships BSD `env` which gained `-S` in macOS 12.3. On older CI images (GitHub Actions `macos-11`) this shebang fails silently, producing a cryptic "No such file or directory" error against the bash binary path, not the script. Python scripts with `#!/usr/bin/env python3` work on macOS 10.15+.

The scripts use `fmt -w 68` to wrap prompt display (line 109, `lib-test-harness.sh`). `fmt` is not on all Linux distros by default (it is in `util-linux` but not always installed in minimal CI containers). The `gemini_quiet` wrapper uses `grep -E` with a multi-pattern expression that depends on GNU grep behavior for the `|` alternation inside `-E`. These are minor but cumulative portability taxes.

**Parallelism**

The scripts are strictly sequential within each tool. Running all three tool scripts in parallel from CI requires external orchestration (parallel job matrix). There is no way to run Phase 1 of all tools in parallel, then Phase 3 of all tools in parallel, as a dependency graph — the bash process model does not support this cleanly. pytest-xdist can parallelize at the test-function level across tools with a single command: `pytest -n auto tests/integration/`.

**Reporting**

Output is ANSI-colored text to stdout. There is no machine-readable report. CI systems (GitHub Actions, Jenkins) cannot parse pass/fail counts from ANSI text reliably. `pytest` produces JUnit XML out of the box (`--junit-xml=report.xml`), which every CI platform can ingest. HTML reports via `pytest-html` require one `pip install` and one flag.

There is no timing breakdown per assertion. The elapsed time shown by `run_cli` is the wall time of the subprocess, but there is no summary of which steps were slowest. pytest's `--durations=10` flag shows the ten slowest tests in every run, making timing regressions immediately visible.

**CI integration**

The scripts exit 0/1 correctly, so CI can detect overall pass/fail. But there is no way to re-run only failed tests, because bash has no concept of test identity. pytest's `--lf` (last-failed) flag re-runs only the tests that failed in the previous run — critical for rapid iteration when one phase fails.

The `AEGIS_TEST_FAIL_FAST=1` env var is a manual mechanism that must be documented and remembered. pytest's `-x` flag does the same thing and is standard across every Python project on earth.

---

## 2. Framework Recommendation: pytest

**The recommendation is pytest.** The reasoning:

1. **The codebase is already Python.** Every script in `pkgs/bootstrap/coding-aegis/skills/coding-aegis/` is Python. `tests/test_aegis_catalog.py` is already `unittest`, which runs under pytest with zero changes. There is no new runtime dependency — Python 3 is already required. Adding `pytest` is one line in a `requirements-dev.txt`.

2. **`subprocess` is the right abstraction for CLI testing.** The integration tests are fundamentally "run a command, check its output." Python's `subprocess.run` with `timeout=`, `input=`, and `capture_output=True` is a direct, typed replacement for `run_cli`. There is no framework overhead — it is stdlib.

3. **pytest fixtures handle tool-specific setup/teardown cleanly.** The `setup_test_dir`, `link_skill`, `init_git_repo`, and `cleanup` operations that are scattered through bash `trap` blocks become pytest fixtures with `yield` and automatic scope (`session`, `module`, `function`). Tool-specific fixtures inherit from a shared base fixture.

4. **Parametrize covers multi-tool testing.** `@pytest.mark.parametrize("tool", ["claude", "codex", "gemini"])` runs the same assertion logic against all tools without copy-paste.

5. **Markers handle conditional skipping properly.** The current bash approach for "tool not installed" is `fail "codex not found in PATH"; exit 1` — this fails the run rather than skipping it. pytest's `@pytest.mark.skipif(not shutil.which("codex"), reason="codex not installed")` skips cleanly and reports it as a skip, not a failure.

**Why not bats-core**: bats-core adds structure to bash (proper TAP output, `setup`/`teardown`, `@test` blocks) but does not fix the fundamental problems: no diff output on failure, no parametrize, no cross-platform portability, still requires bash. It is the right choice for a bash-native project. This project is Python-native.

**Why not Robot Framework**: Robot Framework's keyword-driven DSL adds a layer of indirection that is not warranted here. The test logic is not complex enough to benefit from keyword abstraction, and the learning curve is higher. It excels at acceptance testing with non-technical stakeholders writing keywords — that is not this use case.

---

## 3. Architecture Design

### 3.1 Directory layout

```
tests/
├── lib-test-harness.sh                  # RETAINED — canonical reference (do not modify)
├── test-claude-bootstrapped-skill-install.sh   # RETAINED — canonical reference
├── test-codex-skill-install.sh          # RETAINED — canonical reference
├── test-gemini-skill-install.sh         # RETAINED — canonical reference
├── gemini-test-status.md                # RETAINED — status tracking
├── test_aegis_catalog.py                # RETAINED — existing unit tests (run unchanged)
│
└── integration/
    ├── conftest.py                      # Shared fixtures, CLI runner, env setup
    ├── harness.py                       # Python equivalent of lib-test-harness.sh
    ├── test_phase1_env.py               # Phase 1: environment validation (all tools)
    ├── test_phase2_marketplace.py       # Phase 2: marketplace/registry setup
    ├── test_phase3_install_skill.py     # Phase 3: install coding-aegis skill
    ├── test_phase4_validate_skill.py    # Phase 4: validate skill commands
    ├── test_phase5_install_pkg.py       # Phase 5: install helloworld package
    ├── test_phase6_uninstall_pkg.py     # Phase 6: uninstall helloworld package
    ├── test_phase7_cleanup.py           # Phase 7: full teardown
    └── tools/
        ├── claude.py                    # Claude-specific fixtures and CLI wrappers
        ├── codex.py                     # Codex-specific fixtures and CLI wrappers
        └── gemini.py                    # Gemini-specific fixtures and CLI wrappers
```

### 3.2 `harness.py` — the Python equivalent of `lib-test-harness.sh`

This module is not a test file. It provides the `run_cli` equivalent as a function returning a structured result.

```python
# tests/integration/harness.py (illustrative — not production code)

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_TIMEOUT = 30  # seconds — timeouts are bugs, not tuning knobs

@dataclass
class CLIResult:
    output: str          # combined stdout + stderr
    exit_code: int
    elapsed: float       # wall seconds
    timed_out: bool

def run_cli(
    cmd: list[str],
    *,
    prompt: Optional[str] = None,     # piped via stdin
    cwd: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT,
    env: Optional[dict] = None,
) -> CLIResult:
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            env=env,
        )
        elapsed = time.monotonic() - start
        return CLIResult(
            output=result.stdout + result.stderr,
            exit_code=result.returncode,
            elapsed=elapsed,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return CLIResult(output="", exit_code=-1, elapsed=elapsed, timed_out=True)
```

Key differences from `run_cli` in bash:

- `timed_out` is a first-class field, not a sentinel exit code.
- `elapsed` is available for timing assertions without parsing `date +%s` output.
- `output` is a string, not a global variable — no state leaks between calls.
- The caller receives a value; no `$LAST_OUTPUT` / `$LAST_EXIT` globals.

### 3.3 `conftest.py` — shared fixtures

```python
# tests/integration/conftest.py (illustrative)

import os
import shutil
import tempfile
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT

@pytest.fixture
def test_dir():
    """Fresh temp directory for each test function. Auto-cleaned up."""
    d = tempfile.mkdtemp(prefix="aegis-test-")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)

@pytest.fixture(scope="session")
def catalog_path(repo_root):
    return repo_root / "pkgs"

@pytest.fixture
def clean_env():
    """Environment with Claude Code vars stripped (mirrors Codex/Gemini scripts)."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    return env
```

The `test_dir` fixture replaces `TEST_DIR="$(mktemp -d)"` + `trap cleanup EXIT`. pytest's fixture teardown runs even when tests fail — no `trap` needed, and teardown errors do not mask test failures (which the bash `trap` can do when `print_results` exits non-zero before cleanup completes).

### 3.4 Tool-specific fixtures

Each tool module in `tests/integration/tools/` provides a fixture for that tool's CLI invocation pattern. Example for Codex:

```python
# tests/integration/tools/codex.py (illustrative)

import pytest
import shutil
from pathlib import Path
from tests.integration.harness import run_cli, CLIResult, DEFAULT_TIMEOUT

pytestmark = pytest.mark.skipif(
    not shutil.which("codex"),
    reason="codex not installed"
)

SKILL_INSTALL_DIR = Path.home() / ".codex" / "skills" / "coding-aegis"

def codex_exec(prompt: str, *, cwd: Path, sandbox: str = "read-only",
               timeout: int = DEFAULT_TIMEOUT, env=None) -> CLIResult:
    return run_cli(
        ["codex", "exec", "--ephemeral", "-s", sandbox, "-o", "/dev/stdout"],
        prompt=prompt,
        cwd=cwd,
        timeout=timeout,
        env=env,
    )

@pytest.fixture(scope="module")
def codex_skill_installed(repo_root, clean_env):
    """Install coding-aegis skill via $skill-installer; uninstall after module."""
    github_repo = "robparrott/coding-aegis"
    skill_path = "pkgs/bootstrap/coding-aegis/skills/coding-aegis"
    with tempfile.TemporaryDirectory() as d:
        result = codex_exec(
            f"$skill-installer install --repo {github_repo} --path {skill_path}",
            cwd=Path(d),
            sandbox="danger-full-access",
            timeout=60,
            env=clean_env,
        )
        assert not result.timed_out, "skill-installer timed out"
        yield SKILL_INSTALL_DIR
    shutil.rmtree(SKILL_INSTALL_DIR, ignore_errors=True)
```

The `scope="module"` on `codex_skill_installed` means the skill is installed once for the entire Phase 4–6 test module, not re-installed per test function. This mirrors what the bash script does (install once, run multiple assertions) without requiring careful ordering of `bash` statements.

### 3.5 How the 7 phases map to pytest test functions

See Section 4 (phase mapping table) for the complete mapping. The structural principle:

- Each phase becomes a test file (`test_phase1_env.py`, etc.).
- Within a file, each numbered step (1.1, 1.2, ...) becomes a test function.
- Steps that share setup are grouped in a class with a class-scoped fixture providing the shared state.
- Tool-specific variants are handled via parametrize or separate tool-prefixed functions.

```python
# tests/integration/test_phase1_env.py (illustrative)

import shutil
import pytest
from tests.integration.harness import run_cli

@pytest.mark.parametrize("tool_cmd", [
    pytest.param("claude", marks=pytest.mark.skipif(not shutil.which("claude"), reason="claude not installed")),
    pytest.param("codex",  marks=pytest.mark.skipif(not shutil.which("codex"),  reason="codex not installed")),
    pytest.param("gemini", marks=pytest.mark.skipif(not shutil.which("gemini"), reason="gemini not installed")),
])
def test_tool_installed(tool_cmd):
    """Phase 1.1 — tool binary is on PATH."""
    assert shutil.which(tool_cmd) is not None

def test_claude_authenticated():
    """Phase 1.2 — Claude auth check."""
    result = run_cli(["claude", "-p", "--strict-mcp-config",
                      "--mcp-config", '{"mcpServers":{}}'],
                     prompt="Reply with exactly: AUTH_OK")
    assert not result.timed_out, f"auth check timed out after {result.elapsed:.1f}s"
    assert "AUTH_OK" in result.output, f"expected AUTH_OK, got:\n{result.output}"
```

Note how the failure message now shows the full output automatically via pytest's assertion introspection — no `fail "... expected 'AUTH_OK' not found"` string construction required.

### 3.6 Timeout enforcement

`subprocess.run(timeout=...)` raises `subprocess.TimeoutExpired` (a subclass of `Exception`) when the process does not complete in time. The `run_cli` wrapper catches this and sets `timed_out=True` on the result. Tests check `assert not result.timed_out` before content assertions. This is clean, uniform, and does not depend on sentinel exit codes.

For the timing budget requirement (steps should complete in under 10 seconds), a reusable assertion helper can be added to `harness.py`:

```python
def assert_within_budget(result: CLIResult, budget_seconds: float = 10.0):
    """Fail if elapsed exceeds the UX timing budget."""
    if result.elapsed > budget_seconds:
        pytest.fail(
            f"Step took {result.elapsed:.1f}s, exceeding the {budget_seconds}s "
            f"UX budget. This is a bug, not a tuning issue."
        )
```

### 3.7 Quota error detection

The bash `assert_no_quota_error` pattern becomes a helper used after Gemini calls:

```python
QUOTA_PATTERNS = re.compile(
    r"quota|rate.limit|RESOURCE_EXHAUSTED|429|too many requests|limit exceeded|try again later",
    re.IGNORECASE
)

def assert_no_quota_error(result: CLIResult, tool: str = "agent"):
    if QUOTA_PATTERNS.search(result.output):
        pytest.skip(f"{tool} API quota exhausted — skipping remaining tests")
```

Using `pytest.skip` instead of `pytest.fail` is deliberate: quota exhaustion is an infrastructure constraint, not a code defect. Skipping communicates this clearly in the report.

### 3.8 Logging

pytest captures stdout/stderr per test automatically. Running with `-s` disables capture and streams to the terminal (equivalent to not redirecting to `AEGIS_TEST_LOG`). Running with `--tb=long` shows full local variable state at assertion failure.

For the equivalent of `AEGIS_TEST_LOG` (full agent output without 50-line truncation), use:

```bash
pytest tests/integration/ -s --tb=long 2>&1 | tee /tmp/aegis-test.log
```

No custom logging infrastructure is needed.

### 3.9 Fail-fast

```bash
pytest tests/integration/ -x          # stop at first failure
pytest tests/integration/ --lf        # re-run only last-failed tests
pytest tests/integration/ -x --lf     # re-run failed, stop at first new failure
```

These are standard pytest flags known to every Python developer. No documentation of `AEGIS_TEST_FAIL_FAST=1` is needed.

---

## 4. Phase Mapping Table

| Phase | Step | Description | Current bash | Proposed pytest |
|-------|------|-------------|--------------|-----------------|
| 1 | 1.1 | Tool installed | `command -v <tool>` + manual pass/fail | `test_tool_installed[claude/codex/gemini]` — `@pytest.mark.parametrize` |
| 1 | 1.2 | Tool authenticated | `CLI_PROMPT="...AUTH_OK" run_cli` + `assert_contains` | `test_claude_authenticated()` — `run_cli(..., prompt=...) → assert "AUTH_OK" in result.output` |
| 1 | 1.3 | Working directory initialized | Inline `git -C "$TEST_DIR" init -q` | `test_dir` fixture runs `subprocess.run(["git", "init"], cwd=test_dir)` |
| 2 | 2.1 | Register marketplace | `run_cli "marketplace add" claude plugin marketplace add "$REPO_ROOT"` | `test_marketplace_add()` in `test_phase2_marketplace.py` |
| 2 | 2.2 | Source visible | `run_cli "marketplace list"` + `assert_contains` | `test_marketplace_visible()` — `assert marketplace_name in result.output` |
| 3 | 3.1 | Install skill | Tool-specific install command | `test_install_coding_aegis[<tool>]` — parametrized, tool fixture handles mechanism |
| 3 | 3.2 | Skill discoverable | `run_cli "list/plugin list"` + `assert_contains` | `test_skill_discoverable[<tool>]` — `assert "coding-aegis" in result.output` |
| 3 | 3.3 | `detect_tool.py` present | `assert_file_exists "$CODEX_SKILL_DIR/detect_tool.py"` | `test_detect_tool_py_present()` — `assert (skill_dir / "detect_tool.py").exists()` |
| 4 | 4.1 | Tool detected correctly | `python3 detect_tool.py` + `assert_json_value` | `test_detect_tool_direct[codex]` — `json.loads(subprocess.run(...).stdout)` + plain dict assertions |
| 4 | 4.2 | `detect-tool` skill command | Agent prompt + `assert_contains "claude\|gemini"` | `test_detect_tool_skill[<tool>]` — `assert tool_name in result.output` |
| 4 | 4.3 | `list` skill command | Agent prompt + `assert_contains "helloworld"` | `test_skill_list[<tool>]` — `assert "helloworld" in result.output` |
| 4 | 4.4 | `show` skill command | Agent prompt + 3× `assert_contains` | `test_skill_show[<tool>]` — `assert "helloworld" in output; assert "optional" in output; assert "1.0.0" in output` |
| 5 | 5.1 | Install helloworld | Agent prompt + broad `assert_contains` | `test_install_helloworld[<tool>]` |
| 5 | 5.2 | Rule file present | `assert_file_exists "$RULE_FILE"` | `assert rule_file.exists()` — `rule_file` computed from `test_dir` fixture |
| 5 | 5.3 | Rule frontmatter | 3× `assert_file_contains` | `text = rule_file.read_text(); assert "managed-by: coding-aegis" in text` (3 assertions, all visible on failure) |
| 5 | 5.4 | Skill file present | `assert_file_exists "$SCOPE_DIR/skills/helloworld/SKILL.md"` | `assert (scope_dir / "skills/helloworld/SKILL.md").exists()` |
| 5 | 5.5 | helloworld skill responds | Agent prompt + `assert_contains "Hello, World"` | `test_helloworld_responds[<tool>]` — `assert "Hello, World" in result.output` |
| 6 | 6.1 | Uninstall helloworld | Agent prompt + `assert_not_contains "Error"` | `test_uninstall_helloworld[<tool>]` — `assert not any(e in output for e in ["Error", "not found"])` |
| 6 | 6.2 | Installed files removed | `assert_file_not_exists` + `assert_dir_not_exists` | `assert not rule_file.exists(); assert not skill_dir.exists()` |
| 7 | 7.1 | Uninstall coding-aegis | Tool-specific uninstall command | `test_uninstall_coding_aegis[<tool>]` — in fixture teardown or explicit test |
| 7 | 7.2 | Skill no longer discoverable | `assert_not_contains` on list output | `assert "coding-aegis" not in result.output` |
| 7 | 7.3 | Remove marketplace | Tool-specific remove command | `test_remove_marketplace[claude]` — only Claude has a marketplace |
| 7 | 7.4 | Marketplace not registered | `assert_not_contains` on marketplace list | `assert marketplace_name not in result.output` |
| 7 | 7.5 | Remove test directory | `rm -rf "$TEST_DIR"` | Automatic — `test_dir` fixture teardown via `shutil.rmtree` |
| 7 | 7.6 | Test directory gone | `assert_dir_not_exists "$TEST_DIR"` | `assert not test_dir.exists()` — checked in fixture teardown |

---

## 5. What Stays the Same

The bash scripts are not deleted. They serve three purposes that the new framework does not replace:

1. **Canonical reference implementation.** When there is ambiguity about how a tool's CLI should be invoked (flags, stdin piping, sandbox mode), the bash script is the authoritative answer. The Python harness is derived from it.

2. **Manual debugging tool.** `AEGIS_TEST_FAIL_FAST=1 AEGIS_TEST_LOG=/tmp/aegis-test.log tests/test-codex-skill-install.sh` remains the fastest way to run a single tool's full journey interactively and inspect raw agent output.

3. **CI fallback.** If pytest cannot be installed in an environment (stripped Docker image, restricted CI runner), the bash scripts can still run. They are self-contained.

The `tests/test_aegis_catalog.py` file runs unchanged under pytest. It is already the correct pattern for unit testing Python scripts via `subprocess`. No migration is needed.

---

## 6. Migration Path

### Guiding principle: additive only

Add `tests/integration/` alongside the existing bash scripts. Do not modify any existing test file. Declare success when the pytest suite covers the same phases as the bash scripts and CI runs both.

### Step 1: Infrastructure (no tests yet)

Create `tests/integration/conftest.py` and `tests/integration/harness.py` with the fixtures and `run_cli` wrapper described in Section 3. Add `pytest` and `pytest-html` to `requirements-dev.txt` (or equivalent). Verify `pytest tests/integration/` runs with zero tests collected and zero errors.

### Step 2: Phase 1 — environment validation (all tools)

Port `test_tool_installed` and `test_tool_authenticated` for all three tools. These are the simplest tests: no agent calls, no file I/O, fast feedback. Validate that `pytest.mark.skipif` works correctly when a tool is absent.

This is the right place to validate the `assert_within_budget` helper and confirm timing assertions work.

### Step 3: Claude — Phases 2–7 (full journey)

Claude is the most stable tool. Port the Claude script first. At this point you will discover any gaps in the fixture design (test_dir scoping, catalog symlinking, `--dangerously-skip-permissions` flag handling) before porting the other tools.

The teardown ordering note in `testing-spec.md` (Phase 7 — assert before remove) is implemented by ordering the test functions within `test_phase7_cleanup.py`. pytest executes functions in file order by default.

### Step 4: Codex — Phases 3–7

Codex differs from Claude in three ways: `danger-full-access` sandbox for install, `workspace-write` sandbox for uninstall, and the `AGENTS.md`-based rule delivery. These map to different fixture parameters. The existing `test_aegis_catalog.py` tests for `TestInstallPrepCodex` and `TestUninstallPrep` already cover the catalog-level behavior; the integration tests only need to cover the agent-mediated journey.

### Step 5: Gemini — Phases 3–7, with quota handling

Gemini is last because it is the least stable (quota issues, `keytar` noise, `gemini_quiet` wrapper). By the time Gemini is ported, the fixture patterns are mature.

The `gemini_quiet` wrapper (filtering `keytar` warnings) becomes a Python function in `tests/integration/tools/gemini.py` that post-processes `result.output` before returning it. The quota guard uses `pytest.skip` as described in Section 3.7.

### Step 6: CI integration

Add a GitHub Actions job (or equivalent) that runs:

```bash
pip install pytest pytest-html
pytest tests/ --junit-xml=test-report.xml --html=test-report.html -v
```

This runs both the existing `test_aegis_catalog.py` unit tests and the new integration tests in one command. The JUnit XML is consumed by the CI platform for pass/fail reporting and trend tracking.

### Step 7: Cursor (future)

When the Cursor test is built (`test-cursor-skill-install.sh` is currently TBD), implement it directly in pytest rather than bash. At that point the bash precedent for Cursor never exists, and the new tool is native to the framework from the start.

---

## Summary of concrete improvements

| Problem in bash | Fix in pytest |
|-----------------|---------------|
| No diff on assertion failure | pytest shows full value diff automatically |
| Global `$LAST_OUTPUT` state | `CLIResult` value returned per call |
| `timeout` polyfill for macOS | `subprocess.run(timeout=)` — stdlib, cross-platform |
| `AEGIS_TEST_FAIL_FAST=1` custom env var | `pytest -x` |
| No machine-readable report | `--junit-xml` built in |
| No test re-run for failed tests only | `pytest --lf` |
| Copy-paste between tool scripts | `@pytest.mark.parametrize` + shared fixtures |
| `assert_not_contains "Error"` is fragile (case-insensitive, substring) | Explicit: `assert "Error" not in output` |
| Quota exhaustion fails the run | `pytest.skip` communicates infrastructure constraint |
| `#!/usr/bin/env -S bash -l` portability | `#!/usr/bin/env python3` — universal |
| Teardown races with `trap` + exit codes | pytest fixture teardown is reliable and ordered |
