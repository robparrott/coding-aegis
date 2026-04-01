#!/usr/bin/env -S bash -l
# coding-aegis skill test — OpenAI Codex CLI
# Usage: tests/test-codex-skill-install.sh
#
# Follows the user journey per docs/test/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Register marketplace (validate .codex-plugin/ manifest)
#   T2  Install coding-aegis skill via $skill-installer
#   T3  Use skill: list packages
#   T4  Use skill: show helloworld
#   T5  Use skill: install helloworld
#   T6  Verify installed files
#   T7  Teardown (step-by-step with validation)
#
# The $skill-installer is a built-in Codex system skill that installs
# skills from GitHub repos. T2 asks the Codex agent to use it — this
# is the actual user journey for skill distribution on Codex.
set -euo pipefail

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
  section "T7: Teardown"

  test_header "T7.1 uninstall helloworld via skill"
  CLI_PROMPT="\$coding-aegis uninstall helloworld"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" codex exec --ephemeral -s workspace-write -o /dev/stdout
  assert_not_contains "$LAST_OUTPUT" "not installed\|not found\|error" "uninstall — no errors"
  assert_dir_not_exists "$SKILL_INSTALL_DIR" "helloworld skill dir removed"

  test_header "T7.2 uninstall coding-aegis skill"
  rm -rf "$CODEX_SKILL_DIR"
  assert_dir_not_exists "$CODEX_SKILL_DIR" "coding-aegis removed from ~/.codex/skills/"

  test_header "T7.3 remove test directory"
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

# ── T0: Prerequisites ────────────────────────────────────────
section "T0: Prerequisites"

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

# ── T1: Register marketplace ─────────────────────────────────
section "T1: Register marketplace"

test_header "plugin manifest exists"
assert_file_exists "$PLUGIN_DIR/plugin.json" ".codex-plugin/plugin.json present"
assert_file_contains "$PLUGIN_DIR/plugin.json" '"name": "coding-aegis"' "manifest: name"
assert_file_contains "$PLUGIN_DIR/plugin.json" '"skills"' "manifest: skills path"

# ── T2: Install coding-aegis skill via $skill-installer ──────
section "T2: Install coding-aegis skill"

# Clean stale installation
rm -rf "$CODEX_SKILL_DIR"

test_header "install via \$skill-installer"
CLI_PROMPT="\$skill-installer install --repo ${GITHUB_REPO} --path ${SKILL_PATH}"
RUN_DIR="$TEST_DIR" run_cli "skill install" codex exec --ephemeral -s danger-full-access -o /dev/stdout
assert_contains "$LAST_OUTPUT" "install\|coding-aegis\|skill" "skill-installer ran"

test_header "skill installed to ~/.codex/skills/"
assert_file_exists "$CODEX_SKILL_DIR/SKILL.md" "SKILL.md installed"
assert_file_exists "$CODEX_SKILL_DIR/aegis-catalog.py" "aegis-catalog.py installed"

# Make catalog accessible in test directory
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── T3: Use skill — list ─────────────────────────────────────
section "T3: Use skill — list packages"

test_header "coding-aegis list"
CLI_PROMPT="\$coding-aegis list"
RUN_DIR="$TEST_DIR" run_cli "skill list" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

# ── T4: Use skill — show ─────────────────────────────────────
section "T4: Use skill — show helloworld"

test_header "coding-aegis show helloworld"
CLI_PROMPT="\$coding-aegis show helloworld"
RUN_DIR="$TEST_DIR" run_cli "skill show" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── T5: Use skill — install ──────────────────────────────────
section "T5: Use skill — install helloworld"

test_header "coding-aegis install helloworld"
# Scope must be specified in prompt — the skill's interactive scope picker
# (AskUserQuestion) cannot be used in Codex headless mode.
# Scope must be specified — the skill's interactive scope picker cannot
# be used in Codex headless mode.
CLI_PROMPT="\$coding-aegis install helloworld to Project scope"
RUN_DIR="$TEST_DIR" run_cli "skill install" codex exec --ephemeral -s workspace-write -o /dev/stdout
assert_contains "$LAST_OUTPUT" "install\|aegis--helloworld\|wrote\|created" "install — activity reported"

# ── T6: Verify installed files ────────────────────────────────
section "T6: Verify installed files"

# Rule file verification skipped for Codex — Codex rules go in AGENTS.md,
# not individual files. Tracked in 2sv.15.

test_header "files written by install"
echo -e "  ${DIM}$(find "$TEST_DIR" \( -name 'aegis--*' -o -name 'SKILL.md' -o -name 'AGENTS.md' \) -not -path '*/pkgs/*' 2>/dev/null | head -10 || echo '(none found)')${RESET}"

test_header "skill file exists"
assert_file_exists "$SKILL_INSTALL_DIR/SKILL.md" "skill file: .agents/skills/helloworld/SKILL.md"

# ── T6b: Invoke installed helloworld skill ────────────────────
section "T6b: Invoke helloworld skill"

test_header "helloworld responds"
CLI_PROMPT="\$helloworld"
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# T7 teardown happens in cleanup trap
