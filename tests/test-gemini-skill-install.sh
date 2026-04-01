#!/usr/bin/env -S bash -l
# coding-aegis skill test — Google Gemini CLI
# Usage: tests/test-gemini-skill-install.sh
#
# Follows the user journey per docs/architecture/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Install coding-aegis skill (gemini skills link)
#   T2  Use skill: list packages
#   T3  Use skill: show helloworld
#   T4  Use skill: install helloworld
#   T5  Verify installed files
#   T6  Teardown
#
# Note: Gemini CLI on Homebrew emits keytar/keychain warnings to stderr.
# These are harmless (falls back to file keychain). We filter them out.
set -euo pipefail

# Filter noisy keytar warnings from gemini commands
gemini_quiet() {
  gemini "$@" 2>&1 | grep -v -E "Keychain initialization|keytar\.node|keytar\.js|FileKeychain fallback|Loaded cached credentials\.|^Require stack:"
}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
PASS=0
FAIL=0
TIMEOUT=${AEGIS_TEST_TIMEOUT:-90}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

pass() {
  echo -e "  ${GREEN}PASS${RESET}: $1"
  PASS=$((PASS + 1))
}

fail() {
  echo -e "  ${RED}FAIL${RESET}: $1"
  FAIL=$((FAIL + 1))
}

# Test working directory
TEST_DIR="$(mktemp -d)"

cleanup() {
  echo ""
  echo -e "${BOLD}T6: Teardown${RESET}"
  echo -e "  ${DIM}Unlinking skill...${RESET}"
  gemini_quiet skills uninstall coding-aegis --scope user > /dev/null || true
  echo "  Removing test dir: $TEST_DIR"
  rm -rf "$TEST_DIR"
  echo ""
  echo "================================"
  if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}Results: $PASS passed, $FAIL failed${RESET}"
  else
    echo -e "  ${RED}Results: $PASS passed, $FAIL failed${RESET}"
  fi
  echo "================================"
  [ "$FAIL" -eq 0 ] && exit 0 || exit 1
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Gemini CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"
echo ""

# ══════════════════════════════════════════════════════════════
# T0 — Prerequisites
# ══════════════════════════════════════════════════════════════
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T0: Prerequisites${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: gemini installed${RESET}"
if command -v gemini &>/dev/null; then
  gemini_version=$(gemini --version 2>&1 || echo "unknown")
  echo -e "  ${DIM}Path: $(command -v gemini)${RESET}"
  echo -e "  ${DIM}Version: $gemini_version${RESET}"
  pass "gemini found"
else
  fail "gemini not found in PATH"
  echo -e "  ${RED}Install: npm install -g @google/gemini-cli${RESET}"
  exit 1
fi

echo ""
echo -e "${BOLD}TEST: gemini authenticated${RESET}"
auth_output=$(gemini_quiet -p "Reply with exactly: AUTH_OK" -o text < /dev/null) || true
if echo "$auth_output" | grep -qi "AUTH_OK"; then
  pass "gemini authenticated"
else
  echo -e "  ${YELLOW}$(echo "$auth_output" | head -5)${RESET}"
  fail "gemini auth check failed"
  exit 1
fi

# ══════════════════════════════════════════════════════════════
# T1 — Install coding-aegis skill
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T1: Install coding-aegis skill${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

# Clean stale registration
gemini_quiet skills uninstall coding-aegis --scope user > /dev/null || true

echo -e "${BOLD}TEST: gemini skills link${RESET}"
output=$(gemini_quiet skills link "$SKILL_DIR" --scope user --consent) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "link\|success\|install"; then
  pass "skill linked"
else
  fail "skill link failed"
fi

echo ""
echo -e "${BOLD}TEST: skill visible in list${RESET}"
output=$(gemini_quiet skills list) || true
if echo "$output" | grep -qi "coding-aegis"; then
  pass "coding-aegis in skills list"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "coding-aegis not in skills list"
fi

# Set up test directory with catalog
git -C "$TEST_DIR" init -q
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
echo -e "  ${DIM}Catalog available at $TEST_DIR/pkgs/${RESET}"

# ══════════════════════════════════════════════════════════════
# T2 — Use skill: list packages
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T2: Use skill — list packages${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: coding-aegis list via gemini -p${RESET}"
LIST_PROMPT="You have the coding-aegis skill loaded. Execute its list command. The pkgs/ catalog is at ./pkgs/ in the current directory."
list_output=$(cd "$TEST_DIR" && gemini_quiet -p "$LIST_PROMPT" -o text < /dev/null) || true
echo -e "${YELLOW}$(echo "$list_output" | head -20)${RESET}"
if echo "$list_output" | grep -qi "helloworld"; then
  pass "list — helloworld found in output"
else
  fail "list — helloworld not found"
fi

# ══════════════════════════════════════════════════════════════
# T3 — Use skill: show helloworld
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T3: Use skill — show helloworld${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: coding-aegis show helloworld via gemini -p${RESET}"
SHOW_PROMPT="You have the coding-aegis skill loaded. Execute its show command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory."
show_output=$(cd "$TEST_DIR" && gemini_quiet -p "$SHOW_PROMPT" -o text < /dev/null) || true
echo -e "${YELLOW}$(echo "$show_output" | head -20)${RESET}"
errors=0
if ! echo "$show_output" | grep -qi "helloworld"; then
  echo -e "  ${RED}Missing: helloworld name${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$show_output" | grep -qi "optional"; then
  echo -e "  ${RED}Missing: optional tier${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "show — name and tier present"
else
  fail "show — $errors expected values missing"
fi

# ══════════════════════════════════════════════════════════════
# T4 — Use skill: install helloworld
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T4: Use skill — install helloworld${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: coding-aegis install helloworld via gemini -p${RESET}"
INSTALL_PROMPT="You have the coding-aegis skill loaded. Execute its install command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory. Use Project scope (.claude/ in the current directory) without asking the user. Write all files immediately."
install_output=$(cd "$TEST_DIR" && gemini_quiet -p "$INSTALL_PROMPT" -o text --yolo < /dev/null) || true
echo -e "${YELLOW}$(echo "$install_output" | head -30)${RESET}"
if echo "$install_output" | grep -qi "install\|aegis--helloworld\|wrote\|created"; then
  pass "install — skill reported install activity"
else
  fail "install — no install activity detected"
fi

# ══════════════════════════════════════════════════════════════
# T5 — Verify installed files
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T5: Verify installed files${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

SCOPE_DIR="$TEST_DIR/.claude"

echo -e "${BOLD}TEST: rule file exists${RESET}"
RULE_FILE="$SCOPE_DIR/rules/aegis--helloworld--helloworld.md"
if [ -f "$RULE_FILE" ]; then
  pass "rule file exists"
else
  fail "rule file missing"
  echo "  Files in test dir:"
  find "$TEST_DIR" -path "$TEST_DIR/pkgs" -prune -o -type f -print 2>/dev/null | sed "s|$TEST_DIR/||" | sort | sed 's/^/    /'
fi

echo ""
echo -e "${BOLD}TEST: rule frontmatter${RESET}"
if [ -f "$RULE_FILE" ]; then
  rule_content=$(cat "$RULE_FILE")
  errors=0
  for expect in "managed-by: coding-aegis" "package: helloworld" "tier: optional"; do
    if ! echo "$rule_content" | grep -q "$expect"; then
      echo -e "  ${RED}Missing: $expect${RESET}"
      errors=$((errors + 1))
    fi
  done
  if [ "$errors" -eq 0 ]; then
    pass "rule frontmatter correct"
  else
    fail "rule frontmatter — $errors fields missing"
  fi
else
  fail "rule frontmatter — file not found"
fi

echo ""
echo -e "${BOLD}TEST: skill file exists${RESET}"
SKILL_FILE="$SCOPE_DIR/skills/helloworld/SKILL.md"
if [ -f "$SKILL_FILE" ]; then
  pass "skill file exists"
else
  fail "skill file missing"
fi

# T6 teardown happens in the cleanup trap
