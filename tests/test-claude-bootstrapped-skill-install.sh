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
echo "coding-aegis plugin marketplace test"
echo "========================================"
echo "  Repo root:   $REPO_ROOT"
echo "  GitHub repo: $GITHUB_REPO"
echo -e "  ${DIM}claude: $(command -v claude)${RESET}"

# Phase 1: local directory marketplace
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
FIXTURE_CATALOG="$REPO_ROOT/tests/fixtures/pkgs"

# Test: resolve-catalog
echo -e "${BOLD}TEST: aegis-catalog.py resolve-catalog${RESET}"
output=$(python3 "$CATALOG_SCRIPT" resolve-catalog --from "$REPO_ROOT" 2>&1)
echo -e "  ${YELLOW}${output}${RESET}"
if echo "$output" | grep -q '"catalog"'; then
  pass "resolve-catalog"
else
  fail "resolve-catalog"
fi

# Test: list (using test fixture catalog)
echo ""
echo -e "${BOLD}TEST: aegis-catalog.py list (fixture)${RESET}"
output=$(python3 "$CATALOG_SCRIPT" list --catalog "$FIXTURE_CATALOG" 2>&1)
if echo "$output" | grep -q '"test-stub"'; then
  pass "list finds test-stub in fixture catalog"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "list — test-stub not found"
fi

# Test: show (using test fixture catalog)
echo ""
echo -e "${BOLD}TEST: aegis-catalog.py show test-stub (fixture)${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
if echo "$output" | grep -q '"goodies"' && echo "$output" | grep -q '"1.0.0"'; then
  pass "show test-stub — correct tier and version"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "show test-stub"
fi

# Test: install-prep (using test fixture catalog)
echo ""
echo -e "${BOLD}TEST: aegis-catalog.py install-prep test-stub (fixture)${RESET}"
output=$(python3 "$CATALOG_SCRIPT" install-prep test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
if echo "$output" | grep -q 'aegis--test-stub--test-rule.md' && echo "$output" | grep -q 'managed-by: coding-aegis'; then
  pass "install-prep — correct filename and frontmatter"
else
  echo -e "  ${YELLOW}$(echo "$output" | head -20)${RESET}"
  fail "install-prep"
fi

# Test: show not-found
echo ""
echo -e "${BOLD}TEST: aegis-catalog.py show nonexistent (fixture)${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show nonexistent --catalog "$FIXTURE_CATALOG" 2>&1) || true
if echo "$output" | grep -q '"error"'; then
  pass "show nonexistent — returns error"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "show nonexistent — expected error"
fi

# ══════════════════════════════════════════════════════════════
# Phase 4: Skill commands via aegis-catalog.py (direct)
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 4: Skill commands (direct CLI)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo ""

# Test: show — full detail validation
echo -e "${BOLD}TEST: show test-stub — full detail${RESET}"
output=$(python3 "$CATALOG_SCRIPT" show test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
errors=0
for expect in '"name": "test-stub"' '"version": "1.0.0"' '"tier": "goodies"' '"author": "test-team"' '"artifact_summary": "1 rule, 1 skill"'; do
  if ! echo "$output" | grep -q "$expect"; then
    echo -e "  ${RED}Missing: $expect${RESET}"
    errors=$((errors + 1))
  fi
done
if echo "$output" | grep -q '"readme"'; then
  : # readme field present
else
  echo -e "  ${RED}Missing: readme field${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "show test-stub — all fields correct"
else
  fail "show test-stub — $errors fields missing"
fi

# Test: list — tier structure and package presence
echo ""
echo -e "${BOLD}TEST: list — tier structure${RESET}"
output=$(python3 "$CATALOG_SCRIPT" list --catalog "$FIXTURE_CATALOG" 2>&1)
errors=0
# Verify all 4 tiers present
for tier in required best-practices optional goodies; do
  if ! echo "$output" | grep -q "\"name\": \"$tier\""; then
    echo -e "  ${RED}Missing tier: $tier${RESET}"
    errors=$((errors + 1))
  fi
done
# Verify test-stub appears in goodies
if ! echo "$output" | grep -q '"test-stub"'; then
  echo -e "  ${RED}Missing: test-stub in listing${RESET}"
  errors=$((errors + 1))
fi
# Verify empty tiers have no packages
required_pkgs=$(echo "$output" | python3 -c "import sys,json; d=json.load(sys.stdin); t=[x for x in d['tiers'] if x['name']=='required'][0]; print(len(t['packages']))" 2>/dev/null || echo "?")
if [ "$required_pkgs" = "0" ]; then
  : # correct
else
  echo -e "  ${RED}required tier should be empty, got $required_pkgs packages${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "list — 4 tiers, test-stub in goodies, empty tiers correct"
else
  fail "list — $errors issues"
fi

# Test: install-prep — full artifact validation
echo ""
echo -e "${BOLD}TEST: install-prep test-stub — artifact detail${RESET}"
output=$(python3 "$CATALOG_SCRIPT" install-prep test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
errors=0
# Rule artifact checks
if ! echo "$output" | grep -q '"target_filename": "aegis--test-stub--test-rule.md"'; then
  echo -e "  ${RED}Missing: rule target filename${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$output" | grep -q '"target_subdir": "rules"'; then
  echo -e "  ${RED}Missing: rules subdir${RESET}"
  errors=$((errors + 1))
fi
# Frontmatter in content
if ! echo "$output" | grep -q 'managed-by: coding-aegis'; then
  echo -e "  ${RED}Missing: managed-by in content${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$output" | grep -q 'package: test-stub'; then
  echo -e "  ${RED}Missing: package in frontmatter${RESET}"
  errors=$((errors + 1))
fi
# Skill artifact checks
if ! echo "$output" | grep -q '"target_subdir": "skills/test-stub"'; then
  echo -e "  ${RED}Missing: skill subdir${RESET}"
  errors=$((errors + 1))
fi
# Verify original description preserved
if ! echo "$output" | grep -q 'test rule for validation'; then
  echo -e "  ${RED}Missing: original description preserved${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "install-prep — rule filename, frontmatter, skill copy all correct"
else
  fail "install-prep — $errors issues"
fi

# Test: status — with mock installed files
echo ""
echo -e "${BOLD}TEST: status — detects installed package${RESET}"
TEST_DIR="$(mktemp -d)"
trap 'rm -rf "$TEST_DIR"; print_results' EXIT
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
errors=0
if ! echo "$output" | grep -q '"name": "test-stub"'; then
  echo -e "  ${RED}Missing: test-stub in status${RESET}"
  errors=$((errors + 1))
fi
if ! echo "$output" | grep -q '"status": "current"'; then
  echo -e "  ${RED}Missing: current status${RESET}"
  errors=$((errors + 1))
fi
if [ "$errors" -eq 0 ]; then
  pass "status — detected test-stub as current"
else
  echo -e "  ${YELLOW}${output}${RESET}"
  fail "status — $errors issues"
fi
rm -rf "$TEST_DIR"

# ══════════════════════════════════════════════════════════════
# Phase 5: Install command — full pipeline
# ══════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}══════════════════════════════════════════${RESET}"
echo -e "${BOLD}Phase 5: Install pipeline (direct CLI)${RESET}"
echo -e "${BOLD}══════════════════════════════════════════${RESET}"

source "$(dirname "$0")/lib-install-test.sh"
run_install_tests
