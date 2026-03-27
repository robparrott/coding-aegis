# Package Format Specification

## Package Layout

```
{package-name}/
├── pkg.yaml                    # manifest: name, version, description, author, artifacts
├── skills/                     # Claude Code SKILL.md files
│   └── {skill-name}/
│       └── SKILL.md
├── agents/                     # Agent definitions
│   └── {agent-name}.md
├── rules/                      # Rules / instructions content
│   └── {rule-name}.md
├── mcp/                        # MCP server configurations
│   └── servers.json
└── tools/                      # OPTIONAL: per-tool overrides
    ├── cursor/                 # when auto-adaptation doesn't work
    ├── windsurf/
    └── copilot/
```

## pkg.yaml

### Local package example

```yaml
name: code-review
version: 1.0.0
description: Structured code review with security and quality analysis
author: platform-team
artifacts:
  - type: skill
    path: skills/code-review/SKILL.md
  - type: agent
    path: agents/code-reviewer.md
  - type: rule
    path: rules/review-standards.md
```

### External package example

```yaml
name: superlinter-skill
version: 2.1.0
description: AI-assisted super linting with project-aware rule suggestions
author: linting-team

source:
  type: github
  repo: myorg/superlinter-skill
  ref: v2.1.0
  path: "."

artifacts:
  - type: skill
    path: skills/superlinter/SKILL.md
  - type: rule
    path: rules/lint-standards.md
```

### Fields

- **name**: unique across the catalog, lowercase/hyphens
- **version**: semver
- **description**: what this package provides (shown in catalog listings)
- **author**: team or individual who authored it
- **artifacts**: list of typed artifacts with relative paths within the package
- **source**: (optional) external reference — see below

### Source Field

The `source` field is optional. When present, it declares that the package content is hosted externally. When absent, the package is local (existing behavior).

| Field | Required | Description |
|-------|----------|-------------|
| `source.type` | Yes (if source present) | Source type. Only `github` initially. |
| `source.repo` | Yes (if type=github) | GitHub `owner/repo` identifier |
| `source.ref` | Yes | Git ref — tags strongly recommended for reproducibility |
| `source.path` | No | Subdirectory for monorepos. Default: `"."` |

When `source` is present:
- The local directory must contain only `pkg.yaml` (and optional README.md) — no `skills/`, `agents/`, `rules/`, `mcp/` directories
- Artifact paths are relative to the resolved `source.path` within the external repo
- `source.ref` should be an immutable tag or commit SHA. Branch names are discouraged.

See [AD-12](AD-12-external-package-references.md) for the full decision.

### Rules

- Tier is determined by directory location under `pkgs/` — never specified in `pkg.yaml` (see [AD-1](AD-1-package-catalog.md))
- Skills follow the [Agent Skills Specification](https://agentskills.io/specification): SKILL.md with YAML frontmatter (`name` 1-64 chars lowercase/hyphens, `description` 1-1024 chars)

## Artifact Types

| Type | Claude Code location | Description |
|------|---------------------|-------------|
| `skill` | `.claude/skills/{name}/SKILL.md` | Interactive agent skills |
| `agent` | `.claude/agents/{name}.md` | Specialized agent definitions |
| `rule` | Rendered into AGENTS.md or standalone | Behavioral rules / instructions |
| `mcp` | `.mcp.json` or `.claude/settings.json` | MCP server configurations |
| `plugin` | Plugin format | Bundled plugin artifacts |
