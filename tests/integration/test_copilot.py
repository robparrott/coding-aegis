"""
test_copilot.py — Full integration test for GitHub Copilot CLI.

Follows the same class-scoped journey pattern as test_opencode.py and
test_cursor.py. Key Copilot differences:

  - Binary: ``copilot`` (from github/copilot-cli, not ``gh copilot``).
  - Headless invocation: ``copilot --prompt '<prompt>' --allow-all-tools --silent``
    where the prompt is passed as a flag value (not stdin).
  - Detection: NO env var is injected by copilot into subprocesses (confirmed:
    GitHub docs, April 2026). Detection falls back to path:.github signal.
  - Skill bootstrap: auto-discovered from .github/skills/ in the project directory.
    No install command needed — fixture copies files directly.
  - Rule delivery: file-scoped rules → .github/instructions/*.instructions.md;
    always-on rules → .github/copilot-instructions.md.
  - Skills install to <test_dir>/.github/skills/<name>/.
  - Skill invocation confirmed April 2026: detect-tool works with /coding-aegis slash
    syntax; list, show, install, uninstall work with natural language prompts.
    Phases 4b–6 are unlocked. Phase 5b (helloworld responds) not yet validated.


Run:
    pytest tests/integration/test_copilot.py -v
    pytest tests/integration/test_copilot.py -v -s    # stream agent output
    pytest tests/integration/test_copilot.py -v -x    # stop at first failure
"""

import json as _json
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

# ── Skip entire module if copilot is not on PATH ──────────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("copilot"),
    reason="copilot CLI not installed / not on PATH",
)

# ── Constants ─────────────────────────────────────────────────────────────────

TIMEOUT_LONG = 120  # agent-mediated operations may be slow

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_SCRIPT = REPO_ROOT / "modules/bootstrap/coding-aegis/skills/coding-aegis/aegis-validate.py"

# Phase flags: set to True once live-validated on a Copilot machine.
# Skill invocation confirmed working April 2026 (detect-tool, list, install, uninstall).
# Phases 4b–6 are now unlocked.
_COPILOT_SKILL_INVOCATION_VALIDATED = True
SKIP_REASON_SKILL = (
    "NEEDS VALIDATION ON COPILOT MACHINE: "
    "Copilot CLI skill invocation (/skill-name) is unconfirmed. "
    "Set _COPILOT_SKILL_INVOCATION_VALIDATED=True once confirmed live."
)

# ANSI escape code pattern (precaution — unknown whether copilot emits them in --silent mode)
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mK]")


def _clean(text: str) -> str:
    """Strip ANSI escape codes from output for reliable assertions."""
    return _ANSI_ESCAPE.sub("", text)


def _copilot_cmd(prompt: str) -> list:
    """Return a ``copilot --prompt '<prompt>' --allow-all-tools --silent`` command list.

    Prompt is passed as a single ``--prompt <value>`` flag (not via stdin).
    Confirmed working pattern: ``copilot --prompt '<text>' --allow-all-tools --silent``.
    """
    return ["copilot", "--prompt", prompt, "--allow-all-tools", "--silent"]


# Keep old name as alias so any external callers are not broken.
def _copilot_run(*args) -> list:
    """Legacy shim — prefer _copilot_cmd(prompt). Builds the same command."""
    prompt = " ".join(args) if args else ""
    return _copilot_cmd(prompt)


# ── Test class ────────────────────────────────────────────────────────────────


class TestCopilotJourney:
    """
    Single class covering all phases of the GitHub Copilot CLI integration journey.

    The class-scoped journey fixture:
      - Creates a shared temp directory (with git init — unknown if required).
      - Builds clean_env (CLAUDECODE / CLAUDE_CODE_ENTRYPOINT stripped).
        NOTE: No COPILOT-specific env var is injected — no env var signal exists.
      - Manually bootstraps the coding-aegis skill into
        .github/skills/coding-aegis/ (auto-discovered by copilot).
      - Copies modules/ catalog into test_dir so the skill can access it.
      - Runs teardown (best-effort helloworld uninstall) after all tests.

    Phases 4b–6 are unlocked (confirmed April 2026). Phase 5b not yet validated.
    """

    @pytest.fixture(autouse=True, scope="class")
    def journey(self, tmp_path_factory, repo_root):
        """Class-scoped fixture owning setup and teardown for the full journey.

        SETUP:
          - Creates a shared temporary test directory with git init.
          - Builds clean_env: strips Claude Code vars. No Copilot env var to inject.
          - Copies coding-aegis skill into .github/skills/coding-aegis/.
          - Copies modules/ catalog into test_dir.

        TEARDOWN:
          - Best-effort helloworld uninstall (if helloworld_installed is True).
          - Temp dir cleanup handled automatically by tmp_path_factory.
        """
        # Build a clean env: strip Claude Code vars.
        # No Copilot-specific env var to inject — detection uses path:.github signal.
        clean_env = os.environ.copy()
        clean_env.pop("CLAUDECODE", None)
        clean_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        state = {}
        state["repo_root"] = repo_root
        state["test_dir"] = tmp_path_factory.mktemp("copilot-journey")
        state["clean_env"] = clean_env
        state["helloworld_installed"] = False

        test_dir: Path = state["test_dir"]

        # git init (unknown if required by copilot — precautionary)
        # > NEEDS VALIDATION ON COPILOT MACHINE: confirm git init requirement
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # Bootstrap: copy coding-aegis skill into .github/skills/coding-aegis/
        # copilot auto-discovers skills from this path — no install command needed.
        copilot_skill_dir = test_dir / ".github" / "skills" / "coding-aegis"
        copilot_skill_dir.mkdir(parents=True, exist_ok=True)
        skill_src = (
            repo_root
            / "modules"
            / "bootstrap"
            / "coding-aegis"
            / "skills"
            / "coding-aegis"
        )
        shutil.copytree(str(skill_src), str(copilot_skill_dir), dirs_exist_ok=True)

        # Copy modules/ catalog so the skill can resolve package paths
        pkgs_dest = test_dir / "modules"
        if not pkgs_dest.exists():
            shutil.copytree(str(repo_root / "modules"), str(pkgs_dest))

        state["copilot_skill_dir"] = copilot_skill_dir

        yield state

        # ── TEARDOWN ──────────────────────────────────────────────────────────
        if state.get("helloworld_installed") and _COPILOT_SKILL_INVOCATION_VALIDATED:
            run_cli(
                _copilot_cmd("/coding-aegis uninstall helloworld"),
                cwd=test_dir,
                timeout=TIMEOUT_LONG,
                env=clean_env,
            )

        # Explicit cleanup of tool-specific directories.
        shutil.rmtree(test_dir / ".github", ignore_errors=True)
        (test_dir / "AGENTS.md").unlink(missing_ok=True)
        # Temp dir is cleaned automatically by tmp_path_factory.

    # ── Phase 1: Environment & Tool Validation ────────────────────────────

    def test_phase1_auth(self, journey):
        """Phase 1 — copilot CLI responds and is authenticated.

        > NEEDS VALIDATION ON COPILOT MACHINE: confirm invocation flags and
        > that AUTH_OK appears in the output.
        """
        result = run_cli(
            _copilot_run("Reply with exactly: AUTH_OK"),
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "auth check")
        warn_if_slow(result, label="auth check")
        assert_no_quota_error(result, "copilot")
        assert "AUTH_OK" in _clean(result.stdout), (
            f"Expected AUTH_OK in output, got:\n{result.stdout[:2000]}"
        )

    # ── Phase 2: Bootstrap mechanism (no marketplace) ────────────────────

    def test_phase2_bootstrap_mechanism(self, journey):
        """Phase 2 — Copilot uses file-copy auto-discovery; no manifest required.

        Validates SKILL.md exists at the skill source path and contains the
        required frontmatter fields (name, description). SKILL.md is the entry
        point that gets copied into .github/skills/ for auto-discovery.
        """
        skill_src = (
            journey["repo_root"]
            / "modules" / "bootstrap" / "coding-aegis" / "skills" / "coding-aegis"
        )
        skill_md = skill_src / "SKILL.md"
        assert skill_md.exists(), f"SKILL.md not found at {skill_md}"
        content = skill_md.read_text()
        assert "name: coding-aegis" in content, (
            f"SKILL.md missing 'name: coding-aegis' frontmatter:\n{content[:500]}"
        )
        assert "description:" in content, (
            f"SKILL.md missing 'description:' frontmatter:\n{content[:500]}"
        )

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_files_present(self, journey):
        """Phase 3 — expected files present in .github/skills/coding-aegis/."""
        skill_dir: Path = journey["copilot_skill_dir"]
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
        """Phase 4a — detect_tool.py run directly returns tool=copilot via path:.github.

        NOTE: No env var signal exists for Copilot. Detection relies on the
        path:.github signal — the script must be located under a .github/ directory.
        The fixture copies the skill to .github/skills/coding-aegis/, so this signal
        should fire when the script is run from that installed path.

        > NEEDS VALIDATION ON COPILOT MACHINE: confirm path signal fires correctly.
        """
        skill_dir: Path = journey["copilot_skill_dir"]
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
        assert data.get("tool") == "copilot", (
            f"detect_tool.py: expected tool='copilot', got {data}. "
            f"The path:.github signal requires the script to be inside a .github/ directory."
        )
        assert "path:.github" in data.get("signals", []), (
            f"detect_tool.py: expected 'path:.github' in signals, got {data}"
        )

    @pytest.mark.skipif(
        not _COPILOT_SKILL_INVOCATION_VALIDATED,
        reason=SKIP_REASON_SKILL,
    )
    def test_phase4b_detect_tool_skill(self, journey):
        """Phase 4b — /coding-aegis detect-tool via agent reports copilot.

        Slash-command syntax confirmed working on live Copilot machine (April 2026).
        """
        result = run_cli(
            _copilot_cmd("/coding-aegis detect-tool"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect-tool skill")
        warn_if_slow(result, label="detect-tool skill")
        assert_no_quota_error(result, "copilot")
        cleaned = _clean(result.stdout).lower()
        assert "copilot" in cleaned, (
            f"detect-tool: expected 'copilot' in output:\n{result.stdout[:2000]}"
        )

    @pytest.mark.skipif(
        not _COPILOT_SKILL_INVOCATION_VALIDATED,
        reason=SKIP_REASON_SKILL,
    )
    def test_phase4c_list(self, journey):
        """Phase 4c — list shows helloworld in catalog."""
        result = run_cli(
            _copilot_cmd("/coding-aegis list --catalog modules"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill list")
        warn_if_slow(result, label="skill list")
        assert_no_quota_error(result, "copilot")
        assert "helloworld" in _clean(result.stdout).lower(), (
            f"list: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )

    @pytest.mark.skipif(
        not _COPILOT_SKILL_INVOCATION_VALIDATED,
        reason=SKIP_REASON_SKILL,
    )
    def test_phase4d_show(self, journey):
        """Phase 4d — show helloworld returns name, tier, version."""
        result = run_cli(
            _copilot_cmd("/coding-aegis show helloworld --catalog modules"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill show")
        warn_if_slow(result, label="skill show")
        assert_no_quota_error(result, "copilot")
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

    @pytest.mark.skipif(
        not _COPILOT_SKILL_INVOCATION_VALIDATED,
        reason=SKIP_REASON_SKILL,
    )
    def test_phase5_install_helloworld(self, journey):
        """Phase 5 — install helloworld writes rule and skill files.

        Copilot delivers file-scoped rules to .github/instructions/*.instructions.md
        and skills to .github/skills/<name>/.
        """
        result = run_cli(
            _copilot_cmd("/coding-aegis install helloworld --catalog modules to project scope"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "install helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="install helloworld")
        assert_no_quota_error(result, "copilot")
        cleaned_lower = _clean(result.stdout).lower()
        assert any(kw in cleaned_lower for kw in (
            "install", "helloworld", "wrote", "created"
        )), f"install: expected activity in output:\n{result.stdout[:2000]}"

        # Verify installation via validate-install (direct subprocess — needs absolute path)
        catalog_abs = str(journey["test_dir"] / "modules")
        v = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), "helloworld",
             "--catalog", catalog_abs, "--tool", "copilot"],
            capture_output=True, text=True,
            cwd=str(journey["test_dir"]),
        )
        assert v.returncode == 0, (
            f"validate-install failed:\n{v.stdout}\n{v.stderr}"
        )

        journey["helloworld_installed"] = True

    @pytest.mark.skipif(
        not _COPILOT_SKILL_INVOCATION_VALIDATED,
        reason=SKIP_REASON_SKILL,
    )
    def test_phase5b_helloworld_responds(self, journey):
        """Phase 5b — helloworld skill returns 'Hello, World'.

        Confirmed working on live Copilot machine (April 2026).
        Output: "Hello, World! Governance is active."
        """
        result = run_cli(
            _copilot_cmd("/helloworld"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "invoke helloworld")
        warn_if_slow(result, label="invoke helloworld")
        assert_no_quota_error(result, "copilot")
        assert "Hello, World" in _clean(result.stdout), (
            f"helloworld skill: expected 'Hello, World' in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 6: Uninstall helloworld ─────────────────────────────────────

    @pytest.mark.skipif(
        not _COPILOT_SKILL_INVOCATION_VALIDATED,
        reason=SKIP_REASON_SKILL,
    )
    def test_phase6_uninstall_helloworld(self, journey):
        """Phase 6 — uninstall helloworld removes installed files."""
        result = run_cli(
            _copilot_cmd("/coding-aegis uninstall helloworld"),
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "uninstall helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="uninstall helloworld")
        assert_no_quota_error(result, "copilot")
        cleaned = _clean(result.stdout)
        assert not any(kw in cleaned for kw in ("not installed", "not found", "Error")), (
            f"uninstall: unexpected error in output:\n{result.stdout[:2000]}"
        )

        # Verify rule files are removed (.github/rules/ is the install path)
        rules_dir = journey["test_dir"] / ".github" / "rules"
        if rules_dir.exists():
            leftover_rules = list(rules_dir.glob("aegis--helloworld--*"))
            assert len(leftover_rules) == 0, (
                f"Rule files still present after uninstall: {leftover_rules}"
            )

        # Verify skill directory is removed
        skill_dir = journey["test_dir"] / ".github" / "skills" / "helloworld"
        assert not skill_dir.exists(), (
            f"Skill dir still present after uninstall: {skill_dir}"
        )

        # Verify MCP entry is removed (servers.json should not list helloworld)
        mcp_json = journey["test_dir"] / ".github" / "mcp" / "servers.json"
        if mcp_json.exists():
            import json as _json_mod
            data = _json_mod.loads(mcp_json.read_text())
            servers = data.get("servers", data)
            assert "helloworld" not in servers, (
                f"MCP servers.json still contains helloworld entry after uninstall: {servers}"
            )

        journey["helloworld_installed"] = False
