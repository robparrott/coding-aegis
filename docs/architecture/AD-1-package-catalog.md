# AD-1: Package-based catalog (yum/rpm model)

**Status**: Accepted

## Decision

Packages are the unit of distribution. The `pkgs/` directory is organized by subdirectories, following the yum/rpm repository model. Each package is a self-contained, named, versioned collection of artifacts (skills, agents, rules, MCP configs, etc.) authored by teams or individuals and curated into this repo via PR.

## Structure

```
pkgs/
├── bootstrap/             # entry point — the coding-aegis skill
│   └── coding-aegis/
├── required/              # non-negotiable, auto-installed
│   └── governance-core/
├── best-practices/        # installed by default, opt-out with justification
│   └── code-review/
├── optional/              # available in catalog, opt-in
│   └── perf-profiling/
└── goodies/               # community contributions, experimental
    └── fun-commit-msgs/
```

## Consequences

- **Tier = directory location.** Promotion is moving a directory via PR. Git history is the audit trail.
- No tier metadata in `pkg.yaml` — the directory location is authoritative.
- CODEOWNERS gates reviews by tier for promotion control.
