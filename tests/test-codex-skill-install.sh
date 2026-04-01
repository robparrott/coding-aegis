#!/usr/bin/env -S bash -l
# Smoke test: coding-aegis skill via OpenAI Codex CLI.
# Usage: tests/test-codex-skill-install.sh
#
# Phase 0: Verify codex CLI is installed and authenticated.
# Phase 1: aegis-catalog.py CLI helper (direct — same as Claude tests).
# Phase 2: Skill discovery — copy skill into .agents/skills/, verify codex sees it.
# Phase 3: Skill show command via codex exec.
#
# Codex has no plugin marketplace. Skills are discovered from .agents/skills/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
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

CATALOG_SCRIPT="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis/aegis-catalog.py"
SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
FIXTURE_CATALOG="$REPO_ROOT/tests/fixtures/pkgs"

echo "========================================"
echo "coding-aegis skill test (Codex CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo ""

# ══════════════════════════════════════════════════════════════
# Phase 0: Verify codex CLI
# ══════════════════════════════════════════════════════════════
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 0: Codex CLI check${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: codex installed${RESET}"
if command -v codex &>/dev/null; then
  codex_path=$(command -v codex)
  codex_version=$(codex --version 2>&1 || echo "unknown")
  echo -e "  ${DIM}Path: $codex_path${RESET}"
  echo -e "  ${DIM}Version: $codex_version${RESET}"
  pass "codex found: $codex_version"
else
  fail "codex not found in PATH"
  echo -e "  ${RED}Install: npm install -g @openai/codex${RESET}"
  exit 1
fi

echo ""
echo -e "${BOLD}TEST: codex authenticated${RESET}"
# codex exec with a trivial prompt to verify auth works
auth_output=$(codex exec "Reply with exactly: AUTH_OK" --ephemeral -o /dev/stdout < /dev/null 2>&1) || true
if echo "$auth_output" | grep -qi "AUTH_OK"; then
  pass "codex authenticated"
else
  echo -e "  ${YELLOW}${auth_output}${RESET}"
  fail "codex auth check — run 'codex login' first"
  exit 1
fi

# ══════════════════════════════════════════════════════════════
# Phase 1: aegis-catalog.py CLI helper (direct)
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 1: aegis-catalog.py (direct)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

# Test: resolve-catalog
echo -e "${BOLD}TEST: resolve-catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" resolve-catalog --from "$REPO_ROOT" 2>&1)
if echo "$output" | grep -q '"catalog"'; then
  pass "resolve-catalog"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "resolve-catalog"
fi

# Test: show test-stub
echo ""
echo -e "${BOLD}TEST: show test-stub${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
errors=0
for expect in '"name": "test-stub"' '"version": "1.0.0"' '"tier": "goodies"' '"author": "test-team"'; do
  if ! echo "$output" | grep -q "$expect"; then
    echo -e "  ${RED}Missing: $expect${RESET}"
    errors=$((errors + 1))
  fi
done
if [ "$errors" -eq 0 ]; then
  pass "show test-stub — all fields correct"
else
  fail "show test-stub — $errors fields missing"
fi

# Test: list
echo ""
echo -e "${BOLD}TEST: list fixture catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" list --catalog "$FIXTURE_CATALOG" 2>&1)
if echo "$output" | grep -q '"test-stub"'; then
  pass "list finds test-stub"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "list — test-stub not found"
fi

# Test: install-prep
echo ""
echo -e "${BOLD}TEST: install-prep test-stub${RESET}"
output=$(python3 "$CATALOG_SCRIPT" install-prep test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
if echo "$output" | grep -q 'aegis--test-stub--test-rule.md' && echo "$output" | grep -q 'managed-by: coding-aegis'; then
  pass "install-prep — correct filename and frontmatter"
else
  echo -e "  ${YELLOW}$(echo "$output" | head -20)${RESET}"
  fail "install-prep"
fi

# Test: status with mock installed files
echo ""
echo -e "${BOLD}TEST: status with mock install${RESET}"
TEST_DIR="$(mktemp -d)"
mkdir -p "$TEST_DIR/rules"
cat > "$TEST_DIR/rules/aegis--test-stub--test-rule.md" <<'RULE'
---
package: test-stub
rule: test-rule
version: 1.0.0
tier: goodies
managed-by: coding-aegis
---

# Test Rule
RULE
output=$(python3 "$CATALOG_SCRIPT" status --catalog "$FIXTURE_CATALOG" --scope "$TEST_DIR" 2>&1)
if echo "$output" | grep -q '"name": "test-stub"' && echo "$output" | grep -q '"status": "current"'; then
  pass "status — detected test-stub as current"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "status"
fi
rm -rf "$TEST_DIR"

# ══════════════════════════════════════════════════════════════
# Phase 2: Skill discovery via .agents/skills/
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 2: Codex skill discovery${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"; print_results' EXIT

# Codex discovers skills from .agents/skills/ (not .claude/skills/)
mkdir -p "$TEST_DIR/.agents/skills/coding-aegis"
cp "$SKILL_DIR/SKILL.md" "$TEST_DIR/.agents/skills/coding-aegis/SKILL.md"
cp "$SKILL_DIR/aegis-catalog.py" "$TEST_DIR/.agents/skills/coding-aegis/aegis-catalog.py"
cp -R "$FIXTURE_CATALOG" "$TEST_DIR/pkgs"
# Codex needs a git repo to run
git -C "$TEST_DIR" init -q

echo -e "  ${DIM}Test dir: $TEST_DIR${RESET}"
echo -e "  ${DIM}Skill at: .agents/skills/coding-aegis/SKILL.md${RESET}"

echo -e "${BOLD}TEST: codex exec show test-stub${RESET}"
SHOW_PROMPT="You have the coding-aegis skill loaded. Use it to show the package named test-stub. The pkgs/ catalog directory is at ./pkgs/. Display the package details."
show_output=$(cd "$TEST_DIR" && codex exec "$SHOW_PROMPT" \
  --ephemeral \
  -s read-only \
  -o /dev/stdout \
  < /dev/null 2>&1) || true

echo -e "${YELLOW}$(echo "$show_output" | head -30)${RESET}"
errors=0
if ! echo "$show_output" | grep -qi "test-stub"; then
  echo -e "  ${RED}Missing: test-stub name${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$show_output" | grep -qi "goodies"; then
  echo -e "  ${RED}Missing: goodies tier${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "codex exec show — test-stub details returned"
else
  fail "codex exec show — $errors expected values missing"
fi

rm -rf "$TEST_DIR"

# ══════════════════════════════════════════════════════════════
# Phase 3: Install command — full pipeline
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 3: Install pipeline (direct CLI)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"

source "$(dirname "$0")/lib-install-test.sh"
run_install_tests
