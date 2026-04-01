#!/usr/bin/env -S bash -l
# coding-aegis skill test — OpenAI Codex CLI
# Usage: tests/test-codex-skill-install.sh
#
# Follows the user journey per docs/architecture/testing-spec.md:
#   T0  Prerequisites (installed + authenticated)
#   T1  Install coding-aegis skill (file copy to .agents/skills/)
#   T2  Use skill: list packages
#   T3  Use skill: show helloworld
#   T4  Use skill: install helloworld
#   T5  Verify installed files
#   T6  Teardown
set -euo pipefail

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
echo "coding-aegis skill test (Codex CLI)"
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

echo -e "${BOLD}TEST: codex installed${RESET}"
if command -v codex &>/dev/null; then
  codex_version=$(codex --version 2>&1 || echo "unknown")
  echo -e "  ${DIM}Path: $(command -v codex)${RESET}"
  echo -e "  ${DIM}Version: $codex_version${RESET}"
  pass "codex found"
else
  fail "codex not found in PATH"
  exit 1
fi

echo ""
echo -e "${BOLD}TEST: codex authenticated${RESET}"
# codex exec requires a git repo
git -C "$TEST_DIR" init -q
auth_output=$(cd "$TEST_DIR" && codex exec "Reply with exactly: AUTH_OK" \
  --ephemeral -o /dev/stdout --skip-git-repo-check < /dev/null 2>&1) || true
if echo "$auth_output" | grep -qi "AUTH_OK"; then
  pass "codex authenticated"
else
  echo -e "  ${YELLOW}$(echo "$auth_output" | head -5)${RESET}"
  fail "codex auth check failed"
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

echo -e "${BOLD}TEST: copy skill to .agents/skills/${RESET}"
mkdir -p "$TEST_DIR/.agents/skills/coding-aegis"
cp "$SKILL_DIR/SKILL.md" "$TEST_DIR/.agents/skills/coding-aegis/SKILL.md"
cp "$SKILL_DIR/aegis-catalog.py" "$TEST_DIR/.agents/skills/coding-aegis/aegis-catalog.py"
if [ -f "$TEST_DIR/.agents/skills/coding-aegis/SKILL.md" ]; then
  pass "skill installed to .agents/skills/coding-aegis/"
else
  fail "skill files not found"
fi

# Make catalog accessible
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

echo -e "${BOLD}TEST: coding-aegis list via codex exec${RESET}"
LIST_PROMPT="You have the coding-aegis skill loaded. Execute its list command. The pkgs/ catalog is at ./pkgs/ in the current directory."
list_output=$(cd "$TEST_DIR" && codex exec "$LIST_PROMPT" \
  --ephemeral -s read-only -o /dev/stdout \
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

echo -e "${BOLD}TEST: coding-aegis show helloworld via codex exec${RESET}"
SHOW_PROMPT="You have the coding-aegis skill loaded. Execute its show command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory."
show_output=$(cd "$TEST_DIR" && codex exec "$SHOW_PROMPT" \
  --ephemeral -s read-only -o /dev/stdout \
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

echo -e "${BOLD}TEST: coding-aegis install helloworld via codex exec${RESET}"
INSTALL_PROMPT="You have the coding-aegis skill loaded. Execute its install command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory. Use Project scope (.claude/ in the current directory) without asking the user."
install_output=$(cd "$TEST_DIR" && codex exec "$INSTALL_PROMPT" \
  --ephemeral -s workspace-write -o /dev/stdout \
  < /dev/null 2>&1) || true
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
