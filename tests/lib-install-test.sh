#!/usr/bin/env bash
# Shared install command test for all tool test scripts.
# Source this file after defining CATALOG_SCRIPT, pass(), fail().
#
# Usage in test scripts:
#   source "$(dirname "$0")/lib-install-test.sh"
#   run_install_tests                              # uses helloworld from real catalog
#   run_install_tests test-stub "$FIXTURE_CATALOG" # uses fixture catalog

run_install_tests() {
  local pkg_name="${1:-helloworld}"
  local catalog="${2:-$REPO_ROOT/pkgs}"

  echo ""
  echo -e "${BOLD}TEST: install-prep + file write ($pkg_name)${RESET}"

  local install_dir
  install_dir="$(mktemp -d)"
  local scope_dir="$install_dir/.claude"

  # Step 1: Get prepared artifacts from install-prep
  local prep_json
  prep_json=$(python3 "$CATALOG_SCRIPT" install-prep "$pkg_name" --catalog "$catalog" 2>&1)
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
  echo -e "  ${DIM}$artifact_count artifacts to write${RESET}"

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

  # Step 3: Verify rule file exists with correct naming
  local errors=0
  local rule_file
  rule_file=$(find "$scope_dir/rules" -name "aegis--${pkg_name}--*.md" 2>/dev/null | head -1)

  if [ -z "$rule_file" ]; then
    echo -e "  ${RED}Missing: rules/aegis--${pkg_name}--*.md${RESET}"
    errors=$((errors + 1))
  else
    # Step 4: Verify frontmatter in installed rule
    local rule_content
    rule_content=$(cat "$rule_file")
    for expect in "managed-by: coding-aegis" "package: ${pkg_name}" "tier:"; do
      if ! echo "$rule_content" | grep -q "$expect"; then
        echo -e "  ${RED}Missing in rule frontmatter: $expect${RESET}"
        errors=$((errors + 1))
      fi
    done
  fi

  # Step 5: Verify skill exists
  if [ ! -f "$scope_dir/skills/${pkg_name}/SKILL.md" ]; then
    echo -e "  ${RED}Missing: skills/${pkg_name}/SKILL.md${RESET}"
    errors=$((errors + 1))
  else
    if ! grep -q "$pkg_name" "$scope_dir/skills/${pkg_name}/SKILL.md"; then
      echo -e "  ${RED}Skill SKILL.md missing ${pkg_name} content${RESET}"
      errors=$((errors + 1))
    fi
  fi

  # Step 6: Verify status sees the installed package
  local status_json
  status_json=$(python3 "$CATALOG_SCRIPT" status --catalog "$catalog" --scope "$scope_dir" 2>&1)
  if ! echo "$status_json" | grep -q "\"name\": \"${pkg_name}\""; then
    echo -e "  ${RED}status does not detect installed ${pkg_name}${RESET}"
    errors=$((errors + 1))
  fi
  if ! echo "$status_json" | grep -q '"status": "current"'; then
    echo -e "  ${RED}status does not show current version${RESET}"
    errors=$((errors + 1))
  fi

  if [ "$errors" -eq 0 ]; then
    pass "install pipeline ($pkg_name) — files, frontmatter, status all correct"
  else
    fail "install pipeline ($pkg_name) — $errors issues"
    echo "  Files in scope dir:"
    find "$scope_dir" -type f 2>/dev/null | sed "s|$scope_dir/||" | sort | sed 's/^/    /'
  fi

  rm -rf "$install_dir"
}
