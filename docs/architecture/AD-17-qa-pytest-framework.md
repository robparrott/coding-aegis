# AD-17: QA Architect Proposal — pytest-based Integration Test Framework

**Date**: 2026-04-03
**Author**: QA Architect review
**Status**: Implemented — pytest suite is now the authoritative integration test framework
**Scope**: Replaces bash integration scripts with a Python/pytest framework for the 7-phase user journey tests. The bash scripts have been retired (task `97z.11`).

---

## 1. Current Approach Critique

### What the bash approach got right

The bash scripts were not frivolous. They correctly modelled an external-process integration test: every agent call goes through the real CLI, stdin piping is consistent, timeouts are enforced, and the shared harness prevents per-script divergence. The 7-phase structure maps cleanly to the spec. The `AEGIS_TEST_LOG` / `FAIL_FAST` controls are practical. This was a good starting point that hit the ceiling of what bash can cleanly express.

### Specific weaknesses addressed by this decision

**Maintainability**

The harness was ~340 lines of bash. Each tool script added 150–200 more. Logic that could be a parametrized Python function was copy-pasted: compare the three identical Phase 1 "tool authenticated" blocks. Adding a fourth tool (Cursor) meant copying the entire file structure and manually syncing any harness change. There was no mechanism to express "these three scripts share Phase 4–5 assertions" without another sourced file, which adds another indirection layer without type safety or IDE support.

The `timeout` polyfill existed because macOS does not ship GNU `timeout`. This is a maintenance liability: it does not handle the same exit codes as GNU `timeout` on Linux CI, and the three exit-code checks (124, 142, 143) showed this had already been patched reactively. Python's `subprocess.run(timeout=...)` raises `subprocess.TimeoutExpired` uniformly on all platforms.

**Debuggability**

When `assert_contains` fails, the output is: `FAIL: list — helloworld found — expected 'helloworld' not found`. There is no stack trace, no diff, no indication of which line in the script triggered it. pytest, by contrast, prints the exact file, line number, local variables at failure point, and the diff between expected and actual — without any extra tooling.

The `AEGIS_TEST_LOG` workaround (tee to file, then grep with line offsets) existed solely because bash has no structured output. A pytest run captures stdout per-test automatically and makes it accessible via `-s` or `--tb=long`.

**Assertions**

The assertion vocabulary was: `assert_contains` (regex grep), `assert_not_contains`, `assert_file_exists`, `assert_file_contains`, `assert_file_not_exists`, `assert_dir_not_exists`, `assert_json_value`, `assert_json_nonempty_array`. That is the entire set.

Missing that pytest provides natively:

- Equality with diff: `assert result["tier"] == "optional"` prints the full dict on failure, not just the mismatched field.
- Substring with context: `assert "helloworld" in output` shows the full `output` string on failure.
- Type checking: `assert isinstance(result, dict)` before accessing keys.
- Pytest approx for numeric comparisons (relevant for timing assertions).
- Custom assertion messages using `pytest.fail("message")` with structured data attached via `pytest.fail(..., pytrace=False)`.
- `assert_contains` uses case-insensitive grep — this is implicit and has already caused false passes (e.g., "ERROR" matching "no errors" check if the pattern is wrong). Explicit `in` is unambiguous.

**Portability**

`#!/usr/bin/env -S bash -l` requires GNU coreutils `env` with `-S`. macOS ships BSD `env` which gained `-S` in macOS 12.3. On older CI images (GitHub Actions `macos-11`) this shebang fails silently, producing a cryptic "No such file or directory" error against the bash binary path, not the script. Python scripts with `#!/usr/bin/env python3` work on macOS 10.15+.

The scripts used `fmt -w 68` to wrap prompt display. `fmt` is not on all Linux distros by default (it is in `util-linux` but not always installed in minimal CI containers). The `gemini_quiet` wrapper used `grep -E` with a multi-pattern expression that depends on GNU grep behavior for the `|` alternation inside `-E`. These are minor but cumulative portability taxes.

**Parallelism**

The scripts were strictly sequential within each tool. Running all three tool scripts in parallel from CI required external orchestration (parallel job matrix). There is no way to run Phase 1 of all tools in parallel, then Phase 3 of all tools in parallel, as a dependency graph — the bash process model does not support this cleanly. pytest-xdist can parallelize at the test-function level across tools with a single command: `pytest -n auto tests/integration/`.

**Reporting**

Output was ANSI-colored text to stdout. There is no machine-readable report. CI systems (GitHub Actions, Jenkins) cannot parse pass/fail counts from ANSI text reliably. `pytest` produces JUnit XML out of the box (`--junit-xml=report.xml`), which every CI platform can ingest. HTML reports via `pytest-html` require one `pip install` and one flag.

There is no timing breakdown per assertion. The elapsed time shown by `run_cli` is the wall time of the subprocess, but there is no summary of which steps were slowest. pytest's `--durations=10` flag shows the ten slowest tests in every run, making timing regressions immediately visible.

**CI integration**

The scripts exit 0/1 correctly, so CI can detect overall pass/fail. But there is no way to re-run only failed tests, because bash has no concept of test identity. pytest's `--lf` (last-failed) flag re-runs only the tests that failed in the previous run — critical for rapid iteration when one phase fails.

The `AEGIS_TEST_FAIL_FAST=1` env var is a manual mechanism that must be documented and remembered. pytest's `-x` flag does the same thing and is standard across every Python project on earth.

---

## 2. Framework Decision: pytest

**The decision is pytest.** The reasoning:

1. **The codebase is already Python.** Every script in `pkgs/bootstrap/coding-aegis/skills/coding-aegis/` is Python. `tests/test_aegis_catalog.py` is already `unittest`, which runs under pytest with zero changes. There is no new runtime dependency — Python 3 is already required. Adding `pytest` is one line in a `requirements-dev.txt`.

2. **`subprocess` is the right abstraction for CLI testing.** The integration tests are fundamentally "run a command, check its output." Python's `subprocess.run` with `timeout=`, `input=`, and `capture_output=True` is a direct, typed replacement for `run_cli`. There is no framework overhead — it is stdlib.

3. **pytest fixtures handle tool-specific setup/teardown cleanly.** The `setup_test_dir`, `link_skill`, `init_git_repo`, and `cleanup` operations that are scattered through bash `trap` blocks become pytest fixtures with `yield` and automatic scope (`session`, `module`, `function`). Tool-specific fixtures inherit from a shared base fixture.

4. **Parametrize covers multi-tool testing.** `@pytest.mark.parametrize("tool", ["claude", "codex", "gemini"])` runs the same assertion logic against all tools without copy-paste.

5. **Markers handle conditional skipping properly.** The current bash approach for "tool not installed" is `fail "codex not found in PATH"; exit 1` — this fails the run rather than skipping it. pytest's `@pytest.mark.skipif(not shutil.which("codex"), reason="codex not installed")` skips cleanly and reports it as a skip, not a failure.

**Why not bats-core**: bats-core adds structure to bash (proper TAP output, `setup`/`teardown`, `@test` blocks) but does not fix the fundamental problems: no diff output on failure, no parametrize, no cross-platform portability, still requires bash. It is the right choice for a bash-native project. This project is Python-native.

**Why not Robot Framework**: Robot Framework's keyword-driven DSL adds a layer of indirection that is not warranted here. The test logic is not complex enough to benefit from keyword abstraction, and the learning curve is higher. It excels at acceptance testing with non-technical stakeholders writing keywords — that is not this use case.

---

## 3. Implemented Architecture

### 3.1 Directory layout

```
tests/
├── test_aegis_catalog.py                # unit tests (unchanged)
├── test_aegis_lib.py                    # unit tests (unchanged)
│
└── integration/
    ├── __init__.py
    ├── conftest.py                      # Shared fixtures, CLI runner, env setup
    ├── harness.py                       # Python equivalent of lib-test-harness.sh
    ├── README.md                        # Running and configuring the suite
    ├── test_claude.py                   # Full 7-phase journey for Claude Code
    ├── test_codex.py                    # Full 7-phase journey for Codex
    ├── test_gemini.py                   # Gemini — deferred (quota; see task 97z.13)
    ├── test_cursor.py                   # Full 7-phase journey for Cursor
    └── test_opencode.py                 # Full 7-phase journey for OpenCode
```

### 3.2 `harness.py` — the Python equivalent of `lib-test-harness.sh`

This module is not a test file. It provides the `run_cli` equivalent as a function returning a structured result.

```python
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

### 3.3 Timing enforcement

For the timing budget requirement (steps should complete in under 10 seconds), a reusable helper in `harness.py` can be used:

```python
def assert_within_budget(result: CLIResult, budget_seconds: float = 10.0):
    """Fail if elapsed exceeds the UX timing budget."""
    if result.elapsed > budget_seconds:
        pytest.fail(
            f"Step took {result.elapsed:.1f}s, exceeding the {budget_seconds}s "
            f"UX budget. This is a bug, not a tuning issue."
        )
```

### 3.4 Quota error detection

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

### 3.5 Equivalent pytest flags for bash harness variables

| Bash variable | pytest equivalent |
|---------------|------------------|
| `AEGIS_TEST_FAIL_FAST=1` | `pytest -x` |
| `AEGIS_TEST_LOG=<path>` | `pytest -s 2>&1 \| tee <path>` |
| `TIMEOUT=30` | `DEFAULT_TIMEOUT` in `harness.py` |

---

## 4. Phase Mapping Table

| Phase | Step | Description | Implemented as |
|-------|------|-------------|----------------|
| 1 | 1.1 | Tool installed | `test_auth` — `shutil.which(...)` check |
| 1 | 1.2 | Tool authenticated | `test_auth` — `run_cli(..., prompt="AUTH_OK")` |
| 2 | 2.1 | Register marketplace | `test_plugin_manifest` (Claude) / skip stub (others) |
| 2 | 2.2 | Source visible | `test_plugin_manifest` |
| 3 | 3.1 | Install skill | `test_skill_files_present` / `test_skill_discoverable` |
| 3 | 3.3 | `detect_tool.py` present | `test_skill_files_present` |
| 4 | 4.1 | Tool detected correctly | `test_detect_tool_direct` |
| 4 | 4.2 | `detect-tool` skill command | `test_detect_tool_skill` |
| 4 | 4.3 | `list` skill command | `test_list` |
| 4 | 4.4 | `show` skill command | `test_show` |
| 5 | 5.1 | Install helloworld | `test_install_helloworld` |
| 5 | 5.5 | helloworld skill responds | `test_helloworld_responds` |
| 6 | 6.1 | Uninstall helloworld | `test_uninstall_helloworld` |
| 7 | All | Full cleanup | pytest fixture teardown (module-scoped) |

---

## 5. Summary of Concrete Improvements

| Problem in bash | Fix in pytest |
|-----------------|---------------|
| No diff on assertion failure | pytest shows full value diff automatically |
| Global `$LAST_OUTPUT` state | `CLIResult` value returned per call |
| `timeout` polyfill for macOS | `subprocess.run(timeout=)` — stdlib, cross-platform |
| `AEGIS_TEST_FAIL_FAST=1` custom env var | `pytest -x` |
| No machine-readable report | `--junit-xml` built in |
| No test re-run for failed tests only | `pytest --lf` |
| Copy-paste between tool scripts | Shared fixtures + per-tool test class |
| `assert_not_contains "Error"` is fragile | Explicit: `assert "Error" not in output` |
| Quota exhaustion fails the run | `pytest.skip` communicates infrastructure constraint |
| `#!/usr/bin/env -S bash -l` portability | `#!/usr/bin/env python3` — universal |
| Teardown races with `trap` + exit codes | pytest fixture teardown is reliable and ordered |
