# AD-16: Deterministic CLI scripts for coding-aegis skill

**Status**: Proposed

## Context

Every coding-aegis skill command (list, show, install, uninstall, status) is slow (8-24s per invocation) because the LLM acts as a middleman:

1. LLM reads SKILL.md (~470 lines of procedural instructions)
2. LLM calls `aegis-catalog.py` which returns JSON
3. LLM parses JSON, formats markdown output (or writes files for install/uninstall)

This architecture has three problems:

- **Slow**: LLM inference dominates. A `list` command that reads 5 YAML files and prints a table takes 8-20s because the LLM is interpreting instructions.
- **Inconsistent**: Claude, Codex, and Gemini interpret the same SKILL.md differently — wrong write methods, forgotten steps, incorrect paths.
- **Hard to test**: Integration tests require spinning up an LLM (`codex exec`) for every step, even for operations that are purely deterministic (copy files, format tables).

The `uninstall-prep` subcommand already writes to AGENTS.md directly (aegis-catalog.py line 643-656), proving the Python script can safely perform file I/O. The remaining commands stop short of this, delegating all output formatting and file writes to the LLM unnecessarily.

## Decision

Replace the monolithic `aegis-catalog.py` with dedicated Python scripts — one per command — that each perform their operation end-to-end and print final markdown to stdout. SKILL.md becomes a trivial dispatcher: parse the command name, run the corresponding script, print its output verbatim.

### Scripts

| Script | Reads catalog? | Does file I/O? | Output |
|--------|---------------|----------------|--------|
| `aegis-list.py` | Yes | No | Markdown catalog table |
| `aegis-show.py` | Yes | No | Markdown package detail |
| `aegis-install.py` | Yes | Yes (writes) | Markdown install summary |
| `aegis-uninstall.py` | No | Yes (deletes) | Markdown uninstall summary |
| `aegis-status.py` | Yes | No | Markdown status table |
| `detect_tool.py` | No | No | JSON (unchanged) |

### Catalog resolution

The skill is installed remotely (e.g. `~/.codex/skills/coding-aegis/`). The `pkgs/` catalog is not at the script's location. Scripts that need catalog data perform a sparse `git clone` of just `pkgs/` into `.coding-aegis-catalog/` in the current working directory, reused until a 30-second TTL expires.

```
git clone --depth 1 --filter=blob:none --sparse <repo> .coding-aegis-catalog
git -C .coding-aegis-catalog sparse-checkout set pkgs/
```

A `--catalog PATH` flag overrides this for development and testing.

### Shared library

Common functions (YAML parsing, frontmatter handling, tool detection, catalog resolution, tier scanning) are extracted into `aegis_lib.py`, imported by all scripts.

## Consequences

- All read-only commands (list, show, status) drop from 8-20s to <1s (cached catalog)
- Install/uninstall drop from 16-24s to <2s
- SKILL.md shrinks from ~470 lines to ~150 lines
- Integration tests can validate install/uninstall via direct Python calls (no LLM)
- `aegis-catalog.py` is deleted — the new scripts replace it completely
- Each script is independently testable and debuggable

## References

- AD-3: Two-layer skill architecture
- AD-15: Single-source artifacts with install-time adaptation
