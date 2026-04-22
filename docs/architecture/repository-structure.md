# Repository Structure

## This repository

```
coding-aegis/
├── .claude-plugin/
│   └── marketplace.json                   # Claude Code marketplace registration
├── .cursor-plugin/
│   └── marketplace.json                   # Cursor Team Marketplace registration
├── .codex-plugin/
│   └── plugin.json                        # Codex plugin manifest
├── .claude/
│   └── settings.json
│
├── pkgs/                                  # THE CATALOG
│   ├── bootstrap/
│   │   └── coding-aegis/                  # The entry point skill
│   │       ├── pkg.yaml
│   │       ├── .cursor-plugin/
│   │       │   └── plugin.json            # Cursor plugin metadata
│   │       ├── skills/
│   │       │   └── coding-aegis/
│   │       │       └── SKILL.md           # Canonical skill definition
│   │       └── rules/                     # Bootstrap rules (per-tool variants)
│   ├── required/
│   │   └── <package>/
│   │       ├── pkg.yaml
│   │       ├── skills/
│   │       ├── agents/
│   │       └── rules/
│   ├── best-practices/
│   │   └── <package>/
│   │       ├── pkg.yaml
│   │       └── rules/
│   ├── optional/
│   └── goodies/
│
└── .gitignore
```

> **Note**: This repo contains no tool-specific config files (`.cursor/rules/`, `.gemini/rules/`, etc.). Those are installed into *target* repos by the coding-aegis skill — not used here. See [AGENTS.md](../../AGENTS.md).

## Installed paths in a target repository

When the coding-aegis skill installs a package into a target repo, it writes to tool-specific paths. The full canonical mapping is in [AD-14: Cross-tool artifact model](AD-14-cross-tool-artifact-model.md). Summary:

| Tool | Rules path | Skills path | Rule format |
|------|-----------|-------------|-------------|
| Claude Code | `.claude/rules/aegis--{pkg}--{rule}.md` | `.claude/skills/{name}/` | YAML frontmatter `.md` |
| Codex | `AGENTS.md` (`aegis:begin/end` sections) | `.agents/skills/{name}/` | Inline markdown |
| OpenCode | `AGENTS.md` (`aegis:begin/end` sections) | `.opencode/skills/{name}/` | Inline markdown |
| Cursor | `.cursor/rules/aegis--{pkg}--{rule}.mdc` | `.cursor/skills/{name}/` | YAML frontmatter `.mdc` |
| Gemini | `.gemini/rules/aegis--{pkg}--{rule}.md` | `.gemini/skills/{name}/` | YAML frontmatter `.md` |

## Related Decisions

- [AD-1: Package-based catalog](AD-1-package-catalog.md) — catalog organization
- [AD-2: Canonical format](AD-2-canonical-format.md) — why Claude Code layout is canonical
- [AD-4: Dual marketplace](AD-4-dual-marketplace.md) — marketplace manifest locations
- [AD-14: Cross-tool artifact model](AD-14-cross-tool-artifact-model.md) — full per-tool path mapping
