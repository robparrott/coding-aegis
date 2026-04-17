# OpenCode Integration Spec

**Status**: Draft — detection signal unverified; all other findings confirmed from official docs (2026-04-17).

---

## 1. What OpenCode Is

[OpenCode](https://opencode.ai) (sst/opencode) is an open-source, terminal-based AI coding agent. It runs a local server and exposes a TUI + headless CLI. It supports multiple model providers (Anthropic, OpenAI, Google, etc.) and has a plugin/skill/rules system designed for extensibility.

---

## 2. Headless Invocation

```bash
opencode run '<prompt>' --quiet
```

| Flag | Meaning |
|------|---------|
| `run '<prompt>'` | Execute a single prompt non-interactively |
| `-q` / `--quiet` | Suppress spinner (required for script piping) |
| `-m` / `--model <provider/model>` | Model override, e.g. `anthropic/claude-sonnet-4-20250514` |
| `-a` / `--agent <name>` | Agent selection: `build`, `plan`, `general`, `explore`, or custom |
| `-f json` / `--format json` | Structured JSON output |
| `-s` / `--session <id>` | Resume a specific session |
| `-c` / `--continue` | Resume previous session |
| `--print-logs` | Emit logs to stderr |

The `run` command bootstraps a temporary server and streams the response to stdout. Does not require a pseudo-terminal.

---

## 3. Skill System

### Discovery (no install command)

Skills are auto-discovered by directory scan. No `link`, `install`, or `register` command exists. Priority order (highest first):

| Priority | Path | Scope |
|----------|------|-------|
| 1 | `<git-root>/.opencode/skills/<name>/SKILL.md` | Project |
| 2 | `<git-root>/.claude/skills/<name>/SKILL.md` | Project (Claude compat) |
| 3 | `<git-root>/.agents/skills/<name>/SKILL.md` | Project (open standard) |
| 4 | `~/.config/opencode/skills/<name>/SKILL.md` | User |
| 5 | `~/.claude/skills/<name>/SKILL.md` | User (Claude compat) |
| 6 | `~/.agents/skills/<name>/SKILL.md` | User (open standard) |

Discovery walks up to the git worktree root.

### SKILL.md format

```yaml
---
name: my-skill            # required; 1–64 chars; regex ^[a-z0-9]+(-[a-z0-9]+)*$
description: One-liner    # required; 1–1024 chars
license: MIT              # optional
---
Skill body / instructions shown to the model.
```

Skills are loaded into the system prompt. The agent invokes them via a native `skill({ name: "..." })` tool call — selection is model-driven based on the description.

### Disabling Claude compat skill paths

```bash
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1  # disable .claude/skills/ and ~/.claude/skills/ paths
```

---

## 4. Rules / Always-On Guidance

OpenCode reads `AGENTS.md` natively (same as Codex and Cursor). Discovery order:

1. `<git-root>/AGENTS.md` (project)
2. `~/.config/opencode/AGENTS.md` (user global)
3. Fallback: `CLAUDE.md` (project), then `~/.claude/CLAUDE.md`

Additional files can be referenced via `opencode.json`:

```json
{
  "instructions": ["CONTRIBUTING.md", ".cursor/rules/*.md"]
}
```

**coding-aegis delivery**: Rules are delivered via `AGENTS.md` aegis:begin/end sections (same mechanism as Codex). The `.opencode/rules/` path does not exist; `AGENTS.md` is the canonical delivery target.

---

## 5. Install Paths (coding-aegis)

| Scope | Rules path | Skills path |
|-------|-----------|------------|
| Project | `AGENTS.md` (aegis:begin/end markers) | `{repo}/.opencode/skills/{name}/SKILL.md` |
| User | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/skills/{name}/SKILL.md` |

`TOOL_PATHS["opencode"]` in `aegis_lib.py`:

```python
"opencode": {
    "scope_base": ".opencode",
    "skills_dir": "skills",
    "user_scope_base": ".config/opencode",   # home-relative
}
```

---

## 6. Tool Detection

### Known signals

| Signal | Type | Confidence |
|--------|------|-----------|
| `OPENCODE=1` env var | Env | **Unverified** — not in official docs; may be set by `opencode run` |
| `OPENCODE_PID` env var | Env | **Unverified** — not in official docs |
| `.opencode` in `__file__` path | Path | Low — only fires if skill is installed under `.opencode/skills/` |

### Open question

No official documentation confirms that `opencode run` injects any `OPENCODE_*` env var into agent subprocesses. The `OPENCODE=1` and `OPENCODE_PID` signals currently in `detect_tool.py` are **unverified**. Before shipping OpenCode support, run:

```bash
opencode run 'bash -c "env | grep -i opencode"' --quiet
```

and record what variables appear.

If no env var is set, the path-based signal (`.opencode` in `__file__`) is the fallback — low confidence but functional for project-scoped skills.

---

## 7. Plugin System (separate from skills)

OpenCode has a JavaScript/TypeScript plugin system distinct from skills:

- Project plugins: `.opencode/plugins/` (auto-loaded at startup)
- Global plugins: `~/.config/opencode/plugins/`
- npm plugins: declared in `opencode.json`, auto-installed via Bun

coding-aegis does not target the plugin system. Skills are the correct integration point.

---

## 8. Custom Commands (slash commands)

Markdown files, distinct from skills:

- Global: `~/.config/opencode/commands/<name>.md`
- Project: `.opencode/commands/<name>.md`

Frontmatter: `description`, `agent`, `model`, `subtask`. Supports `$ARGUMENTS`, bash injection, `@filename` inclusion.

coding-aegis does not target custom commands. Skills are the correct integration point.

---

## 9. Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENCODE_CONFIG` | Path to config file override |
| `OPENCODE_CONFIG_DIR` | Config directory override |
| `OPENCODE_DISABLE_AUTOUPDATE` | Skip auto-updates |
| `OPENCODE_PERMISSION` | Default permission level |
| `OPENCODE_DISABLE_CLAUDE_CODE` | Disable all Claude Code compat paths |
| `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` | Disable global `~/.claude/CLAUDE.md` fallback |
| `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` | Disable `.claude/skills/` compat paths |

---

## 10. Relationship to Existing ADRs

| ADR | Relevance |
|-----|-----------|
| AD-5 | Installation targets — `.opencode/skills/` is the OpenCode project-scope path |
| AD-9 | `AGENTS.md` as source of truth — OpenCode reads it natively |
| AD-14 | Cross-tool artifact matrix — OpenCode row needs adding |
| AD-15 | Single-source install adaptation — rule delivery via AGENTS.md sections |

---

*Last updated: 2026-04-17. Sources: opencode.ai/docs, deepwiki.com/sst/opencode.*
