# Repository Structure

```
coding-aegis/
├── .claude-plugin/
│   └── marketplace.json                   # Claude Code marketplace registration
├── .cursor-plugin/
│   └── marketplace.json                   # Cursor Team Marketplace registration
├── .claude/
│   └── settings.json
├── .cursor/rules/governance.mdc           # Self-dogfooding
├── .windsurf/rules/governance.md          # Self-dogfooding
├── .github/
│   ├── copilot-instructions.md            # Self-dogfooding
│   ├── workflows/validate-catalog.yml     # CI: validate pkg.yaml, structure
│   └── CODEOWNERS                         # Tier promotion gates
│
├── pkgs/                                  # THE CATALOG
│   ├── bootstrap/
│   │   └── coding-aegis/                  # The entry point skill
│   │       ├── pkg.yaml
│   │       ├── .cursor-plugin/
│   │       │   └── plugin.json            # Cursor plugin metadata
│   │       ├── skills/
│   │       │   └── coding-aegis/
│   │       │       └── SKILL.md           # Claude Code (canonical)
│   │       └── tools/
│   │           └── cursor/
│   │               └── rules/
│   │                   └── coding-aegis.mdc  # Cursor-native override
│   ├── required/
│   │   └── governance-core/
│   │       ├── pkg.yaml
│   │       ├── skills/
│   │       ├── agents/
│   │       └── rules/
│   ├── best-practices/
│   │   └── code-review/
│   │       ├── pkg.yaml
│   │       ├── skills/
│   │       └── rules/
│   ├── optional/
│   │   └── ...
│   └── goodies/
│       └── ...
│
├── quickstarts/                           # Project scaffolding packages
│   ├── helm-docker/pkg.yaml
│   ├── micronaut-java/pkg.yaml
│   ├── typescript/pkg.yaml
│   └── python/pkg.yaml
│
└── .gitignore
```

## Related Decisions

- [AD-1: Package-based catalog](AD-1-package-catalog.md) — catalog organization
- [AD-2: Canonical format](AD-2-canonical-format.md) — why Claude Code layout is canonical
- [AD-4: Dual marketplace](AD-4-dual-marketplace.md) — marketplace manifest locations
