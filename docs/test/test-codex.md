# Codex — Test Detail

> Tool-specific details for the Codex skill install test. For the full test plan, phase definitions, and pass criteria see [TEST.md](TEST.md).

## Two-Phase Testing Requirement

The Codex `$skill-installer` only supports GitHub sources — it cannot install from local filesystem paths. This means `tests/integration/test_codex.py` cannot validate uncommitted local changes directly:

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

### Phase 2 — Marketplace / Registry Setup

The test validates `.codex-plugin/plugin.json` from the local repo root (not the test dir), confirming the manifest is present and correctly formed.

Assert: `$REPO_ROOT/.codex-plugin/plugin.json` exists and contains `"name": "coding-aegis"` and `"skills"`.

### Phase 3 — Install coding-aegis Skill

Agent-mediated via `$skill-installer` with `danger-full-access` sandbox (needs GitHub network access):

```
$skill-installer install --repo robparrott/coding-aegis --path pkgs/bootstrap/coding-aegis/skills/coding-aegis
```

Assert: output contains `install\|success\|done\|copied\|coding-aegis`; `SKILL.md`, `aegis_lib.py`, `aegis-install.py`, `aegis-uninstall.py`, and `detect_tool.py` present in `~/.codex/skills/coding-aegis/`.

After Phase 3, copy the `pkgs/` catalog into `$TEST_DIR`:

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
| `read-only` | Phases 4.1–4.4, 5.5 |
| `workspace-write` | Phase 5.1 (install helloworld) |
| `danger-full-access` | Phase 3 ($skill-installer needs GitHub network access); Phase 6.1 (uninstall — needed so aegis-uninstall.py can run shutil.rmtree on the skill directory; workspace-write blocks that syscall) |

- `--ephemeral` — no session persistence
- `-o /dev/stdout` — captures output (required; default output goes elsewhere)

## Prompts (phases 4–6)

| Phase | Step | Prompt |
|-------|------|--------|
| 4.1 | tool detection (direct bash) | `python3 ~/.codex/skills/coding-aegis/detect_tool.py` |
| 4.2 | detect-tool skill command | `$coding-aegis detect-tool` |
| 4.3 | list | `$coding-aegis list --catalog pkgs` |
| 4.4 | show | `$coding-aegis show helloworld --catalog pkgs` |
| 5.1 | install helloworld | `$coding-aegis install helloworld to Project scope --catalog $TEST_DIR/pkgs` |
| 5.5 | invoke helloworld | `$helloworld` |
| 6.1 | uninstall helloworld | `$coding-aegis uninstall helloworld` |

Pass `--catalog` in phases 4.3, 4.4, and 5.1 to prevent the agent from scanning the workspace and loading the wrong SKILL.md from the `pkgs/` tree instead of dispatching to the installed skill.

## Tool Detection (Phase 3.3 / 4.1)

- **Method**: direct bash — `python3 ~/.codex/skills/coding-aegis/detect_tool.py`
- **Expected `tool`**: `codex`
- **Expected signal**: `path:.codex` (install path contains `.codex`)

## Phase 5 — Validate install

After the agent completes Phase 5.1, the test runs `aegis-validate.py` directly:

```bash
python3 ~/.codex/skills/coding-aegis/aegis-validate.py \
  helloworld --catalog $REPO_ROOT/pkgs --tool codex
```

Assert: exit code 0.

## Installed Paths

| Artifact | Path |
|----------|------|
| Skill dir | `~/.codex/skills/coding-aegis/` |
| Rules (project scope) | `$TEST_DIR/AGENTS.md` (`aegis:begin/end` sections) |
| Skills (project scope) | `$TEST_DIR/.agents/skills/helloworld/` |

## Teardown

| Phase | Step | Command | Assertion |
|-------|------|---------|-----------|
| 6.1 | Uninstall helloworld | `$coding-aegis uninstall helloworld` via agent (danger-full-access) | no `not installed\|error` in output; `$TEST_DIR/.agents/skills/helloworld` absent |
| 7.1 | Uninstall coding-aegis skill | `rm -rf ~/.codex/skills/coding-aegis` | `assert_dir_not_exists ~/.codex/skills/coding-aegis` |
| 7.3 | Remove marketplace | `rm -rf "$TEST_DIR/.codex-plugin"` | `assert_dir_not_exists $TEST_DIR/.codex-plugin` |
| 7.5 | Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
