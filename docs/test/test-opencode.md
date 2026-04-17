# OpenCode — Test Detail

> Tool-specific details for the OpenCode integration test. For the full test plan, phase definitions, and pass criteria see [testing-spec.md](testing-spec.md). For how OpenCode skills and rules work, see [opencode-integration.md](../architecture/opencode-integration.md).

> **Status**: Spec ready — pytest not yet written. Blocked on confirming the tool-detection signal. See §4.

---

## 1. pytest Location

`tests/integration/test_opencode.py` — not yet written. Skipped automatically when `opencode` is not on PATH.

---

## 2. Headless Invocation

```bash
opencode run '<prompt>' --quiet
```

| Flag | Purpose |
|------|---------|
| `run '<prompt>'` | Non-interactive single-prompt execution |
| `-q` / `--quiet` | Suppress spinner (required for clean stdout capture) |

Prompt is a positional argument. No `--trust` equivalent known (not required — opencode does not have a workspace trust prompt).

---

## 3. Skill Bootstrap (test fixture)

OpenCode auto-discovers skills from `.opencode/skills/` in the project directory. **No install command needed.**

The test fixture copies the coding-aegis skill into the test dir:

```python
skill_src = repo_root / "pkgs" / "bootstrap" / "coding-aegis" / "skills" / "coding-aegis"
opencode_skill_dir = test_dir / ".opencode" / "skills" / "coding-aegis"
opencode_skill_dir.mkdir(parents=True, exist_ok=True)
shutil.copytree(str(skill_src), str(opencode_skill_dir), dirs_exist_ok=True)
```

No user-scope (`~/.config/opencode/skills/`) installation required for project-scoped tests.

---

## 4. Tool Detection — Open Question

**Blocked**: `detect_tool.py` currently asserts `OPENCODE=1` and `OPENCODE_PID` env signals, but these are **not confirmed** in official documentation.

Before writing the pytest, run this inside an `opencode run` session and record the output:

```bash
opencode run 'bash -c "env | grep -i opencode"' --quiet
```

| Signal | Current status |
|--------|---------------|
| `OPENCODE=1` | In detect_tool.py; unverified |
| `OPENCODE_PID` | In detect_tool.py; unverified |

If neither is set by `opencode run`, the test fixture should inject a synthetic env var (same pattern as Cursor's `CURSOR_AGENT=1` injection) and update `detect_tool.py` accordingly.

Phase 4a (`detect_tool.py` direct) must be adjusted to match whatever signal is confirmed.

---

## 5. Rule Delivery

Rules are delivered via `AGENTS.md` aegis:begin/end sections (same mechanism as Codex). The install test should assert:

1. `AGENTS.md` exists in the test dir after install.
2. It contains `<!-- aegis:begin package=helloworld -->` and `<!-- aegis:end package=helloworld -->` markers.

No `.opencode/rules/` path exists. `AGENTS.md` is the only delivery target.

---

## 6. Expected File Locations After Install (helloworld)

| Artifact | Path |
|----------|------|
| Rule (AGENTS.md section) | `<test_dir>/AGENTS.md` |
| Skill | `<test_dir>/.opencode/skills/helloworld/SKILL.md` |

---

## 7. Phases

| Phase | What | Notes |
|-------|------|-------|
| 1 | Auth — `opencode run 'Reply with: AUTH_OK' --quiet` | Confirms binary present and authenticated |
| 2 | No marketplace — skip or assert no error | No plugin registry for opencode |
| 3 | Skill files present in `.opencode/skills/coding-aegis/` | Fixture-created; assert SKILL.md, aegis_lib.py, etc. |
| 4a | `detect_tool.py` direct — confirm tool=opencode | Depends on confirmed signal (see §4) |
| 4b | `/coding-aegis detect-tool` via agent | Assert "opencode" in output |
| 4c | `/coding-aegis list --catalog pkgs` | Assert "helloworld" in output |
| 4d | `/coding-aegis show helloworld --catalog pkgs` | Assert name, tier, version |
| 5 | `/coding-aegis install helloworld` | Assert AGENTS.md updated + `.opencode/skills/helloworld/` created |
| 5b | `/helloworld` | Assert "Hello, World" in output |
| 6 | `/coding-aegis uninstall helloworld` | Assert AGENTS.md section removed + skill dir deleted |

---

## 8. Timeout Budget

| Phase | Timeout |
|-------|---------|
| Phase 1 auth | `DEFAULT_TIMEOUT` (30s) |
| Phases 4b–4d (agent-mediated) | `TIMEOUT_LONG` (120s) |
| Phase 5, 5b (install + invoke) | `TIMEOUT_LONG` (120s) |
| Phase 6 (uninstall) | `TIMEOUT_LONG` (120s) |

---

## 9. Known Unknowns

| Question | Status |
|----------|--------|
| What env var does `opencode run` inject into subprocesses? | **Must confirm before writing test** |
| Does `opencode run` require `git init` in the working directory? | Unverified |
| Does the skill invocation syntax `/coding-aegis` work in opencode? | Unverified — may differ from Claude/Cursor |
| Does opencode read `.opencode/skills/` immediately or require restart? | Unverified |
