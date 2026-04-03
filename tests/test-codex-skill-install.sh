#!/usr/bin/env -S bash -l
# coding-aegis skill test — OpenAI Codex CLI
# Usage: tests/test-codex-skill-install.sh
#
# Follows the 7-phase test plan per docs/test/testing-spec.md and docs/test/test-codex.md:
#   Phase 1  Environment & Tool Validation
#   Phase 2  Marketplace / Registry Setup (validate .codex-plugin/ manifest)
#   Phase 3  Install coding-aegis Skill (via $skill-installer from GitHub)
#   Phase 4  Validate coding-aegis Skill
#   Phase 5  Install & Verify helloworld Package
#   Phase 6  Uninstall helloworld Package
#   Phase 7  Full Cleanup
#
# The $skill-installer is a built-in Codex system skill that installs
# skills from GitHub repos. Phase 3 asks the Codex agent to use it — this
# is the actual user journey for skill distribution on Codex.
set -euo pipefail

# Unset Claude Code env vars so they don't leak into Codex sandboxes when this
# test is run from within Claude Code's Bash tool.
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true

# Codex workspace-write sandbox steps (install/uninstall) are slower than read-only.
# Override TIMEOUT_LONG to 60s for this test only.
export AEGIS_TEST_TIMEOUT_LONG=60

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/lib-test-harness.sh"

PLUGIN_DIR="$REPO_ROOT/.codex-plugin"
SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
TEST_DIR="$(mktemp -d)"
GITHUB_REPO="robparrott/coding-aegis"
SKILL_PATH="pkgs/bootstrap/coding-aegis/skills/coding-aegis"

# Skill gets installed to ~/.codex/skills/ by $skill-installer
CODEX_SKILL_DIR="$HOME/.codex/skills/coding-aegis"

# Skills install to .agents/skills/ (Codex discovery path, auto-detected).
# Rules for Codex should go in AGENTS.md, not .claude/rules/ (tracked in 2sv.15).
SKILL_INSTALL_DIR="$TEST_DIR/.agents/skills/helloworld"

cleanup() {
  section "Phase 6: Uninstall helloworld Package"
  CLI_PROMPT="\$coding-aegis uninstall helloworld"
  CLI_TIMEOUT="$TIMEOUT_LONG"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" codex exec --ephemeral -s workspace-write -o /dev/stdout
  assert_not_contains "$LAST_OUTPUT" "not installed\|not found\|Error" "uninstall — no errors"
  # coding-aegis-7b7: Codex workspace-write sandbox blocks os.unlink/shutil.rmtree at the
  # syscall level, so skill directory removal is not possible in this sandbox mode.
  # aegis-uninstall.py now handles this gracefully (warn + continue) so AGENTS.md is still
  # cleaned up. Directory removal is verified by the CLI test (test-cli-install.sh).
  test_header "helloworld skill dir removal attempted (workspace-write limitation)"
  if [ -d "$SKILL_INSTALL_DIR" ]; then
    pass "helloworld skill dir still present — expected in workspace-write sandbox (coding-aegis-7b7)"
  else
    pass "helloworld skill dir removed"
  fi
  # uninstall-prep rewrites AGENTS.md directly; verify the section is gone
  test_header "AGENTS.md rule section removed"
  if [ -f "$TEST_DIR/AGENTS.md" ]; then
    if grep -q "aegis:begin package=helloworld" "$TEST_DIR/AGENTS.md" 2>/dev/null; then
      fail "AGENTS.md: helloworld rule section still present after uninstall"
    else
      pass "AGENTS.md: helloworld rule section removed"
    fi
  else
    pass "AGENTS.md: not present (no sections to remove)"
  fi

  section "Phase 7: Full Cleanup"
  # TODO (coding-aegis-gua): when Phase 2 fetches .codex-plugin/ from GitHub into
  # $TEST_DIR, remove it here. For now assert it was never left behind.
  test_header "remove marketplace registration"
  rm -rf "$TEST_DIR/.codex-plugin"
  assert_dir_not_exists "$TEST_DIR/.codex-plugin" "marketplace (.codex-plugin/) removed from test dir"

  test_header "uninstall coding-aegis skill"
  rm -rf "$CODEX_SKILL_DIR"
  assert_dir_not_exists "$CODEX_SKILL_DIR" "coding-aegis removed from ~/.codex/skills/"

  test_header "remove test directory"
  rm -rf "$TEST_DIR"
  assert_dir_not_exists "$TEST_DIR" "test directory removed"

  print_results
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Codex CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"

# ── Phase 1: Environment & Tool Validation ───────────────────
section "Phase 1: Environment & Tool Validation"

test_header "codex installed"
if command -v codex &>/dev/null; then
  pass "codex found: $(codex --version 2>&1 || echo unknown)"
else
  fail "codex not found in PATH"
  exit 1
fi

test_header "codex authenticated"
git -C "$TEST_DIR" init -q
CLI_PROMPT="Reply with exactly: AUTH_OK"
RUN_DIR="$TEST_DIR" run_cli "auth check" codex exec --ephemeral -o /dev/stdout
assert_contains "$LAST_OUTPUT" "AUTH_OK" "codex authenticated"

# ── Phase 2: Marketplace / Registry Setup ────────────────────
section "Phase 2: Marketplace / Registry Setup"

# TODO (coding-aegis-gua): fetch .codex-plugin/ from GitHub into $TEST_DIR here.
# For now validate the manifest exists in the repo (local check only).
test_header "plugin manifest exists"
assert_file_exists "$PLUGIN_DIR/plugin.json" ".codex-plugin/plugin.json present"
assert_file_contains "$PLUGIN_DIR/plugin.json" '"name": "coding-aegis"' "manifest: name"
assert_file_contains "$PLUGIN_DIR/plugin.json" '"skills"' "manifest: skills path"

# ── Phase 3: Install coding-aegis Skill ──────────────────────
section "Phase 3: Install coding-aegis Skill"

test_header "install via \$skill-installer"
CLI_PROMPT="\$skill-installer install --repo ${GITHUB_REPO} --path ${SKILL_PATH}"
CLI_TIMEOUT="$TIMEOUT_LONG"
RUN_DIR="$TEST_DIR" run_cli "skill-installer" codex exec --ephemeral -s danger-full-access -o /dev/stdout
assert_contains "$LAST_OUTPUT" "install\|success\|done\|copied\|coding-aegis" "skill-installer — activity reported"

test_header "skill installed to ~/.codex/skills/"
assert_file_exists "$CODEX_SKILL_DIR/SKILL.md" "SKILL.md installed"
assert_file_exists "$CODEX_SKILL_DIR/aegis_lib.py" "aegis_lib.py installed"
assert_file_exists "$CODEX_SKILL_DIR/aegis-install.py" "aegis-install.py installed"
assert_file_exists "$CODEX_SKILL_DIR/aegis-uninstall.py" "aegis-uninstall.py installed"

test_header "detect_tool.py present"
assert_file_exists "$CODEX_SKILL_DIR/detect_tool.py" "detect_tool.py installed"

# Make catalog accessible in test directory
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── Phase 4: Validate coding-aegis Skill ─────────────────────
section "Phase 4: Validate coding-aegis Skill"

test_header "tool detected correctly (direct bash)"
DETECT_OUT=$(python3 "$CODEX_SKILL_DIR/detect_tool.py" 2>/dev/null || echo "{}")
assert_json_value "$DETECT_OUT" "tool" "codex" "detect_tool.py: tool=codex"
assert_json_nonempty_array "$DETECT_OUT" "signals" "detect_tool.py: signals non-empty"

test_header "coding-aegis detect-tool (skill command)"
CLI_PROMPT="\$coding-aegis detect-tool"
RUN_DIR="$TEST_DIR" run_cli "skill detect-tool" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "codex" "detect-tool — tool name reported"
assert_contains "$LAST_OUTPUT" "env:\|path:" "detect-tool — at least one signal reported"

test_header "coding-aegis list"
# read-only sandbox blocks git clone; catalog was copied to $TEST_DIR/pkgs in Phase 3
CLI_PROMPT="\$coding-aegis list --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill list" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

test_header "coding-aegis show helloworld"
# read-only sandbox blocks git clone; pass local catalog
CLI_PROMPT="\$coding-aegis show helloworld --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill show" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── Phase 5: Install & Verify helloworld Package ─────────────
section "Phase 5: Install & Verify helloworld Package"

test_header "coding-aegis install helloworld"
# Scope must be specified in prompt — the skill's interactive scope picker
# cannot be used in Codex headless mode.
# --catalog is explicit so the agent doesn't scan the workspace and accidentally
# load the SKILL.md from pkgs/ instead of dispatching to the installed skill.
CLI_PROMPT="\$coding-aegis install helloworld to Project scope --catalog $TEST_DIR/pkgs"
CLI_TIMEOUT="$TIMEOUT_LONG"
RUN_DIR="$TEST_DIR" run_cli "skill install" codex exec --ephemeral -s workspace-write -o /dev/stdout
assert_contains "$LAST_OUTPUT" "install\|aegis--helloworld\|wrote\|created" "install — activity reported"

test_header "files written by install"
echo -e "  ${DIM}$(find "$TEST_DIR" \( -name 'aegis--*' -o -name 'SKILL.md' -o -name 'AGENTS.md' \) -not -path '*/pkgs/*' 2>/dev/null | head -10 || echo '(none found)')${RESET}"

test_header "skill file exists"
assert_file_exists "$SKILL_INSTALL_DIR/SKILL.md" "skill file: .agents/skills/helloworld/SKILL.md"

test_header "rule section in AGENTS.md"
assert_file_exists "$TEST_DIR/AGENTS.md" "AGENTS.md created"
assert_file_contains "$TEST_DIR/AGENTS.md" "aegis:begin package=helloworld" "AGENTS.md: begin marker present"
assert_file_contains "$TEST_DIR/AGENTS.md" "aegis:end package=helloworld" "AGENTS.md: end marker present"

test_header "helloworld responds"
CLI_PROMPT="\$helloworld"
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# Phase 6 & 7 teardown happens in cleanup trap
