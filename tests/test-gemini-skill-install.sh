#!/usr/bin/env -S bash -l
# Smoke test: coding-aegis skill via Google Gemini CLI.
# Usage: tests/test-gemini-skill-install.sh
#
# Phase 0: Verify gemini CLI is installed and authenticated.
# Phase 1: aegis-catalog.py CLI helper (direct — shared with Claude/Codex tests).
# Phase 2: Skill lifecycle — install, list, uninstall via gemini skills CLI.
# Phase 3: Skill show command via gemini -p.
#
# Note: Gemini CLI on Homebrew emits keytar/keychain warnings to stderr.
# These are harmless (falls back to file keychain). We filter them out.
set -euo pipefail

# Filter noisy keytar warnings from gemini commands
gemini_quiet() {
  gemini "$@" 2>&1 | grep -v -E "Keychain initialization|keytar\.node|keytar\.js|FileKeychain fallback|Loaded cached credentials\.|^Require stack:"
}

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

cleanup() {
  echo ""
  echo -e "${BOLD}Cleanup${RESET}"
  echo -e "  ${DIM}Unlinking skill...${RESET}"
  gemini_quiet skills uninstall coding-aegis --scope user > /dev/null || true
  if [ -n "${TEST_DIR:-}" ] && [ -d "${TEST_DIR:-}" ]; then
    echo "  Removing test dir: $TEST_DIR"
    rm -rf "$TEST_DIR"
  fi
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

CATALOG_SCRIPT="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis/aegis-catalog.py"
SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
REAL_CATALOG="$REPO_ROOT/pkgs"

echo "========================================"
echo "coding-aegis skill test (Gemini CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo ""

# ══════════════════════════════════════════════════════════════
# Phase 0: Verify gemini CLI
# ══════════════════════════════════════════════════════════════
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 0: Gemini CLI check${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

echo -e "${BOLD}TEST: gemini installed${RESET}"
if command -v gemini &>/dev/null; then
  gemini_path=$(command -v gemini)
  gemini_version=$(gemini --version 2>&1 || echo "unknown")
  echo -e "  ${DIM}Path: $gemini_path${RESET}"
  echo -e "  ${DIM}Version: $gemini_version${RESET}"
  pass "gemini found: $gemini_version"
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
  echo -e "  ${YELLOW}$(echo "$auth_output" | head -10)${RESET}"
  fail "gemini auth check — check your API key or login"
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

echo -e "${BOLD}TEST: resolve-catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" resolve-catalog --from "$REPO_ROOT" 2>&1)
if echo "$output" | grep -q '"catalog"'; then
  pass "resolve-catalog"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "resolve-catalog"
fi

echo ""
echo -e "${BOLD}TEST: show helloworld${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show helloworld --catalog "$REAL_CATALOG" 2>&1)
errors=0
for expect in '"name": "helloworld"' '"version": "1.0.0"' '"tier": "optional"' '"author": "platform-team"'; do
  if ! echo "$output" | grep -q "$expect"; then
    echo -e "  ${RED}Missing: $expect${RESET}"
    errors=$((errors + 1))
  fi
done
if [ "$errors" -eq 0 ]; then
  pass "show helloworld — all fields correct"
else
  fail "show helloworld — $errors fields missing"
fi

echo ""
echo -e "${BOLD}TEST: list fixture catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" list --catalog "$REAL_CATALOG" 2>&1)
if echo "$output" | grep -q '"helloworld"'; then
  pass "list finds helloworld"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "list — helloworld not found"
fi

echo ""
echo -e "${BOLD}TEST: install-prep helloworld${RESET}"
output=$(python3 "$CATALOG_SCRIPT" install-prep helloworld --catalog "$REAL_CATALOG" 2>&1)
if echo "$output" | grep -q 'aegis--helloworld--helloworld.md' && echo "$output" | grep -q 'managed-by: coding-aegis'; then
  pass "install-prep — correct filename and frontmatter"
else
  echo -e "  ${YELLOW}$(echo "$output" | head -20)${RESET}"
  fail "install-prep"
fi

echo ""
echo -e "${BOLD}TEST: status with mock install${RESET}"
MOCK_DIR="$(mktemp -d)"
mkdir -p "$MOCK_DIR/rules"
cat > "$MOCK_DIR/rules/aegis--helloworld--helloworld.md" <<'RULE'
---
package: helloworld
rule: helloworld
version: 1.0.0
tier: optional
managed-by: coding-aegis
---

# Hello World
RULE
output=$(python3 "$CATALOG_SCRIPT" status --catalog "$REAL_CATALOG" --scope "$MOCK_DIR" 2>&1)
if echo "$output" | grep -q '"name": "helloworld"' && echo "$output" | grep -q '"status": "current"'; then
  pass "status — detected helloworld as current"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "status"
fi
rm -rf "$MOCK_DIR"

# ══════════════════════════════════════════════════════════════
# Phase 2: Gemini skill lifecycle (link/list/uninstall)
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 2: Gemini skill lifecycle${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

# Clean stale registration
gemini_quiet skills uninstall coding-aegis --scope user > /dev/null || true

# Test: skill link (local development path — no git clone needed)
echo -e "${BOLD}TEST: gemini skills link${RESET}"
output=$(gemini_quiet skills link "$SKILL_DIR" --scope user --consent) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "link\|success\|install"; then
  pass "skills link"
else
  fail "skills link — unexpected output"
fi

# Test: skill list
echo ""
echo -e "${BOLD}TEST: gemini skills list${RESET}"
output=$(gemini_quiet skills list) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "coding-aegis"; then
  pass "skills list shows coding-aegis"
else
  fail "skills list — coding-aegis not found"
fi

# Test: skill uninstall
echo ""
echo -e "${BOLD}TEST: gemini skills uninstall${RESET}"
output=$(gemini_quiet skills uninstall coding-aegis --scope user) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "uninstall\|remov\|success"; then
  pass "skills uninstall"
else
  fail "skills uninstall — unexpected output"
fi

# Test: skill gone after uninstall
echo ""
echo -e "${BOLD}TEST: gemini skills list after uninstall${RESET}"
output=$(gemini_quiet skills list) || true
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -qi "coding-aegis"; then
  fail "skill still present after uninstall"
else
  pass "skill removed from list"
fi

# ══════════════════════════════════════════════════════════════
# Phase 3: Skill commands via aegis-catalog.py (direct)
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 3: Skill commands (direct CLI)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

# Test: show — full detail validation
echo -e "${BOLD}TEST: show helloworld — full detail${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show helloworld --catalog "$REAL_CATALOG" 2>&1)
errors=0
for expect in '"name": "helloworld"' '"version": "1.0.0"' '"tier": "optional"' '"author": "platform-team"' '"artifact_summary": "1 rule, 1 skill"'; do
  if ! echo "$output" | grep -q "$expect"; then
    echo -e "  ${RED}Missing: $expect${RESET}"
    errors=$((errors + 1))
  fi
done
if [ "$errors" -eq 0 ]; then
  pass "show helloworld — all fields correct"
else
  fail "show helloworld — $errors fields missing"
fi

# Test: list — tier structure
echo ""
echo -e "${BOLD}TEST: list — tier structure${RESET}"
output=$(python3 "$CATALOG_SCRIPT" list --catalog "$REAL_CATALOG" 2>&1)
errors=0
for tier in required best-practices optional goodies; do
  if ! echo "$output" | grep -q "\"name\": \"$tier\""; then
    echo -e "  ${RED}Missing tier: $tier${RESET}"
    errors=$((errors + 1))
  fi
done
if ! echo "$output" | grep -q '"helloworld"'; then
  echo -e "  ${RED}Missing: helloworld in listing${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "list — 4 tiers, helloworld in optional"
else
  fail "list — $errors issues"
fi

# Test: install-prep — artifact validation
echo ""
echo -e "${BOLD}TEST: install-prep helloworld — artifact detail${RESET}"
output=$(python3 "$CATALOG_SCRIPT" install-prep helloworld --catalog "$REAL_CATALOG" 2>&1)
errors=0
if ! echo "$output" | grep -q '"target_filename": "aegis--helloworld--helloworld.md"'; then
  echo -e "  ${RED}Missing: rule target filename${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$output" | grep -q 'managed-by: coding-aegis'; then
  echo -e "  ${RED}Missing: managed-by in content${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$output" | grep -q '"target_subdir": "skills/helloworld"'; then
  echo -e "  ${RED}Missing: skill subdir${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "install-prep — rule filename, frontmatter, skill copy all correct"
else
  fail "install-prep — $errors issues"
fi

# ══════════════════════════════════════════════════════════════
# Phase 4: Install command — full pipeline
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 4: Install pipeline (direct CLI)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"

source "$(dirname "$0")/lib-install-test.sh"
run_install_tests helloworld "$REPO_ROOT/pkgs"
