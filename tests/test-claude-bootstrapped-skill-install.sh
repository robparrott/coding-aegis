#!/usr/bin/env -S bash -l
# coding-aegis skill test — Claude Code
# Usage: tests/test-claude-bootstrapped-skill-install.sh
#
# Follows the user journey per docs/test/testing-spec.md:
#   T0   Prerequisites (installed + authenticated)
#   T1   Register marketplace
#   T2   Install coding-aegis plugin
#   T3   Use skill: detect-tool
#   T4   Use skill: list packages
#   T5   Use skill: show helloworld
#   T6   Use skill: install helloworld
#   T7   Verify installed files
#   T8   Invoke installed helloworld skill
#   T9   Teardown: uninstall helloworld
#   T10  Teardown: uninstall coding-aegis plugin
#   T11  Teardown: remove marketplace
#   T12  Teardown: remove test directory
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
  section "T9: Teardown — uninstall helloworld"
  CLI_PROMPT="/coding-aegis uninstall helloworld"
  CLI_TIMEOUT="$TIMEOUT_LONG"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" claude -p \
    --allowedTools "Bash,Read,Glob,Skill" --dangerously-skip-permissions $CLAUDE_COMMON
  assert_not_contains "$LAST_OUTPUT" "not installed\|not found\|error" "uninstall — no errors"

  section "T10: Teardown — uninstall coding-aegis plugin"
  RUN_DIR="$TEST_DIR" run_cli "uninstall plugin" claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope project || true

  section "T11: Teardown — remove marketplace"
  run_cli "remove marketplace" claude plugin marketplace remove "$MARKETPLACE_NAME" || true
  run_cli "marketplace list" claude plugin marketplace list || true
  assert_not_contains "$LAST_OUTPUT" "$MARKETPLACE_NAME" "marketplace no longer in list"

  section "T12: Teardown — remove test directory"
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

# ── T0: Prerequisites ────────────────────────────────────────
section "T0: Prerequisites"

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

# ── T1: Register Marketplace ─────────────────────────────────
section "T1: Register marketplace"

test_header "marketplace add (local)"
run_cli "marketplace add" claude plugin marketplace add "$REPO_ROOT"
assert_contains "$LAST_OUTPUT" "added\|success" "marketplace add"
detected=$(echo "$LAST_OUTPUT" | grep -oi 'marketplace: [a-z_-]*' | head -1 | sed 's/marketplace: //')
[ -n "$detected" ] && MARKETPLACE_NAME="$detected"

test_header "marketplace visible in list"
run_cli "marketplace list" claude plugin marketplace list
assert_contains "$LAST_OUTPUT" "$MARKETPLACE_NAME" "marketplace in list"

# ── T2: Install coding-aegis plugin ──────────────────────────
section "T2: Install coding-aegis plugin"

test_header "plugin install"
RUN_DIR="$TEST_DIR" run_cli "plugin install" claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope project
assert_contains "$LAST_OUTPUT" "install" "plugin install"

test_header "plugin visible in list"
RUN_DIR="$TEST_DIR" run_cli "plugin list" claude plugin list
assert_contains "$LAST_OUTPUT" "coding-aegis" "coding-aegis in plugin list"

# Set up test directory with catalog
ln -s "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs" 2>/dev/null || cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── T3: Use skill — detect-tool ──────────────────────────────
section "T3: Use skill — detect-tool"

test_header "coding-aegis detect-tool"
CLI_PROMPT="/coding-aegis detect-tool"
RUN_DIR="$TEST_DIR" run_cli "skill detect-tool" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "claude" "detect-tool — tool name reported"
assert_contains "$LAST_OUTPUT" "env:\|path:" "detect-tool — at least one signal reported"

# ── T4: Use skill — list ─────────────────────────────────────
section "T4: Use skill — list packages"

test_header "coding-aegis list"
CLI_PROMPT="/coding-aegis list"
RUN_DIR="$TEST_DIR" run_cli "skill list" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

# ── T5: Use skill — show ─────────────────────────────────────
section "T5: Use skill — show helloworld"

test_header "coding-aegis show helloworld"
CLI_PROMPT="/coding-aegis show helloworld"
RUN_DIR="$TEST_DIR" run_cli "skill show" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── T6: Use skill — install ──────────────────────────────────
section "T6: Use skill — install helloworld"

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

# ── T7: Verify installed files ────────────────────────────────
section "T7: Verify installed files"

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

# ── T8: Invoke installed helloworld skill ─────────────────────
section "T8: Invoke helloworld skill"

test_header "helloworld responds"
CLI_PROMPT="/helloworld"
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" claude -p \
  --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# T9–T12 teardown happens in cleanup trap
