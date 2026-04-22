"""
test_codex.py — Full 7-phase integration test for OpenAI Codex CLI.

Ports tests/test-codex-skill-install.sh to pytest.

Uses Pattern 1: a single TestCodexJourney class with a class-scoped journey
fixture. Key Codex differences from the Claude test:

  - No marketplace (Phase 2 N/A) — validates .codex-plugin/ manifest instead.
  - Skill install via $skill-installer from GitHub (danger-full-access sandbox).
  - CLAUDECODE / CLAUDE_CODE_ENTRYPOINT are unset (via clean_env fixture) so
    detect_tool.py returns "codex" not "claude" when run from Claude Code.
  - Rules delivered via AGENTS.md sections (not .claude/rules/).
  - Skills installed to .agents/skills/<name>/ (not .claude/skills/).
  - Phase 6 uninstall uses danger-full-access so shutil.rmtree can remove the
    skill directory (workspace-write blocks that syscall).
  - TIMEOUT_LONG = 60s for install/uninstall (agent-mediated operations are slower).

Run:
    pytest tests/integration/test_codex.py -v
    pytest tests/integration/test_codex.py -v -s    # stream agent output
    pytest tests/integration/test_codex.py -v -x    # stop at first failure
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
    assert_no_timeout,
    assert_no_quota_error,
    run_cli,
    warn_if_slow,
)

# ── Skip entire module if codex is not on PATH ───────────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("codex"),
    reason="codex not installed / not on PATH",
)

# ── Constants ─────────────────────────────────────────────────────────────────

GITHUB_REPO = "robparrott/coding-aegis"
SKILL_PATH = "pkgs/bootstrap/coding-aegis/skills/coding-aegis"
CODEX_SKILL_DIR = Path.home() / ".codex" / "skills" / "coding-aegis"
TIMEOUT_LONG = 60  # install/uninstall via workspace-write are slower

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATE_SCRIPT = REPO_ROOT / "pkgs/bootstrap/coding-aegis/skills/coding-aegis/aegis-validate.py"


def _codex_exec(*sandbox_flags, extra_flags=()) -> list:
    """Return the base ``codex exec`` command list."""
    return ["codex", "exec", "--ephemeral"] + list(sandbox_flags) + list(extra_flags) + ["-o", "/dev/stdout"]


# ── Test class ────────────────────────────────────────────────────────────────

class TestCodexJourney:
    """
    Single class covering all 7 phases of the Codex CLI integration journey.

    The class-scoped journey fixture installs the coding-aegis skill from GitHub
    once (setup) and removes it after all tests (teardown).
    """

    @pytest.fixture(autouse=True, scope="class")
    def journey(self, tmp_path_factory, repo_root):
        """Class-scoped fixture owning setup and teardown for the full journey.

        SETUP (phases 1-3):
          - Creates a shared temporary test directory with git init.
          - Installs coding-aegis skill via $skill-installer (danger-full-access).
          - Copies pkgs/ catalog into test_dir so read-only sandbox can reach it.

        TEARDOWN (phases 6-7):
          - Best-effort helloworld uninstall (if helloworld_installed is still True).
          - Removes ~/.codex/skills/coding-aegis/.
          - Temp dir cleanup handled automatically by tmp_path_factory.
        """
        # Build a clean env without Claude Code vars leaking in
        clean_env = os.environ.copy()
        clean_env.pop("CLAUDECODE", None)
        clean_env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        state = {}
        state["repo_root"] = repo_root
        state["test_dir"] = tmp_path_factory.mktemp("codex-journey")
        state["clean_env"] = clean_env
        state["helloworld_installed"] = False

        test_dir: Path = state["test_dir"]

        # Phase 1 precondition: git init
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # Phase 3: install coding-aegis via $skill-installer from GitHub
        result = run_cli(
            _codex_exec("-s", "danger-full-access"),
            prompt=f"$skill-installer install --repo {GITHUB_REPO} --path {SKILL_PATH}",
            cwd=test_dir,
            timeout=TIMEOUT_LONG,
            env=clean_env,
        )
        assert_no_timeout(result, "skill-installer install (setup)")
        assert any(kw in result.stdout.lower() for kw in (
            "install", "success", "done", "copied", "coding-aegis"
        )), f"skill-installer (setup): no activity reported:\n{result.stdout[:2000]}"
        assert CODEX_SKILL_DIR.exists(), (
            f"coding-aegis not installed to {CODEX_SKILL_DIR} after skill-installer"
        )

        # Copy pkgs/ catalog into test_dir so read-only sandbox can access it
        pkgs_dest = test_dir / "pkgs"
        if not pkgs_dest.exists():
            shutil.copytree(str(repo_root / "pkgs"), str(pkgs_dest))

        yield state

        # ── TEARDOWN ──────────────────────────────────────────────────────────
        # Phase 6: best-effort helloworld uninstall
        if state.get("helloworld_installed"):
            run_cli(
                _codex_exec("-s", "workspace-write"),
                prompt="$coding-aegis uninstall helloworld",
                cwd=test_dir,
                timeout=TIMEOUT_LONG,
                env=clean_env,
            )

        # Phase 7: remove coding-aegis skill
        shutil.rmtree(CODEX_SKILL_DIR, ignore_errors=True)
        assert not CODEX_SKILL_DIR.exists(), (
            f"Bootstrap skill not cleaned up — global state leak: {CODEX_SKILL_DIR}"
        )

        # Explicit cleanup of tool-specific directories so pytest's retained
        # temp dirs don't pollute subsequent test runs.
        shutil.rmtree(test_dir / ".agents", ignore_errors=True)
        (test_dir / "AGENTS.md").unlink(missing_ok=True)
        # Temp dir is cleaned automatically by tmp_path_factory.

    # ── Phase 1: Environment & Tool Validation ────────────────────────────

    def test_phase1_auth(self, journey):
        """Phase 1 — codex can authenticate and respond."""
        result = run_cli(
            _codex_exec(),
            prompt="Reply with exactly: AUTH_OK",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "auth check")
        warn_if_slow(result, label="auth check")
        assert "AUTH_OK" in result.stdout, (
            f"Expected AUTH_OK in output, got:\n{result.stdout[:2000]}"
        )

    # ── Phase 2: Marketplace / Registry (manifest check only) ────────────

    def test_phase2_plugin_manifest(self, journey):
        """Phase 2 — .codex-plugin/plugin.json exists and contains expected fields."""
        manifest = journey["repo_root"] / ".codex-plugin" / "plugin.json"
        assert manifest.exists(), f".codex-plugin/plugin.json not found at {manifest}"
        data = json.loads(manifest.read_text())
        assert data.get("name") == "coding-aegis", (
            f"manifest 'name' != 'coding-aegis': {data}"
        )
        assert "skills" in str(data), f"manifest missing 'skills' key: {data}"

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_files_present(self, journey):
        """Phase 3 — expected files installed to ~/.codex/skills/coding-aegis/."""
        for filename in ("SKILL.md", "aegis_lib.py", "aegis-install.py",
                         "aegis-uninstall.py", "detect_tool.py"):
            assert (CODEX_SKILL_DIR / filename).exists(), (
                f"{filename} not found in {CODEX_SKILL_DIR}"
            )

    # ── Phase 4: Validate coding-aegis skill ──────────────────────────────

    def test_phase4a_detect_tool_direct(self, journey):
        """Phase 4a — detect_tool.py run directly returns tool=codex with signals."""
        result = run_cli(
            ["python3", str(CODEX_SKILL_DIR / "detect_tool.py")],
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect_tool.py direct")
        # Parse the JSON block from stdout (may have python warnings before it)
        json_start = result.stdout.find("{")
        assert json_start != -1, f"No JSON in detect_tool.py output:\n{result.stdout}"
        data = json.loads(result.stdout[json_start:])
        assert data.get("tool") == "codex", (
            f"detect_tool.py: expected tool='codex', got {data}"
        )
        assert len(data.get("signals", [])) > 0, (
            f"detect_tool.py: expected non-empty signals, got {data}"
        )

    def test_phase4b_detect_tool_skill(self, journey):
        """Phase 4b — $coding-aegis detect-tool via agent reports codex + signals."""
        result = run_cli(
            _codex_exec("-s", "read-only"),
            prompt="$coding-aegis detect-tool",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect-tool skill")
        warn_if_slow(result, label="detect-tool skill")
        assert "codex" in result.stdout.lower(), (
            f"detect-tool: expected 'codex' in output:\n{result.stdout[:2000]}"
        )
        assert any(sig in result.stdout.lower() for sig in ("env:", "path:")), (
            f"detect-tool: expected at least one signal in output:\n{result.stdout[:2000]}"
        )

    def test_phase4c_list(self, journey):
        """Phase 4c — $coding-aegis list shows helloworld."""
        result = run_cli(
            _codex_exec("-s", "read-only"),
            prompt="$coding-aegis list --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill list")
        warn_if_slow(result, label="skill list")
        assert "helloworld" in result.stdout.lower(), (
            f"list: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )

    def test_phase4d_show(self, journey):
        """Phase 4d — $coding-aegis show helloworld returns name, tier, version."""
        result = run_cli(
            _codex_exec("-s", "read-only"),
            prompt="$coding-aegis show helloworld --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill show")
        warn_if_slow(result, label="skill show")
        assert "helloworld" in result.stdout.lower(), (
            f"show: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )
        assert "optional" in result.stdout.lower(), (
            f"show: expected 'optional' (tier) in output:\n{result.stdout[:2000]}"
        )
        assert "1.0.0" in result.stdout, (
            f"show: expected '1.0.0' (version) in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 5: Install & verify helloworld ──────────────────────────────

    def test_phase5_install_helloworld(self, journey):
        """Phase 5 — $coding-aegis install helloworld writes AGENTS.md and skill file."""
        catalog_arg = str(journey["test_dir"] / "pkgs")
        result = run_cli(
            _codex_exec("-s", "workspace-write"),
            prompt=f"$coding-aegis install helloworld to Project scope --catalog {catalog_arg}",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "install helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="install helloworld")
        assert any(kw in result.stdout.lower() for kw in (
            "install", "aegis--helloworld", "wrote", "created"
        )), f"install: expected activity in output:\n{result.stdout[:2000]}"

        # Verify installation via validate-install
        v = subprocess.run(
            [sys.executable, str(VALIDATE_SCRIPT), "helloworld",
             "--catalog", str(REPO_ROOT / "pkgs"), "--tool", "codex"],
            capture_output=True, text=True,
            cwd=str(journey["test_dir"]),
        )
        assert v.returncode == 0, (
            f"validate-install failed:\n{v.stdout}\n{v.stderr}"
        )

        journey["helloworld_installed"] = True

    def test_phase5b_helloworld_responds(self, journey):
        """Phase 5b — $helloworld skill returns 'Hello, World'."""
        result = run_cli(
            _codex_exec("-s", "read-only"),
            prompt="$helloworld",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "invoke helloworld")
        warn_if_slow(result, label="invoke helloworld")
        assert "Hello, World" in result.stdout, (
            f"helloworld skill: expected 'Hello, World' in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 6: Uninstall helloworld ─────────────────────────────────────

    def test_phase6_uninstall_helloworld(self, journey):
        """Phase 6 — $coding-aegis uninstall helloworld cleans AGENTS.md and skill dir.

        Uses danger-full-access so aegis-uninstall.py can run shutil.rmtree on the
        skill directory (workspace-write blocks that syscall).
        """
        result = run_cli(
            _codex_exec("-s", "danger-full-access"),
            prompt="$coding-aegis uninstall helloworld",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "uninstall helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="uninstall helloworld")
        assert not any(kw in result.stdout for kw in ("not installed", "not found", "Error")), (
            f"uninstall: unexpected error in output:\n{result.stdout[:2000]}"
        )

        # AGENTS.md rule section must be removed
        agents_md = journey["test_dir"] / "AGENTS.md"
        if agents_md.exists():
            agents_text = agents_md.read_text()
            assert "aegis:begin package=helloworld" not in agents_text, (
                f"AGENTS.md: helloworld rule section still present after uninstall:\n"
                f"{agents_text[:500]}"
            )

        # Skill dir must be fully removed (danger-full-access allows shutil.rmtree)
        skill_dir = journey["test_dir"] / ".agents" / "skills" / "helloworld"
        assert not skill_dir.exists(), (
            f"Skill dir still present after uninstall: {skill_dir}"
        )

        journey["helloworld_installed"] = False
