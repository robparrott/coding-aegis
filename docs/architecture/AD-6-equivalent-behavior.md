# AD-6: Equivalent behavior across tools

**Status**: Accepted

## Decision

Once `coding-aegis` is installed, all coding agents should behave equivalently — same governance capabilities, expressed in each tool's native UX idiom:

- **Claude Code**: Interactive SKILL.md — agent can browse, fetch, apply conversationally
- **Cursor**: Rich `.mdc` rule — agent follows governance instructions when relevant
- **Windsurf**: `.md` rule — Cascade follows governance instructions equivalently
- **Copilot**: `.instructions.md` — Copilot applies governance context to suggestions

## Runtime Shim Creation

The coding-aegis skill creates tool-specific files at runtime rather than requiring them to be checked in. For Claude Code, this means generating a `CLAUDE.md` containing `@AGENTS.md` — bridging the gap where Claude Code doesn't natively read AGENTS.md. See [AD-9](AD-9-agents-md-source-of-truth.md) for the full decision.

## Rationale

Teams using different coding agents should get equivalent governance enforcement. The content is the same; only the delivery format differs per tool.
