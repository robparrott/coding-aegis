#!/usr/bin/env -S bash -l
# coding-aegis skill test — Claude Code
# Usage: tests/test-claude-bootstrapped-skill-install.sh
#
# Follows the 7-phase test plan per docs/test/testing-spec.md and docs/test/test-claude.md:
#   Phase 1  Environment & Tool Validation
#   Phase 2  Marketplace / Registry Setup
#   Phase 3  Install coding-aegis Skill
#   Phase 4  Validate coding-aegis Skill
#   Phase 5  Install & Verify helloworld Package
#   Phase 6  Uninstall helloworld Package
#   Phase 7  Full Cleanup
#
# Prompts are piped via stdin to avoid shell quoting issues.
# MCP servers are disabled via --strict-mcp-config to avoid startup hangs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/lib-test-harness.sh"

MARKETPLACE_NAME="coding-aegis"
TEST_DIR="$(mktemp -d)"

# Common flags for claude -p: disable MCP, use stdin for prompts
CLAUDE_COMMON="--strict-mcp-config --mcp-config {\"mcpServers\":{}}"

cleanup() {
  section "Phase 6: Uninstall helloworld Package"
  CLI_PROMPT="/coding-aegis uninstall helloworld"
  CLI_TIMEOUT="$TIMEOUT_LONG"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" claude -p \
    --allowedTools "Bash,Read,Glob,Skill" --dangerously-skip-permissions $CLAUDE_COMMON
  assert_not_contains "$LAST_OUTPUT" "not installed\|not found\|error" "uninstall — no errors"

  section "Phase 7: Full Cleanup"
  test_header "uninstall coding-aegis plugin"
  RUN_DIR="$TEST_DIR" run_cli "uninstall plugin" claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope project || true

  test_header "remove marketplace"
  run_cli "remove marketplace" claude plugin marketplace remove "$MARKETPLACE_NAME" || true
  run_cli "marketplace list" claude plugin marketplace list || true
  assert_not_contains "$LAST_OUTPUT" "$MARKETPLACE_NAME" "marketplace no longer in list"

  test_header "remove test directory"
  rm -rf "$TEST_DIR"
  assert_dir_not_exists "$TEST_DIR" "test directory removed"

  print_results
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Claude Code)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"

# ── Phase 1: Environment & Tool Validation ───────────────────
section "Phase 1: Environment & Tool Validation"

test_header "claude installed"
if command -v claude &>/dev/null; then
  pass "claude found: $(claude --version 2>&1 || echo unknown)"
else
  fail "claude not found in PATH"
  exit 1
fi

test_header "claude authenticated"
CLI_PROMPT="Reply with exactly: AUTH_OK"
run_cli "auth check" claude -p $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "AUTH_OK" "claude authenticated"

# ── Phase 2: Marketplace / Registry Setup ────────────────────
section "Phase 2: Marketplace / Registry Setup"

test_header "marketplace add (local)"
run_cli "marketplace add" claude plugin marketplace add "$REPO_ROOT"
assert_contains "$LAST_OUTPUT" "added\|success\|already" "marketplace add"
detected=$(echo "$LAST_OUTPUT" | grep -oi 'marketplace: [a-z_-]*' | head -1 | sed 's/marketplace: //' || true)
[ -n "$detected" ] && MARKETPLACE_NAME="$detected"

test_header "marketplace visible in list"
run_cli "marketplace list" claude plugin marketplace list
assert_contains "$LAST_OUTPUT" "$MARKETPLACE_NAME" "marketplace in list"

# ── Phase 3: Install coding-aegis Skill ──────────────────────
section "Phase 3: Install coding-aegis Skill"

test_header "plugin install"
RUN_DIR="$TEST_DIR" run_cli "plugin install" claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope project
assert_contains "$LAST_OUTPUT" "install" "plugin install"

test_header "plugin visible in list"
RUN_DIR="$TEST_DIR" run_cli "plugin list" claude plugin list
assert_contains "$LAST_OUTPUT" "coding-aegis" "coding-aegis in plugin list"

# Set up test directory with catalog
ln -s "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs" 2>/dev/null || cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── Phase 4: Validate coding-aegis Skill ─────────────────────
# Note: Claude's plugin system loads skill files from the marketplace source
# dynamically — it does not copy them into $TEST_DIR. Phase 3.3 (detect_tool.py
# present) and 4.1 (direct-bash detection) are validated via Codex, where
# $skill-installer physically copies files to ~/.codex/skills/.
section "Phase 4: Validate coding-aegis Skill"

test_header "coding-aegis detect-tool (skill command)"
CLI_PROMPT="/coding-aegis detect-tool"
RUN_DIR="$TEST_DIR" run_cli "skill detect-tool" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "claude" "detect-tool — tool name reported"
assert_contains "$LAST_OUTPUT" "env:\|path:" "detect-tool — at least one signal reported"

test_header "coding-aegis list"
CLI_PROMPT="/coding-aegis list"
RUN_DIR="$TEST_DIR" run_cli "skill list" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

test_header "coding-aegis show helloworld"
CLI_PROMPT="/coding-aegis show helloworld"
RUN_DIR="$TEST_DIR" run_cli "skill show" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── Phase 5: Install & Verify helloworld Package ─────────────
section "Phase 5: Install & Verify helloworld Package"

# Pre-create .claude/ directory structure so the agent doesn't balk at
# writing to a "sensitive" path that doesn't exist yet.
mkdir -p "$TEST_DIR/.claude/rules" "$TEST_DIR/.claude/skills"

test_header "coding-aegis install helloworld"
# Scope specified in prompt — the skill's interactive scope picker may not
# resolve correctly in headless (-p) mode.
CLI_PROMPT="/coding-aegis install helloworld to Project scope"
CLI_TIMEOUT="$TIMEOUT_LONG"
RUN_DIR="$TEST_DIR" run_cli "skill install" claude -p \
  --allowedTools "Bash,Read,Write,Glob,Skill,AskUserQuestion" \
  --dangerously-skip-permissions $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "aegis--helloworld\|Installed\|helloworld.*rule\|helloworld.*skill" "install — files written"
assert_not_contains "$LAST_OUTPUT" "denied\|unable to write\|permission" "install — no permission errors"

SCOPE_DIR="$TEST_DIR/.claude"
RULE_FILE="$SCOPE_DIR/rules/aegis--helloworld--helloworld.md"

test_header "rule file exists"
assert_file_exists "$RULE_FILE" "rule file: aegis--helloworld--helloworld.md"

test_header "rule frontmatter"
assert_file_contains "$RULE_FILE" "managed-by: coding-aegis" "frontmatter: managed-by"
assert_file_contains "$RULE_FILE" "package: helloworld" "frontmatter: package"
assert_file_contains "$RULE_FILE" "tier: optional" "frontmatter: tier"

test_header "skill file exists"
assert_file_exists "$SCOPE_DIR/skills/helloworld/SKILL.md" "skill file: helloworld/SKILL.md"

test_header "helloworld responds"
CLI_PROMPT="/helloworld"
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# Phase 6 & 7 teardown happens in cleanup trap
