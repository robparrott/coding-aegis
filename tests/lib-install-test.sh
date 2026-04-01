#!/usr/bin/env bash
# Shared install command test for all tool test scripts.
# Source this file after defining CATALOG_SCRIPT, FIXTURE_CATALOG, pass(), fail().
#
# Usage in test scripts:
#   source "$(dirname "$0")/lib-install-test.sh"
#   run_install_tests

run_install_tests() {
  echo ""
  echo -e "${BOLD}TEST: install-prep + file write${RESET}"

  local install_dir
  install_dir="$(mktemp -d)"
  local scope_dir="$install_dir/.claude"

  # Step 1: Get prepared artifacts from install-prep
  local prep_json
  prep_json=$(python3 "$CATALOG_SCRIPT" install-prep test-stub --catalog "$FIXTURE_CATALOG" 2>&1)
  if echo "$prep_json" | grep -q '"error"'; then
    echo -e "  ${YELLOW}${prep_json}${RESET}"
    fail "install-prep returned error"
    rm -rf "$install_dir"
    return
  fi

  # Step 2: Write artifacts using the JSON output
  local artifact_count
  artifact_count=$(echo "$prep_json" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['artifacts']))" 2>/dev/null)
  if [ -z "$artifact_count" ] || [ "$artifact_count" -eq 0 ]; then
    fail "install-prep returned no artifacts"
    rm -rf "$install_dir"
    return
  fi

  # Write each artifact to the scope dir
  echo "$prep_json" | python3 -c "
import sys, json, os
data = json.load(sys.stdin)
scope = sys.argv[1]
for a in data['artifacts']:
    target = os.path.join(scope, a['target_subdir'], a['target_filename'])
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, 'w') as f:
        f.write(a['content'])
    print(f'  wrote: {a[\"target_subdir\"]}/{a[\"target_filename\"]}')
" "$scope_dir"

  # Step 3: Verify files exist
  local errors=0

  if [ ! -f "$scope_dir/rules/aegis--test-stub--test-rule.md" ]; then
    echo -e "  ${RED}Missing: rules/aegis--test-stub--test-rule.md${RESET}"
    errors=$((errors + 1))
  fi

  if [ ! -f "$scope_dir/skills/test-stub/SKILL.md" ]; then
    echo -e "  ${RED}Missing: skills/test-stub/SKILL.md${RESET}"
    errors=$((errors + 1))
  fi

  # Step 4: Verify frontmatter in installed rule
  if [ -f "$scope_dir/rules/aegis--test-stub--test-rule.md" ]; then
    local rule_content
    rule_content=$(cat "$scope_dir/rules/aegis--test-stub--test-rule.md")
    for expect in "managed-by: coding-aegis" "package: test-stub" "version: 1.0.0" "tier: goodies"; do
      if ! echo "$rule_content" | grep -q "$expect"; then
        echo -e "  ${RED}Missing in rule frontmatter: $expect${RESET}"
        errors=$((errors + 1))
      fi
    done
    # Verify original description preserved
    if ! echo "$rule_content" | grep -q "test rule for validation"; then
      echo -e "  ${RED}Missing: original description not preserved${RESET}"
      errors=$((errors + 1))
    fi
  fi

  # Step 5: Verify skill content
  if [ -f "$scope_dir/skills/test-stub/SKILL.md" ]; then
    if ! grep -q "test-stub" "$scope_dir/skills/test-stub/SKILL.md"; then
      echo -e "  ${RED}Skill SKILL.md missing test-stub content${RESET}"
      errors=$((errors + 1))
    fi
  fi

  # Step 6: Verify status sees the installed package
  local status_json
  status_json=$(python3 "$CATALOG_SCRIPT" status --catalog "$FIXTURE_CATALOG" --scope "$scope_dir" 2>&1)
  if ! echo "$status_json" | grep -q '"name": "test-stub"'; then
    echo -e "  ${RED}status does not detect installed test-stub${RESET}"
    errors=$((errors + 1))
  fi
  if ! echo "$status_json" | grep -q '"status": "current"'; then
    echo -e "  ${RED}status does not show current version${RESET}"
    errors=$((errors + 1))
  fi

  if [ "$errors" -eq 0 ]; then
    pass "install-prep + write — files correct, frontmatter valid, status detects install"
  else
    fail "install-prep + write — $errors issues"
    echo "  Files in scope dir:"
    find "$scope_dir" -type f 2>/dev/null | sed "s|$scope_dir/||" | sort | sed 's/^/    /'
  fi

  rm -rf "$install_dir"
}
