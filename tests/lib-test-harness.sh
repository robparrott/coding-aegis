#!/usr/bin/env bash
# Shared test harness for coding-aegis skill test scripts.
# Source this at the top of each test script.
#
# Provides: run_cli, assert_contains, assert_not_contains,
#           assert_file_exists, assert_file_contains,
#           pass, fail, print_results
#
# Usage:
#   source "$(dirname "$0")/lib-test-harness.sh"
#   run_cli "auth check" claude -p "Reply with AUTH_OK"
#   assert_contains "$LAST_OUTPUT" "AUTH_OK" "authenticated"

# Counters
PASS=0
FAIL=0

# Timeout (override with AEGIS_TEST_TIMEOUT env var)
TIMEOUT=${AEGIS_TEST_TIMEOUT:-90}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

# Last command results (set by run_cli)
LAST_OUTPUT=""
LAST_EXIT=0

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

# ── Core functions ──────────────────────────────────────────

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

# ── CLI invocation ──────────────────────────────────────────

# run_cli <description> <command...>
#
# Executes a CLI command with timeout. Sets LAST_OUTPUT and LAST_EXIT.
# Prints command, elapsed time, and an output snippet.
#
# Set RUN_DIR before calling to execute in a different directory.
# Set CLI_PROMPT to pipe a prompt via stdin (avoids shell quoting issues).
# When CLI_PROMPT is set, stdin is piped; otherwise stdin is /dev/null.
# Both reset after each call.
RUN_DIR=""
CLI_PROMPT=""

run_cli() {
  local description="$1"; shift

  # Print command in dim text
  local display_cmd="$*"
  if [ ${#display_cmd} -gt 120 ]; then
    display_cmd="${display_cmd:0:117}..."
  fi
  echo -e "  ${DIM}\$ ${display_cmd}${RESET}"
  [ -n "$RUN_DIR" ] && echo -e "  ${DIM}  (in $RUN_DIR)${RESET}"
  [ -n "$CLI_PROMPT" ] && echo -e "  ${DIM}  prompt: ${CLI_PROMPT:0:100}${RESET}"

  local start_time
  start_time=$(date +%s)

  LAST_EXIT=0
  if [ -n "$RUN_DIR" ] && [ -n "$CLI_PROMPT" ]; then
    LAST_OUTPUT=$(cd "$RUN_DIR" && echo "$CLI_PROMPT" | timeout "$TIMEOUT" "$@" 2>&1) || LAST_EXIT=$?
  elif [ -n "$RUN_DIR" ]; then
    LAST_OUTPUT=$(cd "$RUN_DIR" && timeout "$TIMEOUT" "$@" < /dev/null 2>&1) || LAST_EXIT=$?
  elif [ -n "$CLI_PROMPT" ]; then
    LAST_OUTPUT=$(echo "$CLI_PROMPT" | timeout "$TIMEOUT" "$@" 2>&1) || LAST_EXIT=$?
  else
    LAST_OUTPUT=$(timeout "$TIMEOUT" "$@" < /dev/null 2>&1) || LAST_EXIT=$?
  fi
  RUN_DIR=""
  CLI_PROMPT=""

  local end_time elapsed
  end_time=$(date +%s)
  elapsed=$((end_time - start_time))

  # Normalize timeout exit codes
  if [ "$LAST_EXIT" -eq 124 ] || [ "$LAST_EXIT" -eq 142 ] || [ "$LAST_EXIT" -eq 143 ]; then
    echo -e "  ${RED}TIMEOUT after ${TIMEOUT}s${RESET}"
    echo -e "  ${DIM}(${elapsed}s elapsed)${RESET}"
    return "$LAST_EXIT"
  fi

  echo -e "  ${DIM}(${elapsed}s elapsed, exit ${LAST_EXIT})${RESET}"

  # Print output snippet (first 20 lines)
  if [ -n "$LAST_OUTPUT" ]; then
    echo -e "${YELLOW}$(echo "$LAST_OUTPUT" | head -20)${RESET}"
  fi

  # Always return 0 so set -e doesn't abort the script.
  # Callers check LAST_EXIT for the real exit code.
  return 0
}

# ── Assertions ──────────────────────────────────────────────

# assert_contains <output> <pattern> <description>
assert_contains() {
  local output="$1"
  local pattern="$2"
  local description="$3"

  if echo "$output" | grep -qi "$pattern"; then
    pass "$description"
  else
    fail "$description — expected '$pattern' not found"
  fi
}

# assert_not_contains <output> <pattern> <description>
assert_not_contains() {
  local output="$1"
  local pattern="$2"
  local description="$3"

  if echo "$output" | grep -qi "$pattern"; then
    fail "$description — '$pattern' should not be present"
  else
    pass "$description"
  fi
}

# assert_file_exists <path> <description>
assert_file_exists() {
  local path="$1"
  local description="$2"

  if [ -f "$path" ]; then
    pass "$description"
  else
    fail "$description — file not found: $path"
  fi
}

# assert_file_contains <path> <pattern> <description>
assert_file_contains() {
  local path="$1"
  local pattern="$2"
  local description="$3"

  if [ ! -f "$path" ]; then
    fail "$description — file not found: $path"
    return
  fi

  if grep -q "$pattern" "$path"; then
    pass "$description"
  else
    fail "$description — '$pattern' not found in $(basename "$path")"
  fi
}

# ── Section headers ─────────────────────────────────────────

# section <title>
section() {
  echo ""
  echo -e "${BOLD}══════════════════════════════════════════${RESET}"
  echo -e "${BOLD}$1${RESET}"
  echo -e "${BOLD}══════════════════════════════════════════${RESET}"
  echo ""
}

# test_header <title>
test_header() {
  echo -e "${BOLD}TEST: $1${RESET}"
}
