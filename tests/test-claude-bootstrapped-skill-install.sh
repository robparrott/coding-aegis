#!/usr/bin/env -S bash -l
# coding-aegis skill test — Claude Code
# Usage: tests/test-claude-bootstrapped-skill-install.sh
#
# Follows the user journey per docs/architecture/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Install coding-aegis plugin via marketplace
#   T2  Use skill: list packages
#   T3  Use skill: show helloworld
#   T4  Use skill: install helloworld
#   T5  Verify installed files
#   T6  Teardown
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
MARKETPLACE_NAME="coding-aegis"
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

# macOS doesn't ship `timeout`; shell-based fallback
if ! command -v timeout &>/dev/null; then
  timeout() {
    local secs="$1"; shift
    "$@" &
    local pid=$!
    ( sleep "$secs" && kill "$pid" 2>/dev/null ) &
    local watcher=$!
    wait "$pid" 2>/dev/null
    local exit_code=$?
    kill "$watcher" 2>/dev/null
    wait "$watcher" 2>/dev/null
    return $exit_code
  }
fi

# Test working directory — all skill operations happen here
TEST_DIR="$(mktemp -d)"

cleanup() {
  echo ""
  echo -e "${BOLD}T6: Teardown${RESET}"
  echo -e "  ${DIM}Uninstalling plugin...${RESET}"
  claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope user 2>/dev/null || true
  echo -e "  ${DIM}Removing marketplace...${RESET}"
  claude plugin marketplace remove "$MARKETPLACE_NAME" 2>/dev/null || true
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
echo "coding-aegis skill test (Claude Code)"
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

echo -e "${BOLD}TEST: claude installed${RESET}"
if command -v claude &>/dev/null; then
  claude_version=$(claude --version 2>&1 || echo "unknown")
  echo -e "  ${DIM}Path: $(command -v claude)${RESET}"
  echo -e "  ${DIM}Version: $claude_version${RESET}"
  pass "claude found"
else
  fail "claude not found in PATH"
  exit 1
fi

echo ""
echo -e "${BOLD}TEST: claude authenticated${RESET}"
auth_output=$(timeout "$TIMEOUT" claude -p "Reply with exactly: AUTH_OK" < /dev/null 2>&1) || true
if echo "$auth_output" | grep -qi "AUTH_OK"; then
  pass "claude authenticated"
else
  echo -e "  ${YELLOW}$(echo "$auth_output" | head -5)${RESET}"
  fail "claude auth check failed"
  exit 1
fi

# ══════════════════════════════════════════════════════════════
# T1 — Install coding-aegis plugin
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T1: Install coding-aegis plugin${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

# Clean stale registrations
claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope user 2>/dev/null || true
claude plugin marketplace remove "$MARKETPLACE_NAME" 2>/dev/null || true

echo -e "${BOLD}TEST: marketplace add (local)${RESET}"
output=$(claude plugin marketplace add "$REPO_ROOT" 2>&1) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "added\|success"; then
  pass "marketplace add"
  detected=$(echo "$output" | grep -oi 'marketplace: [a-z_-]*' | head -1 | sed 's/marketplace: //')
  [ -n "$detected" ] && MARKETPLACE_NAME="$detected"
else
  fail "marketplace add"
fi

echo ""
echo -e "${BOLD}TEST: plugin install${RESET}"
output=$(claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope user 2>&1) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "install"; then
  pass "plugin install"
else
  fail "plugin install"
fi

echo ""
echo -e "${BOLD}TEST: plugin visible in list${RESET}"
output=$(claude plugin list 2>&1) || true
if echo "$output" | grep -qi "coding-aegis"; then
  pass "coding-aegis in plugin list"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "coding-aegis not in plugin list"
fi

# Set up test directory with catalog symlink (skill needs access to pkgs/)
ln -s "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs" 2>/dev/null || cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
echo -e "  ${DIM}Catalog available at $TEST_DIR/pkgs/${RESET}"

# ══════════════════════════════════════════════════════════════
# T2 — Use skill: list packages
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T2: Use skill — list packages${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: coding-aegis list via claude -p${RESET}"
LIST_PROMPT="You have the coding-aegis skill loaded. Execute its list command. The pkgs/ catalog is at ./pkgs/ in the current directory."
list_output=$(set +x; cd "$TEST_DIR" && timeout "$TIMEOUT" claude -p "$LIST_PROMPT" \
  --allowedTools "Bash,Read,Glob" \
  < /dev/null 2>&1) || true
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

echo -e "${BOLD}TEST: coding-aegis show helloworld via claude -p${RESET}"
SHOW_PROMPT="You have the coding-aegis skill loaded. Execute its show command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory."
show_output=$(set +x; cd "$TEST_DIR" && timeout "$TIMEOUT" claude -p "$SHOW_PROMPT" \
  --allowedTools "Bash,Read,Glob" \
  < /dev/null 2>&1) || true
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
if ! echo "$show_output" | grep -qi "1.0.0"; then
  echo -e "  ${RED}Missing: version 1.0.0${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "show — name, tier, version present"
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

echo -e "${BOLD}TEST: coding-aegis install helloworld via claude -p${RESET}"
INSTALL_PROMPT="You have the coding-aegis skill loaded. Execute its install command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory. Use Project scope (.claude/ in the current directory) without asking — do not use AskUserQuestion."
install_output=$(set +x; cd "$TEST_DIR" && timeout "$TIMEOUT" claude -p "$INSTALL_PROMPT" \
  --allowedTools "Bash,Read,Write,Glob" \
  --permission-mode dontAsk \
  < /dev/null 2>&1) || true
echo -e "${YELLOW}$(echo "$install_output" | head -30)${RESET}"
if echo "$install_output" | grep -qi "install\|aegis--helloworld"; then
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
  pass "rule file exists: aegis--helloworld--helloworld.md"
else
  fail "rule file missing"
  echo "  Files in test dir:"
  find "$TEST_DIR/.claude" -type f 2>/dev/null | sed "s|$TEST_DIR/||" | sort | sed 's/^/    /' || echo "    (no .claude dir)"
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
  pass "skill file exists: skills/helloworld/SKILL.md"
else
  fail "skill file missing"
fi

# T6 teardown happens in the cleanup trap
