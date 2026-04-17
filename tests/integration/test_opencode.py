"""
test_opencode.py — Full integration test for OpenCode CLI.

Follows the same class-scoped journey pattern as test_cursor.py and
test_gemini.py. Key OpenCode differences:

  - Headless invocation: ``opencode run '<prompt>'`` where the prompt is
    a positional argument (not stdin). No --quiet flag exists.
  - Detection: OPENCODE=1 and OPENCODE_PID are injected by ``opencode run``
    into all subprocesses. Confirmed live against opencode v1.4.7.
  - Skill bootstrap: auto-discovered from .opencode/skills/ in the project
    directory. No install command needed — fixture copies files directly.
  - Rule delivery: via AGENTS.md aegis:begin/end sections (same as Codex).
    There is no .opencode/rules/ path.
  - Skills install to <test_dir>/.opencode/skills/<name>/.
  - Output contains ANSI escape codes; use _clean() for assertions.
  - No marketplace (phase 2 is omitted).
  - git init is required in the working directory.

Run:
    pytest tests/integration/test_opencode.py -v
    pytest tests/integration/test_opencode.py -v -s    # stream agent output
    pytest tests/integration/test_opencode.py -v -x    # stop at first failure
"""

import os
import re
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

# ── Skip entire module if opencode is not on PATH ────────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("opencode"),
    reason="opencode not installed / not on PATH",
)

# ── Constants ─────────────────────────────────────────────────────────────────

TIMEOUT_LONG = 120  # agent-mediated operations may be slow

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_SCRIPT = REPO_ROOT / "pkgs/bootstrap/coding-aegis/skills/coding-aegis/aegis-validate.py"

# ANSI escape code pattern (opencode emits coloured output by default)
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mK]")


def _clean(text: str) -> str:
    """Strip ANSI escape codes from opencode output for reliable assertions."""
    return _ANSI_ESCAPE.sub("", text)


def _opencode_run(*args) -> list:
    """Return an ``opencode run <prompt>`` command list.

    Prompt is passed as a positional argument, not via stdin.
    Additional args (flags) are inserted before the prompt.
    """
    return ["opencode", "run"] + list(args)


# ── Test class ────────────────────────────────────────────────────────────────


class TestOpenCodeJourney:
    """
    Single class covering all phases of the OpenCode integration journey.

    The class-scoped journey fixture:
      - Creates a shared temp directory with git init.
      - Builds clean_env (CLAUDECODE / CLAUDE_CODE_ENTRYPOINT stripped,
        OPENCODE=1 injected for detect_tool detection in direct invocations).
      - Manually bootstraps the coding-aegis skill into
        .opencode/skills/coding-aegis/ (auto-discovered by opencode).
      - Copies pkgs/ catalog into test_dir so the skill can access it.
      - Runs teardown (best-effort helloworld uninstall) after all tests.
    """

    @pytest.fixture(autouse=True, scope="class")
    def journey(self, tmp_path_factory, repo_root):
        """Class-scoped fixture owning setup and teardown for the full journey.

        SETUP:
          - Creates a shared temporary test directory with git init.
          - Builds clean_env: strips Claude Code vars, injects OPENCODE=1.
          - Copies coding-aegis skill into .opencode/skills/coding-aegis/.
          - Copies pkgs/ catalog into test_dir.

        TEARDOWN:
          - Best-effort helloworld uninstall (if helloworld_installed is True).
          - Temp dir cleanup handled automatically by tmp_path_factory.
        """
        # Build a clean env: strip Claude Code vars, inject OpenCode signal
        clean_env = os.environ.copy()
        clean_env.pop("CLAUDECODE", None)
        clean_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
        clean_env["OPENCODE"] = "1"

        state = {}
        state["repo_root"] = repo_root
        state["test_dir"] = tmp_path_factory.mktemp("opencode-journey")
        state["clean_env"] = clean_env
        state["helloworld_installed"] = False

        test_dir: Path = state["test_dir"]

        # git init required by opencode
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # Bootstrap: copy coding-aegis skill into .opencode/skills/coding-aegis/
        # opencode auto-discovers skills from this path — no install command needed.
        opencode_skill_dir = test_dir / ".opencode" / "skills" / "coding-aegis"
        opencode_skill_dir.mkdir(parents=True, exist_ok=True)
        skill_src = (
            repo_root
            / "pkgs"
            / "bootstrap"
            / "coding-aegis"
            / "skills"
            / "coding-aegis"
        )
        shutil.copytree(str(skill_src), str(opencode_skill_dir), dirs_exist_ok=True)

        # Copy pkgs/ catalog so the skill can resolve package paths
        pkgs_dest = test_dir / "pkgs"
        if not pkgs_dest.exists():
            shutil.copytree(str(repo_root / "pkgs"), str(pkgs_dest))

        state["opencode_skill_dir"] = opencode_skill_dir

        yield state

        # ── TEARDOWN ──────────────────────────────────────────────────────────
        if state.get("helloworld_installed"):
            run_cli(
                _opencode_run("/coding-aegis uninstall helloworld"),
                cwd=test_dir,
                timeout=TIMEOUT_LONG,
                env=clean_env,
            )

    # ── Phase 1: Environment & Tool Validation ────────────────────────────

    def test_phase1_auth(self, journey):
        """Phase 1 — opencode run responds and is authenticated."""
        result = run_cli(
            _opencode_run("Reply with exactly: AUTH_OK"),
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "auth check")
        warn_if_slow(result, label="auth check")
        assert_no_quota_error(result, "opencode")
        assert "AUTH_OK" in _clean(result.stdout), (
            f"Expected AUTH_OK in output, got:\n{result.stdout[:2000]}"
        )

    # ── Phase 2: No marketplace ───────────────────────────────────────────

    def test_phase2_no_marketplace(self, journey):
        """Phase 2 — OpenCode has no plugin marketplace; phase not applicable."""
        pytest.skip("OpenCode has no plugin marketplace; phase 2 not applicable")

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_files_present(self, journey):
        """Phase 3 — expected files present in .opencode/skills/coding-aegis/."""
        skill_dir: Path = journey["opencode_skill_dir"]
        for filename in (
            "SKILL.md",
            "aegis_lib.py",
            "aegis-install.py",
            "aegis-uninstall.py",
            "detect_tool.py",
        ):
            assert (skill_dir / filename).exists(), (
                f"{filename} not found in {skill_dir}"
            )

    # ── Phase 4: Validate coding-aegis skill ──────────────────────────────

    def test_phase4a_detect_tool_direct(self, journey):
        """Phase 4a — detect_tool.py run directly returns tool=opencode."""
        import json as _json

        skill_dir: Path = journey["opencode_skill_dir"]
        result = run_cli(
            ["python3", str(skill_dir / "detect_tool.py")],
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect_tool.py direct")
        json_start = result.stdout.find("{")
        assert json_start != -1, (
            f"No JSON in detect_tool.py output:\n{result.stdout}"
        )
        data = _json.loads(result.stdout[json_start:])
        assert data.get("tool") == "opencode", (
            f"detect_tool.py: expected tool='opencode', got {data}"
        )
        assert len(data.get("signals", [])) > 0, (
            f"detect_tool.py: expected non-empty signals, got {data}"
        )

    def test_phase4b_detect_tool_skill(self, journey):
        """Phase 4b — /coding-aegis detect-tool via agent reports opencode."""
        result = run_cli(
            _opencode_run("/coding-aegis detect-tool"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect-tool skill")
        warn_if_slow(result, label="detect-tool skill")
        assert_no_quota_error(result, "opencode")
        cleaned = _clean(result.stdout).lower()
        assert "opencode" in cleaned, (
            f"detect-tool: expected 'opencode' in output:\n{result.stdout[:2000]}"
        )

    def test_phase4c_list(self, journey):
        """Phase 4c — /coding-aegis list shows helloworld in catalog."""
        result = run_cli(
            _opencode_run("/coding-aegis list --catalog pkgs"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill list")
        warn_if_slow(result, label="skill list")
        assert_no_quota_error(result, "opencode")
        assert "helloworld" in _clean(result.stdout).lower(), (
            f"list: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )

    def test_phase4d_show(self, journey):
        """Phase 4d — /coding-aegis show helloworld returns name, tier, version."""
        result = run_cli(
            _opencode_run("/coding-aegis show helloworld --catalog pkgs"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill show")
        warn_if_slow(result, label="skill show")
        assert_no_quota_error(result, "opencode")
        cleaned = _clean(result.stdout).lower()
        assert "helloworld" in cleaned, (
            f"show: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )
        assert "optional" in cleaned, (
            f"show: expected 'optional' (tier) in output:\n{result.stdout[:2000]}"
        )
        assert "1.0.0" in _clean(result.stdout), (
            f"show: expected '1.0.0' (version) in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 5: Install & verify helloworld ──────────────────────────────

    def test_phase5_install_helloworld(self, journey):
        """Phase 5 — /coding-aegis install helloworld writes AGENTS.md section
        and skill directory.

        OpenCode delivers rules via AGENTS.md aegis:begin/end markers (same as
        Codex). Skills install to .opencode/skills/<name>/.
        """
        catalog_arg = str(journey["test_dir"] / "pkgs")
        result = run_cli(
            _opencode_run(
                f"/coding-aegis install helloworld to Project scope --catalog {catalog_arg}"
            ),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "install helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="install helloworld")
        assert_no_quota_error(result, "opencode")
        cleaned_lower = _clean(result.stdout).lower()
        assert any(kw in cleaned_lower for kw in (
            "install", "helloworld", "wrote", "created", "agents.md"
        )), f"install: expected activity in output:\n{result.stdout[:2000]}"

        # Verify installation via validate-install
        v = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), "helloworld",
             "--catalog", str(REPO_ROOT / "pkgs"), "--tool", "opencode"],
            capture_output=True, text=True,
            cwd=str(journey["test_dir"]),
        )
        assert v.returncode == 0, (
            f"validate-install failed:\n{v.stdout}\n{v.stderr}"
        )

        journey["helloworld_installed"] = True

    def test_phase5b_helloworld_responds(self, journey):
        """Phase 5b — /helloworld skill returns 'Hello, World'."""
        result = run_cli(
            _opencode_run("/helloworld"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "invoke helloworld")
        warn_if_slow(result, label="invoke helloworld")
        assert_no_quota_error(result, "opencode")
        assert "Hello, World" in _clean(result.stdout), (
            f"helloworld skill: expected 'Hello, World' in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 6: Uninstall helloworld ─────────────────────────────────────

    def test_phase6_uninstall_helloworld(self, journey):
        """Phase 6 — /coding-aegis uninstall helloworld removes AGENTS.md
        section and skill directory.
        """
        result = run_cli(
            _opencode_run("/coding-aegis uninstall helloworld"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "uninstall helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="uninstall helloworld")
        assert_no_quota_error(result, "opencode")
        cleaned = _clean(result.stdout)
        assert not any(kw in cleaned for kw in ("not installed", "not found", "Error")), (
            f"uninstall: unexpected error in output:\n{result.stdout[:2000]}"
        )

        # Verify AGENTS.md aegis section is removed
        agents_md = journey["test_dir"] / "AGENTS.md"
        if agents_md.exists():
            text = agents_md.read_text()
            assert "aegis:begin" not in text or "helloworld" not in text, (
                f"AGENTS.md still contains helloworld aegis section after uninstall:\n{text[:1000]}"
            )

        # Verify skill directory is removed
        skill_dir = journey["test_dir"] / ".opencode" / "skills" / "helloworld"
        assert not skill_dir.exists(), (
            f"Skill dir still present after uninstall: {skill_dir}"
        )

        journey["helloworld_installed"] = False
