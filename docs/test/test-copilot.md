# GitHub Copilot CLI — Test Detail

> Tool-specific details for the GitHub Copilot CLI integration test. For the full test plan,
> phase definitions, and pass criteria see [TEST.md](TEST.md).

> **Status**: Test file written (`tests/integration/test_copilot.py`). Skipped on machines
> without `copilot` on PATH. Phases 1–6 require external validation on a machine with
> Copilot CLI installed and authenticated.

---

## 1. Headless Invocation

### Expected invocation form

> **NEEDS VALIDATION ON COPILOT MACHINE**

Based on the `github/copilot-cli` documentation (April 2026):

```bash
copilot --prompt '<prompt>' --allow-all-tools --silent
```

| Flag | Meaning |
|------|---------|
| `--prompt` / `-p` | Single non-interactive prompt; CLI exits on completion |
| `--allow-all-tools` | Pre-approve all tools (required for programmatic use) |
| `--silent` / `-s` | Suppress usage statistics; useful for scripting with `-p` |
| `--allow-all` | Equivalent to `--allow-all-tools --allow-all-paths --allow-all-urls` |
| `--output-format=json` | Return JSONL format (one JSON object per line) |
| `--no-ask-user` | Disable interactive prompts |

Authentication is resolved via env vars in order: `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_TOKEN`.

**Open questions:**

| Question | Status |
|----------|--------|
| Is binary name `copilot` (not `gh copilot`)? | **Assumed** — from `github/copilot-cli` README; needs live confirmation |
| Does `--prompt` / `-p` work headlessly? | **Documented** — needs live confirmation |
| Does `--allow-all-tools` suppress tool-approval prompts? | **Documented** — needs live confirmation |
| Does `--silent` suppress all non-response output? | **Documented** — needs live confirmation |
| Does `copilot` require `git init` in the working directory? | **Unknown** |
| What does `copilot --version` output? | **Unknown** |

---

## 2. Bootstrap Mechanism (Phase 2)

> **NEEDS VALIDATION ON COPILOT MACHINE**

Copilot CLI has **no plugin marketplace** equivalent to Claude Code or Cursor. Skills are
installed by placing a `SKILL.md` file in a scanned directory. The test fixture copies skill
files directly — no install command is needed.

Scanned directories (project scope, in priority order):
1. `.github/skills/<name>/SKILL.md`
2. `.claude/skills/<name>/SKILL.md`
3. `.agents/skills/<name>/SKILL.md`

Scanned directories (user scope):
1. `~/.copilot/skills/<name>/SKILL.md`
2. `~/.claude/skills/<name>/SKILL.md`
3. `~/.agents/skills/<name>/SKILL.md`

The test fixture copies the coding-aegis skill into `.github/skills/coding-aegis/`:

```python
copilot_skill_dir = test_dir / ".github" / "skills" / "coding-aegis"
copilot_skill_dir.mkdir(parents=True, exist_ok=True)
shutil.copytree(str(skill_src), str(copilot_skill_dir), dirs_exist_ok=True)
```

Phase 2 pytest test validates the `SKILL.md` frontmatter (same as OpenCode/Gemini — no
marketplace manifest to check).

**Open questions:**

| Question | Status |
|----------|--------|
| Does `copilot` load `.github/skills/` from CWD (not just git root)? | **Documented** — needs live confirmation |
| Does skill invocation use `/skill-name` syntax? | **Unknown** — Copilot has no confirmed skill invocation today |
| Does `copilot` read `AGENTS.md` natively? | **Unverified** |

---

## 3. Tool Detection Signals

### No env var injected (confirmed)

From `spec-tool-detection.md` (research April 2026, confirmed via GitHub docs):

> Copilot CLI injects **no Copilot-specific environment variable** into subprocesses.
> `GITHUB_ACTIONS=true` may be present in cloud agent runs but is not Copilot-specific.

**Primary detection signal: none** (no env var).

**Fallback detection signal:** `path:.github` — `__file__` contains `.github` if the skill
is installed at `.github/skills/coding-aegis/`.

```python
("path:.github",
 lambda env, fp: ".github" in fp.parts,
 "copilot"),
```

**IMPORTANT CAVEAT**: The `.github` path signal is low-confidence. Many repositories contain
a `.github/` directory, and other tools also scan `.github/skills/` (Codex, OpenCode). This
signal should only fire as a last resort.

Since Copilot has no confirmed skill-execution path today (rules only), `detect_tool.py`
will return `UNKNOWN` in a live Copilot CLI session unless the skill is run from `.github/skills/`.

> **NEEDS VALIDATION ON COPILOT MACHINE**: Confirm that `copilot` does not inject any
> `COPILOT_*` or `GITHUB_COPILOT_*` env var into subprocess environments.

| Signal | Status |
|--------|--------|
| `COPILOT_GITHUB_TOKEN` (auth token, not an agent signal) | Not a detection signal |
| `GITHUB_COPILOT_*` env vars | **Unconfirmed** — investigate on live machine |
| `path:.github` | Path fallback — low-confidence |

---

## 4. Rule Delivery

Rules are delivered differently from all other tools:

| Rule type | Path | Notes |
|-----------|------|-------|
| Always-on (global) | `.github/copilot-instructions.md` | Single file; all content always included |
| File-scoped | `.github/instructions/aegis--{pkg}--{rule}.instructions.md` | `applyTo:` frontmatter key |

The `aegis_lib.py` `TOOL_PATHS["copilot"]` entry uses `rule_ext: ".instructions.md"` for
file-scoped rules installed to `.github/instructions/`.

There is no `.github/rules/` directory equivalent to `.claude/rules/` or `.cursor/rules/`.

---

## 5. Expected File Locations After Install (helloworld)

> **NEEDS VALIDATION ON COPILOT MACHINE**

| Artifact | Path |
|----------|------|
| Rule (file-scoped) | `<test_dir>/.github/instructions/aegis--helloworld--<rule>.instructions.md` |
| Skill | `<test_dir>/.github/skills/helloworld/SKILL.md` |

Note: If helloworld includes an always-on rule, it would be appended to
`.github/copilot-instructions.md`. The test must be updated once install behavior is
confirmed live.

---

## 6. Phases

| Phase | What | Notes |
|-------|------|-------|
| 1 | Auth — `copilot -p 'Reply with: AUTH_OK' --allow-all-tools --silent` | Confirms binary and auth |
| 2 | Bootstrap mechanism — assert `SKILL.md` present at source with required frontmatter | No marketplace; SKILL.md file-copy discovery |
| 3 | Skill files present in `.github/skills/coding-aegis/` | Fixture-created |
| 4a | `detect_tool.py` direct — confirm path signal fires for `.github` | env var unavailable; path fallback tested |
| 4b | `/coding-aegis detect-tool` via agent | **NEEDS VALIDATION** — Copilot skill invocation unconfirmed |
| 4c | `/coding-aegis list --catalog modules` | **NEEDS VALIDATION** |
| 4d | `/coding-aegis show helloworld --catalog modules` | **NEEDS VALIDATION** |
| 5 | `/coding-aegis install helloworld to Project scope --catalog $TEST_DIR/modules` | **NEEDS VALIDATION** |
| 5b | `/helloworld` | **NEEDS VALIDATION** — Copilot skill invocation syntax unconfirmed |
| 6 | `/coding-aegis uninstall helloworld` | **NEEDS VALIDATION** |

Phases 4b–6 are marked `pytest.skip` in the test file with explicit `NEEDS_COPILOT_VALIDATION`
reasons until confirmed working on a live Copilot machine.

---

## 7. Timeout Budget

> **NEEDS VALIDATION ON COPILOT MACHINE** — defaults mirror OpenCode.

| Phase | Timeout |
|-------|---------|
| Phase 1 auth | `DEFAULT_TIMEOUT` (30s) |
| Phase 4a direct detect | `DEFAULT_TIMEOUT` (30s) |
| Phases 4b–4d (agent-mediated, if enabled) | `TIMEOUT_LONG` (120s) |
| Phase 5, 5b (install + invoke, if enabled) | `TIMEOUT_LONG` (120s) |
| Phase 6 (uninstall, if enabled) | `TIMEOUT_LONG` (120s) |

---

## 8. Output Handling

Unknown whether Copilot CLI emits ANSI escape codes in `--silent --prompt` mode.

> **NEEDS VALIDATION ON COPILOT MACHINE**: Confirm whether ANSI stripping is required.
> The test includes an `_ANSI_ESCAPE` stripper as a precaution (same pattern as OpenCode).

---

## 9. Known Unknowns

| # | Question | Impact | How to investigate |
|---|----------|--------|-------------------|
| KU-1 | Does `copilot` inject any env var into subprocesses? | Detection reliability | `copilot -p 'run: env \| grep -i copilot' --allow-all-tools --silent` |
| KU-2 | Binary name: `copilot` or `gh copilot`? | Invocation, skip condition | `which copilot; copilot --version` |
| KU-3 | Does Copilot CLI support `/skill-name` invocation syntax? | Phases 4b–6 | Check `copilot --help`; try `/coding-aegis detect-tool` |
| KU-4 | Does `copilot` read `.github/skills/` from CWD? | Phase 3 | Copy skill; run `copilot -p '/coding-aegis detect-tool'` |
| KU-5 | Does `git init` need to exist in working dir? | Test fixture setup | Try without `git init` |
| KU-6 | Does `copilot` read `AGENTS.md` natively? | Rule delivery fallback | Check docs or run prompt referencing AGENTS.md |
| KU-7 | Exact rule install path for always-on rules? | Phase 5 verification | Check `.github/copilot-instructions.md` or `.github/instructions/` after install |

---

## 10. Relationship to Existing ADRs

| ADR | Relevance |
|-----|-----------|
| AD-4 | Dual marketplace — no Copilot marketplace manifest today |
| AD-9 | AGENTS.md source of truth — Copilot reads `.github/copilot-instructions.md`, not AGENTS.md directly |
| AD-14 | Cross-tool artifact matrix — confirms Copilot rules-only delivery |

---

*Last updated: 2026-04-22.*
