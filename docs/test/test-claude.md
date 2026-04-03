# Claude Code — Test Detail

> Tool-specific details for the Claude Code skill install test. For the full test plan, phase definitions, and pass criteria see [testing-spec.md](testing-spec.md).

## Install Mechanisms

### T1 — Register Marketplace

```bash
claude plugin marketplace add "$REPO_ROOT"
```

Assert: output contains `added\|success`; name appears in `claude plugin marketplace list`.

### T2 — Install Skill

```bash
claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope project
```

Assert: output contains `install`; `claude plugin list` shows `coding-aegis`.

After T2, symlink or copy the `pkgs/` catalog into `$TEST_DIR`:

```bash
ln -s "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs" 2>/dev/null || cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
```

## CLI Invocation Flags

**Agent-mediated calls** (T2b–T7.1):

```bash
claude -p --allowedTools "Bash,Read,Glob,Skill" $CLAUDE_COMMON
```

**Install step** (needs Write + AskUserQuestion; `--dangerously-skip-permissions` required because `.claude/` is a protected path that even `--permission-mode bypassPermissions` will not override):

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
run_cli "marketplace add"  claude plugin marketplace add "$REPO_ROOT"
run_cli "plugin install"   claude plugin install "coding-aegis@${MARKETPLACE_NAME}" --scope project
run_cli "plugin uninstall" claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope project
run_cli "marketplace remove" claude plugin marketplace remove "$MARKETPLACE_NAME"
run_cli "marketplace list"   claude plugin marketplace list
```

## Prompts (T2b–T7.1)

| Step | Prompt |
|------|--------|
| T2b detect-tool (direct bash) | `python3 ~/.claude/skills/coding-aegis/detect_tool.py` |
| T2c detect-tool (skill) | `/coding-aegis detect-tool` |
| T3 list | `/coding-aegis list` |
| T4 show | `/coding-aegis show helloworld` |
| T5 install | `/coding-aegis install helloworld to Project scope` |
| T6b invoke | `/helloworld` |
| T7.1 uninstall | `/coding-aegis uninstall helloworld` |

## Tool Detection (T2b)

- **Method**: direct bash — `python3 ~/.claude/skills/coding-aegis/detect_tool.py`
- **Expected `tool`**: `claude`
- **Expected signal**: `path:.claude` (install path contains `.claude`)

## Installed Paths

| Artifact | Path |
|----------|------|
| Skill dir | `~/.claude/skills/coding-aegis/` |
| Rules (project scope) | `$TEST_DIR/.claude/rules/aegis--*` |
| Skills (project scope) | `$TEST_DIR/.claude/skills/helloworld/` |

## Teardown

| Step | Command | Assertion |
|------|---------|-----------|
| T7.1 Uninstall helloworld | `/coding-aegis uninstall helloworld` via agent | no `not installed\|error` in output |
| T7.2 Uninstall plugin | `claude plugin uninstall "coding-aegis@${MARKETPLACE_NAME}" --scope project` | — |
| T7.3 Remove marketplace | `claude plugin marketplace remove "$MARKETPLACE_NAME"` | `claude plugin marketplace list` no longer shows the entry |
| T7.4 Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
