# Claude Code — Test Detail

> Tool-specific details for the Claude Code skill install test. For the full test plan, phase definitions, and pass criteria see [TEST.md](TEST.md).

## Install Mechanisms

### Phase 2 — Marketplace / Registry Setup

```bash
claude plugin marketplace add "$REPO_ROOT"
```

Assert: output contains `added\|success`; name appears in `claude plugin marketplace list`.

### Phase 3 — Install coding-aegis Skill

```bash
claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope project
```

Assert: output contains `install`; `claude plugin list` shows `coding-aegis`.

After Phase 3, symlink or copy the `pkgs/` catalog into `$TEST_DIR`:

```bash
ln -s "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs" 2>/dev/null || cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
```

## CLI Invocation Flags

**Agent-mediated calls** (phases 4–6):

```bash
claude -p --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
```

**Phase 5.1 install step** (needs Write + AskUserQuestion; `--dangerously-skip-permissions` required because `.claude/` is a protected path that even `--permission-mode bypassPermissions` will not override):

```bash
claude -p --allowedTools "Bash,Read,Write,Glob,Skill,AskUserQuestion" \
  --dangerously-skip-permissions $CLAUDE_COMMON
```

**Common flags** (defined as `CLAUDE_COMMON` in the test script):

```bash
--strict-mcp-config --mcp-config '{"mcpServers":{}}'
```

Disables MCP servers to prevent startup hangs in headless mode.

**Non-agent management commands** do not use `CLI_PROMPT`:

```bash
run_cli "marketplace add"    claude plugin marketplace add "$REPO_ROOT"
run_cli "plugin install"     claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope project
run_cli "plugin uninstall"   claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope project
run_cli "marketplace remove" claude plugin marketplace remove "$MARKETPLACE_NAME"
run_cli "marketplace list"   claude plugin marketplace list
```

## Prompts (phases 4–6)

| Phase | Step | Prompt |
|-------|------|--------|
| 4.1 | tool detection (direct bash) | `python3 $TEST_DIR/.claude/skills/coding-aegis/detect_tool.py` |
| 4.2 | detect-tool skill command | `/coding-aegis detect-tool` |
| 4.3 | list | `/coding-aegis list` |
| 4.4 | show | `/coding-aegis show helloworld` |
| 5.1 | install helloworld | `/coding-aegis install helloworld to Project scope` |
| 5.5 | invoke helloworld | `/helloworld` |
| 6.1 | uninstall helloworld | `/coding-aegis uninstall helloworld` |

## Tool Detection (Phase 4.2)

Claude's plugin system loads skill files from the marketplace source dynamically — it does not copy them into the project directory. Phases 3.3 and 4.1 (detect_tool.py present, direct-bash detection) are therefore not applicable for Claude and are validated via Codex instead.

- **Method**: skill command — `/coding-aegis detect-tool` (agent-mediated)
- **Expected `tool`**: `claude`
- **Expected signal**: `env:CLAUDECODE=1`

## Installed Paths

| Artifact | Path |
|----------|------|
| Skill dir | `$TEST_DIR/.claude/skills/coding-aegis/` (project scope) |
| Rules (project scope) | `$TEST_DIR/.claude/rules/aegis--*` |
| Skills (project scope) | `$TEST_DIR/.claude/skills/helloworld/` |

## Teardown

| Phase | Step | Command | Assertion |
|-------|------|---------|-----------|
| 6.1 | Uninstall helloworld | `/coding-aegis uninstall helloworld` via agent | no `not installed\|error` in output |
| 7.1 | Uninstall plugin | `claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope project` | — |
| 7.3 | Remove marketplace | `claude plugin marketplace remove "$MARKETPLACE_NAME"` | `claude plugin marketplace list` no longer shows the entry |
| 7.5 | Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
