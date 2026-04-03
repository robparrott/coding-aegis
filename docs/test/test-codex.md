# Codex — Test Detail

> Tool-specific details for the Codex skill install test. For the full test plan, phase definitions, and pass criteria see [testing-spec.md](testing-spec.md).

## Two-Phase Testing Requirement

The Codex `$skill-installer` only supports GitHub sources — it cannot install from local filesystem paths. This means `test-codex-skill-install.sh` cannot validate uncommitted local changes directly:

1. **Push to GitHub** — commit and push all skill changes to the remote repository.
2. **Run the Codex test** — the test installs from GitHub, reflecting the pushed changes.

Do not run the Codex test against a local working copy. If changes have not been pushed, note that the Codex test is blocked and get user agreement before closing the task.

## Environment Setup

Claude Code sets `CLAUDECODE=1` in the parent process; Codex passes env vars through to sandbox subprocesses. This causes `detect_tool.py` to return `claude` instead of `codex`. The test script must unset these before sourcing the harness:

```bash
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true
```

Workspace-write sandbox steps are slower than read-only. The Codex test overrides `AEGIS_TEST_TIMEOUT_LONG` before sourcing the harness:

```bash
export AEGIS_TEST_TIMEOUT_LONG=60
```

## Install Mechanisms

### T1 — Register Marketplace

Codex discovers plugin manifests from `.codex-plugin/plugin.json` relative to the working directory. The test must fetch this from the remote GitHub repo (not the local working copy) into `$TEST_DIR/.codex-plugin/` so the user journey — starting from a fresh directory — is faithfully exercised.

Assert: `$TEST_DIR/.codex-plugin/plugin.json` exists and contains `"name": "coding-aegis"` and `"skills"`.

Tracked in coding-aegis-gua (fetch manifest from remote in test setup).

### T2 — Install Skill

Agent-mediated via `$skill-installer` with `danger-full-access` sandbox (needs GitHub network access):

```
$skill-installer install --repo robparrott/coding-aegis --path pkgs/bootstrap/coding-aegis/skills/coding-aegis
```

Assert: output contains `install\|success\|done\|copied\|coding-aegis`; SKILL.md and aegis-catalog.py present in `~/.codex/skills/coding-aegis/`.

After T2, copy the `pkgs/` catalog into `$TEST_DIR`:

```bash
cp -R "$REPO_ROOT/pkgs" "$TEST_DIR/pkgs"
```

Note: this local copy is a temporary workaround. Tracked in coding-aegis-6pp to replace with remote-based catalog sourcing.

## CLI Invocation Flags

All agent calls use `codex exec`. Requires `git init` in the working directory.

```bash
codex exec --ephemeral -s <sandbox> -o /dev/stdout
```

| Sandbox | When to use |
|---------|-------------|
| `read-only` | T2b, T2c, T3, T4, T6b |
| `workspace-write` | T5 (install helloworld), T7.1 (uninstall helloworld) |
| `danger-full-access` | T2 ($skill-installer needs GitHub network access) |

- `--ephemeral` — no session persistence
- `-o /dev/stdout` — captures output (required; default output goes elsewhere)

## Prompts (T2b–T7.1)

| Step | Prompt |
|------|--------|
| T2b detect-tool (direct bash) | `python3 ~/.codex/skills/coding-aegis/detect_tool.py` |
| T2c detect-tool (skill) | `$coding-aegis detect-tool` |
| T3 list | `$coding-aegis list` |
| T4 show | `$coding-aegis show helloworld` |
| T5 install | `$coding-aegis install helloworld to Project scope --catalog $TEST_DIR/pkgs` |
| T6b invoke | `$helloworld` |
| T7.1 uninstall | `$coding-aegis uninstall helloworld --catalog $TEST_DIR/pkgs` |

Pass `--catalog $TEST_DIR/pkgs` in T5 and T7.1 to prevent the agent from scanning the workspace and loading the wrong SKILL.md from the `pkgs/` tree instead of dispatching to the installed skill.

## Tool Detection (T2b)

- **Method**: direct bash — `python3 ~/.codex/skills/coding-aegis/detect_tool.py`
- **Expected `tool`**: `codex`
- **Expected signal**: `path:.codex` (install path contains `.codex`)

## Installed Paths

| Artifact | Path |
|----------|------|
| Skill dir | `~/.codex/skills/coding-aegis/` |
| Rules (project scope) | `$TEST_DIR/.agents/rules/aegis--*` |
| Skills (project scope) | `$TEST_DIR/.agents/skills/helloworld/` |

## Teardown

| Step | Command | Assertion |
|------|---------|-----------|
| T7.1 Uninstall helloworld | `$coding-aegis uninstall helloworld --catalog $TEST_DIR/pkgs` via agent (workspace-write) | no `not installed\|error` in output; `$TEST_DIR/.agents/skills/helloworld` absent |
| T7.2 Uninstall coding-aegis skill | `rm -rf ~/.codex/skills/coding-aegis` | `assert_dir_not_exists ~/.codex/skills/coding-aegis` |
| T7.3 Remove marketplace | `rm -rf "$TEST_DIR/.codex-plugin"` | `assert_dir_not_exists $TEST_DIR/.codex-plugin` |
| T7.4 Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
