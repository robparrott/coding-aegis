"""
test_claude.py — Full 7-phase integration test for Claude Code.

Ports tests/test-claude-bootstrapped-skill-install.sh to pytest.

Uses Pattern 1: a single TestClaudeJourney class with a class-scoped journey
fixture. The 7-phase test is inherently sequential with shared state and
mandatory cleanup, so all phases share one fixture:

  - Phases 2-3 (marketplace add, plugin install, catalog symlink, .claude/ dirs)
    run in fixture SETUP — they are preconditions, not assertions.
  - Phases 4-5 are test methods that assert observable behavior.
  - Phase 6 uninstall is both a test method (assert it succeeds) AND attempted
    in fixture TEARDOWN (so cleanup always runs even if the test is skipped).
  - Phases 7 cleanup (plugin uninstall, marketplace remove) run in fixture
    TEARDOWN — they always execute regardless of test outcomes.

Run:
    pytest tests/integration/test_claude.py -v
    pytest tests/integration/test_claude.py -v -s    # stream agent output
    pytest tests/integration/test_claude.py -v -x    # stop at first failure

Claude invocation flags (from the bash script):
    claude -p --strict-mcp-config --mcp-config '{"mcpServers":{}}' \\
        --allowedTools Bash,Read,Write,Glob,Skill,AskUserQuestion \\
        --dangerously-skip-permissions
"""

import re
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

# ── Skip entire module if claude is not on PATH ──────────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("claude"),
    reason="claude not installed / not on PATH",
)

# ── Constants ─────────────────────────────────────────────────────────────────

TIMEOUT_LONG = 60  # install/uninstall/write operations

CLAUDE_COMMON_FLAGS = [
    "--strict-mcp-config",
    "--mcp-config",
    '{"mcpServers":{}}',
]

ALLOWED_TOOLS_RO = "--allowedTools=Bash,Read,Glob,Skill"
ALLOWED_TOOLS_RW = "--allowedTools=Bash,Read,Write,Glob,Skill,AskUserQuestion"

MARKETPLACE_NAME = "coding-aegis"


# ── Helper ────────────────────────────────────────────────────────────────────

def _claude_p(*extra_flags, allowed_tools: str = ALLOWED_TOOLS_RO) -> list:
    """Return the base ``claude -p`` command list."""
    return ["claude", "-p", allowed_tools] + list(CLAUDE_COMMON_FLAGS) + list(extra_flags)


# ── Test class ────────────────────────────────────────────────────────────────

class TestClaudeJourney:
    """
    Single class covering all 7 phases of the Claude Code integration journey.

    The class-scoped journey fixture runs setup (phases 2-3) once before any
    test method and teardown (phases 6-7 cleanup) once after all test methods,
    regardless of test outcomes.
    """

    @pytest.fixture(autouse=True, scope="class")
    def journey(self, tmp_path_factory, repo_root):
        """Class-scoped fixture that owns setup and teardown for the full journey.

        SETUP (phases 2-3):
          - Creates the shared temporary test directory.
          - Registers the local repo as a Claude plugin marketplace.
          - Installs the coding-aegis plugin into the test project scope.
          - Creates a pkgs/ symlink so the agent can locate the catalog.
          - Pre-creates .claude/rules and .claude/skills directories.

        TEARDOWN (phases 6-7):
          - Best-effort uninstall helloworld (in case phase 6 test was skipped).
          - Uninstall coding-aegis plugin from project scope.
          - Remove the marketplace registration.
          - Temp dir cleanup is handled automatically by tmp_path_factory.
        """
        state = {}
        state["repo_root"] = repo_root
        state["test_dir"] = tmp_path_factory.mktemp("claude-journey")
        state["marketplace_name"] = MARKETPLACE_NAME
        state["helloworld_installed"] = False

        test_dir: Path = state["test_dir"]
        marketplace_name: str = state["marketplace_name"]

        # ── Phase 1 precondition: git init ────────────────────────────────────
        run_cli(["git", "init", "-q"], cwd=test_dir)

        # ── Phase 2: Marketplace setup ────────────────────────────────────────
        result = run_cli(
            ["claude", "plugin", "marketplace", "add", str(repo_root)],
        )
        assert_no_timeout(result, "marketplace add (setup)")
        lower = result.stdout.lower()
        assert any(kw in lower for kw in ("added", "success", "already")), (
            f"marketplace add (setup): unexpected output:\n{result.stdout[:2000]}"
        )
        # Detect actual marketplace name from output, if reported
        m = re.search(r"marketplace:\s*([a-z_-]+)", result.stdout, re.IGNORECASE)
        if m:
            state["marketplace_name"] = m.group(1)
            marketplace_name = state["marketplace_name"]

        # ── Phase 3: Install coding-aegis plugin ──────────────────────────────
        result = run_cli(
            ["claude", "plugin", "install",
             f"coding-aegis@{marketplace_name}", "--scope", "project"],
            cwd=test_dir,
        )
        assert_no_timeout(result, "plugin install (setup)")
        assert "install" in result.stdout.lower(), (
            f"plugin install (setup): expected 'install' in output:\n{result.stdout[:2000]}"
        )

        # Catalog symlink so agent can find packages
        pkgs_link = test_dir / "pkgs"
        if not pkgs_link.exists():
            pkgs_link.symlink_to(repo_root / "pkgs")

        # Pre-create .claude directories so the agent can write to them
        scope_dir = test_dir / ".claude"
        (scope_dir / "rules").mkdir(parents=True, exist_ok=True)
        (scope_dir / "skills").mkdir(parents=True, exist_ok=True)

        # ── Hand off to test methods ──────────────────────────────────────────
        yield state

        # ── TEARDOWN ──────────────────────────────────────────────────────────
        # Phase 6: uninstall helloworld (best-effort, in case test was skipped)
        if state.get("helloworld_installed"):
            run_cli(
                _claude_p("--dangerously-skip-permissions", allowed_tools=ALLOWED_TOOLS_RW),
                prompt="/coding-aegis uninstall helloworld",
                cwd=test_dir,
                timeout=DEFAULT_TIMEOUT,
            )

        # Phase 7: uninstall plugin (best-effort)
        run_cli(
            ["claude", "plugin", "uninstall",
             f"coding-aegis@{state['marketplace_name']}", "--scope", "project"],
            cwd=test_dir,
        )

        # Phase 7: remove marketplace (best-effort)
        run_cli(
            ["claude", "plugin", "marketplace", "remove", state["marketplace_name"]],
        )

        # Temp dir is cleaned automatically by tmp_path_factory.

    # ── Phase 1: Environment & Tool Validation ─────────────────────────────

    def test_phase1_auth(self, journey):
        """Phase 1 — claude can authenticate and respond."""
        result = run_cli(
            _claude_p(),
            prompt="Reply with exactly: AUTH_OK",
            timeout=DEFAULT_TIMEOUT,
        )
        assert_no_timeout(result, "auth check")
        warn_if_slow(result, label="auth check")
        assert "AUTH_OK" in result.stdout, (
            f"Expected AUTH_OK in output, got:\n{result.stdout[:2000]}"
        )

    # ── Phase 2: Plugin manifest ──────────────────────────────────────────

    def test_phase2_plugin_manifest(self, journey):
        """Phase 2 — .claude-plugin/marketplace.json exists with expected fields."""
        manifest = journey["repo_root"] / ".claude-plugin" / "marketplace.json"
        assert manifest.exists(), (
            f".claude-plugin/marketplace.json not found at {manifest}"
        )
        import json
        data = json.loads(manifest.read_text())
        plugins = data.get("plugins", [])
        assert len(plugins) > 0, f"marketplace.json 'plugins' list is empty: {data}"
        names = [p.get("name", "") for p in plugins]
        assert "coding-aegis" in names, (
            f"marketplace.json does not list 'coding-aegis': {data}"
        )

    # ── Phase 3: Skill discoverability ────────────────────────────────────

    def test_phase3_skill_discoverable(self, journey):
        """Phase 3 — coding-aegis appears in claude plugin list."""
        result = run_cli(
            ["claude", "plugin", "list"],
            cwd=journey["test_dir"],
        )
        assert_no_timeout(result, "plugin list")
        assert "coding-aegis" in result.stdout, (
            f"Expected 'coding-aegis' in plugin list:\n{result.stdout[:2000]}"
        )

    # ── Phase 4: Validate coding-aegis skill ──────────────────────────────

    def test_phase4a_detect_tool_direct(self, journey):
        """Phase 4a — detect_tool.py run directly returns tool=claude.

        Runs detect_tool.py from the repo source (the claude plugin mechanism
        does not copy files to a predictable local path). The test runs inside
        a Claude Code session so CLAUDECODE=1 is already set.
        """
        import json as _json
        skill_dir = (
            journey["repo_root"]
            / "pkgs" / "bootstrap" / "coding-aegis" / "skills" / "coding-aegis"
        )
        result = run_cli(
            ["python3", str(skill_dir / "detect_tool.py")],
        )
        assert_no_timeout(result, "detect_tool.py direct")
        json_start = result.stdout.find("{")
        assert json_start != -1, (
            f"No JSON in detect_tool.py output:\n{result.stdout}"
        )
        data = _json.loads(result.stdout[json_start:])
        assert data.get("tool") == "claude", (
            f"detect_tool.py: expected tool='claude', got {data}"
        )
        assert len(data.get("signals", [])) > 0, (
            f"detect_tool.py: expected non-empty signals, got {data}"
        )

    def test_phase4b_detect_tool_skill(self, journey):
        """Phase 4b — /coding-aegis detect-tool via agent reports 'claude' and a signal."""
        result = run_cli(
            _claude_p(ALLOWED_TOOLS_RO),
            prompt="/coding-aegis detect-tool",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
        )
        assert_no_timeout(result, "detect-tool skill")
        warn_if_slow(result, label="detect-tool skill")
        assert_no_quota_error(result, "claude")
        assert "claude" in result.stdout.lower(), (
            f"detect-tool: expected 'claude' in output:\n{result.stdout[:2000]}"
        )
        assert any(sig in result.stdout.lower() for sig in ("env:", "path:")), (
            f"detect-tool: expected at least one signal (env: or path:) in output:\n"
            f"{result.stdout[:2000]}"
        )

    def test_phase4c_list(self, journey):
        """Phase 4c — /coding-aegis list shows helloworld."""
        result = run_cli(
            _claude_p(ALLOWED_TOOLS_RO),
            prompt="/coding-aegis list --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
        )
        assert_no_timeout(result, "skill list")
        warn_if_slow(result, label="skill list")
        assert_no_quota_error(result, "claude")
        assert "helloworld" in result.stdout.lower(), (
            f"list: expected 'helloworld' in output:\n{result.stdout[:2000]}"
        )

    def test_phase4d_show(self, journey):
        """Phase 4d — /coding-aegis show helloworld returns name, tier, version."""
        result = run_cli(
            _claude_p(ALLOWED_TOOLS_RO),
            prompt="/coding-aegis show helloworld --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
        )
        assert_no_timeout(result, "skill show")
        warn_if_slow(result, label="skill show")
        assert_no_quota_error(result, "claude")
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
            _claude_p("--dangerously-skip-permissions", allowed_tools=ALLOWED_TOOLS_RW),
            prompt="/coding-aegis install helloworld to Project scope --catalog pkgs",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
        )
        assert_no_timeout(result, "install helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="install helloworld")
        assert_no_quota_error(result, "claude")
        output_lower = result.stdout.lower()
        assert any(kw in output_lower for kw in (
            "aegis--helloworld", "installed", "helloworld.*rule", "helloworld.*skill"
        )) or "helloworld" in output_lower, (
            f"install: expected install activity in output:\n{result.stdout[:2000]}"
        )
        assert not any(kw in output_lower for kw in ("denied", "unable to write", "permission")), (
            f"install: permission error in output:\n{result.stdout[:2000]}"
        )

        # Verify rule file was written
        rule_file = (
            journey["test_dir"] / ".claude" / "rules" / "aegis--helloworld--helloworld.md"
        )
        assert rule_file.exists(), (
            f"Rule file not found: {rule_file}\n"
            f"Contents of .claude/rules/: "
            f"{list((journey['test_dir'] / '.claude' / 'rules').iterdir())}"
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

        # Verify skill file was written
        skill_file = (
            journey["test_dir"] / ".claude" / "skills" / "helloworld" / "SKILL.md"
        )
        assert skill_file.exists(), f"Skill file not found: {skill_file}"

        # Mark installed so teardown knows to attempt cleanup
        journey["helloworld_installed"] = True

    def test_phase5b_helloworld_responds(self, journey):
        """Phase 5b — /helloworld skill returns 'Hello, World'."""
        result = run_cli(
            _claude_p(ALLOWED_TOOLS_RO),
            prompt="/helloworld",
            cwd=journey["test_dir"],
            timeout=DEFAULT_TIMEOUT,
        )
        assert_no_timeout(result, "invoke helloworld")
        warn_if_slow(result, label="invoke helloworld")
        assert_no_quota_error(result, "claude")
        assert "Hello, World" in result.stdout, (
            f"helloworld skill: expected 'Hello, World' in output:\n{result.stdout[:2000]}"
        )

    # ── Phase 6: Uninstall helloworld (assertion + teardown backup) ────────

    def test_phase6_uninstall_helloworld(self, journey):
        """Phase 6 — /coding-aegis uninstall helloworld removes installed files."""
        result = run_cli(
            _claude_p("--dangerously-skip-permissions", allowed_tools=ALLOWED_TOOLS_RW),
            prompt="/coding-aegis uninstall helloworld",
            cwd=journey["test_dir"],
            timeout=TIMEOUT_LONG,
        )
        assert_no_timeout(result, "uninstall helloworld")
        warn_if_slow(result, budget_seconds=TIMEOUT_LONG, label="uninstall helloworld")
        assert_no_quota_error(result, "claude")
        assert not any(kw in result.stdout for kw in ("not installed", "not found", "Error")), (
            f"uninstall: unexpected error in output:\n{result.stdout[:2000]}"
        )

        # Verify installed files are gone
        rule_file = (
            journey["test_dir"] / ".claude" / "rules" / "aegis--helloworld--helloworld.md"
        )
        skill_dir = journey["test_dir"] / ".claude" / "skills" / "helloworld"
        assert not rule_file.exists(), f"Rule file still present after uninstall: {rule_file}"
        assert not skill_dir.exists(), f"Skill dir still present after uninstall: {skill_dir}"

        # Mark as uninstalled so teardown does not attempt a redundant uninstall
        journey["helloworld_installed"] = False
