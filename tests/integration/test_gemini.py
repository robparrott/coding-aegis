"""
test_gemini.py — Full 7-phase integration test for Google Gemini CLI.

Ports tests/test-gemini-skill-install.sh to pytest.

Uses Pattern 1: a single TestGeminiJourney class with a class-scoped journey
fixture. Key Gemini differences from the Claude and Codex tests:

  - No marketplace (Phase 2 N/A) — Gemini uses ``gemini skills link`` directly.
  - Skill install via ``gemini skills link <path> --scope user --consent``.
  - Skill discovery via ``gemini skills list``.
  - Agent prompts via ``gemini -m gemini-3-flash-preview -o text --yolo`` with prompt
    passed via stdin.
  - CLAUDECODE / CLAUDE_CODE_ENTRYPOINT are unset (clean_env built inline) so
    detect_tool.py returns "gemini" when invoked through the agent.
  - Rules written to .gemini/rules/, skills to .gemini/skills/ (confirmed 2026-04-17).
  - Quota errors trigger pytest.skip (not fail) via assert_no_quota_error.
  - TIMEOUT_LONG = 120s — Gemini retries internally; steps can take 60-90s
    under quota pressure.

Phase 4a (detect_tool.py direct run) does NOT assert tool=="gemini" because the
GEMINI_CLI=1 env var is only set when the Gemini agent invokes the script. When
run directly from the test process, the tool detection is environment-dependent.
Only the structural JSON output (keys present) is asserted for phase 4a.

Run:
    pytest tests/integration/test_gemini.py -v
    pytest tests/integration/test_gemini.py -v -s    # stream agent output
    pytest tests/integration/test_gemini.py -v -x    # stop at first failure
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .harness import (
    DEFAULT_TIMEOUT,
    assert_no_quota_error,
    assert_no_timeout,
    run_cli,
    warn_if_slow,
)

# ── Skip entire module if gemini is not on PATH ──────────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("gemini"),
    reason="gemini not installed / not on PATH",
)

# ── Constants ─────────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-3-flash-preview"
SKILL_PATH = "pkgs/bootstrap/coding-aegis/skills/coding-aegis"
TIMEOUT_LONG = 120  # Gemini retries internally; each step can take 60-90s

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_SCRIPT = REPO_ROOT / "pkgs/bootstrap/coding-aegis/skills/coding-aegis/aegis-validate.py"


def _gemini_prompt(*extra_flags) -> list:
    """Return the base gemini agent prompt command list."""
    return ["gemini", "-m", GEMINI_MODEL, "-o", "text", "--yolo"] + list(extra_flags)


# ── Test class ────────────────────────────────────────────────────────────────


class TestGeminiJourney:
    """
    Single class covering all phases of the Gemini CLI integration journey.

    The class-scoped journey fixture links the coding-aegis skill once (setup)
    and unlinks it after all tests (teardown).
    """

    @pytest.fixture(autouse=True, scope="class")
    def journey(self, tmp_path_factory, repo_root):
        """Class-scoped fixture owning setup and teardown for the full journey.

        SETUP:
          - Builds a clean env without Claude Code vars leaking in.
          - Resolves the skill_dir from the repo root.
          - Creates a shared temporary test directory with git init.
          - Catalog fetched from GitHub by ensure_catalog() on first agent command.
          - Links the coding-aegis skill via ``gemini skills link``.
          - Asserts "coding-aegis" appears in ``gemini skills list``.
          - Pre-creates .gemini/rules and .gemini/skills directories.

        TEARDOWN:
          - Best-effort helloworld uninstall (if helloworld_installed is True).
          - Best-effort coding-aegis skill unlink.
          - Temp dir cleanup handled automatically by tmp_path_factory.
        """
        # Build a clean env without Claude Code vars leaking in
        clean_env = os.environ.copy()
        clean_env.pop("CLAUDECODE", None)
        clean_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        state = {}
        state["repo_root"] = repo_root
        state["skill_dir"] = repo_root / SKILL_PATH
        state["test_dir"] = tmp_path_factory.mktemp("gemini-journey")
        state["clean_env"] = clean_env
        state["helloworld_installed"] = False

        test_dir: Path = state["test_dir"]
        skill_dir: Path = state["skill_dir"]

        # git init the test directory
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # Phase 3: link the coding-aegis skill
        result = run_cli(
            ["gemini", "skills", "link", str(skill_dir), "--scope", "user", "--consent"],
            env=clean_env,
        )
        assert_no_timeout(result, "skills link (setup)")
        # skills list to confirm coding-aegis is visible
        list_result = run_cli(
            ["gemini", "skills", "list"],
            env=clean_env,
        )
        assert "coding-aegis" in list_result.stdout, (
            f"coding-aegis not found in skills list after link:\n{list_result.stdout[:2000]}"
        )

        # Pre-create .gemini directories so the agent can write to them
        scope_dir = test_dir / ".gemini"
        (scope_dir / "rules").mkdir(parents=True, exist_ok=True)
        (scope_dir / "skills").mkdir(parents=True, exist_ok=True)

        yield state

        # ── TEARDOWN ──────────────────────────────────────────────────────────
        # Best-effort helloworld uninstall
        if state.get("helloworld_installed"):
            run_cli(
                _gemini_prompt(),
                prompt="/coding-aegis uninstall helloworld",
                cwd=test_dir,
                timeout=TIMEOUT_LONG,
                env=clean_env,
            )

        # Best-effort coding-aegis skill unlink
        run_cli(
            ["gemini", "skills", "uninstall", "coding-aegis", "--scope", "user"],
            env=clean_env,
        )

        # Temp dir is cleaned automatically by tmp_path_factory.

    # ── Phase 1: Environment & Tool Validation ────────────────────────────

    def test_phase1_auth(self, journey):
        """Phase 1 — gemini can authenticate and respond."""
        result = run_cli(
            _gemini_prompt(),
            prompt="Reply with exactly: AUTH_OK",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "auth check")
        warn_if_slow(result, label="auth check")
        assert_no_quota_error(result, "gemini")
        assert "AUTH_OK" in result.stdout, (
            f"Expected AUTH_OK in output, got:\n{result.stdout[:2000]}"
        )

    # ── Phase 2: No marketplace ───────────────────────────────────────────

    def test_phase2_no_marketplace(self, journey):
        """Phase 2 — Gemini CLI has no plugin marketplace; phase not applicable."""
        pytest.skip("Gemini CLI has no plugin marketplace; phase 2 not applicable")

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_linked(self, journey):
        """Phase 3 — coding-aegis appears in gemini skills list."""
        result = run_cli(
            ["gemini", "skills", "list"],
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skills list")
        assert "coding-aegis" in result.stdout, (
            f"Expected 'coding-aegis' in skills list:\n{result.stdout[:2000]}"
        )

    # ── Phase 4: Validate coding-aegis skill ──────────────────────────────

    def test_phase4a_detect_tool_direct(self, journey):
        """Phase 4a — detect_tool.py run directly returns valid JSON with tool and signals keys.

        Note: GEMINI_CLI=1 is only set when the Gemini agent invokes the script.
        When run directly from the test process, the tool field may be any value
        (e.g. "unknown" or "claude"). Only structural validity is asserted here.
        """
        detect_tool_path = journey["skill_dir"] / "detect_tool.py"
        result = run_cli(
            ["python3", str(detect_tool_path)],
        )
        assert_no_timeout(result, "detect_tool.py direct")
        # Parse the JSON block from stdout (may have python warnings before it)
        json_start = result.stdout.find("{")
        assert json_start != -1, (
            f"No JSON in detect_tool.py output:\n{result.stdout}"
        )
        data = json.loads(result.stdout[json_start:])
        assert "tool" in data, (
            f"detect_tool.py: expected 'tool' key in JSON output:\n{data}"
        )
        assert "signals" in data, (
            f"detect_tool.py: expected 'signals' key in JSON output:\n{data}"
        )

    def test_phase4b_detect_tool_skill(self, journey):
        """Phase 4b — /coding-aegis detect-tool via agent reports gemini + signals.

        The Gemini agent sets GEMINI_CLI=1, so detect_tool.py returns tool='gemini'.
        Uses TIMEOUT_LONG — Gemini retries internally under quota pressure.
        """
        result = run_cli(
            _gemini_prompt(),
            prompt="/coding-aegis detect-tool",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect-tool skill")
        warn_if_slow(result, label="detect-tool skill")
        assert_no_quota_error(result, "gemini")
        assert "gemini" in result.stdout.lower(), (
            f"detect-tool: expected 'gemini' in output:\n{result.stdout[:2000]}"
        )
        assert any(sig in result.stdout.lower() for sig in ("env:", "path:")), (
            f"detect-tool: expected at least one signal (env: or path:) in output:\n"
            f"{result.stdout[:2000]}"
        )

    def test_phase4c_list(self, journey):
        """Phase 4c — /coding-aegis list shows helloworld."""
        result = run_cli(
            _gemini_prompt(),
            prompt="/coding-aegis list",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill list")
        warn_if_slow(result, label="skill list")
        assert_no_quota_error(result, "gemini")
        assert "helloworld" in result.stdout.lower(), (
            f"list: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )

    def test_phase4d_show(self, journey):
        """Phase 4d — /coding-aegis show helloworld returns name, tier, version."""
        result = run_cli(
            _gemini_prompt(),
            prompt="/coding-aegis show helloworld",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill show")
        warn_if_slow(result, label="skill show")
        assert_no_quota_error(result, "gemini")
        output_lower = result.stdout.lower()
        assert "helloworld" in output_lower, (
            f"show: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )
        assert "optional" in output_lower, (
            f"show: expected 'optional' (tier) in output:\n{result.stdout[:2000]}"
        )
        assert "1.0.0" in result.stdout, (
            f"show: expected '1.0.0' (version) in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 5: Install & verify helloworld ──────────────────────────────

    def test_phase5_install_helloworld(self, journey):
        """Phase 5 — /coding-aegis install helloworld writes rule and skill files."""
        result = run_cli(
            _gemini_prompt(),
            prompt="/coding-aegis install helloworld to Project scope",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "install helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="install helloworld")
        assert_no_quota_error(result, "gemini")
        assert any(kw in result.stdout.lower() for kw in (
            "install", "aegis--helloworld", "wrote", "created"
        )), f"install: expected activity in output:\n{result.stdout[:2000]}"

        # Verify installation via validate-install
        v = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), "helloworld",
             "--catalog", str(REPO_ROOT / "pkgs"), "--tool", "gemini"],
            capture_output=True, text=True,
            cwd=str(journey["test_dir"]),
        )
        assert v.returncode == 0, (
            f"validate-install failed:\n{v.stdout}\n{v.stderr}"
        )

        # Mark installed so teardown knows to attempt cleanup
        journey["helloworld_installed"] = True

    def test_phase5b_helloworld_responds(self, journey):
        """Phase 5b — /helloworld skill returns 'Hello, World'."""
        result = run_cli(
            _gemini_prompt(),
            prompt="/helloworld",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "invoke helloworld")
        warn_if_slow(result, label="invoke helloworld")
        assert_no_quota_error(result, "gemini")
        assert "Hello, World" in result.stdout, (
            f"helloworld skill: expected 'Hello, World' in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 6: Uninstall helloworld ─────────────────────────────────────

    def test_phase6_uninstall_helloworld(self, journey):
        """Phase 6 — /coding-aegis uninstall helloworld removes installed files."""
        result = run_cli(
            _gemini_prompt(),
            prompt="/coding-aegis uninstall helloworld",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "uninstall helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="uninstall helloworld")
        assert_no_quota_error(result, "gemini")
        assert not any(kw in result.stdout for kw in ("not installed", "not found", "Error")), (
            f"uninstall: unexpected error in output:\n{result.stdout[:2000]}"
        )

        # Verify rule file was removed
        rule_file = (
            journey["test_dir"] / ".gemini" / "rules" / "aegis--helloworld--helloworld.md"
        )
        assert not rule_file.exists(), (
            f"Rule file still present after uninstall: {rule_file}"
        )

        # Verify skill directory was removed
        skill_dir = journey["test_dir"] / ".gemini" / "skills" / "helloworld"
        assert not skill_dir.exists(), (
            f"Skill dir still present after uninstall: {skill_dir}"
        )

        # Mark as uninstalled so teardown does not attempt a redundant uninstall
        journey["helloworld_installed"] = False
