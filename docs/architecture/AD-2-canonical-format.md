# AD-2: Claude Code conventions as canonical format

**Status**: Accepted

## Decision

Package authors write artifacts in Claude Code's native layout (SKILL.md, agents/*.md, etc.) because it is the most expressive format. Adaptation tooling transforms these into Cursor, Windsurf, and Copilot native formats.

## Rationale

Claude Code's skill and agent format is the most expressive of the four tools. Writing canonical content in this format means no information is lost during adaptation — other formats are subsets.

## Override Mechanism

Optional `tools/` override directory for cases where automatic adaptation doesn't work:

```
{package-name}/
├── skills/
│   └── {skill-name}/SKILL.md     # canonical (Claude Code)
└── tools/
    ├── cursor/                    # when auto-adaptation doesn't work
    ├── windsurf/
    └── copilot/
```
