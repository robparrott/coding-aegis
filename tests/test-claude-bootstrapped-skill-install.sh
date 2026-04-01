#!/usr/bin/env -S bash -l
# Smoke test: coding-aegis plugin marketplace install/uninstall.
# Usage: tests/test-claude-bootstrapped-skill-install.sh
#
# Validates that the coding-aegis plugin can be registered as a marketplace,
# installed, listed, and cleanly uninstalled via the Claude Code CLI.
# Tests both local directory and remote GitHub sources.
#
# Future: skill command tests (list, show, install, status) via claude -p.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GITHUB_REPO="robparrott/coding-aegis"
PASS=0
FAIL=0

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

# Run the full marketplace lifecycle for a given source.
# Usage: test_marketplace_lifecycle <label> <source> <marketplace_name>
test_marketplace_lifecycle() {
  local label="$1"
  local source="$2"
  local mp_name="$3"

  echo ""
  echo -e "${BOLD}══════════════════════════════════════════${RESET}"
  echo -e "${BOLD}${label}${RESET}"
  echo -e "${BOLD}══════════════════════════════════════════${RESET}"
  echo -e "  ${DIM}Source: ${source}${RESET}"
  echo ""

  # Clean stale registrations from previous runs
  claude plugin uninstall "coding-aegis@${mp_name}" --scope user 2>/dev/null || true
  claude plugin marketplace remove "$mp_name" 2>/dev/null || true

  # marketplace add
  echo -e "${BOLD}TEST: ${label} — marketplace add${RESET}"
  local output
  output=$(claude plugin marketplace add "$source" 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "added\|success"; then
    pass "${label} — marketplace add"
    # Capture actual marketplace name
    local detected
    detected=$(echo "$output" | grep -oi 'marketplace: [a-z_-]*' | head -1 | sed 's/marketplace: //')
    if [ -n "$detected" ]; then
      mp_name="$detected"
      echo -e "  ${DIM}Marketplace name: $mp_name${RESET}"
    fi
  else
    fail "${label} — marketplace add"
  fi

  # marketplace list
  echo ""
  echo -e "${BOLD}TEST: ${label} — marketplace list${RESET}"
  output=$(claude plugin marketplace list 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "coding-aegis"; then
    pass "${label} — marketplace list"
  else
    fail "${label} — marketplace list"
  fi

  # plugin install
  echo ""
  echo -e "${BOLD}TEST: ${label} — plugin install${RESET}"
  output=$(claude plugin install "coding-aegis@${mp_name}" --scope user 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "install"; then
    pass "${label} — plugin install"
  else
    fail "${label} — plugin install"
  fi

  # plugin list
  echo ""
  echo -e "${BOLD}TEST: ${label} — plugin list${RESET}"
  output=$(claude plugin list 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "coding-aegis"; then
    pass "${label} — plugin list"
  else
    fail "${label} — plugin list"
  fi

  # plugin uninstall
  echo ""
  echo -e "${BOLD}TEST: ${label} — plugin uninstall${RESET}"
  output=$(claude plugin uninstall "coding-aegis@${mp_name}" --scope user 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "uninstall"; then
    pass "${label} — plugin uninstall"
  else
    fail "${label} — plugin uninstall"
  fi

  # verify plugin gone
  echo ""
  echo -e "${BOLD}TEST: ${label} — plugin gone after uninstall${RESET}"
  output=$(claude plugin list 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "coding-aegis@${mp_name}"; then
    fail "${label} — plugin still present"
  else
    pass "${label} — plugin removed"
  fi

  # marketplace remove
  echo ""
  echo -e "${BOLD}TEST: ${label} — marketplace remove${RESET}"
  output=$(claude plugin marketplace remove "$mp_name" 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "removed\|success"; then
    pass "${label} — marketplace remove"
  else
    fail "${label} — marketplace remove"
  fi

  # verify marketplace gone
  echo ""
  echo -e "${BOLD}TEST: ${label} — marketplace gone after remove${RESET}"
  output=$(claude plugin marketplace list 2>&1) || true
  echo -e "  ${YELLOW}${output}${RESET}"
  if echo "$output" | grep -qi "$mp_name"; then
    fail "${label} — marketplace still present"
  else
    pass "${label} — marketplace removed"
  fi
}

print_results() {
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
trap print_results EXIT

echo "========================================"
echo "coding-aegis skill test (Claude Code)"
echo "========================================"
echo "  Repo root:   $REPO_ROOT"
echo "  GitHub repo: $GITHUB_REPO"
echo ""

# ══════════════════════════════════════════════════════════════
# T0 — Tool Prerequisites
# ══════════════════════════════════════════════════════════════
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}T0: Claude Code prerequisites${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: claude installed${RESET}"
if command -v claude &>/dev/null; then
  claude_path=$(command -v claude)
  claude_version=$(claude --version 2>&1 || echo "unknown")
  echo -e "  ${DIM}Path: $claude_path${RESET}"
  echo -e "  ${DIM}Version: $claude_version${RESET}"
  pass "claude found: $claude_version"
else
  fail "claude not found in PATH"
  exit 1
fi

echo ""
echo -e "${BOLD}TEST: claude authenticated${RESET}"
auth_output=$(claude -p "Reply with exactly: AUTH_OK" < /dev/null 2>&1) || true
if echo "$auth_output" | grep -qi "AUTH_OK"; then
  pass "claude authenticated"
else
  echo -e "  ${YELLOW}$(echo "$auth_output" | head -5)${RESET}"
  fail "claude auth — run 'claude auth' first"
  exit 1
fi

# T1 — Local marketplace
test_marketplace_lifecycle "Local marketplace" "$REPO_ROOT" "coding-aegis"

# Phase 2: remote GitHub marketplace
test_marketplace_lifecycle "Remote marketplace (GitHub)" "$GITHUB_REPO" "coding-aegis"

# Phase 3: skill command test via claude -p
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 3: aegis-catalog.py CLI helper${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

CATALOG_SCRIPT="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis/aegis-catalog.py"
REAL_CATALOG="$REPO_ROOT/pkgs"

# Test: resolve-catalog
echo -e "${BOLD}TEST: resolve-catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" resolve-catalog --from "$REPO_ROOT" 2>&1)
if echo "$output" | grep -q '"catalog"'; then
  pass "resolve-catalog"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "resolve-catalog"
fi

# Test: list
echo ""
echo -e "${BOLD}TEST: list catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" list --catalog "$REAL_CATALOG" 2>&1)
if echo "$output" | grep -q '"helloworld"'; then
  pass "list finds helloworld"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "list — helloworld not found"
fi

# Test: show helloworld
echo ""
echo -e "${BOLD}TEST: show helloworld${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show helloworld --catalog "$REAL_CATALOG" 2>&1)
if echo "$output" | grep -q '"optional"' && echo "$output" | grep -q '"1.0.0"'; then
  pass "show helloworld — correct tier and version"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "show helloworld"
fi

# Test: install-prep helloworld
echo ""
echo -e "${BOLD}TEST: install-prep helloworld${RESET}"
output=$(python3 "$CATALOG_SCRIPT" install-prep helloworld --catalog "$REAL_CATALOG" 2>&1)
if echo "$output" | grep -q 'aegis--helloworld--helloworld.md' && echo "$output" | grep -q 'managed-by: coding-aegis'; then
  pass "install-prep — correct filename and frontmatter"
else
  echo -e "  ${YELLOW}$(echo "$output" | head -20)${RESET}"
  fail "install-prep"
fi

# Test: show not-found
echo ""
echo -e "${BOLD}TEST: show nonexistent${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show nonexistent --catalog "$REAL_CATALOG" 2>&1) || true
if echo "$output" | grep -q '"error"'; then
  pass "show nonexistent — returns error"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "show nonexistent — expected error"
fi

# ══════════════════════════════════════════════════════════════
# Phase 4: Install pipeline (helloworld, real catalog)
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 4: Install pipeline (direct CLI)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"

source "$(dirname "$0")/lib-install-test.sh"
run_install_tests helloworld "$REAL_CATALOG"
