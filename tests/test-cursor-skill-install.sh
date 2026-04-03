#!/usr/bin/env -S bash -l
# coding-aegis skill test — Cursor
# Usage: tests/test-cursor-skill-install.sh
#
# !! WIP — THIS TEST DOES NOT PASS YET !!
#
# Framed out per the user journey contract (testing-spec.md) but not
# yet functional. Blockers:
#   - cursor-agent CLI not installed on this machine
#   - Plugin/skill CLI install not documented (may be IDE-only)
#   - Headless skill invocation untested
#   - aegis-catalog.py cursor path mapping not validated
# See wpi.8, wpi.9, wpi.10 for tracking.
#
# Follows the user journey per docs/test/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Register marketplace (TBD — Cursor plugin install mechanism)
#   T2  Install coding-aegis plugin
#   T3  Use skill: list packages
#   T4  Use skill: show helloworld
#   T5  Use skill: install helloworld
#   T6  Verify installed files
#   T6b Invoke installed helloworld skill
#   T7  Teardown (step-by-step with validation)
#
# Cursor CLI:
#   Binary: `cursor-agent` (Homebrew) or `agent` (vendor curl install)
#   Headless: `cursor-agent -p "prompt"` (same -p pattern as Claude)
#   Auto-approve: `--force` or `--yolo`
#   Output: `--output-format text`
#   Sandbox: `--sandbox <mode>`
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/lib-test-harness.sh"

PLUGIN_DIR="$REPO_ROOT/.cursor-plugin"
SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
TEST_DIR="$(mktemp -d)"

# Cursor installs rules to .cursor/rules/, skills to .cursor/skills/
SCOPE_DIR="$TEST_DIR/.cursor"
RULE_FILE="$SCOPE_DIR/rules/aegis--helloworld--helloworld.md"
SKILL_INSTALL_DIR="$SCOPE_DIR/skills/helloworld"

cleanup() {
  section "T7: Teardown"

  test_header "T7.1 uninstall helloworld via skill"
  CLI_PROMPT="/coding-aegis uninstall helloworld"
  RUN_DIR="$TEST_DIR" run_cli "skill uninstall" cursor-agent -p --output-format text --force
  assert_not_contains "$LAST_OUTPUT" "not installed\|not found\|Error" "uninstall — no errors"

  # T7.2: Cursor plugin uninstall mechanism TBD
  test_header "T7.2 uninstall coding-aegis plugin (TBD)"

  test_header "T7.3 remove test directory"
  rm -rf "$TEST_DIR"
  assert_dir_not_exists "$TEST_DIR" "test directory removed"

  print_results
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Cursor)"
echo "========================================"
echo ""
echo -e "  ${RED}!! WIP — THIS TEST DOES NOT PASS YET !!${RESET}"
echo "  Framed out per user journey contract. Blockers:"
echo "    - cursor-agent CLI not installed"
echo "    - Plugin CLI install not documented"
echo "    - See wpi.8, wpi.9, wpi.10"
echo ""
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"

# ── T0: Prerequisites ────────────────────────────────────────
section "T0: Prerequisites"

test_header "cursor-agent CLI installed"
if command -v cursor-agent &>/dev/null; then
  pass "cursor-agent found: $(cursor-agent --version 2>&1 || echo unknown)"
else
  fail "cursor-agent (Cursor CLI) not found in PATH"
  echo "  Install: brew install cursor-agent (or: curl https://cursor.com/install -fsS | bash)"
  exit 1
fi

test_header "cursor authenticated"
CLI_PROMPT="Reply with exactly: AUTH_OK"
run_cli "auth check" cursor-agent -p --output-format text
assert_contains "$LAST_OUTPUT" "AUTH_OK" "cursor authenticated"

# ── T1: Register marketplace ─────────────────────────────────
section "T1: Register marketplace"

# Cursor plugin marketplace mechanism is IDE-based.
# CLI plugin install not yet documented. See wpi.8 for research.
test_header "plugin manifest exists"
assert_file_exists "$PLUGIN_DIR/marketplace.json" ".cursor-plugin/marketplace.json present"

# ── T2: Install coding-aegis plugin ──────────────────────────
section "T2: Install coding-aegis plugin"

# TBD: Cursor plugin install via CLI is not documented.
# For now, validate the manifest and copy skill locally.
# This should be replaced with the native mechanism once discovered.
test_header "TBD — Cursor plugin CLI install not yet available"
pass "SKIP: awaiting Cursor CLI plugin install research (wpi.8, wpi.9)"

# Make catalog accessible in test directory
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── T3: Use skill — list ─────────────────────────────────────
section "T3: Use skill — list packages"

test_header "coding-aegis list"
# Pass local catalog — avoids git clone and is explicit about which catalog to use
CLI_PROMPT="/coding-aegis list --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill list" cursor-agent -p --output-format text
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

# ── T4: Use skill — show ─────────────────────────────────────
section "T4: Use skill — show helloworld"

test_header "coding-aegis show helloworld"
# Pass local catalog — avoids git clone and is explicit about which catalog to use
CLI_PROMPT="/coding-aegis show helloworld --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill show" cursor-agent -p --output-format text
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"

# ── T5: Use skill — install ──────────────────────────────────
section "T5: Use skill — install helloworld"

test_header "coding-aegis install helloworld"
# Scope specified in prompt — scope picker can't run in headless mode.
CLI_PROMPT="/coding-aegis install helloworld to Project scope --catalog pkgs"
RUN_DIR="$TEST_DIR" run_cli "skill install" cursor-agent -p --output-format text --force
assert_contains "$LAST_OUTPUT" "install\|aegis--helloworld\|wrote\|created" "install — activity reported"

# ── T6: Verify installed files ────────────────────────────────
section "T6: Verify installed files"

test_header "rule file exists"
assert_file_exists "$RULE_FILE" "rule file: aegis--helloworld--helloworld.md"

test_header "rule frontmatter"
assert_file_contains "$RULE_FILE" "managed-by: coding-aegis" "frontmatter: managed-by"
assert_file_contains "$RULE_FILE" "package: helloworld" "frontmatter: package"
assert_file_contains "$RULE_FILE" "tier: optional" "frontmatter: tier"

test_header "skill file exists"
assert_file_exists "$SKILL_INSTALL_DIR/SKILL.md" "skill file: helloworld/SKILL.md"

# ── T6b: Invoke installed helloworld skill ────────────────────
section "T6b: Invoke helloworld skill"

test_header "helloworld responds"
CLI_PROMPT="/helloworld"
RUN_DIR="$TEST_DIR" run_cli "invoke helloworld" cursor-agent -p --output-format text
assert_contains "$LAST_OUTPUT" "Hello, World" "helloworld skill responded"

# T7 teardown happens in cleanup trap
