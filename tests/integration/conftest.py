"""
conftest.py — shared pytest fixtures for coding-aegis integration tests.

Fixtures provided:
  repo_root      — Path to the repository root (session scope)
  catalog_path   — Path to pkgs/ in the repo (session scope)
  test_dir       — Fresh temp directory per test function, auto-cleaned up
  clean_env      — os.environ copy with Claude Code vars stripped
  run_cli        — The harness run_cli function (for convenience)
  timeout        — Default timeout integer
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from .harness import DEFAULT_TIMEOUT, run_cli as _run_cli

# ── Constants ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Session-scoped fixtures (computed once per pytest run) ───────────────────

@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the coding-aegis repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def catalog_path(repo_root: Path) -> Path:
    """Absolute path to the pkgs/ catalog directory."""
    return repo_root / "pkgs"


@pytest.fixture(scope="session")
def timeout() -> int:
    """Default CLI timeout in seconds."""
    return DEFAULT_TIMEOUT


# ── Function-scoped fixtures (fresh per test) ────────────────────────────────

@pytest.fixture
def test_dir() -> Generator[Path, None, None]:
    """Fresh temporary directory for each test function.

    Equivalent to ``TEST_DIR=$(mktemp -d)`` + ``trap cleanup EXIT`` in bash.
    pytest teardown runs even when tests fail, and teardown errors do not
    mask the original test failure.
    """
    d = Path(tempfile.mkdtemp(prefix="aegis-test-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def clean_env() -> dict:
    """Environment with Claude Code vars stripped.

    Mirrors the ``unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT`` at the top of
    test-codex-skill-install.sh and test-gemini-skill-install.sh.
    Claude tests should NOT use this fixture — CLAUDECODE is expected there.
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    return env


@pytest.fixture
def run_cli():
    """Expose harness.run_cli as a fixture for test functions that prefer it."""
    return _run_cli
