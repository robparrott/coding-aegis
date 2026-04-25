# Gemini — Test Detail

> **STATUS (2026-04-22)**: Bootstrap switched to `gemini skills install` from GitHub. **10/10 passing** on free tier when quota is available. Agent-mediated phases (4b–6) produce UX budget warnings (50–100s) under quota pressure but complete. Steps that timeout at 120s indicate quota exhaustion — rerun when quota recovers.

> Tool-specific details for the Gemini skill install test. For the full test plan, phase definitions, and pass criteria see [TEST.md](TEST.md).

> **NOTE**: `gemini skills install` fetches from GitHub, so changes must be pushed to the remote before running these tests — same requirement as Codex.

## Install Mechanisms

### Phase 2 — Bootstrap Mechanism

Gemini has no plugin marketplace. The bootstrap mechanism is `gemini skills install` from a GitHub URL — the skill is installed from the remote repo into `.gemini/skills/coding-aegis/` at workspace scope. Phase 2 validates that `SKILL.md` exists at the skill source path (in the repo) and contains the required frontmatter (`name`, `description`) that `gemini skills install` reads.

```bash
python3 -c "
from pathlib import Path
skill_md = Path('$REPO_ROOT/modules/bootstrap/coding-aegis/skills/coding-aegis') / 'SKILL.md'
assert skill_md.exists()
content = skill_md.read_text()
assert 'name: coding-aegis' in content
assert 'description:' in content
print('PASS')
"
```

### Phase 3 — Install coding-aegis Skill

```bash
gemini skills install https://github.com/robparrott/coding-aegis \
  --path modules/bootstrap/coding-aegis/skills/coding-aegis \
  --scope workspace --consent
```

Assert: `gemini skills list` shows `coding-aegis`; skill files present at `$TEST_DIR/.gemini/skills/coding-aegis/`.

Also requires `git init` in `$TEST_DIR` (Gemini requires a git repo in the working directory).

**No local clone needed** — `gemini skills install` fetches directly from GitHub. The skill calls `ensure_catalog()` which also fetches the catalog from GitHub on first use and caches it in `.coding-aegis-catalog/`.

## CLI Invocation Flags

**Agent-mediated calls** (phases 4–6):

```bash
gemini -m gemini-3-flash-preview -o text --yolo
```

| Flag | Meaning |
|------|---------|
| `-m gemini-3-flash-preview` | Model override (use a fast model for tests) |
| `-o text` | Plain text output (no JSON event stream) |
| `--yolo` | Auto-approve tool use; without this Gemini prompts for approval which hangs in headless mode |

Prompt is passed via stdin by the harness (`run_cli(..., prompt=...)`).

Keytar warnings from Homebrew (`Keychain initialization`, `keytar.node`) appear on stderr. The pytest harness captures stdout and stderr separately — warnings do not pollute assertions.

**Non-agent management commands** do not go through the model:

```bash
gemini skills install https://github.com/robparrott/coding-aegis \
  --path modules/bootstrap/coding-aegis/skills/coding-aegis \
  --scope workspace --consent
gemini skills list
gemini skills uninstall coding-aegis --scope workspace
```

## Quota Handling

All agent-mediated steps must call `assert_no_quota_error "$LAST_OUTPUT" "Gemini"` immediately after `run_cli`. If a quota error is detected, the harness fails and aborts — do not attempt to continue.

Phase 6.1 (uninstall helloworld) includes a quota fallback: if the agent call returns a quota error, fall back to manual file removal so teardown can complete cleanly.

## Prompts (phases 4–6)

| Phase | Step | Prompt / command |
|-------|------|-----------------|
| 4a | detect_tool direct (bash) | `python3 $SKILL_DIR/detect_tool.py` — validates JSON structure only (GEMINI_CLI=1 not set in test process) |
| 4.2 | detect-tool skill command | `/coding-aegis detect-tool` |
| 4.3 | list | `/coding-aegis list` |
| 4.4 | show | `/coding-aegis show helloworld` |
| 5.1 | install helloworld | `/coding-aegis install helloworld to Project scope` |
| 5.5 | invoke helloworld | `/helloworld` |
| 6.1 | uninstall helloworld | `/coding-aegis uninstall helloworld` |

After Phase 5.1, the test also runs `aegis-validate.py` directly to confirm artifacts:

```bash
python3 $REPO_ROOT/modules/bootstrap/coding-aegis/skills/coding-aegis/aegis-validate.py \
  helloworld --catalog $REPO_ROOT/modules --tool gemini
```

Assert: exit code 0.

## Tool Detection (Phase 4.2)

Gemini installs skills with no tool-specific directory segment other than `.gemini`. The `path:.claude` / `path:.codex` signals do not fire. Detection requires an agent-mediated invocation so the `GEMINI_CLI=1` env var is present.

- **Method**: agent-mediated — `/coding-aegis detect-tool` (or direct bash with env var set)
- **Expected `tool`**: `gemini`
- **Expected signal**: `env:GEMINI_CLI=1`

Note: Phase 4a (`detect_tool.py` direct run) uses the installed copy at `$TEST_DIR/.gemini/skills/coding-aegis/detect_tool.py`. Only JSON structural validity is asserted — `GEMINI_CLI=1` is only set when the Gemini agent invokes the script.

## Installed Paths

| Artifact | Path |
|----------|------|
| Skill dir (coding-aegis) | `$TEST_DIR/.gemini/skills/coding-aegis/` (installed copy) |
| Rules (project scope) | `$TEST_DIR/.gemini/rules/aegis--*` |
| Skills (project scope) | `$TEST_DIR/.gemini/skills/helloworld/` |

## Teardown

| Phase | Step | Command | Assertion |
|-------|------|---------|-----------|
| 6.1 | Uninstall helloworld | `/coding-aegis uninstall helloworld` via agent | no `not installed\|error`; quota fallback removes files manually if needed |
| 7.1 | Uninstall coding-aegis skill | `gemini skills uninstall coding-aegis --scope workspace` | `gemini skills list` no longer shows `coding-aegis`; `.gemini/skills/coding-aegis/` removed |
| 7.3 | Remove marketplace | N/A — no separate marketplace | — |
| 7.5 | Remove test dir | `rm -rf "$TEST_DIR"` | `assert_dir_not_exists "$TEST_DIR"` |
