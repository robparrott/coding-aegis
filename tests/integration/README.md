# Integration Tests

pytest-based integration tests for coding-aegis. Ports the 7-phase user journey
from the bash scripts in `tests/` to a Python/pytest framework.

Reference design: [AD-17: QA pytest Framework](../../docs/architecture/AD-17-qa-pytest-framework.md)

## Prerequisites

```bash
pip install pytest
# Optional: richer HTML reports
pip install pytest-html
```

## Running tests

```bash
# From repo root — run all integration tests
python3 -m pytest tests/integration/ -v

# Run only Claude tests
python3 -m pytest tests/integration/test_claude.py -v

# Stream agent output (disable capture)
python3 -m pytest tests/integration/test_claude.py -v -s

# Stop at first failure
python3 -m pytest tests/integration/test_claude.py -v -x

# Re-run only last-failed tests
python3 -m pytest tests/integration/ --lf

# JUnit XML report (for CI)
python3 -m pytest tests/integration/ --junit-xml=test-report.xml

# HTML report
python3 -m pytest tests/integration/ --html=test-report.html
```

## pytest configuration

Add this to `pyproject.toml` (or create a `pytest.ini` at the repo root):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v"
```

Or use a minimal `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v
```

## File layout

```
tests/integration/
├── __init__.py          # package marker
├── conftest.py          # shared fixtures (repo_root, test_dir, clean_env, run_cli)
├── harness.py           # CLIResult dataclass, run_cli(), assert helpers
├── test_claude.py       # full 7-phase journey for Claude Code
├── test_codex.py        # full 7-phase journey for Codex
├── test_cursor.py       # full 7-phase journey for Cursor
├── test_gemini.py       # Gemini — deferred (quota; see task 97z.13)
├── test_opencode.py     # full 7-phase journey for OpenCode
└── README.md            # this file
```

## Key design decisions

- `CLIResult` has `.stdout` (combined stdout+stderr), `.returncode`, `.elapsed`, `.timed_out`.
  `.output` is an alias for `.stdout` for compatibility.
- Tool availability is checked with `pytest.mark.skipif(not shutil.which(...))` — a missing tool
  is a skip, not a failure.
- `assert_no_quota_error` calls `pytest.skip` (not `pytest.fail`) because quota exhaustion is
  an infrastructure constraint, not a code defect.
- Timing: `warn_if_slow` emits a warning at 15s; it does not fail the test.
- The `claude_ctx` fixture is module-scoped so all phases share one temp directory.
  Fixture teardown handles cleanup even when tests fail.
- `--catalog modules` is passed explicitly to list/show/install prompts to prevent workspace scan.
- `--dangerously-skip-permissions` is passed only for write operations (Phases 5–6).

## Equivalent pytest flags for bash harness variables

| Bash variable | pytest equivalent |
|---------------|------------------|
| `AEGIS_TEST_FAIL_FAST=1` | `pytest -x` |
| `AEGIS_TEST_LOG=<path>` | `pytest -s 2>&1 \| tee <path>` |
| `TIMEOUT=30` | `DEFAULT_TIMEOUT` in `harness.py` |
