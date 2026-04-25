# Spec: Robust Coding-Agent Tool Detection

**Task:** `coding-aegis-ghv`
**Status:** Research complete — ready for implementation review.

---

## Problem

`aegis_lib.py` needs to know which coding agent is running it so it can compute
correct install/uninstall paths. The current `_detect_tool()` function is unreliable:
it mixes unvalidated assumptions with real signals and has no tests. When it misidentifies
the tool, downstream path logic silently produces wrong results — causing the skill to
look in the wrong directories and the agent to spin until timeout.

---

## Validated Signals (Research Complete)

### Environment variables

Confirmed by running `env` inside each tool's runtime or by reading tool source code:

| Tool | Env var | Value | Source | Confidence |
|------|---------|-------|--------|------------|
| Claude Code | `CLAUDECODE` | `1` | Observed in live session | ✅ Confirmed |
| Claude Code | `CLAUDE_CODE_ENTRYPOINT` | `cli` | Observed in live session | ✅ Confirmed |
| Gemini CLI | `GEMINI_CLI` | `1` | Observed: user ran `env` in Gemini | ✅ Confirmed |
| Gemini CLI | `GEMINI_CLI_NO_RELAUNCH` | `true` | Observed: user ran `env` in Gemini | ✅ Confirmed |
| Codex CLI | `CODEX_CI` | `1` | Force-set on every subprocess via `UNIFIED_EXEC_ENV` | ✅ Confirmed (source) |
| Codex CLI | `CODEX_THREAD_ID` | UUID string | Always injected per session | ✅ Confirmed (source) |
| Codex CLI | `CODEX_SANDBOX` | `seatbelt` | Set on macOS when sandboxed | ✅ Confirmed (source) |
| Cursor | `CURSOR_AGENT` | `1` | Injected by Cursor CLI in agent terminal | ✅ Confirmed (community + bug report) |
| OpenCode | `OPENCODE` | `1` | Injected by `opencode run` into all subprocesses | ✅ Confirmed (v1.4.7, 2026-04-17) |
| OpenCode | `OPENCODE_PID` | server PID | Secondary signal, always present with `OPENCODE=1` | ✅ Confirmed (v1.4.7, 2026-04-17) |
| Copilot | *(none)* | — | No Copilot-specific vars injected into subprocesses (confirmed: GitHub docs Apr 2026). Auth vars (`COPILOT_GITHUB_TOKEN`, `GH_TOKEN`) are config, not agent signals. | ❌ No reliable env signal |

**Notes:**
- `CODEX_CI=1` is the most reliable Codex signal — it is force-set by the runtime on every
  subprocess regardless of sandbox mode. `CODEX_THREAD_ID` is also always present.
- `CURSOR_AGENT=1` was accidentally removed in one Cursor release and restored; it is
  the intended mechanism. Treat as reliable but add `__file__` fallback.
- `OPENCODE=1` and `OPENCODE_PID` are both confirmed live signals. Use `OPENCODE=1` as
  the primary signal; check `OPENCODE_PID` as secondary.
- An `AGENT=codex` convention (following Goose/Amp) was proposed in Codex issue #13416
  but not merged as of April 2026. Do not rely on it.
- Copilot's cloud agent runs in a GitHub Actions runner. `GITHUB_ACTIONS=true` is present
  but that is not Copilot-specific.

### Script path (`__file__`)

When `aegis_lib.py` is invoked by an agent, `__file__` reflects the install location.
Used as fallback when env vars are absent (e.g. Copilot or degraded environments).

| Tool | Install path | `__file__` contains | Confidence |
|------|-------------|----------------------|------------|
| Claude Code | `~/.claude/skills/<name>/` | `.claude` | ✅ Confirmed (test output) |
| Codex CLI | `.agents/skills/<name>/` (CWD-relative) | `.agents` | ✅ Confirmed (test output) |
| OpenCode | `.opencode/skills/<name>/` (project) | `.opencode` | ✅ Confirmed (test output) |
| Cursor | `~/.cursor/skills/<name>/` (assumed) | `.cursor` | ⚠️ Unverified |
| Gemini CLI | `.gemini/skills/<name>/` (workspace-installed copy) | `.gemini` | ✅ Confirmed — env var is primary, path fallback confirmed |
| Copilot | `.github/skills/<name>/` (project) | `.github` | ⚠️ Low-confidence — no env var; path signal only. Copilot has no confirmed skill execution. > NEEDS VALIDATION |

---

## Unknowns Remaining

1. **Cursor `__file__` path** — `~/.cursor/skills/` is assumed but not confirmed by running
   the skill inside Cursor. `CURSOR_AGENT=1` is the primary signal; `__file__` is fallback.

2. **Gemini `__file__` path** — Confirmed. `gemini skills install` copies the skill to
   `.gemini/skills/coding-aegis/`, so `__file__` contains `.gemini`. `GEMINI_CLI=1` env var
   is still the primary signal; path detection is the fallback.

3. **`CURSOR_AGENT=1` reliability across Cursor versions** — It regressed once. The fallback
   to `__file__` is important until this stabilises.

---

## Detection Design

### Priority order (first match wins)

Env vars are checked first (process-intrinsic, unambiguous). `__file__` is fallback only.

```
1.  CLAUDECODE=1              → claude   (env, confirmed)
2.  GEMINI_CLI=1              → gemini   (env, confirmed)
3.  CODEX_CI=1                → codex    (env, confirmed — always set by runtime)
4.  CODEX_THREAD_ID present   → codex    (env, secondary codex signal)
5.  CURSOR_AGENT=1            → cursor   (env, confirmed)
6.  OPENCODE=1                → opencode (env, confirmed v1.4.7)
7.  OPENCODE_PID present      → opencode (env, secondary opencode signal)
8.  __file__ contains .codex  → codex    (path, confirmed)
9.  __file__ contains .agents → codex    (path, confirmed — CWD-relative install)
10. __file__ contains .opencode → opencode (path, confirmed)
11. __file__ contains .cursor → cursor   (path, assumed)
12. __file__ contains .gemini → gemini   (path, assumed)
13. __file__ contains .github → copilot  (path, low-confidence fallback — no env var exists)
14. default                   → UNKNOWN  (no match)
```

### Implementation contract

- `detect_tool()` returns `{"tool": "<name>", "signals": [...]}` where `signals` is a list
  of the signal names that fired (aids debugging).
- Can be called with an override dict for testing (dependency injection — no `os.environ`
  globals).
- Standalone: `python3 detect-tool.py` prints JSON and exits 0.
- Importable: `from detect_tool import detect_tool`.

### Testing strategy

**Never assume install scope in tests.** Path-based signals (`.claude`, `.codex`, etc.) are
only reliable when the script is actually installed at a known path, which depends on scope
(user vs. project). Tests must not hardcode user-scope paths (`~/.claude/`, `~/.codex/`).

**Unit-level detection tests use env var injection:**

```bash
# Claude
env CLAUDECODE=1 python3 detect_tool.py   # → {"tool":"claude","signals":["env:CLAUDECODE=1"]}

# Codex
env CODEX_CI=1 python3 detect_tool.py    # → {"tool":"codex","signals":["env:CODEX_CI=1"]}

# Gemini — agent-mediated only (GEMINI_CLI=1 is set by the Gemini runtime)
```

Run `detect_tool.py` from the repo source path (`modules/bootstrap/coding-aegis/skills/coding-aegis/`),
not from an installed location. This makes the test scope-independent.

**Integration detection (T2c) runs inside the actual agent** (`claude -p`, `codex exec`, etc.),
which naturally injects the env var. Those tests validate end-to-end detection without
any scope assumption.

### Explicitly excluded

- **Filesystem markers** (`.cursor/`, `.opencode/` in CWD) — excluded because they fail
  in multi-tool repos. Confirmed in AD-11.
- **Parent process inspection** — fragile across shells and subprocess chains.
- **Heuristics** — every signal used must be validated.

---

## Tool Paths

`TOOL_PATHS` in `aegis_lib.py`:

| Tool | `scope_base` | `skills_dir` | `skills_base` | Notes |
|------|-------------|--------------|---------------|-------|
| claude | `.claude` | `skills` | *(none)* | Relative to `~` (user) or CWD (project) |
| codex | `.agents` | `.agents/skills` | `.` | CWD-relative; skills go in `.agents/skills/` |
| cursor | `.cursor` | `skills` | *(none)* | `rule_ext: .mdc` |
| opencode | `.opencode` | `skills` | *(none)* | `user_scope_base: .config/opencode` |
| gemini | `.gemini` | `skills` | *(none)* | `skills_base: .gemini` |
| copilot | `.github` | `skills` | *(none)* | `user_scope_base: .copilot`; `rule_ext: .instructions.md`; file-scoped rules → `.github/instructions/`; always-on → `.github/copilot-instructions.md` |

---

## Open Tasks

- [ ] Confirm Cursor `__file__` path by running a skill inside Cursor (task `coding-aegis-wpi.8`)

---

## Sources

- Claude Code env: observed live in this session (`CLAUDECODE=1`, `CLAUDE_CODE_ENTRYPOINT=cli`)
- Gemini CLI env: user ran `env` inside Gemini CLI session (`GEMINI_CLI=1`, `GEMINI_CLI_NO_RELAUNCH=true`)
- Codex env vars: `codex-rs/core/src/exec_env.rs`, `unified_exec/process_manager.rs`, `spawn.rs`
- Codex issue #13416: AGENT=codex proposal (unmerged, April 2026)
- Cursor: [Cursor forum bug report](https://forum.cursor.com/t/cursor-cli-is-not-setting-cursor-agent-1-environment-variable-while-executing-bash-commands/132427) — `CURSOR_AGENT=1` confirmed intentional
- Windsurf skills: [Cascade Skills docs](https://docs.windsurf.com/windsurf/cascade/skills) — no env vars injected
- Copilot: [GitHub Copilot agent docs](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment) — no Copilot-specific env vars
