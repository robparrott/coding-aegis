# AD-5: Two installation targets

**Status**: Accepted

## Decision

Packages can be installed into:

- **Project repo** (`.claude/skills/`, `.cursor/rules/`, `.cursor/skills/`, `.agents/skills/`, etc.) — scoped to one repo
- **User home directory** (`~/.claude/skills/`, etc.) — available across all repos

## Skill installation targets

Skills are installed to tool-native locations per [AD-14](AD-14-cross-tool-artifact-model.md):

| Tool | Skill path |
|------|------------|
| Claude Code | `.claude/skills/{name}/SKILL.md` |
| Cursor | `.cursor/skills/{name}/SKILL.md` |
| Windsurf | `.agents/skills/{name}/SKILL.md` |
| Copilot | Not supported |

## Rule installation targets

Rules are installed with the `aegis--` prefix:

| Tool | Rule path |
|------|-----------|
| Claude Code | `.claude/rules/aegis--{name}.md` |
| Cursor | `.cursor/rules/aegis--{name}.mdc` |
| Windsurf | `.windsurf/rules/aegis--{name}.md` |
| Copilot | `.github/instructions/aegis--{name}.instructions.md` |

## Rationale

Project-scoped installation allows per-repo governance customization. User-scoped installation provides personal defaults and cross-repo consistency. Both are valid depending on the use case.
