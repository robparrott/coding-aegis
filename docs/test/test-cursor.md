# Cursor — Test Detail

> Tool-specific details for the Cursor skill install test. For the full test plan, phase definitions, and pass criteria see [TEST.md](TEST.md).

> **Status**: **10/10 passing** (2026-04-17, `cursor-agent 2026.04.16-2d20146`). Requires macOS quarantine fix after install — see §12.

## Test Script / pytest

- `tests/integration/test_cursor.py` — 7-phase pytest journey (`TestCursorJourney`); skipped automatically when `cursor-agent` is not on PATH.

---

## 1. Headless Invocation

### Confirmed invocation form

```bash
cursor-agent -p --output-format text --force
```

Confirmed from `cursor-agent --help` (live output, 2026-04-03):

| Flag | Meaning |
|------|---------|
| `-p` / `--print` | Print responses to console (headless/non-interactive) |
| `--output-format text` | Plain text output (`text \| json \| stream-json`; default: `"text"`) |
| `-f` / `--force` | Auto-approve writes unless explicitly denied |
| `--yolo` | Alias for `--force` |
| `--model <model>` | Override model |

Prompt is passed as a positional argument OR via stdin (both confirmed). The pytest harness uses stdin (`input=prompt`).

`--trust` is required for headless use in non-interactive temp directories — without it, cursor-agent prints a Workspace Trust prompt and exits. Add it to all headless invocations that don't already use `--force`/`--yolo`.

Version: `2026.03.30-a5d3e17`

| Question | Status |
|----------|--------|
| Is `-p` the correct headless flag? | **Confirmed** |
| Is `--output-format text` supported? | **Confirmed** |
| Is `--force` or `--yolo` the auto-approve flag? | **Confirmed** (both work) |
| Is `--trust` required for temp dirs? | **Confirmed** — must be set for non-interactive use |
| Is the binary `cursor-agent` or `agent`? | **Confirmed** — `cursor-agent` on Homebrew |
| What does `cursor-agent --version` output? | **Confirmed** — `2026.03.30-a5d3e17` |
| Is there a `run` subcommand analogous to `codex exec`? | **Confirmed — no** |
| Does it require `git init` in the working directory? | **Confirmed** — yes, required |
| Does cursor-agent load `.cursor/skills/` from CWD? | **Confirmed** — yes |

---

## 2. Rule / Instruction Files

### Confirmed paths (from ADR-14 and codebase)

| Artifact type | Project scope | User scope |
|---------------|--------------|-----------|
| Always-on rules | `AGENTS.md`, `.cursor/rules/*.mdc` (`alwaysApply: true`) | `~/.cursor/rules/*.mdc` |
| File-scoped rules | `.cursor/rules/*.mdc` (`globs:`) | `~/.cursor/rules/*.mdc` |
| Invocable skills | `.cursor/skills/{name}/SKILL.md` | `~/.cursor/skills/{name}/SKILL.md` |
| MCP config | `.mcp.json` (project) | `~/.cursor/mcp.json` (user) |

Rule files use `.mdc` extension (not `.md`). The `alwaysApply` frontmatter key controls always-on vs. invoked behaviour.

**Fixed (wpi.12)**: `compute_target_filename()` now accepts an optional `tool` parameter and writes `.mdc` for Cursor.

### AGENTS.md

Cursor reads `AGENTS.md`. For Cursor, the preferred delivery mechanism is `.cursor/rules/*.mdc`; `AGENTS.md` is a fallback.

### `.cursorrules`

Legacy Cursor global instructions file (project root). Still read but deprecated in favour of `.cursor/rules/`. coding-aegis does not target this file.

---

## 3. Skills / Custom Commands

### Confirmed: Cursor supports SKILL.md natively

AD-14 (accepted) states:

> **Cursor**: Native support via `.cursor/skills/{name}/SKILL.md` and `.agents/skills/{name}/SKILL.md`

The `.cursor/skills/` path is preferred. Skill invocation uses `/skill-name` slash-command syntax (same as Claude).

### Skill discovery within cursor-agent

Whether `cursor-agent` (headless CLI) picks up skills from `.cursor/skills/` in the CWD the same way the GUI IDE does is unconfirmed.

| Question | Status |
|----------|--------|
| Does headless cursor-agent load `.cursor/skills/` from CWD? | UNVERIFIED |
| Skill invocation syntax: `/skill-name`? | UNVERIFIED — likely `/` |
| Does `cursor-agent` read `.cursor/rules/` from CWD? | UNVERIFIED |

---

## 4. Detection Signals

### Confirmed: `CURSOR_AGENT=1`

From `spec-tool-detection.md` (research complete, April 2026):

> **Cursor**: `CURSOR_AGENT=1` injected by Cursor CLI in agent terminal.
> Note: it regressed once in a Cursor release and was restored; treat as reliable but maintain `__file__` fallback.

`detect_tool.py` implements this at priority 5:

```python
("env:CURSOR_AGENT=1",
 lambda env, fp: env.get("CURSOR_AGENT") == "1",
 "cursor"),
```

### Verify with live CLI

```bash
cursor-agent -p --output-format text \
  'Run bash: python3 -c "import os,json; d={k:v for k,v in os.environ.items() if \"CURSOR\" in k}; print(json.dumps(d, indent=2))"'
```

| Env var | Expected | Status |
|---------|---------|--------|
| `CURSOR_AGENT` | `1` | Confirmed via forum; unverified live |
| Any other `CURSOR_*` | Unknown | UNVERIFIED |

---

## 5. Install Paths

### Confirmed (from ADR-14, AD-5, aegis_lib.py)

| Scope | Rules path | Skills path |
|-------|-----------|------------|
| Project | `{repo}/.cursor/rules/aegis--{pkg}--{rule}.mdc` | `{repo}/.cursor/skills/{name}/SKILL.md` |
| User | `~/.cursor/rules/aegis--{pkg}--{rule}.mdc` | `~/.cursor/skills-cursor/{name}/SKILL.md` |

**Note**: The user-scope skills directory is `~/.cursor/skills-cursor/` (not `skills/`). Confirmed from live `~/.cursor/` directory listing. The `TOOL_PATHS["cursor"]` user scope may need updating.

Rule files use `.mdc` extension for Cursor (not `.md`). Fixed in `coding-aegis-wpi.12`.

### Plugin / marketplace path

`.cursor-plugin/marketplace.json` at repo root is used for IDE-based marketplace install (Option E from AD-13):

```json
{
  "plugins": [
    {
      "name": "coding-aegis",
      "path": "./pkgs/bootstrap/coding-aegis"
    }
  ]
}
```

### Current TOOL_PATHS entry

```python
"cursor": {
    "scope_base": ".cursor",
    "skills_dir": "skills",
    "rule_ext": ".mdc",
}
```

---

## 6. Cursor Plugin Install Mechanism

There is no documented CLI mechanism for installing a Cursor plugin headlessly. The integration test bootstrap copies skill files directly:

```python
shutil.copytree(skill_src, test_dir / ".cursor" / "skills" / "coding-aegis")
```

| Question | Status |
|----------|--------|
| Can `cursor-agent` install a plugin from a local path? | UNVERIFIED |
| Is there a `cursor-agent plugin install` subcommand? | UNVERIFIED |

---

## 7. Phase 2 Marketplace Verification

The pytest Phase 2 test validates the manifest file structure only — no CLI marketplace command is known.

1. Verify `.cursor-plugin/marketplace.json` exists and lists `"coding-aegis"`.
2. Proceed with local skill copy as Phase 3 fallback.

---

## 8. CLI Prompts

Expected to use `/coding-aegis ...` syntax (same as Claude and Gemini).

---

## 9. Open Questions (Ordered by Priority)

| # | Question | Blocks | Investigation method |
|---|----------|--------|---------------------|
| Q1 | What are the exact `cursor-agent --help` flags? | All phases | **Confirmed** — see §1 |
| Q2 | Does `-p` flag work for headless invocation? | Phase 1 auth | **Confirmed** |
| Q3 | What is the auto-approve flag (`--force` or `--yolo`)? | Phase 5 | **Confirmed** (both) |
| Q4 | Does `cursor-agent` set `CURSOR_AGENT=1` in subprocesses? | Phase 4a | Tests pass with env injected; live unverified |
| Q5 | Does cursor-agent load `.cursor/skills/` from CWD? | Phase 3/5 | **Confirmed** — yes |
| Q6 | Is there a `cursor-agent plugin install` subcommand? | Phase 3 | **Confirmed — no** |
| Q7 | User-scope skills dir path? | User scope | **Confirmed** — `~/.cursor/skills-cursor/` (not `skills/`) |
| Q8 | What does `cursor-agent --version` return? | Version tracking | **Confirmed** — `2026.03.30-a5d3e17` |
| Q9 | Are there additional `CURSOR_*` env vars? | Detection | Unverified; tests pass without it |
| Q10 | Is `--trust` required for headless temp dirs? | All phases | **Confirmed** — yes, must add to base invocation |

---

## 10. Teardown

Integration test teardown: best-effort `cursor-agent -p --force "/coding-aegis uninstall helloworld"`. Temp dir cleaned by `tmp_path_factory`.

---

## 11. Relationship to Existing ADRs

| ADR | Relevance |
|-----|-----------|
| AD-4 | Dual marketplace — `.cursor-plugin/marketplace.json` already present |
| AD-5 | Installation targets — confirms `.cursor/rules/` and `.cursor/skills/` |
| AD-13 | Cursor remote distribution — local symlink (Option E) is current workaround |
| AD-14 | Cross-tool artifact matrix — canonical source for path and format decisions |

---

## 12. macOS Quarantine (Gatekeeper)

After installing cursor-cli via Homebrew on Apple Silicon, macOS may block the bundled native binaries (`merkle-tree-napi.darwin-arm64.node`, `pty.node`, `rg`, etc.) with a "Not Opened" Gatekeeper dialog.

**Symptom**: Gatekeeper dialog appears for `merkle-tree-napi.darwin-arm64.node` or `rg` on first use; `cursor-agent` may crash or produce garbled output.

**Fix**: Strip the quarantine extended attribute from the entire Caskroom package after install:

```bash
xattr -rd com.apple.quarantine $(brew --prefix)/Caskroom/cursor-cli/<version>/
# Example:
xattr -rd com.apple.quarantine /opt/homebrew/Caskroom/cursor-cli/2026.04.16-2d20146/
```

If Gatekeeper prompts appear, click **Done** (not "Move to Trash"), then run the command above. Running `xattr -rd` on the whole directory clears all quarantine flags at once and prevents further dialogs.

This is a one-time step after each `brew install` or `brew upgrade` of `cursor-cli`.

---

## 13. Investigation Commands (for the person with cursor-agent installed)

```bash
# 1. Version
cursor-agent --version

# 2. List cursor config directory
ls -la ~/.cursor/

# 3. Env var detection inside agent subprocess
cursor-agent -p --output-format text \
  'Run bash: python3 -c "import os,json; d={k:v for k,v in os.environ.items() if \"CURSOR\" in k}; print(json.dumps(d, indent=2))"'

# 4. Skill loading check
mkdir -p /tmp/cursor-test/.cursor/skills/helloworld
cat > /tmp/cursor-test/.cursor/skills/helloworld/SKILL.md <<'EOF'
---
name: helloworld
description: Returns Hello World
---
Reply with exactly: Hello, World
EOF
cd /tmp/cursor-test
cursor-agent -p --output-format text "/helloworld"

# 5. Check plugin / skills subcommands
cursor-agent plugin --help 2>/dev/null || echo "no plugin subcommand"
cursor-agent skills --help 2>/dev/null || echo "no skills subcommand"
```

---

*Last updated: 2026-04-17.*
