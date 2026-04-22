"""
harness.py — Python equivalent of tests/lib-test-harness.sh

Provides CLIResult and run_cli for integration tests.
Not a test file; imported by test modules and conftest.py.
"""
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Default timeout for most CLI steps (seconds).
# Per testing-spec.md: timeouts are bugs, not tuning knobs.
DEFAULT_TIMEOUT = 30

# Patterns that indicate API quota / rate-limit exhaustion.
QUOTA_PATTERN = re.compile(
    r"quota|rate.limit|RESOURCE_EXHAUSTED|429|too many requests|limit exceeded|try again later",
    re.IGNORECASE,
)

# Gemini CLI emits "Attempt N failed: ... Retrying after Xms..." for transient
# quota errors it retries internally.  These lines contain quota-matching text
# but do NOT indicate a terminal failure — the call may still succeed.
# We strip them before quota-checking so transient retries don't cause false skips.
_RETRY_LINE = re.compile(r"Retrying after \d+ms", re.IGNORECASE)


@dataclass
class CLIResult:
    """Result of a single CLI subprocess invocation."""

    stdout: str          # combined stdout + stderr
    returncode: int
    elapsed: float       # wall-clock seconds
    timed_out: bool = False

    # Alias for compatibility with code that uses result.output
    @property
    def output(self) -> str:
        return self.stdout


def run_cli(
    cmd: list,
    *,
    prompt: Optional[str] = None,
    cwd: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT,
    env: Optional[dict] = None,
) -> "CLIResult":
    """Run *cmd* as a subprocess and return a CLIResult.

    Parameters
    ----------
    cmd:
        Command and arguments (no shell expansion).
    prompt:
        If set, piped to the process via stdin (equivalent to ``CLI_PROMPT``).
    cwd:
        Working directory for the subprocess.
    timeout:
        Seconds before the process is killed (raises TimeoutExpired, caught here).
    env:
        Environment dict. If None, the current process environment is inherited.
    """
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            env=env,
        )
        elapsed = time.monotonic() - start
        combined = proc.stdout + proc.stderr
        return CLIResult(
            stdout=combined,
            returncode=proc.returncode,
            elapsed=elapsed,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return CLIResult(
            stdout="",
            returncode=-1,
            elapsed=elapsed,
            timed_out=True,
        )


# ── Assertion helpers ────────────────────────────────────────────────────────


def assert_no_timeout(result: CLIResult, description: str = "step") -> None:
    """Raise AssertionError if the result timed out."""
    assert not result.timed_out, (
        f"{description} timed out after {result.elapsed:.1f}s "
        f"(timeout is a bug, not a tuning knob)"
    )


def warn_if_slow(result: CLIResult, budget_seconds: float = 15.0, label: str = "step") -> None:
    """Emit a warning (not a failure) if elapsed exceeds the UX budget.

    Per testing-spec.md: steps taking over 10s are a UX problem.
    We warn at 15s to give a safety margin without failing fast.
    """
    import warnings

    if result.elapsed > budget_seconds:
        warnings.warn(
            f"{label} took {result.elapsed:.1f}s, exceeding the {budget_seconds}s "
            "UX budget. Investigate slow agent response.",
            stacklevel=2,
        )


def assert_no_quota_error(result: CLIResult, tool: str = "agent") -> None:
    """Skip (not fail) if the output contains a terminal quota / rate-limit error.

    Uses pytest.skip so the report reflects an infrastructure constraint,
    not a code defect.

    Transient retry lines emitted by the Gemini CLI
    ("Attempt N failed: ... Retrying after Xms...") are stripped before
    checking, so a step that eventually succeeded despite internal retries
    is not incorrectly skipped.
    """
    import pytest  # imported here to avoid hard dependency outside pytest

    terminal_output = "\n".join(
        line for line in result.stdout.splitlines()
        if not _RETRY_LINE.search(line)
    )
    if QUOTA_PATTERN.search(terminal_output):
        pytest.skip(f"{tool} API quota exhausted — skipping remaining tests")
