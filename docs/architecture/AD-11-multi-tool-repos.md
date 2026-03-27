# AD-11: Multi-tool repository support

**Status**: Proposed (open question)

## Context

A single repository may be used by developers on different coding agent tools simultaneously. When the coding-aegis skill installs governance rules, it needs to decide which tool directories to populate.

## Open Questions

1. **Detection**: How does the skill know which tools are in use? Presence of `.cursor/`, `.windsurf/`, `.claude/` directories? Config files? Or explicit user declaration?

2. **Install scope**: Should the skill install to all detected tools, only the current tool, or ask the developer?

3. **Consistency**: If one developer uses Claude Code and another uses Cursor, how do we ensure both get the same governance content? Who maintains the tool-specific directories?

4. **Git hygiene**: Should tool-specific directories be committed (shared with team) or gitignored (local to each developer)?

5. **Drift**: If tool A's rules are committed but tool B's aren't, new developers on tool B get no governance until they run the skill.

## Candidate Approaches

### A: Install all detected tools
Detect tool presence by directory/config markers. Install governance rules to all detected tool locations. All files committed to git.

Pro: Everyone gets governance regardless of tool. Con: Repo accumulates directories for tools some developers don't use.

### B: Install current tool only, document in AGENTS.md
Install only to the active tool's directory. AGENTS.md lists what should be installed and provides instructions for other tools.

Pro: Clean — only what's needed. Con: Relies on developers running the skill for their tool.

### C: Install all tools always
Always install to all four tool directories regardless of detection. Treat governance files like CI config — present even if not all tools are in use.

Pro: No drift, no detection logic. Con: Noise in repos that only use one tool.

### D: Configurable per-repo
A `.coding-aegis.yaml` manifest in the target repo declares which tools to target:

```yaml
tools:
  - claude-code
  - cursor
```

Pro: Explicit, no guessing. Con: Another config file.

## Decision

TBD — to be resolved through discussion and prototyping.

## Related Decisions

- [AD-10: Modular guidance files](AD-10-modular-guidance-files.md) — file composition model
- [AD-6: Equivalent behavior across tools](AD-6-equivalent-behavior.md) — all tools should behave equivalently
