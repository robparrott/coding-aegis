#!/usr/bin/env -S bash -l
# coding-aegis skill test — Google Gemini CLI
# Usage: tests/test-gemini-skill-install.sh
#
# Follows the 7-phase test plan per docs/test/testing-spec.md and docs/test/test-gemini.md:
#   Phase 1  Environment & Tool Validation
#   Phase 2  Marketplace / Registry Setup (N/A — Gemini uses skills link directly)
#   Phase 3  Install coding-aegis Skill (gemini skills link)
#   Phase 4  Validate coding-aegis Skill
#   Phase 5  Install & Verify helloworld Package
#   Phase 6  Uninstall helloworld Package
#   Phase 7  Full Cleanup
#
# Note: Gemini CLI on Homebrew emits keytar/keychain warnings.
# We filter them via gemini_quiet wrapper.
set -euo pipefail

# Unset Claude Code env vars so they don't leak into Gemini subprocesses when
# this test is run from within Claude Code's Bash tool.
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/lib-test-harness.sh"

SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
TEST_DIR="$(mktemp -d)"

# Model to use for all agent invocations — flash keeps latency low and avoids quota burn
GEMINI_MODEL="gemini-3-flash-preview"

# Filter noisy keytar warnings from gemini chat commands; pin model via -m
gemini_quiet() {
  gemini -m "$GEMINI_MODEL" "$@" 2>&1 | grep -v -E "Keychain initialization|keytar\.node|keytar\.js|FileKeychain fallback|Loaded cached credentials\.|^Require stack:"
}

# Filter keytar warnings from gemini subcommands (skills, etc.) — no -m flag
gemini_sub() {
  gemini "$@" 2>&1 | grep -v -E "Keychain initialization|keytar\.node|keytar\.js|FileKeychain fallback|Loaded cached credentials\.|^Require stack:"
}

cleanup() {
  section "Phase 6: Uninstall helloworld Package"
  # Skip agent-mediated uninstall if quota is exhausted — fall back to manual
  # cleanup so teardown doesn't hang.
  CLI_PROMPT="/coding-aegis uninstall helloworld"
  CLI_TIMEOUT="$TIMEOUT_LONG"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" gemini_quiet -o text --yolo
  assert_not_contains "$LAST_OUTPUT" "not installed\|not found\|Error" "uninstall — no errors"
  if echo "$LAST_OUTPUT" | grep -qi "quota\|RESOURCE_EXHAUSTED\|429"; then
    echo -e "  ${DIM}quota exhausted — falling back to manual cleanup${RESET}"
    rm -rf "$TEST_DIR/.claude/rules/aegis--helloworld--helloworld.md"
    rm -rf "$TEST_DIR/.claude/skills/helloworld"
  fi

  section "Phase 7: Full Cleanup"
  test_header "uninstall coding-aegis skill"
  run_cli "skills uninstall" gemini_sub skills uninstall coding-aegis --scope workspace || true
  run_cli "skills list" gemini_sub skills list || true
  assert_not_contains "$LAST_OUTPUT" "coding-aegis" "coding-aegis no longer in skills list"

  test_header "remove test directory"
  rm -rf "$TEST_DIR"
  assert_dir_not_exists "$TEST_DIR" "test directory removed"

  print_results
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Gemini CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"

# ── Phase 1: Environment & Tool Validation ───────────────────
section "Phase 1: Environment & Tool Validation"

test_header "gemini installed"
if command -v gemini &>/dev/null; then
  pass "gemini found: $(gemini --version 2>&1 || echo unknown)"
else
  fail "gemini not found in PATH"
  exit 1
fi

test_header "gemini authenticated"
CLI_PROMPT="Reply with exactly: AUTH_OK"
run_cli "auth check" gemini_quiet -o text
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "AUTH_OK" "gemini authenticated"

# ── Phase 2: Marketplace / Registry Setup ────────────────────
# Gemini uses `skills link` directly — no separate marketplace registration.
# Skipping to Phase 3 per testing-spec.md.

# ── Phase 3: Install coding-aegis Skill ──────────────────────
section "Phase 3: Install coding-aegis Skill"

test_header "gemini skills link"
run_cli "skills link" gemini_sub skills link "$SKILL_DIR" --scope workspace --consent
assert_contains "$LAST_OUTPUT" "link\|success\|install" "skill linked"

test_header "skill visible in list"
run_cli "skills list" gemini_sub skills list
assert_contains "$LAST_OUTPUT" "coding-aegis" "coding-aegis in skills list"

test_header "detect_tool.py present"
assert_file_exists "$SKILL_DIR/detect_tool.py" "detect_tool.py present at linked skill path"

# Set up test directory with catalog
git -C "$TEST_DIR" init -q
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── Phase 4: Validate coding-aegis Skill ─────────────────────
section "Phase 4: Validate coding-aegis Skill"

# Gemini detection requires agent-mediated invocation so GEMINI_CLI=1 is set.
# Direct bash would not fire the env: signal since the skill path has no
# tool-specific segment (.claude/, .codex/).
test_header "coding-aegis detect-tool (skill command)"
CLI_PROMPT="/coding-aegis detect-tool"
RUN_DIR="$TEST_DIR" run_cli "skill detect-tool" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "gemini" "detect-tool — tool name reported"
assert_contains "$LAST_OUTPUT" "env:\|path:" "detect-tool — at least one signal reported"

test_header "coding-aegis list"
# Pass local catalog — avoids git clone and is explicit about which catalog to use
CLI_PROMPT="/coding-aegis list --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill list" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

test_header "coding-aegis show helloworld"
# Pass local catalog — avoids git clone and is explicit about which catalog to use
CLI_PROMPT="/coding-aegis show helloworld --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill show" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── Phase 5: Install & Verify helloworld Package ─────────────
section "Phase 5: Install & Verify helloworld Package"

test_header "coding-aegis install helloworld"
# Scope specified in prompt — the skill's interactive scope picker cannot
# be used in headless mode.
CLI_PROMPT="/coding-aegis install helloworld to Project scope --catalog pkgs"
CLI_TIMEOUT="$TIMEOUT_LONG"
RUN_DIR="$TEST_DIR" run_cli "skill install" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "install\|aegis--helloworld\|wrote\|created" "install — activity reported"

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
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# Phase 6 & 7 teardown happens in cleanup trap
