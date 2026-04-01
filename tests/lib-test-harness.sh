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
    ( sleep "$secs" && kill "$pid" 2>/dev/null ) >/dev/null 2>&1 &
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
# RUN_DIR and CLI_PROMPT reset after each call.
RUN_DIR=""
CLI_PROMPT=""

run_cli() {
  local description="$1"; shift

  # Build display command: strip _quiet suffix from wrapper function names
  local display_cmd="$*"
  if [[ "$1" == *_quiet ]]; then
    display_cmd="${1%_quiet} ${*:2}"
  fi

  # Show as: $ echo "prompt" | command   or just   $ command
  if [ -n "$CLI_PROMPT" ]; then
    # Wrap prompt text and pipe to command
    local prompt_lines
    prompt_lines=$(echo "$CLI_PROMPT" | fmt -w 68)
    local first_line last_line
    first_line=$(echo "$prompt_lines" | head -1)
    local line_count
    line_count=$(echo "$prompt_lines" | wc -l | tr -d ' ')

    if [ "$line_count" -eq 1 ]; then
      echo -e "  ${DIM}\$ echo \"${first_line}\" \\\\${RESET}"
      echo -e "  ${DIM}    | ${display_cmd}${RESET}"
    else
      echo -e "  ${DIM}\$ echo \"${first_line}${RESET}"
      echo "$prompt_lines" | tail -n +2 | while IFS= read -r line; do
        echo -e "  ${DIM}    ${line}${RESET}"
      done
      echo -e "  ${DIM}    \" | ${display_cmd}${RESET}"
    fi
  else
    echo -e "  ${DIM}\$ ${display_cmd}${RESET}"
  fi
  [ -n "$RUN_DIR" ] && echo -e "  ${DIM}    (in $RUN_DIR)${RESET}"

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

  # Normalize timeout exit codes — register as a failure and return 0
  # so set -e doesn't abort the script before subsequent assertions run.
  if [ "$LAST_EXIT" -eq 124 ] || [ "$LAST_EXIT" -eq 142 ] || [ "$LAST_EXIT" -eq 143 ]; then
    echo -e "  ${DIM}(${elapsed}s elapsed)${RESET}"
    fail "TIMEOUT after ${TIMEOUT}s: $description"
    return 0
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

# ── Quota / rate-limit guard ────────────────────────────────

# assert_no_quota_error <output> [tool-name]
# Check if output contains quota/rate-limit errors. If detected,
# register a FAIL and exit (cleanup trap handles teardown).
assert_no_quota_error() {
  local output="$1"
  local tool="${2:-agent}"

  if echo "$output" | grep -qi "quota\|rate.limit\|RESOURCE_EXHAUSTED\|429\|too many requests\|limit exceeded\|try again later"; then
    fail "${tool} API quota exhausted — aborting test run"
    echo ""
    echo -e "  ${RED}Quota/rate-limit error detected in ${tool} output:${RESET}"
    echo "$output" | grep -i "quota\|rate.limit\|RESOURCE_EXHAUSTED\|429\|too many requests\|limit exceeded\|try again later" | head -5 | while IFS= read -r line; do
      echo -e "    ${DIM}${line}${RESET}"
    done
    exit 1
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
