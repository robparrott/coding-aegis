# Cursor — Test Detail

> Tool-specific details for the Cursor skill install test. For the full test plan, phase definitions, and pass criteria see [testing-spec.md](testing-spec.md).

> **Status**: Research largely complete — live CLI investigation (Q1–Q9) still required before the full integration test can be validated end-to-end. See [Open Questions](#9-open-questions-ordered-by-priority) below.

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

Prompt is passed as a positional argument after all flags.

### Still to verify

| Question | Status |
|----------|--------|
| Is `-p` the correct headless flag? | **Confirmed** (from `--help`) |
| Is `--output-format text` supported? | **Confirmed** |
| Is `--force` or `--yolo` the auto-approve flag? | **Confirmed** (both work) |
| Is the binary `cursor-agent` or `agent`? | **Confirmed** — `cursor-agent` on Homebrew |
| What does `cursor-agent --version` output? | UNVERIFIED |
| Is there a `run` subcommand analogous to `codex exec`? | **Confirmed — no** `run` subcommand exists |
| Does it require `git init` in the working directory? | UNVERIFIED |

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

**Known bug**: `compute_target_filename()` in `aegis_lib.py` currently writes `.md` for all tools. Cursor needs `.mdc`. Tracked in `coding-aegis-wpi.12`.

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
| User | `~/.cursor/rules/aegis--{pkg}--{rule}.mdc` | `~/.cursor/skills/{name}/SKILL.md` |

Rule files use `.mdc` extension for Cursor (not `.md`). See `coding-aegis-wpi.12` for the fix.

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

### Proposed TOOL_PATHS entry (pending wpi.12)

```python
"cursor": {
    "scope_base": ".cursor",
    "skills_dir": "skills",
    "rule_ext": ".mdc",   # NEW: rule file extension override (wpi.12)
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
| Q1 | What are the exact `cursor-agent --help` flags? | All phases | **Done** — see §1 above |
| Q2 | Does `-p` flag work for headless invocation? | Phase 1 auth, all agent phases | **Confirmed** |
| Q3 | What is the auto-approve flag (`--force` or `--yolo`)? | Phase 5 | **Confirmed** (both) |
| Q4 | Does `cursor-agent` set `CURSOR_AGENT=1` in subprocesses? | Phase 4a | UNVERIFIED live |
| Q5 | Does cursor-agent load `.cursor/skills/` from CWD? | Phase 3/5 | UNVERIFIED |
| Q6 | Is there a `cursor-agent plugin install` subcommand? | Phase 3 install | **Confirmed — no** |
| Q7 | Does `~/.cursor/skills/` exist and work for user-scope install? | User scope | UNVERIFIED |
| Q8 | What does `cursor-agent --version` return? | Version tracking | UNVERIFIED |
| Q9 | Are there additional `CURSOR_*` env vars beyond `CURSOR_AGENT`? | Detection completeness | UNVERIFIED |

See `coding-aegis-wpi.11` for the CLI investigation task.

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

## 12. Investigation Commands (for the person with cursor-agent installed)

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

*Last updated: 2026-04-03.*
