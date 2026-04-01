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
source "$(dirname "$0")/lib-test-harness.sh"

SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
TEST_DIR="$(mktemp -d)"

cleanup() {
  section "T6: Teardown"
  echo "  Removing test dir: $TEST_DIR"
  rm -rf "$TEST_DIR"
  print_results
}
trap cleanup EXIT

echo "========================================"
echo "coding-aegis skill test (Codex CLI)"
echo "========================================"
echo "  Repo root: $REPO_ROOT"
echo "  Test dir:  $TEST_DIR"
echo "  Timeout:   ${TIMEOUT}s"

# ── T0: Prerequisites ────────────────────────────────────────
section "T0: Prerequisites"

test_header "codex installed"
if command -v codex &>/dev/null; then
  pass "codex found: $(codex --version 2>&1 || echo unknown)"
else
  fail "codex not found in PATH"
  exit 1
fi

test_header "codex authenticated"
git -C "$TEST_DIR" init -q
CLI_PROMPT="Reply with exactly: AUTH_OK"
RUN_DIR="$TEST_DIR" run_cli "auth check" codex exec --ephemeral -o /dev/stdout
assert_contains "$LAST_OUTPUT" "AUTH_OK" "codex authenticated"

# ── T1: Install coding-aegis skill ───────────────────────────
section "T1: Install coding-aegis skill"

test_header "copy skill to .agents/skills/"
mkdir -p "$TEST_DIR/.agents/skills/coding-aegis"
cp "$SKILL_DIR/SKILL.md" "$TEST_DIR/.agents/skills/coding-aegis/SKILL.md"
cp "$SKILL_DIR/aegis-catalog.py" "$TEST_DIR/.agents/skills/coding-aegis/aegis-catalog.py"
assert_file_exists "$TEST_DIR/.agents/skills/coding-aegis/SKILL.md" "skill installed to .agents/skills/"

# Make catalog accessible
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"

# ── T2: Use skill — list ─────────────────────────────────────
section "T2: Use skill — list packages"

test_header "coding-aegis list"
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its list command. The pkgs/ catalog is at ./pkgs/ in the current directory."
RUN_DIR="$TEST_DIR" run_cli "skill list" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "helloworld" "list — helloworld found"

# ── T3: Use skill — show ─────────────────────────────────────
section "T3: Use skill — show helloworld"

test_header "coding-aegis show helloworld"
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its show command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory."
RUN_DIR="$TEST_DIR" run_cli "skill show" codex exec --ephemeral -s read-only -o /dev/stdout
assert_contains "$LAST_OUTPUT" "helloworld" "show — name present"
assert_contains "$LAST_OUTPUT" "optional" "show — tier present"

# ── T4: Use skill — install ──────────────────────────────────
section "T4: Use skill — install helloworld"

test_header "coding-aegis install helloworld"
CLI_PROMPT="You have the coding-aegis skill loaded. Execute its install command for the package named helloworld. The pkgs/ catalog is at ./pkgs/ in the current directory. Use Project scope (.claude/ in the current directory) without asking the user."
RUN_DIR="$TEST_DIR" run_cli "skill install" codex exec --ephemeral -s workspace-write -o /dev/stdout
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
