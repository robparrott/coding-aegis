"""
test_gemini.py — Full 7-phase integration test for Google Gemini CLI.

Ports tests/test-gemini-skill-install.sh to pytest.

Uses Pattern 1: a single TestGeminiJourney class with a class-scoped journey
fixture. Key Gemini differences from the Claude and Codex tests:

  - No marketplace (Phase 2 N/A) — Gemini uses ``gemini skills install`` from GitHub.
  - Skill install via ``gemini skills install <git-url> --path <path> --scope workspace --consent``.
  - The skill is COPIED (not linked) to .gemini/skills/coding-aegis/ in the test dir.
  - Skill discovery via ``gemini skills list``.
  - Agent prompts via ``gemini -m gemini-3-flash-preview -o text --yolo`` with prompt
    passed via stdin.
  - CLAUDECODE / CLAUDE_CODE_ENTRYPOINT are unset (clean_env built inline) so
    detect_tool.py returns "gemini" when invoked through the agent.
  - Rules written to .gemini/rules/, skills to .gemini/skills/ (confirmed 2026-04-17).
  - Quota errors trigger pytest.skip (not fail) via assert_no_quota_error.
  - TIMEOUT_LONG = 120s — Gemini retries internally; steps can take 60-90s
    under quota pressure.

IMPORTANT: ``gemini skills install`` fetches from GitHub, so changes must be pushed
to the remote before running these tests (same requirement as Codex).

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
GITHUB_REPO = "https://github.com/robparrott/coding-aegis"
SKILL_PATH = "modules/bootstrap/coding-aegis/skills/coding-aegis"
TIMEOUT_LONG = 120  # Gemini retries internally; each step can take 60-90s

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_SCRIPT = REPO_ROOT / "modules/bootstrap/coding-aegis/skills/coding-aegis/aegis-validate.py"


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
          - Creates a shared temporary test directory with git init.
          - Installs coding-aegis from GitHub via ``gemini skills install`` at workspace scope.
          - skill_dir points to the installed copy: test_dir/.gemini/skills/coding-aegis/.
          - Catalog fetched from GitHub by ensure_catalog() on first agent command.
          - Asserts "coding-aegis" appears in ``gemini skills list``.
          - Pre-creates .gemini/rules directory.

        NOTE: ``gemini skills install`` fetches from GitHub, so changes must be
        pushed to the remote before running these tests.

        TEARDOWN:
          - Best-effort helloworld uninstall (if helloworld_installed is True).
          - Best-effort coding-aegis skill uninstall.
          - Temp dir cleanup handled automatically by tmp_path_factory.
        """
        # Build a clean env without Claude Code vars leaking in
        clean_env = os.environ.copy()
        clean_env.pop("CLAUDECODE", None)
        clean_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        test_dir: Path = tmp_path_factory.mktemp("gemini-journey")

        state = {}
        state["repo_root"] = repo_root
        state["test_dir"] = test_dir
        state["clean_env"] = clean_env
        state["helloworld_installed"] = False

        # git init the test directory (Gemini requires a git repo)
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # Phase 3: install coding-aegis from GitHub at workspace scope
        result = run_cli(
            [
                "gemini", "skills", "install", GITHUB_REPO,
                "--path", SKILL_PATH,
                "--scope", "workspace",
                "--consent",
            ],
            cwd=test_dir,
            env=clean_env,
        )
        assert_no_timeout(result, "skills install (setup)")

        # skill_dir is the workspace-scope install path (copied, not linked)
        state["skill_dir"] = test_dir / ".gemini" / "skills" / "coding-aegis"

        # skills list to confirm coding-aegis is visible
        list_result = run_cli(
            ["gemini", "skills", "list"],
            cwd=test_dir,
            env=clean_env,
        )
        assert "coding-aegis" in list_result.stdout, (
            f"coding-aegis not found in skills list after install:\n{list_result.stdout[:2000]}"
        )

        # Pre-create .gemini/rules so the agent can write rules there
        (test_dir / ".gemini" / "rules").mkdir(parents=True, exist_ok=True)

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

        # Best-effort coding-aegis skill uninstall
        run_cli(
            ["gemini", "skills", "uninstall", "coding-aegis", "--scope", "workspace"],
            cwd=test_dir,
            env=clean_env,
        )
        # Verify skill was removed (workspace-scoped state).
        list_result = run_cli(
            ["gemini", "skills", "list"],
            cwd=test_dir,
            env=clean_env,
        )
        assert "coding-aegis" not in list_result.stdout, (
            f"coding-aegis skill still present after teardown — "
            f"workspace state leak.\n{list_result.stdout[:500]}"
        )

        # Explicit cleanup of tool-specific directories so pytest's retained
        # temp dirs don't pollute subsequent test runs.
        shutil.rmtree(test_dir / ".gemini", ignore_errors=True)
        shutil.rmtree(test_dir / ".coding-aegis-catalog", ignore_errors=True)
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

    # ── Phase 2: Bootstrap mechanism (no marketplace) ────────────────────

    def test_phase2_bootstrap_mechanism(self, journey):
        """Phase 2 — Gemini uses ``gemini skills install`` from GitHub; no manifest file required.

        Validates SKILL.md exists at the skill source path (in the repo) and contains
        the required frontmatter fields (name, description). SKILL.md is the entry
        point that ``gemini skills install`` reads when installing from the remote repo.
        """
        skill_md = journey["repo_root"] / SKILL_PATH / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found at {skill_md}"
        content = skill_md.read_text()
        assert "name: coding-aegis" in content, (
            f"SKILL.md missing 'name: coding-aegis' frontmatter:\n{content[:500]}"
        )
        assert "description:" in content, (
            f"SKILL.md missing 'description:' frontmatter:\n{content[:500]}"
        )

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_linked(self, journey):
        """Phase 3 — coding-aegis appears in gemini skills list."""
        result = run_cli(
            ["gemini", "skills", "list"],
            cwd=journey["test_dir"],
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
             "--catalog", str(REPO_ROOT / "modules"), "--tool", "gemini"],
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
