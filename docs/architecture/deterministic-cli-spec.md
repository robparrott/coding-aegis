# Design Spec: Deterministic CLI Scripts

Implements [AD-16](AD-16-deterministic-skill-cli.md).

## Motivation: measured cost of LLM-mediated skill commands

The following data was collected on 2026-04-03 by running `tests/test-codex-skill-install.sh` against Codex CLI 0.118.0 (gpt-5.4). Every skill command is routed through `codex exec`, which means the LLM reads SKILL.md (~470 lines), calls `aegis-catalog.py` (JSON output), parses the JSON, and formats or acts on the result. The Python helper itself finishes in <100ms for every command; the rest is LLM inference overhead.

### Per-step timing

| Phase | Step | Wall time | What the LLM actually did |
|-------|------|-----------|---------------------------|
| 1 | Auth check (`AUTH_OK`) | 7s | Echo a string |
| 3 | `$skill-installer` (GitHub clone) | 13s | Ran a Python install script — acceptable |
| 4.2 | `detect-tool` (skill command) | 11s | Read SKILL.md, ran `python3 detect_tool.py`, formatted 2-line JSON |
| 4.3 | `list` | 11s | Read SKILL.md, ran `aegis-catalog.py list`, reformatted JSON → markdown table |
| 4.4 | `show helloworld` | 14s | Read SKILL.md, ran `aegis-catalog.py show`, reformatted JSON → markdown |
| 5.1 | `install helloworld` | 47s | Read SKILL.md, ran `install-prep`, parsed JSON, wrote 2 files + AGENTS.md |
| 5.5 | `$helloworld` (invoke skill) | 9s | Read a 6-line SKILL.md, printed a sentence |
| 6.1 | `uninstall helloworld` | **60s TIMEOUT** | Read SKILL.md, ran `uninstall-prep`, started but never completed `rm -rf` |

**Total wall time: 2m52s** for a test that writes 2 files and deletes them.

### Failures (3 of 30 assertions)

All three failures stem from the uninstall timeout:

1. `TIMEOUT after 60s: skill uninstall` — the LLM could not complete the uninstall within the 60s budget
2. `uninstall — no errors` — timeout output contained error indicators
3. `helloworld skill dir removed` — `.agents/skills/helloworld/` still existed because `rm -rf` never ran

Note: `uninstall-prep` did successfully strip the AGENTS.md rule section (Python-side I/O that runs before the LLM needs to act), confirming that Python-side file operations work. The LLM simply ran out of time before executing the subsequent `rm -rf` shell command.

### Analysis

The LLM adds no value in any of these steps. Every command follows the same pattern:

1. Read SKILL.md instructions (~470 lines of procedural guidance)
2. Call a Python script that returns JSON
3. Parse the JSON
4. Either format it as markdown (read commands) or write files (install/uninstall)

Steps 2-4 are fully deterministic. The Python script already computes every path, every file content, every frontmatter value. The LLM is a slow, expensive, unreliable middleman that converts JSON to markdown or JSON to file writes — tasks that Python handles in milliseconds.

### Expected improvement

With deterministic scripts that output final markdown and perform their own file I/O:

| Step | Current | Expected | Speedup |
|------|---------|----------|---------|
| detect-tool | 11s | <0.1s | ~100x |
| list | 11s | <0.5s (cached catalog) | ~20x |
| show | 14s | <0.5s (cached catalog) | ~30x |
| install | 47s | <1s | ~50x |
| uninstall | 60s (timeout) | <0.5s | eliminates failure |
| **Full test** | **2m52s** | **~30s** (mostly `$skill-installer` clone) | ~6x |

The only steps that genuinely require an LLM are Phase 3 (`$skill-installer` — agent-mediated GitHub install) and Phase 5.5 (invoking a skill that produces natural language). Everything else becomes a direct `python3` call.

---

## File layout

All files in `modules/bootstrap/coding-aegis/skills/coding-aegis/`:

```
aegis_lib.py          # Shared library
aegis-list.py         # /coding-aegis list
aegis-show.py         # /coding-aegis show <name>
aegis-install.py      # /coding-aegis install <name>
aegis-uninstall.py    # /coding-aegis uninstall <name>
aegis-status.py       # /coding-aegis status
detect_tool.py        # /coding-aegis detect-tool (unchanged)
SKILL.md              # Dispatcher (rewritten)
```

Delete: `aegis-catalog.py`

## aegis_lib.py

### Constants

```python
GITHUB_REPO = "https://github.com/robparrott/coding-aegis.git"
CACHE_DIR = ".coding-aegis-catalog"
CACHE_TTL = 30  # seconds

TIERS = ["required", "best-practices", "optional", "goodies"]
ARTIFACT_TYPE_ORDER = ["rule", "skill", "agent", "mcp", "plugin"]

TOOL_PATHS = {
    "claude":   {"scope_base": ".claude",   "skills_dir": "skills"},
    "gemini":   {"scope_base": ".gemini",   "skills_dir": "skills", "skills_base": ".gemini"},
    "codex":    {"scope_base": ".agents",   "skills_dir": ".agents/skills", "skills_base": "."},
    "cursor":   {"scope_base": ".cursor",   "skills_dir": "skills", "rule_ext": ".mdc"},
    "opencode": {"scope_base": ".opencode", "skills_dir": "skills",
                 "user_scope_base": ".config/opencode"},
    "copilot":  {"scope_base": ".github",   "skills_dir": "skills"},
}
```

### ensure_catalog(catalog_override=None) -> Path

1. If `catalog_override` is set, return `Path(catalog_override)` directly.
2. Check `CWD/.coding-aegis-catalog/.cache_ts`:
   - If exists and `time.time() - float(contents) < CACHE_TTL` → return `CWD/.coding-aegis-catalog/modules`
3. If `.coding-aegis-catalog/` exists but stale:
   - `subprocess.run(["git", "-C", cache_dir, "pull", "--ff-only"], ...)`
   - Write current timestamp to `.cache_ts`
4. If no cache dir:
   - `subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", GITHUB_REPO, cache_dir], ...)`
   - `subprocess.run(["git", "-C", cache_dir, "sparse-checkout", "set", "modules/"], ...)`
   - Write current timestamp to `.cache_ts`
5. Return `Path(cache_dir) / "modules"`

### Carried over from aegis-catalog.py

These functions are extracted unchanged:

- `parse_simple_yaml(text) -> dict`
- `parse_frontmatter(text) -> (dict, str)`
- `render_frontmatter(fm_dict, body) -> str`
- `merge_frontmatter(source_fm, managed_keys) -> dict`
- `scan_tier(catalog, tier) -> list[dict]`
- `compute_artifact_summary(artifacts) -> str`
- `compute_target_filename(pkg_name, artifact) -> str`
- `detect_tool() -> str` (imports from detect_tool.py)

### New helper: resolve_scope_base(tool, scope) -> Path

```python
def resolve_scope_base(tool, scope):
    cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])
    if scope == "user":
        return Path.home() / cfg["scope_base"]
    return Path.cwd() / cfg["scope_base"]
```

### New helper: find_package(catalog, name) -> (dict, Path) | None

Searches all tiers + bootstrap for a package by name. Returns `(pkg_data, pkg_dir)` or `None`.

## aegis-list.py

```
Usage: aegis-list.py [--catalog PATH]
```

1. `catalog = ensure_catalog(args.catalog)`
2. For each tier in `TIERS`, call `scan_tier(catalog, tier)`
3. Print markdown:

```markdown
## coding-aegis catalog

### required
(none)

### optional
| Package | Version | Artifacts | Description |
|---------|---------|-----------|-------------|
| helloworld | 1.0.0 | 1 rule, 1 skill | Hello world test... |
```

Exit 0.

## aegis-show.py

```
Usage: aegis-show.py <name> [--catalog PATH]
```

1. `catalog = ensure_catalog(args.catalog)`
2. `pkg, pkg_dir = find_package(catalog, name)` — exit 1 if not found
3. Read `README.md` from `pkg_dir` if it exists
4. Print markdown with metadata table + artifacts table + README body

Exit 0.

## aegis-install.py

```
Usage: aegis-install.py <name> --scope <project|user> [--catalog PATH] [--tool TOOL]
```

1. `catalog = ensure_catalog(args.catalog)`
2. `tool = args.tool or detect_tool()`
3. `pkg, pkg_dir = find_package(catalog, name)` — exit 1 if not found
4. `scope_base = resolve_scope_base(tool, args.scope)`
5. For each artifact in `pkg["artifacts"]`:
   - **rule/agent, tool=codex or opencode**: Build `aegis:begin`/`aegis:end` section, append to `AGENTS.md`
   - **rule/agent, other tools**: Merge frontmatter, write to `{scope_base}/rules/aegis--{pkg}--{rule}.md`
   - **skill**: Copy entire skill directory to `{skills_dir}/{skill_name}/`
6. For Claude + project scope: rebuild `## Installed Governance Rules` table in `AGENTS.md`
7. Print markdown install summary

Exit 0.

### File write details

- `os.makedirs(parent, exist_ok=True)` for all directories
- `Path(install_path).write_text(content)` for all files
- AGENTS.md appends: read existing, check for existing section (replace if found, append if not), write back
- Idempotent: running install twice produces the same result

## aegis-uninstall.py

```
Usage: aegis-uninstall.py <name> [--scope PATH] [--tool TOOL]
```

1. `tool = args.tool or detect_tool()`
2. Scan for installed artifacts (same logic as current `uninstall-prep`)
3. Delete files with `os.unlink()`, directories with `shutil.rmtree()`
4. For Codex/OpenCode: strip `aegis:begin/end` sections from `AGENTS.md`
5. For Claude: rebuild or remove governance table in `AGENTS.md`
6. Print markdown uninstall summary

Exit 0. Does not need catalog access.

## aegis-status.py

```
Usage: aegis-status.py [--catalog PATH] [--scope PATH...]
```

1. `catalog = ensure_catalog(args.catalog)`
2. Scan scope directories for `aegis--*` files and skill directories
3. Cross-reference installed versions with catalog versions
4. Print markdown status table

Exit 0.

## SKILL.md rewrite

~150 lines. Structure:

```markdown
---
name: coding-aegis
description: Browse, install, and manage coding agent governance packages.
---

# coding-aegis

## Command Dispatch

| Input | Script |
|-------|--------|
| list | aegis-list.py |
| show <name> | aegis-show.py <name> |
| install <name> | aegis-install.py <name> |
| uninstall <name> | aegis-uninstall.py <name> |
| status | aegis-status.py |
| detect-tool | detect_tool.py |
| validate-install | aegis-validate-install.py |
| *(no input)* | aegis-list.py (default) |

## Execution

For all commands except `install`:
1. Run the script: `python3 "{skill-dir}/<script>" [args]`
2. Print stdout verbatim.

For `install`:
1. If scope not specified in user input, ask: Project or User?
2. Run: `python3 "{skill-dir}/aegis-install.py" <name> --scope <project|user>`
3. Print stdout verbatim.
4. Remind user to restart their coding tool.

## Error handling

If any script exits non-zero, print stderr verbatim. Do not improvise or retry.
```

## Test plan

### tests/test-cli-install.sh (new, no LLM)

```bash
# Phase 1: aegis-list.py outputs correct markdown
# Phase 2: aegis-show.py outputs correct package detail
# Phase 3: aegis-install.py --tool claude writes correct files
# Phase 4: aegis-install.py --tool codex writes AGENTS.md sections
# Phase 5: Idempotent re-install
# Phase 6: aegis-uninstall.py --tool claude removes files
# Phase 7: aegis-uninstall.py --tool codex strips AGENTS.md
# Phase 8: Cleanup
```

Runs in <5s total.

### tests/unit/test_aegis_lib.py (new, unit tests)

Test `aegis_lib.py` functions:
- `parse_simple_yaml`, `parse_frontmatter`, `render_frontmatter`
- `merge_frontmatter`, `scan_tier`, `compute_artifact_summary`
- `find_package`, `resolve_scope_base`
- `ensure_catalog` (with `--catalog` override, skipping git)
