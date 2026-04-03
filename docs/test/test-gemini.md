# Gemini — Test Detail

> Tool-specific details for the Gemini skill install test. For the full test plan, phase definitions, and pass criteria see [testing-spec.md](testing-spec.md).

## Install Mechanisms

### T1 — Register Marketplace

Gemini has no separate marketplace registration step. Skip T1 and proceed directly to T2.

### T2 — Install Skill

```bash
gemini_quiet skills link "$SKILL_DIR" --scope workspace --consent
```

Where `$SKILL_DIR` is the local path to `pkgs/bootstrap/coding-aegis/skills/coding-aegis`.

Assert: output contains `link\|success\|install`; `gemini skills list` shows `coding-aegis`.

After T2, copy the `pkgs/` catalog into `$TEST_DIR`:

```bash
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
```

Also requires `git init` in `$TEST_DIR` (Gemini requires a git repo in the working directory).

## CLI Invocation Flags

**Agent-mediated calls** (T2b–T7.1):

```bash
gemini_quiet -o text --yolo
```

- `-o text` — plain text output
- `--yolo` — auto-approve tool use; without this Gemini prompts for approval which hangs in headless mode

**`gemini_quiet` wrapper** filters Homebrew keytar warnings that pollute output:

```bash
gemini_quiet() {
  gemini "$@" 2>&1 | grep -v -E "Keychain initialization|keytar\.node|keytar\.js|FileKeychain fallback|Loaded cached credentials\.|^Require stack:"
}
```

**Non-agent management commands** do not use `CLI_PROMPT`:

```bash
run_cli "skills link"      gemini_quiet skills link "$SKILL_DIR" --scope workspace --consent
run_cli "skills list"      gemini_quiet skills list
run_cli "skills uninstall" gemini_quiet skills uninstall coding-aegis --scope workspace
```

## Quota Handling

All agent-mediated steps must call `assert_no_quota_error "$LAST_OUTPUT" "Gemini"` immediately after `run_cli`. If a quota error is detected, the harness fails and aborts — do not attempt to continue.

T7.1 (uninstall helloworld) includes a quota fallback: if the agent call returns a quota error, fall back to manual file removal so teardown can complete cleanly.

## Prompts (T2b–T7.1)

| Step | Prompt |
|------|--------|
| T2b detect-tool (agent) | `/coding-aegis detect-tool` |
| T2c detect-tool (skill) | `/coding-aegis detect-tool` |
| T3 list | `/coding-aegis list` |
| T4 show | `/coding-aegis show helloworld` |
| T5 install | `/coding-aegis install helloworld to Project scope` |
| T6b invoke | `/helloworld` |
| T7.1 uninstall | `/coding-aegis uninstall helloworld` |

## Tool Detection (T2b)

Gemini links skills from local paths with no tool-specific directory segment. The `path:.claude` / `path:.codex` signals do not fire. Detection requires an agent-mediated invocation so the `GEMINI_CLI=1` env var is present.

- **Method**: agent-mediated — `/coding-aegis detect-tool` (or direct bash with env var set)
- **Expected `tool`**: `gemini`
- **Expected signal**: `env:GEMINI_CLI=1`

## Installed Paths

Gemini uses the same install paths as Claude Code (`.claude/` for project scope) because it reads Claude-compatible rule files.

| Artifact | Path |
|----------|------|
| Skill dir | `$SKILL_DIR` (linked repo path, not copied) |
| Rules (project scope) | `$TEST_DIR/.claude/rules/aegis--*` |
| Skills (project scope) | `$TEST_DIR/.claude/skills/helloworld/` |

## Teardown

| Step | Command | Assertion |
|------|---------|-----------|
| T7.1 Uninstall helloworld | `/coding-aegis uninstall helloworld` via agent | no `not installed\|error`; quota fallback removes files manually if needed |
| T7.2 Uninstall coding-aegis skill | `gemini_quiet skills uninstall coding-aegis --scope workspace` | `gemini skills list` no longer shows `coding-aegis` |
| T7.3 Remove marketplace | N/A — no separate marketplace | — |
| T7.4 Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
