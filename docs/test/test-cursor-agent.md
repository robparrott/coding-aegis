# Cursor Agent CLI — Research Spec

**Status**: Research incomplete — live CLI investigation required before implementation.

This document records what is known, what is assumed, and what must be verified via
hands-on `cursor-agent` invocation before writing implementation code. It supersedes
the placeholder in [test-cursor.md](test-cursor.md) and feeds directly into
`tests/test-cursor-skill-install.sh` (task `coding-aegis-wpi.10`) and the Cursor
`TOOL_PATHS` entry in `aegis_lib.py` (task `coding-aegis-wpi.8`).

---

## 1. Headless Invocation

### What the codebase records

The existing `tests/test-cursor-skill-install.sh` was authored with this invocation pattern:

```bash
cursor-agent -p --output-format text --force
```

This mirrors the `claude -p` pattern (headless / print mode). The comment block at the
top of that file notes:

- Binary name: `cursor-agent` (Homebrew install) or `agent` (vendor curl install).
- `-p` — headless/print mode.
- `--output-format text` — plain text output.
- `--force` or `--yolo` — auto-approve file modifications (exact flag unconfirmed).

### What must be verified

Run the following and record the exact output:

```bash
cursor-agent --help
cursor-agent --version
cursor-agent run --help 2>/dev/null || echo "no run subcommand"
```

Confirm:

| Question | Expected | Status |
|----------|----------|--------|
| Is `-p` the correct headless flag? | Yes, same as Claude | UNVERIFIED |
| Is `--output-format text` supported? | Yes | UNVERIFIED |
| Is `--force` or `--yolo` the auto-approve flag? | One of these | UNVERIFIED |
| Is the binary `cursor-agent` or `agent`? | `cursor-agent` on Homebrew | UNVERIFIED |
| What does `cursor-agent --version` output? | e.g. `cursor-agent 1.x.y` | UNVERIFIED |
| Is there a `run` subcommand analogous to `codex exec`? | Unknown | UNVERIFIED |
| Does it require `git init` in the working directory? | Likely yes | UNVERIFIED |

### Proposed invocation form (tentative)

```bash
cursor-agent -p --output-format text --force
```

Prompt is passed as the next positional argument or via stdin. Clarify which.

---

## 2. Rule / Instruction Files

### Confirmed paths (from ADR-14 and codebase)

AD-14 establishes the canonical paths. These are based on documented Cursor behavior
and are treated as confirmed for implementation purposes:

| Artifact type | Project scope | User scope |
|---------------|--------------|-----------|
| Always-on rules | `AGENTS.md`, `.cursor/rules/*.mdc` (`alwaysApply: true`) | `~/.cursor/rules/*.mdc` |
| File-scoped rules | `.cursor/rules/*.mdc` (`globs:`) | `~/.cursor/rules/*.mdc` |
| Invocable skills | `.cursor/skills/{name}/SKILL.md` | `~/.cursor/skills/{name}/SKILL.md` |
| MCP config | `.mcp.json` (project) | `~/.cursor/mcp.json` (user) |

Rule files use `.mdc` extension (not `.md`). The `alwaysApply` frontmatter key
controls always-on vs. invoked behaviour.

### AGENTS.md

Cursor reads `AGENTS.md` (confirmed via codebase comment in AD-14 and the cross-tool
matrix). It is listed first in the "Always-on guidance" row for Cursor. coding-aegis
uses `AGENTS.md` sections (aegis:begin/end markers) for rule delivery on tools that
lack a native rules directory (e.g. Codex). For Cursor, the preferred delivery
mechanism is `.cursor/rules/*.mdc`.

### `.cursorrules`

`.cursorrules` is the legacy Cursor global instructions file (project root). Cursor
still reads it but it is deprecated in favour of `.cursor/rules/`. coding-aegis does
not target this file.

### `.cursor/instructions.md`

Not a standard Cursor path. Cursor does not read `.cursor/instructions.md` natively.
This is not a target for coding-aegis.

### User-scope configuration

```
~/.cursor/
  mcp.json          — user-scoped MCP server config
  rules/            — user-scoped rule files (assumed, verify)
  skills/           — user-scoped skills (assumed, verify)
```

Verify the exact contents of `~/.cursor/` on the test machine:

```bash
ls ~/.cursor/
```

---

## 3. Skills / Custom Commands

### Confirmed: Cursor supports SKILL.md natively

AD-14 (accepted) states:

> **Cursor**: Native support via `.cursor/skills/{name}/SKILL.md` and
> `.agents/skills/{name}/SKILL.md`

The `.cursor/skills/` path is preferred for Cursor. The `.agents/skills/` path is
the Windsurf / open-standard path; Cursor also reads it but it is not the primary
install target.

Skill invocation uses `/skill-name` slash-command syntax (same as Claude).

### Skill discovery within cursor-agent

Whether `cursor-agent` (the headless CLI) picks up skills from `.cursor/skills/` in
the working directory the same way the GUI IDE does is unconfirmed. Verify:

```bash
# Create test skill
mkdir -p /tmp/cursor-test/.cursor/skills/helloworld
cat > /tmp/cursor-test/.cursor/skills/helloworld/SKILL.md <<'EOF'
---
name: helloworld
description: Test skill
---
Reply with exactly: Hello, World
EOF

# Invoke via CLI
cd /tmp/cursor-test && cursor-agent -p --output-format text "/helloworld"
```

| Question | Status |
|----------|--------|
| Does headless cursor-agent load `.cursor/skills/` from CWD? | UNVERIFIED |
| Skill invocation syntax: `/skill-name` or `$skill-name`? | UNVERIFIED — likely `/` |
| Does `cursor-agent` read `.cursor/rules/` from CWD? | UNVERIFIED |

---

## 4. Detection Signals

### Confirmed: `CURSOR_AGENT=1`

From `spec-tool-detection.md` (research complete, April 2026):

> **Cursor**: `CURSOR_AGENT=1` injected by Cursor CLI in agent terminal.
> Confidence: Confirmed (community + bug report).
> Note: it regressed once in a Cursor release and was restored; treat as reliable
> but maintain `__file__` fallback.

Source: [Cursor forum bug report](https://forum.cursor.com/t/cursor-cli-is-not-setting-cursor-agent-1-environment-variable-while-executing-bash-commands/132427)

`detect_tool.py` already implements this signal at priority 5 (after Claude, Gemini,
and Codex env signals):

```python
("env:CURSOR_AGENT=1",
 lambda env, fp: env.get("CURSOR_AGENT") == "1",
 "cursor"),
```

### Verify with live CLI

Run a prompt that prints env vars inside cursor-agent to confirm the signal fires:

```bash
cursor-agent -p --output-format text \
  "Run: python3 -c \"import os,json; print(json.dumps({k:v for k,v in os.environ.items() if 'CURSOR' in k or 'cursor' in k.lower()}))\""
```

Also check for any additional `CURSOR_*` vars that could serve as secondary signals.

| Env var | Expected value | Status |
|---------|---------------|--------|
| `CURSOR_AGENT` | `1` | Confirmed via forum, unverified live |
| Any other `CURSOR_*` | Unknown | UNVERIFIED |

---

## 5. Install Paths

### Confirmed (from ADR-14, AD-5, and aegis_lib.py)

| Scope | Rules path | Skills path |
|-------|-----------|------------|
| Project | `{repo}/.cursor/rules/aegis--{pkg}--{rule}.mdc` | `{repo}/.cursor/skills/{name}/SKILL.md` |
| User | `~/.cursor/rules/aegis--{pkg}--{rule}.mdc` | `~/.cursor/skills/{name}/SKILL.md` |

Rule files use `.mdc` extension for Cursor (not `.md`). This is a difference from
Claude Code and must be reflected in the install logic.

### Plugin / marketplace path

The `.cursor-plugin/marketplace.json` manifest at repo root is already present and
used for IDE-based marketplace install (local symlink, Option E from AD-13).

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

### Skill install path: which takes precedence?

Cursor supports both `.cursor/skills/` and `.agents/skills/`. AD-14 calls
`.cursor/skills/` the native path. coding-aegis should install to `.cursor/skills/`
for project scope (not `.agents/skills/`, which is the Windsurf / Codex path).

### User-scope path

The current `TOOL_PATHS["cursor"]` in `aegis_lib.py` does not set `user_scope_base`,
meaning user scope resolves to `~/.cursor` (same as `scope_base`). This is consistent
with AD-14 and is likely correct; verify by checking whether `~/.cursor/skills/` is
a valid user-scope install location.

---

## 6. Proposed TOOL_PATHS Entry

### Current entry in aegis_lib.py (line 43)

```python
"cursor":    {"scope_base": ".cursor",   "skills_dir": "skills"},
```

This entry looks correct based on current research. It would install skills to
`.cursor/skills/{name}/` for project scope and `~/.cursor/skills/{name}/` for user
scope.

### Proposed entry (no change required unless CLI investigation reveals otherwise)

```python
"cursor": {
    "scope_base": ".cursor",
    "skills_dir": "skills",
    # user_scope_base not set — resolves to ~/.cursor (same as scope_base)
}
```

### Rule file extension

The current install logic writes rule files as `.md`. For Cursor the correct
extension is `.mdc`. This is a bug (or a gap) in `aegis_lib.py` and/or
`aegis-install.py` — the file extension must be determined per-tool at install time.
This is tracked in AD-14 ("Known bugs and limitations").

The `compute_target_filename` function in `aegis_lib.py` currently produces:

```
aegis--{pkg}--{rule}.md
```

For Cursor it should produce:

```
aegis--{pkg}--{rule}.mdc
```

This requires a tool-aware extension mapping — not part of `TOOL_PATHS` today.
Propose adding:

```python
"cursor": {
    "scope_base": ".cursor",
    "skills_dir": "skills",
    "rule_ext": ".mdc",   # NEW: rule file extension override
}
```

Other tools (`claude`, `gemini`, `windsurf`, `copilot`) use `.md` by default and
would not need this key.

---

## 7. Cursor Plugin Install Mechanism (Phase 2 / 3)

### Current state

There is no documented CLI mechanism for installing a Cursor plugin from a local
path or from GitHub without the IDE. AD-13 records the current workaround as
Option E (local symlink into `~/.cursor/plugins/`).

### What needs to be determined for the test

| Question | Status |
|----------|--------|
| Can `cursor-agent` install a plugin from a local path? | UNVERIFIED |
| Is there a `cursor-agent plugin install` subcommand? | UNVERIFIED |
| Is the skill install mechanism via `.cursor/skills/` copy + `cursor-agent`? | UNVERIFIED |
| Does cursor-agent need the skill already present at `.cursor/skills/` to invoke it? | UNVERIFIED |

For integration test Phase 3 (install coding-aegis skill), the fallback is to copy
skill files directly into `.cursor/skills/coding-aegis/` in the test directory,
analogous to how Gemini uses `gemini skills link`. This is the "local file copy"
mechanism (4th preference in testing-spec.md).

---

## 8. Phase 2 Marketplace Verification

The `.cursor-plugin/marketplace.json` file exists at repo root. For IDE-based
workflows this enables Team Marketplace install. For headless test purposes (wpi.8,
wpi.9), the test should:

1. Verify the manifest file exists and has the correct structure.
2. Proceed with local skill copy as Phase 3 fallback (no CLI marketplace command known).

---

## 9. Open Questions (Ordered by Priority)

| # | Question | Blocks | Investigation method |
|---|----------|--------|---------------------|
| Q1 | What are the exact `cursor-agent --help` flags? | All phases | Run `cursor-agent --help` |
| Q2 | Does `-p` flag work for headless invocation? | Phase 1 auth, all agent phases | `cursor-agent -p "Reply with: AUTH_OK"` |
| Q3 | What is the auto-approve flag (`--force` or `--yolo`)? | Phase 5 (install needs write) | Run with both and observe |
| Q4 | Does `cursor-agent` set `CURSOR_AGENT=1` in subprocesses? | Phase 4.1 (detect_tool) | Run env-print prompt |
| Q5 | Does cursor-agent load `.cursor/skills/` from CWD? | Phase 3/5 (skill invocation) | Create test skill, invoke `/skill-name` |
| Q6 | Is there a `cursor-agent plugin install` or `skills` subcommand? | Phase 3 install | `cursor-agent --help` subcommands |
| Q7 | Does `~/.cursor/skills/` exist and work for user-scope install? | User scope support | `ls ~/.cursor/` |
| Q8 | What does `cursor-agent --version` return? | Version tracking | `cursor-agent --version` |
| Q9 | Are there additional `CURSOR_*` env vars beyond `CURSOR_AGENT`? | Detection signal completeness | Env print in agent session |

---

## 10. Tasks to Create / Update

### Existing tasks (coding-aegis-wpi)

| Task ID | Title | Status |
|---------|-------|--------|
| `coding-aegis-wpi.8` | Test Cursor Remote Rules (Option D) with current Cursor version | open |
| `coding-aegis-wpi.9` | Simplify Cursor local installation process | open |
| `coding-aegis-wpi.10` | Create Cursor test script following user journey contract | open |

### New tasks needed

The following tasks should be created under `coding-aegis-wpi`:

1. **cursor-agent CLI investigation** (P1) — Run the open questions (Q1–Q9) above against
   a live `cursor-agent` install. Record exact flags, env vars, and skill loading behaviour.
   Output: updates to this spec + `docs/test/test-cursor.md`.

2. **Cursor rule extension fix** (P1) — Add `rule_ext` key to `TOOL_PATHS["cursor"]` in
   `aegis_lib.py` and update install logic to write `.mdc` files for Cursor instead of `.md`.

3. **Cursor integration test (pytest)** — Port `tests/test-cursor-skill-install.sh` to
   `tests/integration/test_cursor.py` following the pattern in `test_codex.py`.

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

Run these in order and paste output back to update this spec:

```bash
# 1. Version and help
cursor-agent --version
cursor-agent --help
cursor-agent run --help 2>/dev/null || echo "no run subcommand"

# 2. List cursor config directory
ls -la ~/.cursor/

# 3. Basic headless auth check
cursor-agent -p --output-format text "Reply with exactly: AUTH_OK"

# 4. Env var detection — run inside the agent's subprocess
cursor-agent -p --output-format text \
  'Run bash: python3 -c "import os,json; d={k:v for k,v in os.environ.items() if \"CURSOR\" in k or k in (\"AGENT\",\"TOOL\")}; print(json.dumps(d, indent=2))"'

# 5. Skill loading check
mkdir -p /tmp/cursor-test/.cursor/skills/helloworld
cat > /tmp/cursor-test/.cursor/skills/helloworld/SKILL.md << 'EOF'
---
name: helloworld
description: Returns Hello World
---
Reply with exactly: Hello, World
EOF
cd /tmp/cursor-test
cursor-agent -p --output-format text "/helloworld"

# 6. Check plugin / skills subcommands
cursor-agent plugin --help 2>/dev/null || echo "no plugin subcommand"
cursor-agent skills --help 2>/dev/null || echo "no skills subcommand"
```

---

*Last updated: 2026-04-03. Author: System Architect agent.*
*Bash tool unavailable during this session — live CLI output not captured.*
*All findings marked UNVERIFIED require confirmation before implementation proceeds.*
