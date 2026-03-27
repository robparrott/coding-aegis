# AD-5: Two installation targets

**Status**: Accepted

## Decision

Packages can be installed into:

- **Project repo** (`.claude/skills/`, `.cursor/rules/`, etc.) — scoped to one repo
- **User home directory** (`~/.claude/skills/`, etc.) — available across all repos

## Rationale

Project-scoped installation allows per-repo governance customization. User-scoped installation provides personal defaults and cross-repo consistency. Both are valid depending on the use case.
