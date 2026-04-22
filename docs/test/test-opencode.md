# OpenCode — Test Detail

> Tool-specific details for the OpenCode integration test. For the full test plan, phase definitions, and pass criteria see [TEST.md](TEST.md). For how OpenCode skills and rules work, see [opencode-integration.md](../architecture/opencode-integration.md).

> **Status**: Tests written and passing (9/10). Detection signals confirmed. See §4.

---

## 1. pytest Location

`tests/integration/test_opencode.py` — Skipped automatically when `opencode` is not on PATH.

---

## 2. Headless Invocation

```bash
opencode run '<prompt>'
```

| Flag | Purpose |
|------|---------|
| `run '<prompt>'` | Non-interactive single-prompt execution |
| `--format json` | Raw JSON event stream (use for structured output) |
| `-m <provider/model>` | Model override |
| `--agent <name>` | Agent selection (build, plan, general, explore) |

Prompt is a positional argument. No `--trust` equivalent (opencode has no workspace trust prompt). No `--quiet` flag exists.

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

**Confirmed** (opencode v1.4.7, 2026-04-17): `opencode run` injects both signals into all subprocesses.

```
OPENCODE=1
OPENCODE_PID=<server-pid>
```

| Signal | Status |
|--------|--------|
| `OPENCODE=1` | **Confirmed** — use as primary detection signal |
| `OPENCODE_PID` | **Confirmed** — secondary signal |

`detect_tool.py` signals are correct as-is. Phase 4a can assert `tool == "opencode"` when `OPENCODE=1` is in the environment.

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
| 1 | Auth — `opencode run 'Reply with: AUTH_OK'` | Confirms binary present and authenticated |
| 2 | Bootstrap mechanism — assert `SKILL.md` present at skill source path with `name: coding-aegis` and `description:` frontmatter | No marketplace; bootstrap is file-copy auto-discovery into `.opencode/skills/` |
| 3 | Skill files present in `.opencode/skills/coding-aegis/` | Fixture-created; assert SKILL.md, aegis_lib.py, etc. |
| 4a | `detect_tool.py` direct — confirm tool=opencode | Depends on confirmed signal (see §4) |
| 4b | `/coding-aegis detect-tool` via agent | Assert "opencode" in output |
| 4c | `/coding-aegis list --catalog pkgs` | Assert "helloworld" in output |
| 4d | `/coding-aegis show helloworld --catalog pkgs` | Assert name, tier, version |
| 5 | `/coding-aegis install helloworld to Project scope --catalog $TEST_DIR/pkgs` | Assert AGENTS.md updated + `.opencode/skills/helloworld/` created; then run `aegis-validate.py` |
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

## 9. Output Handling

OpenCode emits ANSI colour codes in output. The test strips them before assertions:

```python
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mK]")
_clean(result.stdout)  # strip ANSI before asserting
```

## 10. Known Unknowns

None outstanding.
