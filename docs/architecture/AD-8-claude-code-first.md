# AD-8: Claude Code as reference implementation

**Status**: Accepted

## Decision

Claude Code is the reference implementation for all coding agent governance tooling. Other tool adapters (Cursor, Windsurf, Copilot) follow after the package format and core skill stabilize on Claude Code.

## Rationale

- Claude Code's skill/agent format is the most expressive (AD-2)
- Plugin marketplace provides the cleanest distribution mechanism currently available
- Iterating on one tool first reduces risk and accelerates learning
- Other tools can be added incrementally without rearchitecting
