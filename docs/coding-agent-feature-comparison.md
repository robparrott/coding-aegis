# Coding Agent Feature Comparison

Per-tool reference for engineers integrating coding-aegis. Covers marketplace/plugin installation, bootstrap skill installation, feature support, and current coding-aegis delivery status for each tool.

`(confirmed)` = validated live against the tool runtime or source code. `(unverified)` = documented expectation or ADR-derived assumption not yet live-validated.

---

## Quick Reference: Feature Support Matrix

| Feature | Claude Code | Codex | Cursor | OpenCode | Gemini CLI | Windsurf | Copilot |
|---------|:-----------:|:-----:|:------:|:--------:|:----------:|:--------:|:-------:|
| Always-on rules | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| File-scoped rules | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Invocable skills (`/skill-name`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| MCP server config | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Custom agents | ✅ | ❌ | ⚠️ built-in | ⚠️ built-in | ❌ | ⚠️ built-in | ⚠️ built-in |
| Plugin/marketplace | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ⚠️ GitHub |
| User scope install | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ VS Code |
| Project scope install | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| coding-aegis supported | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ unverified | ⚠️ unverified |

Notes on "Custom agents" row: Cursor, Windsurf, Copilot, and OpenCode have built-in agent modes but do not support user-defined `AGENT.md` artifacts in the same way Claude Code does. Copilot agent mode runs in GitHub Actions.

---

## Claude Code

Full support across all coding-aegis features; the reference implementation tool.

### Marketplace / Plugin installation

- Has a plugin marketplace system (confirmed).
- Install via CLI:
  ```
  claude plugin marketplace add {org}/coding-aegis
  claude plugin install coding-aegis@{marketplace-name} --scope project
  ```
- Manifest file: `.claude-plugin/marketplace.json` at repo root (confirmed).

### Bootstrap skill installation

- Mechanism: marketplace install via `claude plugin install`.
- The skill is loaded dynamically from the marketplace source — it is not copied into the project directory (confirmed).
- Project-scope landing path: `.claude/skills/coding-aegis/` (confirmed from test output).
- User-scope landing path: `~/.claude/skills/coding-aegis/` (confirmed).

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `.claude/rules/aegis--{pkg}--{rule}.md` | All rule files in `.claude/rules/` are always-on |
| File-scoped rules | `.claude/rules/aegis--{pkg}--{rule}.md` with `globs:` frontmatter | `paths:` key is documented but not functional — use `globs:` (confirmed bug) |
| Invocable skills | `.claude/skills/{name}/SKILL.md` | `/skill-name` slash-command syntax |
| MCP config | `.mcp.json` (project), `~/.claude.json` (user) | |
| Custom agents | `.claude/agents/{name}/AGENT.md` | |

### coding-aegis install status

- Fully supported (confirmed). Test suite: 10/10 phases passing (confirmed).
- Rules delivered as `.md` files written to `.claude/rules/` (project) or `~/.claude/rules/` (user).
- AGENTS.md is bridged via `@AGENTS.md` import in `CLAUDE.md`; `CLAUDE.md` is a generated artifact, not checked in.
- Detection signal: `CLAUDECODE=1` env var (confirmed).

---

## Codex

Full coding-aegis support; rules delivered via `AGENTS.md` sections rather than discrete rule files.

### Marketplace / Plugin installation

- No `codex plugin install` CLI command exists (confirmed from source).
- Plugin discovery is automatic: Codex scans for `marketplace.json` at startup in this order (confirmed from source):
  1. `$REPO_ROOT/.agents/plugins/marketplace.json`
  2. `~/.agents/plugins/marketplace.json`
  3. Official Plugin Directory (curated; self-serve publishing not yet available)
- Manifest file used by coding-aegis: `.codex-plugin/plugin.json` at repo root.
- Bootstrap: copy or reference `.codex-plugin/plugin.json` into the appropriate marketplace scan path; Codex auto-discovers on next start.

### Bootstrap skill installation

- Mechanism: `$skill-installer` built-in skill, invoked agent-mediated:
  ```
  $skill-installer install --repo {org}/coding-aegis --path pkgs/bootstrap/coding-aegis/skills/coding-aegis
  ```
- Requires GitHub network access (`danger-full-access` sandbox) (confirmed).
- Only installs from GitHub sources — local filesystem paths are not supported (confirmed).
- User-scope landing path: `~/.codex/skills/coding-aegis/` (confirmed from test output).
- Project-scope skills: `.agents/skills/{name}/SKILL.md`.

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `AGENTS.md` (aegis:begin/end markers) | No `.codex/rules/` equivalent |
| File-scoped rules | ❌ not supported | AGENTS.md is global |
| Invocable skills | `.agents/skills/{name}/SKILL.md` | `$skill-name` dollar-sign syntax |
| MCP config | ❌ not supported | |
| Custom agents | ❌ not supported | |

### coding-aegis install status

- Fully supported (confirmed). Test suite: passing (confirmed).
- Rules delivered as marked sections in `AGENTS.md` using `<!-- aegis:begin -->` / `<!-- aegis:end -->` HTML comment markers.
- Detection signal: `CODEX_CI=1` env var (confirmed from source); `CODEX_THREAD_ID` present as secondary signal.
- Note: `CLAUDECODE=1` bleeds from a parent Claude Code session into Codex subprocess env — test harness must `unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT` before invoking Codex (confirmed).

---

## Cursor

Full coding-aegis support; rule files use `.mdc` extension with YAML frontmatter.

### Marketplace / Plugin installation

- Has a Team Marketplace system (confirmed).
- GUI-only install (no CLI marketplace command confirmed): Dashboard → Settings → Plugins → Import → paste repo URL.
- Private repo prerequisite: register a GitHub Enterprise App at `cursor.com/dashboard?tab=integrations` and grant access to the governance repo.
- Manifest file: `.cursor-plugin/marketplace.json` at repo root (confirmed).
- No headless `cursor-agent plugin install` subcommand exists (confirmed).

### Bootstrap skill installation

- No `cursor-agent plugin install` CLI command (confirmed).
- Integration test bootstrap copies skill files directly into `.cursor/skills/coding-aegis/` (confirmed from test harness).
- Project-scope skills: `.cursor/skills/{name}/SKILL.md` (confirmed — `cursor-agent` loads `.cursor/skills/` from CWD).
- User-scope skills: `~/.cursor/skills-cursor/{name}/SKILL.md` (confirmed from live `~/.cursor/` directory listing; note: `skills-cursor/` not `skills/`).

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `.cursor/rules/aegis--{pkg}--{rule}.mdc` with `alwaysApply: true` | `alwaysApply` injected by coding-aegis renderer |
| File-scoped rules | `.cursor/rules/aegis--{pkg}--{rule}.mdc` with `globs:` | Same `globs:` syntax as Claude Code |
| Invocable skills | `.cursor/skills/{name}/SKILL.md` | `/skill-name` slash-command syntax (unverified in headless `cursor-agent`) |
| MCP config | `.mcp.json` (project), `~/.cursor/mcp.json` (user) | |
| Custom agents | ⚠️ background agents are built-in; no `AGENT.md` format | |

Cursor also reads `AGENTS.md` natively; `.cursor/rules/*.mdc` is the preferred delivery mechanism and AGENTS.md is a fallback (confirmed).

Legacy `.cursorrules` file (project root) is still read by Cursor but deprecated. coding-aegis does not target it.

### coding-aegis install status

- Fully supported (confirmed). Test suite: 10/10 passing (`cursor-agent 2026.04.16-2d20146`, 2026-04-17).
- Rules delivered as `.mdc` files in `.cursor/rules/` (project or user scope).
- Detection signal: `CURSOR_AGENT=1` env var (confirmed via forum; regressed once in a prior Cursor release and was restored — `__file__` path fallback is maintained).
- macOS users: after `brew install cursor-cli`, run `xattr -rd com.apple.quarantine $(brew --prefix)/Caskroom/cursor-cli/<version>/` to clear Gatekeeper quarantine on bundled binaries.

---

## OpenCode

Full coding-aegis support; rules delivered via `AGENTS.md` sections (same mechanism as Codex).

### Marketplace / Plugin installation

- No plugin marketplace system (confirmed). OpenCode has a separate JS/TS plugin system for `.opencode/plugins/`, but coding-aegis does not target it.
- No install command needed for skills.

### Bootstrap skill installation

- Mechanism: auto-discovery — no install command (confirmed against opencode v1.4.7).
- Skills are discovered by directory scan in priority order (highest first):
  1. `{git-root}/.opencode/skills/{name}/SKILL.md` (project)
  2. `{git-root}/.claude/skills/{name}/SKILL.md` (Claude compat)
  3. `{git-root}/.agents/skills/{name}/SKILL.md` (open standard)
  4. `~/.config/opencode/skills/{name}/SKILL.md` (user)
  5. `~/.claude/skills/{name}/SKILL.md` (user, Claude compat)
  6. `~/.agents/skills/{name}/SKILL.md` (user, open standard)
- Preferred project-scope path: `.opencode/skills/{name}/SKILL.md` (confirmed).
- User-scope path: `~/.config/opencode/skills/{name}/SKILL.md` (confirmed).
- Claude compat paths can be disabled with `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`.

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `AGENTS.md` (aegis:begin/end markers) | Native AGENTS.md reader; no `.opencode/rules/` path |
| File-scoped rules | ❌ not supported | AGENTS.md is global |
| Invocable skills | `.opencode/skills/{name}/SKILL.md` | `skill()` tool call, model-driven selection |
| MCP config | ❌ (unverified) | `opencode.json` supports npm plugins; MCP not confirmed |
| Custom agents | ⚠️ built-in named agents (build, plan, general, explore) | No user-defined AGENT.md format |

Additional instruction files can be referenced via `opencode.json` `instructions` array (confirmed).

### coding-aegis install status

- Supported (confirmed). Integration test spec ready; pytest not yet written (`yjy.5` open task).
- Rules delivered as marked sections in `AGENTS.md` (same aegis:begin/end mechanism as Codex).
- Detection signals: `OPENCODE=1` and `OPENCODE_PID=<server-pid>` both confirmed live (opencode v1.4.7, 2026-04-17).

---

## Gemini CLI

Supported; uses `gemini skills link` for skill installation. All artifacts install under `.gemini/`.

### Marketplace / Plugin installation

- No marketplace or registry system (confirmed). Skip marketplace phase.

### Bootstrap skill installation

- Mechanism: `gemini skills link` CLI command (confirmed from test harness):
  ```
  gemini skills link "$SKILL_DIR" --scope workspace --consent
  ```
- The skill is linked from the local path — not copied to a tool-specific directory (confirmed).
- `gemini skills list` confirms installation.
- User-scope install: `--scope user` instead of `--scope workspace` (unverified path).

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `.gemini/rules/aegis--{pkg}--{rule}.md` | Confirmed 2026-04-17 manual walkthrough |
| File-scoped rules | ❌ (unverified) | No confirmed file-scoped mechanism |
| Invocable skills | `.gemini/skills/{name}/SKILL.md` | Confirmed 2026-04-17; `/skill-name` slash-command syntax works after install |
| MCP config | ❌ not supported | |
| Custom agents | ❌ not supported | |

### coding-aegis install status

- Supported; integration tests exist (`tests/integration/test_gemini.py`) but currently deferred due to free-tier quota constraints (task `97z.13`).
- Rules delivered to `.gemini/rules/aegis--*` (confirmed 2026-04-17 manual walkthrough; previous `.claude/rules/` assumption was wrong).
- Skills delivered to `.gemini/skills/{name}/SKILL.md` (confirmed 2026-04-17; previous `.claude/skills/` assumption was wrong — Gemini only discovers skills from `.gemini/skills/`).
- Detection signal: `GEMINI_CLI=1` env var (confirmed live — user ran `env` in a Gemini session); `GEMINI_CLI_NO_RELAUNCH=true` also present.
- Note: `__file__` path-based fallback detection is unverified for Gemini since skills are linked, not copied to a tool-specific directory.
- Output filtering required in headless tests: Homebrew keytar warnings pollute stdout and must be filtered.

---

## Windsurf

Partially supported; rules and skills paths are known from docs but no live integration test exists.

### Marketplace / Plugin installation

- No plugin marketplace system for Windsurf (confirmed — AD-14).

### Bootstrap skill installation

- Mechanism: manual copy or Cascade Skills install (unverified live).
- Project-scope skills: `.agents/skills/{name}/SKILL.md` (from Windsurf docs).
- User-scope skills: `~/.codeium/windsurf/skills/{name}/SKILL.md` (from Windsurf docs).
- Workspace-scope: `.windsurf/skills/{name}/SKILL.md` (unverified).

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `.windsurf/rules/aegis--{pkg}--{rule}.md` | All files in `.windsurf/rules/` are always-on; no `alwaysApply` key |
| File-scoped rules | `.windsurf/rules/aegis--{pkg}--{rule}.md` with `globs:` | Same `globs:` syntax |
| Invocable skills | `.agents/skills/{name}/SKILL.md` | Cascade Skills |
| MCP config | `.mcp.json` (project), `~/.codeium/windsurf/mcp_config.json` (user) | |
| Custom agents | ⚠️ Cascade is built-in; no `AGENT.md` format | |

### coding-aegis install status

- Unverified (no live integration test). Paths are ADR-derived from Windsurf documentation.
- Rules would be delivered as `.md` files in `.windsurf/rules/` — no `alwaysApply` injection needed (all rules in that directory are always active).
- No env var detection signal for Windsurf (confirmed — no `WINDSURF_*` vars documented or observed). Detection falls back to `__file__` path containing `.codeium/windsurf` or `.windsurf`.

---

## GitHub Copilot

Limited support; no skill execution, no MCP. Rules delivered via a single instructions file or per-file instruction files.

### Marketplace / Plugin installation

- GitHub Marketplace for VS Code extensions (unverified as a coding-aegis delivery mechanism).
- No plugin system equivalent to Claude/Cursor marketplaces.

### Bootstrap skill installation

- No skill execution support (confirmed — AD-14).
- coding-aegis cannot be installed as an invocable skill in Copilot.
- Rules only: delivered to `.github/instructions/aegis--{pkg}--{rule}.instructions.md` with `applyTo:` frontmatter, or to `.github/copilot-instructions.md` for global always-on guidance.

### Feature support details

| Feature | Path / config | Notes |
|---------|--------------|-------|
| Always-on rules | `.github/copilot-instructions.md` | Single global instructions file |
| File-scoped rules | `.github/instructions/aegis--{pkg}--{rule}.instructions.md` with `applyTo:` | Newer feature; less widely adopted |
| Invocable skills | ❌ not supported | |
| MCP config | ❌ not supported | |
| Custom agents | ⚠️ Agent mode built-in; runs in GitHub Actions | Cloud-based; `GITHUB_ACTIONS=true` present but not Copilot-specific |

### coding-aegis install status

- Unverified (no live integration test). Rules-only delivery.
- Always-on guidance via `AGENTS.md` content rendered into `.github/copilot-instructions.md`.
- File-scoped instructions via `.github/instructions/` use `applyTo:` (translated from `globs:` in canonical source).
- No env var detection signal (confirmed — no Copilot-specific vars injected by the runtime). Detection falls back to `__file__` path; Copilot has no skill execution so the script would not run agent-mediated in any case.

---

## Path Reference Summary

### Rule install paths (project scope)

| Tool | Path | Extension |
|------|------|-----------|
| Claude Code | `.claude/rules/aegis--{pkg}--{rule}.md` | `.md` |
| Codex | `AGENTS.md` (aegis:begin/end markers) | — |
| Cursor | `.cursor/rules/aegis--{pkg}--{rule}.mdc` | `.mdc` |
| OpenCode | `AGENTS.md` (aegis:begin/end markers) | — |
| Gemini CLI | `.gemini/rules/aegis--{pkg}--{rule}.md` | `.md` |
| Windsurf | `.windsurf/rules/aegis--{pkg}--{rule}.md` | `.md` |
| Copilot | `.github/instructions/aegis--{pkg}--{rule}.instructions.md` | `.instructions.md` |

### Skill install paths (project scope)

| Tool | Path |
|------|------|
| Claude Code | `.claude/skills/{name}/SKILL.md` |
| Codex | `.agents/skills/{name}/SKILL.md` |
| Cursor | `.cursor/skills/{name}/SKILL.md` |
| OpenCode | `.opencode/skills/{name}/SKILL.md` |
| Gemini CLI | `.gemini/skills/{name}/SKILL.md` |
| Windsurf | `.agents/skills/{name}/SKILL.md` |
| Copilot | Not supported |

### Detection signals

| Tool | Primary env var | Status |
|------|----------------|--------|
| Claude Code | `CLAUDECODE=1` | confirmed |
| Codex | `CODEX_CI=1` | confirmed |
| Cursor | `CURSOR_AGENT=1` | confirmed (with regression history) |
| OpenCode | `OPENCODE=1` | confirmed |
| Gemini CLI | `GEMINI_CLI=1` | confirmed |
| Windsurf | none | no env signal; `__file__` fallback only |
| Copilot | none | no env signal; no skill execution |
