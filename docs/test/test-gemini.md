# Gemini — Test Detail

> **STATUS (2026-04-22)**: Path bugs fixed. Tests run and produce: 3 pass / 1 skip (no marketplace) / 6 quota-skip. Phases 1, 3, 4a pass on free tier. Agent-mediated phases (4b–6) skip gracefully on quota exhaustion. Full pass requires paid Gemini quota — tracked in `97z.13`.

> Tool-specific details for the Gemini skill install test. For the full test plan, phase definitions, and pass criteria see [TEST.md](TEST.md).

## Install Mechanisms

### Phase 2 — Marketplace / Registry Setup

Gemini has no separate marketplace registration step. Skip Phase 2 and proceed directly to Phase 3.

### Phase 3 — Install coding-aegis Skill

```bash
gemini_quiet skills link "$SKILL_DIR" --scope workspace --consent
```

Where `$SKILL_DIR` is the local path to `pkgs/bootstrap/coding-aegis/skills/coding-aegis`.

Assert: output contains `link\|success\|install`; `gemini skills list` shows `coding-aegis`.

After Phase 3, copy the `pkgs/` catalog into `$TEST_DIR`:

```bash
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
```

Also requires `git init` in `$TEST_DIR` (Gemini requires a git repo in the working directory).

## CLI Invocation Flags

**Agent-mediated calls** (phases 4–6):

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

Phase 6.1 (uninstall helloworld) includes a quota fallback: if the agent call returns a quota error, fall back to manual file removal so teardown can complete cleanly.

## Prompts (phases 4–6)

| Phase | Step | Prompt |
|-------|------|--------|
| 4.2 | detect-tool skill command | `/coding-aegis detect-tool` |
| 4.3 | list | `/coding-aegis list` |
| 4.4 | show | `/coding-aegis show helloworld` |
| 5.1 | install helloworld | `/coding-aegis install helloworld to Project scope` |
| 5.5 | invoke helloworld | `/helloworld` |
| 6.1 | uninstall helloworld | `/coding-aegis uninstall helloworld` |

## Tool Detection (Phase 4.2)

Gemini links skills from local paths with no tool-specific directory segment. The `path:.claude` / `path:.codex` signals do not fire. Detection requires an agent-mediated invocation so the `GEMINI_CLI=1` env var is present.

- **Method**: agent-mediated — `/coding-aegis detect-tool` (or direct bash with env var set)
- **Expected `tool`**: `gemini`
- **Expected signal**: `env:GEMINI_CLI=1`

Note: Phase 3.3 (`detect_tool.py` present) is verified against the linked `$SKILL_DIR` path directly, since the skill is not copied to a tool-specific install directory.

## Installed Paths

Gemini uses the same install paths as Claude Code (`.claude/` for project scope) because it reads Claude-compatible rule files.

| Artifact | Path |
|----------|------|
| Skill dir | `$SKILL_DIR` (linked repo path, not copied) |
| Rules (project scope) | `$TEST_DIR/.gemini/rules/aegis--*` |
| Skills (project scope) | `$TEST_DIR/.gemini/skills/helloworld/` |

## Teardown

| Phase | Step | Command | Assertion |
|-------|------|---------|-----------|
| 6.1 | Uninstall helloworld | `/coding-aegis uninstall helloworld` via agent | no `not installed\|error`; quota fallback removes files manually if needed |
| 7.1 | Uninstall coding-aegis skill | `gemini_quiet skills uninstall coding-aegis --scope workspace` | `gemini skills list` no longer shows `coding-aegis` |
| 7.3 | Remove marketplace | N/A — no separate marketplace | — |
| 7.5 | Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
