# Testing Specification: Skill Setup Pipeline

Cross-tool testing standard for the coding-aegis install lifecycle. The primary test flow exercises the **actual user journey**: install the coding-aegis skill, then use it through the tool's agent to manage packages. Direct CLI tests exist as fast secondary validation but never replace the skill-mediated flow.

## Primary Test Flow (Required)

Every tool's test script MUST follow this sequence. The coding-aegis skill is the primary interface — tests must go through it, not around it.

### T0 — Tool Prerequisites

Verify the CLI tool is installed, accessible, and authenticated.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T0.1 | Tool binary in PATH | `command -v <tool>` succeeds, version printed |
| T0.2 | Tool authenticated | Non-interactive prompt returns a response |

**Tool-specific commands:**

| Tool | T0.1 | T0.2 |
|------|------|------|
| Claude | `command -v claude` | `claude -p "AUTH_OK" < /dev/null` |
| Codex | `command -v codex`, `codex --version` | `codex exec "AUTH_OK" --ephemeral` (requires git repo) |
| Gemini | `command -v gemini`, `gemini --version` | `gemini -p "AUTH_OK" -o text < /dev/null` |
| Cursor | TBD — research CLI availability | TBD |

### T1 — Install coding-aegis Skill

Register and install the coding-aegis skill so it is available to the tool's agent.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T1.1 | Register marketplace / copy skill | CLI reports success or files present |
| T1.2 | Verify coding-aegis skill is discoverable | Skill name visible in list/discovery |

**Tool-specific mapping:**

| Tool | T1.1 | T1.2 |
|------|------|------|
| Claude | `claude plugin marketplace add <path>` + `claude plugin install` | `claude plugin list` shows coding-aegis |
| Codex | Copy skill dir to `.agents/skills/coding-aegis/` | Files present at expected path |
| Gemini | `gemini skills link <path> --consent` | `gemini skills list` shows coding-aegis |
| Cursor | TBD | TBD |

### T2 — Use Skill: List Packages

Use the installed coding-aegis skill through the tool's agent to list the catalog.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T2.1 | Agent executes coding-aegis list command | Output contains "helloworld" |
| T2.2 | Output contains tier information | "optional" tier visible |

**The agent must invoke the skill, which calls aegis-catalog.py internally. The test must NOT call aegis-catalog.py directly.**

### T3 — Use Skill: Show Package

Use the installed skill to show helloworld package details.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T3.1 | Agent executes coding-aegis show helloworld | Output contains package name |
| T3.2 | Output contains correct metadata | Version "1.0.0", tier "optional" visible |

### T4 — Use Skill: Install Package

Use the installed skill to install helloworld into a test directory.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T4.1 | Agent executes coding-aegis install helloworld | Agent reports successful install |
| T4.2 | Rule file exists with correct naming | `aegis--helloworld--helloworld.md` present |
| T4.3 | Rule file has managed-by frontmatter | Contains `managed-by: coding-aegis`, `package: helloworld` |
| T4.4 | Skill file installed | `skills/helloworld/SKILL.md` present |

**Notes:**
- The install command uses AskUserQuestion for scope selection. In non-interactive mode, the prompt must instruct the agent to use Project scope without asking.
- The agent calls `aegis-catalog.py install-prep` internally, then uses Write tool to create files.
- Codex may need `--sandbox workspace-write` or `--full-auto` for file writes.

### T5 — Verify Installed Package

Validate the installed files without going through the agent. These are filesystem checks.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T5.1 | Rule file frontmatter complete | `package`, `rule`, `version`, `tier`, `managed-by` all present |
| T5.2 | Original source description preserved | Source `description` field in frontmatter |
| T5.3 | Skill content correct | `skills/helloworld/SKILL.md` contains "helloworld" |

### T6 — Teardown

Remove the installed package and the coding-aegis skill. Clean up all state.

| Step | Description | Pass criteria |
|------|-------------|---------------|
| T6.1 | Remove installed helloworld files | `aegis--helloworld--*` and `skills/helloworld/` removed |
| T6.2 | Uninstall coding-aegis skill | CLI reports success or files removed |
| T6.3 | Remove marketplace registration | CLI reports success (Claude only) |
| T6.4 | Verify clean state | No coding-aegis artifacts remain |

## Secondary Tests (Fast Validation)

These validate the CLI helper in isolation. They run fast and catch regressions in aegis-catalog.py without needing an agent. They do NOT replace the primary flow.

### TS1 — Unit Tests (`tests/test_aegis_catalog.py`)

Python unittest suite testing aegis-catalog.py subcommands, YAML parser, frontmatter merge, and helpers. Run with `python3 -m unittest tests.test_aegis_catalog`.

### TS2 — Direct CLI Tests (in test scripts)

Quick validation of `aegis-catalog.py` resolve-catalog, list, show, install-prep, and status. These confirm the helper works before the agent-mediated tests depend on it.

### TS3 — Install Pipeline (`lib-install-test.sh`)

Direct filesystem test of install-prep → write → verify → status. Validates the install data flow without an agent.

## Tool-Specific Notes

### Claude Code
- `claude -p` requires `< /dev/null` to prevent stdin hang.
- `--allowedTools "Bash,Read,Write,Glob"` needed for install (Write for file creation).
- Plugin marketplace has a two-step model: marketplace add → plugin install.
- Skills discovered from `.claude/skills/` (project) or `~/.claude/skills/` (user).

### OpenAI Codex
- `codex exec` requires a git repo in the working directory.
- No marketplace CLI — skill installed by copying to `.agents/skills/`.
- `--ephemeral` prevents session persistence in tests.
- `-s workspace-write` or `--full-auto` needed for install commands that write files.
- `-o /dev/stdout` captures output for assertion.

### Google Gemini
- `gemini -p` is the non-interactive mode.
- `gemini skills link` for local install, `gemini skills install` for remote.
- Homebrew install emits keytar warnings — filter with `grep -v`.
- `-o text` for plain text output.
- Rate limits can cause retries and slower execution.

### Cursor
- TBD — research CLI availability.
- `.cursor-plugin/` marketplace manifest exists in repo.

## Test Script Structure

Each tool's test script should follow this order:

```
T0  — Prerequisites (installed + authenticated)
T1  — Install coding-aegis skill
TS2 — Quick CLI validation (optional, fast)
T2  — Use skill: list
T3  — Use skill: show helloworld
T4  — Use skill: install helloworld
T5  — Verify installed files
T6  — Teardown
```

## Test Package

All end-to-end tests use `helloworld` from `pkgs/optional/helloworld/`. This package:
- Has 1 rule + 1 skill (exercises both artifact types)
- Lives in the real catalog (available via remote install after push)
- Has no side effects (rule just adds "Hello, World!" greeting)
- Has predictable, assertable content

## Coverage Matrix

| Test | Claude | Codex | Gemini | Cursor |
|------|--------|-------|--------|--------|
| T0 (prerequisites) | done | done | done | TBD |
| T1 (install skill) | done | done | done | TBD |
| T2 (skill: list) | TODO | TODO | TODO | TBD |
| T3 (skill: show) | TODO | TODO | TODO | TBD |
| T4 (skill: install) | TODO | TODO | TODO | TBD |
| T5 (verify files) | TODO | TODO | TODO | TBD |
| T6 (teardown) | partial | partial | partial | TBD |
| TS1 (unit tests) | done | done | done | done |
| TS2 (direct CLI) | done | done | done | TBD |
| TS3 (install pipeline) | done | done | done | done |
