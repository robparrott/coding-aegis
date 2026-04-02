#!/usr/bin/env -S bash -l
# coding-aegis skill test — Google Gemini CLI
# Usage: tests/test-gemini-skill-install.sh
#
# Follows the user journey per docs/test/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Register marketplace (N/A for Gemini — skipped)
#   T2  Install coding-aegis skill (gemini skills link)
#   T3  Use skill: list packages
#   T4  Use skill: show helloworld
#   T5  Use skill: install helloworld
#   T6  Verify installed files
#   T7  Teardown
#
# Note: Gemini CLI on Homebrew emits keytar/keychain warnings.
# We filter them via gemini_quiet wrapper.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/lib-test-harness.sh"

SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
TEST_DIR="$(mktemp -d)"

# Filter noisy keytar warnings from gemini commands
gemini_quiet() {
  gemini "$@" 2>&1 | grep -v -E "Keychain initialization|keytar\.node|keytar\.js|FileKeychain fallback|Loaded cached credentials\.|^Require stack:"
}

cleanup() {
  section "T7: Teardown"

  test_header "T7.1 uninstall helloworld via skill"
  # Skip agent-mediated uninstall if quota is exhausted — fall back to manual
  # cleanup so teardown doesn't hang.
  CLI_PROMPT="/coding-aegis uninstall helloworld"
  CLI_TIMEOUT="$TIMEOUT_LONG"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" gemini_quiet -o text --yolo
  if echo "$LAST_OUTPUT" | grep -qi "quota\|RESOURCE_EXHAUSTED\|429"; then
    echo -e "  ${DIM}quota exhausted — falling back to manual cleanup${RESET}"
    rm -rf "$TEST_DIR/.claude/rules/aegis--helloworld--helloworld.md"
    rm -rf "$TEST_DIR/.claude/skills/helloworld"
  fi

  test_header "T7.2 uninstall coding-aegis skill"
  gemini_quiet skills uninstall coding-aegis --scope user > /dev/null 2>&1 || true

  test_header "T7.3 remove test directory"
  rm -rf "$TEST_DIR"

  print_results
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Gemini CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"

# ── T0: Prerequisites ────────────────────────────────────────
section "T0: Prerequisites"

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

# ── T1: Register marketplace (N/A for Gemini) ────────────────
# Gemini uses `skills link` directly — no separate marketplace registration.
# Skipping to T2 per testing-spec.md.

# ── T2: Install coding-aegis skill ───────────────────────────
section "T2: Install coding-aegis skill"

# Clean stale registration
gemini_quiet skills uninstall coding-aegis --scope user > /dev/null || true

test_header "gemini skills link"
run_cli "skills link" gemini_quiet skills link "$SKILL_DIR" --scope user --consent
assert_contains "$LAST_OUTPUT" "link\|success\|install" "skill linked"

test_header "skill visible in list"
run_cli "skills list" gemini_quiet skills list
assert_contains "$LAST_OUTPUT" "coding-aegis" "coding-aegis in skills list"

# Set up test directory with catalog
git -C "$TEST_DIR" init -q
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── T2b: Verify tool detection ───────────────────────────────
section "T2b: Verify tool detection"

# Agent-mediated — Gemini skills link to the local repo path (not ~/.gemini/), so
# __file__ has no tool-specific segment. Detection relies on GEMINI_CLI=1 in env,
# which is only set when running inside the Gemini CLI agent.
test_header "detect_tool.py installed"
assert_file_exists "$SKILL_DIR/detect_tool.py" "detect_tool.py present in skill directory"

test_header "detect_tool.py identifies gemini (agent-mediated)"
CLI_PROMPT="Use shell to run: python3 $SKILL_DIR/detect_tool.py — output the result exactly as printed, do not paraphrase"
RUN_DIR="$TEST_DIR" run_cli "detect tool" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_json_value "$LAST_OUTPUT" "tool" "gemini" "detected tool: gemini"
assert_json_nonempty_array "$LAST_OUTPUT" "signals" "at least one signal fired"

# ── T2c: Use skill — detect-tool command ─────────────────────
section "T2c: Skill detect-tool command"

test_header "coding-aegis detect-tool"
CLI_PROMPT="/coding-aegis detect-tool"
RUN_DIR="$TEST_DIR" run_cli "skill detect-tool" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "gemini" "detect-tool — tool name reported"
assert_contains "$LAST_OUTPUT" "env:\|path:" "detect-tool — at least one signal reported"

# ── T3: Use skill — list ─────────────────────────────────────
section "T3: Use skill — list packages"

test_header "coding-aegis list"
CLI_PROMPT="/coding-aegis list"
RUN_DIR="$TEST_DIR" run_cli "skill list" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

# ── T4: Use skill — show ─────────────────────────────────────
section "T4: Use skill — show helloworld"

test_header "coding-aegis show helloworld"
CLI_PROMPT="/coding-aegis show helloworld"
RUN_DIR="$TEST_DIR" run_cli "skill show" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── T5: Use skill — install ──────────────────────────────────
section "T5: Use skill — install helloworld"

test_header "coding-aegis install helloworld"
# Scope specified in prompt — the skill's interactive scope picker cannot
# be used in headless mode.
CLI_PROMPT="/coding-aegis install helloworld to Project scope"
CLI_TIMEOUT="$TIMEOUT_LONG"
RUN_DIR="$TEST_DIR" run_cli "skill install" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "install\|aegis--helloworld\|wrote\|created" "install — activity reported"

# ── T6: Verify installed files ────────────────────────────────
section "T6: Verify installed files"

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

# ── T6b: Invoke installed helloworld skill ────────────────────
section "T6b: Invoke helloworld skill"

test_header "helloworld responds"
CLI_PROMPT="/helloworld"
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" gemini_quiet -o text --yolo
assert_no_quota_error "$LAST_OUTPUT" "Gemini"
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# T7 teardown happens in cleanup trap
