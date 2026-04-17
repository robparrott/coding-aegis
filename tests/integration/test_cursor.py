"""
test_cursor.py — Full 7-phase integration test for Cursor Agent CLI.

Ports tests/test-cursor-skill-install.sh to pytest.

Uses Pattern 1: a single TestCursorJourney class with a class-scoped journey
fixture. Key Cursor differences from Claude and Codex tests:

  - No marketplace CLI (Phase 2) — validates .cursor-plugin/marketplace.json
    manifest instead; plugin install is IDE-only (TBD).
  - CLAUDECODE / CLAUDE_CODE_ENTRYPOINT are unset (via clean_env built inline)
    so detect_tool.py does not mis-detect claude when run from Claude Code.
  - CURSOR_AGENT=1 is injected into the environment passed to detect_tool.py
    to simulate the Cursor runtime signal.
  - Skill bootstrap: no $skill-installer equivalent exists for Cursor.
    The fixture manually copies the coding-aegis skill into
    <test_dir>/.cursor/skills/coding-aegis/ to simulate a plugin install.
  - Rule delivery: .cursor/rules/ markdown files (same layout as Claude but
    under .cursor/, not .claude/).
  - Skills install to <test_dir>/.cursor/skills/<name>/ (project scope).
  - No user-global skill directory to clean up (unlike Codex's ~/.codex/).

  # TODO: verify invocation — the CLI flags below are based on the bash
  # prototype in tests/test-cursor-skill-install.sh and docs/test/test-cursor.md
  # but have NOT been validated against a live cursor-agent binary.
  # Specifically:
  #   - `-p` for headless/print mode (same as Claude: confirmed in bash script)
  #   - `--output-format text` for plain output (from bash script)
  #   - `--force` for auto-approve writes (from bash script; `--yolo` is alt)
  # Update these flags once cursor-agent is installed and the flags are verified.

Run:
    pytest tests/integration/test_cursor.py -v
    pytest tests/integration/test_cursor.py -v -s    # stream agent output
    pytest tests/integration/test_cursor.py -v -x    # stop at first failure
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from .harness import (
    DEFAULT_TIMEOUT,
    assert_no_quota_error,
    assert_no_timeout,
    run_cli,
    warn_if_slow,
)

# ── Skip entire module if cursor-agent is not on PATH ────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("cursor-agent"),
    reason="cursor-agent not installed / not on PATH",
)

# ── Constants ─────────────────────────────────────────────────────────────────

TIMEOUT_LONG = 60  # install/uninstall operations may be slower


def _cursor_p(*extra_flags) -> list:
    """Return the base ``cursor-agent -p`` command list."""
    # --trust: required for headless mode in temp dirs (no interactive trust prompt)
    # --output-format text: plain text (no rich/ANSI decorations)
    return ["cursor-agent", "-p", "--output-format", "text", "--trust"] + list(extra_flags)


# ── Test class ────────────────────────────────────────────────────────────────


class TestCursorJourney:
    """
    Single class covering all 7 phases of the Cursor Agent CLI integration journey.

    The class-scoped journey fixture:
      - Creates a shared temp directory with git init.
      - Manually bootstraps the coding-aegis skill into .cursor/skills/coding-aegis/
        (simulating a plugin install, since no CLI plugin install exists yet).
      - Copies pkgs/ catalog into test_dir so the skill can access it.
      - Runs teardown (best-effort helloworld uninstall) after all tests.
    """

    @pytest.fixture(autouse=True, scope="class")
    def journey(self, tmp_path_factory, repo_root):
        """Class-scoped fixture owning setup and teardown for the full journey.

        SETUP (phases 1-3):
          - Creates a shared temporary test directory with git init.
          - Builds clean_env (CLAUDECODE / CLAUDE_CODE_ENTRYPOINT stripped,
            CURSOR_AGENT=1 injected for detect_tool detection).
          - Manually installs coding-aegis skill into .cursor/skills/coding-aegis/
            (workaround for absent CLI plugin install).
          - Copies pkgs/ catalog into test_dir.
          - Pre-creates .cursor/rules and .cursor/skills directories.

        TEARDOWN (phase 6):
          - Best-effort helloworld uninstall (if helloworld_installed is True).
          - Temp dir cleanup handled automatically by tmp_path_factory.
        """
        # Build a clean env: strip Claude Code vars, inject Cursor signal
        clean_env = os.environ.copy()
        clean_env.pop("CLAUDECODE", None)
        clean_env.pop("CLAUDE_CODE_ENTRYPOINT", None)
        clean_env["CURSOR_AGENT"] = "1"

        state = {}
        state["repo_root"] = repo_root
        state["test_dir"] = tmp_path_factory.mktemp("cursor-journey")
        state["clean_env"] = clean_env
        state["helloworld_installed"] = False

        test_dir: Path = state["test_dir"]

        # Phase 1 precondition: git init
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # Phase 3 bootstrap: manually copy coding-aegis skill into .cursor/skills/
        # This simulates what a cursor plugin install would do.
        # TODO: replace with native CLI plugin install once Cursor documents it.
        cursor_skill_dir = test_dir / ".cursor" / "skills" / "coding-aegis"
        cursor_skill_dir.mkdir(parents=True, exist_ok=True)
        skill_src = (
            repo_root
            / "pkgs"
            / "bootstrap"
            / "coding-aegis"
            / "skills"
            / "coding-aegis"
        )
        shutil.copytree(str(skill_src), str(cursor_skill_dir), dirs_exist_ok=True)

        # Pre-create .cursor/rules so the agent can write rule files
        (test_dir / ".cursor" / "rules").mkdir(parents=True, exist_ok=True)

        # Copy pkgs/ catalog into test_dir so the skill can access it
        pkgs_dest = test_dir / "pkgs"
        if not pkgs_dest.exists():
            shutil.copytree(str(repo_root / "pkgs"), str(pkgs_dest))

        state["cursor_skill_dir"] = cursor_skill_dir

        yield state

        # ── TEARDOWN ──────────────────────────────────────────────────────────
        # Phase 6: best-effort helloworld uninstall (if still marked installed)
        if state.get("helloworld_installed"):
            run_cli(
                _cursor_p("--force"),
                prompt="/coding-aegis uninstall helloworld",
                cwd=test_dir,
                timeout=TIMEOUT_LONG,
                env=clean_env,
            )

        # Temp dir is cleaned automatically by tmp_path_factory.

    # ── Phase 1: Environment & Tool Validation ────────────────────────────

    def test_phase1_auth(self, journey):
        """Phase 1 — cursor-agent can authenticate and respond."""
        result = run_cli(
            _cursor_p(),
            prompt="Reply with exactly: AUTH_OK",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "auth check")
        warn_if_slow(result, label="auth check")
        assert_no_quota_error(result, "cursor-agent")
        assert "AUTH_OK" in result.stdout, (
            f"Expected AUTH_OK in output, got:\n{result.stdout[:2000]}"
        )

    # ── Phase 2: Marketplace / Registry (manifest check only) ────────────

    def test_phase2_plugin_manifest(self, journey):
        """Phase 2 — .cursor-plugin/marketplace.json exists with expected fields.

        Cursor plugin marketplace is IDE-based; CLI registration is not yet
        documented. This test validates the manifest file only.
        """
        manifest = journey["repo_root"] / ".cursor-plugin" / "marketplace.json"
        assert manifest.exists(), (
            f".cursor-plugin/marketplace.json not found at {manifest}"
        )
        data = json.loads(manifest.read_text())
        # Manifest should list at least one plugin entry referencing coding-aegis
        plugins = data.get("plugins", [])
        assert len(plugins) > 0, f"marketplace.json 'plugins' list is empty: {data}"
        names = [p.get("name", "") for p in plugins]
        assert "coding-aegis" in names, (
            f"marketplace.json does not list 'coding-aegis': {data}"
        )

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_files_present(self, journey):
        """Phase 3 — expected files present in .cursor/skills/coding-aegis/."""
        skill_dir: Path = journey["cursor_skill_dir"]
        for filename in ("SKILL.md", "aegis_lib.py", "aegis-install.py",
                         "aegis-uninstall.py", "detect_tool.py"):
            assert (skill_dir / filename).exists(), (
                f"{filename} not found in {skill_dir}"
            )

    # ── Phase 4: Validate coding-aegis skill ──────────────────────────────

    def test_phase4a_detect_tool_direct(self, journey):
        """Phase 4a — detect_tool.py run directly returns tool=cursor with signals."""
        skill_dir: Path = journey["cursor_skill_dir"]
        result = run_cli(
            ["python3", str(skill_dir / "detect_tool.py")],
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect_tool.py direct")
        # Parse the JSON block from stdout (may have python warnings before it)
        json_start = result.stdout.find("{")
        assert json_start != -1, (
            f"No JSON in detect_tool.py output:\n{result.stdout}"
        )
        data = json.loads(result.stdout[json_start:])
        assert data.get("tool") == "cursor", (
            f"detect_tool.py: expected tool='cursor', got {data}"
        )
        assert len(data.get("signals", [])) > 0, (
            f"detect_tool.py: expected non-empty signals, got {data}"
        )

    def test_phase4b_detect_tool_skill(self, journey):
        """Phase 4b — /coding-aegis detect-tool via agent reports cursor + signals."""
        result = run_cli(
            _cursor_p(),
            prompt="/coding-aegis detect-tool",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "detect-tool skill")
        warn_if_slow(result, label="detect-tool skill")
        assert_no_quota_error(result, "cursor-agent")
        assert "cursor" in result.stdout.lower(), (
            f"detect-tool: expected 'cursor' in output:\n{result.stdout[:2000]}"
        )
        assert any(sig in result.stdout.lower() for sig in ("env:", "path:")), (
            f"detect-tool: expected at least one signal in output:\n{result.stdout[:2000]}"
        )

    def test_phase4c_list(self, journey):
        """Phase 4c — /coding-aegis list shows helloworld."""
        result = run_cli(
            _cursor_p(),
            prompt="/coding-aegis list --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill list")
        warn_if_slow(result, label="skill list")
        assert_no_quota_error(result, "cursor-agent")
        assert "helloworld" in result.stdout.lower(), (
            f"list: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )

    def test_phase4d_show(self, journey):
        """Phase 4d — /coding-aegis show helloworld returns name, tier, version."""
        result = run_cli(
            _cursor_p(),
            prompt="/coding-aegis show helloworld --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "skill show")
        warn_if_slow(result, label="skill show")
        assert_no_quota_error(result, "cursor-agent")
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
        """Phase 5 — /coding-aegis install helloworld writes rule and skill files.

        Cursor delivers rules to .cursor/rules/ as markdown files with YAML
        frontmatter (same layout as Claude but under .cursor/, not .claude/).
        Skills install to .cursor/skills/<name>/.
        """
        catalog_arg = str(journey["test_dir"] / "pkgs")
        result = run_cli(
            _cursor_p("--force"),
            prompt=f"/coding-aegis install helloworld to Project scope --catalog {catalog_arg}",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "install helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="install helloworld")
        assert_no_quota_error(result, "cursor-agent")
        output_lower = result.stdout.lower()
        assert any(kw in output_lower for kw in (
            "install", "aegis--helloworld", "wrote", "created", "helloworld"
        )), f"install: expected activity in output:\n{result.stdout[:2000]}"
        assert not any(kw in output_lower for kw in (
            "denied", "unable to write", "permission"
        )), f"install: permission error in output:\n{result.stdout[:2000]}"

        # Verify rule file was written to .cursor/rules/
        rule_file = (
            journey["test_dir"]
            / ".cursor"
            / "rules"
            / "aegis--helloworld--helloworld.mdc"
        )
        assert rule_file.exists(), (
            f"Rule file not found: {rule_file}\n"
            f"Contents of .cursor/rules/: "
            f"{list((journey['test_dir'] / '.cursor' / 'rules').iterdir())}"
        )

        # Verify rule file frontmatter
        text = rule_file.read_text()
        assert "managed-by: coding-aegis" in text, (
            f"frontmatter missing 'managed-by: coding-aegis':\n{text[:500]}"
        )
        assert "package: helloworld" in text, (
            f"frontmatter missing 'package: helloworld':\n{text[:500]}"
        )
        assert "tier: optional" in text, (
            f"frontmatter missing 'tier: optional':\n{text[:500]}"
        )

        # Verify skill file was written to .cursor/skills/helloworld/
        skill_file = (
            journey["test_dir"] / ".cursor" / "skills" / "helloworld" / "SKILL.md"
        )
        assert skill_file.exists(), f"Skill file not found: {skill_file}"

        journey["helloworld_installed"] = True

    def test_phase5b_helloworld_responds(self, journey):
        """Phase 5b — /helloworld skill returns 'Hello, World'."""
        result = run_cli(
            _cursor_p(),
            prompt="/helloworld",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "invoke helloworld")
        warn_if_slow(result, label="invoke helloworld")
        assert_no_quota_error(result, "cursor-agent")
        assert "Hello, World" in result.stdout, (
            f"helloworld skill: expected 'Hello, World' in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 6: Uninstall helloworld ─────────────────────────────────────

    def test_phase6_uninstall_helloworld(self, journey):
        """Phase 6 — /coding-aegis uninstall helloworld removes installed files."""
        result = run_cli(
            _cursor_p("--force"),
            prompt="/coding-aegis uninstall helloworld",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
            env=journey["clean_env"],
        )
        assert_no_timeout(result, "uninstall helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="uninstall helloworld")
        assert_no_quota_error(result, "cursor-agent")
        assert not any(kw in result.stdout for kw in ("not installed", "not found", "Error")), (
            f"uninstall: unexpected error in output:\n{result.stdout[:2000]}"
        )

        # Verify rule file and skill dir are removed
        rule_file = (
            journey["test_dir"]
            / ".cursor"
            / "rules"
            / "aegis--helloworld--helloworld.mdc"
        )
        skill_dir = journey["test_dir"] / ".cursor" / "skills" / "helloworld"
        assert not rule_file.exists(), (
            f"Rule file still present after uninstall: {rule_file}"
        )
        assert not skill_dir.exists(), (
            f"Skill dir still present after uninstall: {skill_dir}"
        )

        journey["helloworld_installed"] = False
