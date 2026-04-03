#!/usr/bin/env bash
# coding-aegis CLI install/uninstall test — no LLM required
#
# Validates all aegis-*.py scripts directly via python3.
# Expected runtime: <5 seconds.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$(dirname "$0")/lib-test-harness.sh"

SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
CATALOG="$REPO_ROOT/pkgs"
TEST_DIR="$(mktemp -d)"

run_py() {
  local desc="$1"; shift
  test_header "$desc"
  local out
  out=$(python3 "$@" 2>&1)
  local rc=$?
  LAST_OUTPUT="$out"
  if [ $rc -ne 0 ]; then
    fail "$desc — script exited $rc"
    echo "  $out"
  fi
}

cleanup() {
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis CLI test (no LLM)"
echo "========================================"
echo "  Skill dir: $SKILL_DIR"
echo "  Catalog:   $CATALOG"
echo "  Test dir:  $TEST_DIR"

# ── Phase 1: aegis-list ───────────────────────────────────────
section "Phase 1: aegis-list.py"

run_py "list runs" "$SKILL_DIR/aegis-list.py" --catalog "$CATALOG"
assert_contains "$LAST_OUTPUT" "coding-aegis catalog" "list — header present"
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld package present"
assert_contains "$LAST_OUTPUT" "optional" "list — optional tier present"

# ── Phase 2: aegis-show ───────────────────────────────────────
section "Phase 2: aegis-show.py"

run_py "show helloworld" "$SKILL_DIR/aegis-show.py" helloworld --catalog "$CATALOG"
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "1.0.0" "show — version present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"
assert_contains "$LAST_OUTPUT" "rule" "show — rule artifact listed"
assert_contains "$LAST_OUTPUT" "skill" "show — skill artifact listed"

test_header "show unknown package exits non-zero"
if python3 "$SKILL_DIR/aegis-show.py" no-such-package --catalog "$CATALOG" 2>/dev/null; then
  fail "show unknown package — should have exited non-zero"
else
  pass "show unknown package — exited non-zero as expected"
fi

# ── Phase 3: install (claude) ─────────────────────────────────
section "Phase 3: aegis-install.py — claude, project scope"

( cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-install.py" helloworld \
    --scope project --tool claude --catalog "$CATALOG" )

assert_file_exists "$TEST_DIR/.claude/rules/aegis--helloworld--helloworld.md" \
  "claude: rule file written"
assert_file_contains "$TEST_DIR/.claude/rules/aegis--helloworld--helloworld.md" \
  "managed-by: coding-aegis" "claude: managed-by frontmatter present"
assert_file_contains "$TEST_DIR/.claude/rules/aegis--helloworld--helloworld.md" \
  "package: helloworld" "claude: package frontmatter present"
assert_file_exists "$TEST_DIR/.claude/skills/helloworld/SKILL.md" \
  "claude: skill file written"

# ── Phase 4: install (codex) ──────────────────────────────────
section "Phase 4: aegis-install.py — codex, project scope"

( cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-install.py" helloworld \
    --scope project --tool codex --catalog "$CATALOG" )

assert_file_exists "$TEST_DIR/AGENTS.md" "codex: AGENTS.md created"
assert_file_contains "$TEST_DIR/AGENTS.md" \
  "aegis:begin package=helloworld" "codex: begin marker in AGENTS.md"
assert_file_contains "$TEST_DIR/AGENTS.md" \
  "aegis:end package=helloworld" "codex: end marker in AGENTS.md"
assert_file_exists "$TEST_DIR/.agents/skills/helloworld/SKILL.md" \
  "codex: skill file written to .agents/"

# ── Phase 5: idempotent re-install ────────────────────────────
section "Phase 5: Idempotent re-install"

( cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-install.py" helloworld \
    --scope project --tool codex --catalog "$CATALOG" )

test_header "AGENTS.md has exactly one begin marker after re-install"
count=$(grep -c "aegis:begin package=helloworld" "$TEST_DIR/AGENTS.md" || true)
if [ "$count" -eq 1 ]; then
  pass "AGENTS.md: exactly one begin marker ($count)"
else
  fail "AGENTS.md: expected 1 begin marker, found $count"
fi

# ── Phase 6: aegis-status ─────────────────────────────────────
section "Phase 6: aegis-status.py"

out=$(cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-status.py" --catalog "$CATALOG" \
  --scope "$TEST_DIR/.claude" 2>&1)
assert_contains "$out" "helloworld" "status — helloworld listed"
assert_contains "$out" "current" "status — version is current"

# ── Phase 7: uninstall (codex) ────────────────────────────────
section "Phase 7: aegis-uninstall.py — codex"

( cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-uninstall.py" helloworld --tool codex )

test_header "codex: AGENTS.md section removed"
if grep -q "aegis:begin package=helloworld" "$TEST_DIR/AGENTS.md" 2>/dev/null; then
  fail "AGENTS.md: begin marker still present after codex uninstall"
else
  pass "AGENTS.md: begin marker removed"
fi
assert_dir_not_exists "$TEST_DIR/.agents/skills/helloworld" \
  "codex: .agents/skills/helloworld/ removed"

# ── Phase 8: uninstall (claude) ───────────────────────────────
section "Phase 8: aegis-uninstall.py — claude"

( cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-uninstall.py" helloworld --tool claude )

assert_file_not_exists \
  "$TEST_DIR/.claude/rules/aegis--helloworld--helloworld.md" \
  "claude: rule file removed"
assert_dir_not_exists "$TEST_DIR/.claude/skills/helloworld" \
  "claude: skill dir removed"

test_header "uninstall already-removed package exits non-zero"
if ( cd "$TEST_DIR" && python3 "$SKILL_DIR/aegis-uninstall.py" helloworld --tool claude 2>/dev/null ); then
  fail "second uninstall — should exit non-zero"
else
  pass "second uninstall — exited non-zero as expected"
fi

print_results
