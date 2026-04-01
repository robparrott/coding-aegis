#!/usr/bin/env -S bash -l
# coding-aegis skill test — Google Gemini CLI
# Usage: tests/test-gemini-skill-install.sh
#
# Follows the user journey per docs/test/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Install coding-aegis skill (gemini skills link)
#   T2  Use skill: list packages
#   T3  Use skill: show helloworld
#   T4  Use skill: install helloworld
#   T5  Verify installed files
#   T6  Teardown
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
  section "T6: Teardown"
  echo -e "  ${DIM}\$ gemini skills uninstall coding-aegis --scope user${RESET}"
  gemini_quiet skills uninstall coding-aegis --scope user > /dev/null || true
  echo "  Removing test dir: $TEST_DIR"
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
assert_contains "$LAST_OUTPUT" "AUTH_OK" "gemini authenticated"

# ── T1: Install coding-aegis skill ───────────────────────────
section "T1: Install coding-aegis skill"

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

# ── T2: Use skill — list ─────────────────────────────────────
section "T2: Use skill — list packages"

test_header "coding-aegis list"
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its list command. The pkgs/ catalog is at ./pkgs/ in the current directory."
RUN_DIR="$TEST_DIR" run_cli "skill list" gemini_quiet -o text
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

# ── T3: Use skill — show ─────────────────────────────────────
section "T3: Use skill — show helloworld"

test_header "coding-aegis show helloworld"
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its show command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory."
RUN_DIR="$TEST_DIR" run_cli "skill show" gemini_quiet -o text
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"

# ── T4: Use skill — install ──────────────────────────────────
section "T4: Use skill — install helloworld"

test_header "coding-aegis install helloworld"
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its install command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory. Use Project scope (.claude/ in the current directory) without asking the user. Write all files immediately."
RUN_DIR="$TEST_DIR" run_cli "skill install" gemini_quiet -o text --yolo
assert_contains "$LAST_OUTPUT" "install\|aegis--helloworld\|wrote\|created" "install — activity reported"

# ── T5: Verify installed files ────────────────────────────────
section "T5: Verify installed files"

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

# T6 teardown happens in cleanup trap
