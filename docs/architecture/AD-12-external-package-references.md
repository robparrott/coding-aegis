# AD-12: External package references (registry pointers)

**Status**: Proposed

## Context

The catalog currently requires all package content to live physically within `pkgs/<tier>/<name>/`. Teams maintaining skills in their own repos have no way to register them in the governance catalog without duplicating content. This limits adoption — teams want to maintain skills in their own repos with their own CI, versioning, and release lifecycle.

## Decision

Extend `pkg.yaml` with an optional `source` field that turns the local package entry into a **registry pointer** — a lightweight reference to content hosted in an external GitHub repo. The pointer lives in the catalog (subject to tier gates and CODEOWNERS), but artifacts are fetched from the external repo at install time.

## Schema

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

| Field | Required | Description |
|-------|----------|-------------|
| `source` | No | When present, declares external content origin. When absent, package is local (existing behavior). |
| `source.type` | Yes (if source present) | Source type. Only `github` initially. Extensible to `gitlab`, `url` later. |
| `source.repo` | Yes (if type=github) | GitHub `owner/repo` identifier. |
| `source.ref` | Yes | Git ref to fetch. Tags strongly recommended for reproducibility. |
| `source.path` | No | Subdirectory within the external repo containing the package content. Defaults to `"."`. Useful for monorepos. |

### Local directory contents

For an external package, the `pkgs/<tier>/<name>/` directory contains ONLY:

```
pkgs/optional/superlinter-skill/
├── pkg.yaml          # The pointer manifest (with source field)
└── README.md         # Optional: rationale, review notes
```

No `skills/`, `agents/`, `rules/`, or other artifact directories. If any artifact directories are present locally alongside a `source` field, that is a validation error.

Artifact paths in the `artifacts` list are relative to the resolved package root (`source.path` within the external repo).

## Fetch Strategy

**Fetch at install time, no persistent cache.**

1. Skill reads `pkg.yaml` from `pkgs/<tier>/<name>/`
2. Extracts `source.repo`, `source.ref`, `source.path`
3. Fetches content via GitHub archive API (preferred) or shallow clone (fallback)
4. Validates that all declared artifact paths exist in the fetched content
5. Installs artifacts using the same logic as local packages
6. Cleans up temporary fetched content

**Catalog browsing does not fetch.** Listing available packages reads only local `pkg.yaml` metadata. An `[external]` indicator is shown in catalog listings.

**Version checking** compares the `version` field in the local `pkg.yaml` against installed frontmatter. The skill does NOT poll external repos. Version updates happen when the catalog maintainer explicitly bumps the pointer via PR.

## Governance

The pointer `pkg.yaml` lives in `pkgs/<tier>/<name>/`. Existing CODEOWNERS gates apply:

- **Adding** an external package requires CODEOWNERS approval for that tier
- **Promoting** is a directory move PR, gated by the higher tier's CODEOWNERS
- **Updating the pinned ref** modifies `pkg.yaml`, requiring that tier's CODEOWNERS approval

### Reviewer responsibilities

1. **Source legitimacy**: Is `source.repo` an org-owned or trusted repo?
2. **Ref pinning**: Is `source.ref` a specific tag or SHA (not `main`)?
3. **Content review**: Inspect the external repo at the pinned ref
4. **Artifact declarations**: Do they accurately describe the external content?

### Trust boundary

The catalog vouches for external content at a specific point in time (the pinned ref). External repo changes don't affect the catalog until someone explicitly updates `source.ref` and that change passes review. Analogous to Go module commit pinning or Terraform provider version locks.

## Version Pinning

| Ref type | Recommended? | Rationale |
|----------|-------------|-----------|
| Semver tag (e.g., `v2.1.0`) | Strongly recommended | Immutable, clear version alignment |
| Full commit SHA | Acceptable | Most immutable, but opaque |
| Branch name (e.g., `main`) | Discouraged | Mutable — violates curation model |
| Partial SHA | Not allowed | Ambiguous |

The `version` field and `source.ref` should be semantically aligned. CI warns if they appear misaligned.

### Update workflow

1. External team tags a new release in their repo
2. Catalog maintainer submits PR updating `version` and `source.ref`
3. CODEOWNERS for that tier reviews and approves
4. Users see the version bump and can reinstall

No automation pulls new versions into the catalog. All bumps are deliberate, reviewed changes.

## CI Validation

| Check | Severity | Description |
|-------|----------|-------------|
| `source` field schema | Error | If present, `type`, `repo`, and `ref` must be valid |
| No local artifacts with `source` | Error | No `skills/`, `agents/`, `rules/`, `mcp/` dirs alongside `source` |
| Ref is not a mutable branch | Warning | Warn if `source.ref` looks like a branch name |
| Version-ref alignment | Warning | Warn if `version` and `source.ref` appear misaligned |
| External repo accessibility | Skipped in CI | No network fetch in CI — schema-only validation |

## Monorepo Example

```yaml
name: team-alpha-review
version: 1.0.0
description: Team Alpha's specialized code review workflow
author: team-alpha

source:
  type: github
  repo: myorg/team-alpha-tools
  ref: skills-v1.0.0
  path: packages/code-review

artifacts:
  - type: skill
    path: skills/team-review/SKILL.md
```

Artifact paths are relative to `packages/code-review/` within the external repo.

## Consequences

- External teams can maintain skills in their own repos with their own CI and release lifecycle
- Catalog remains curated — pointers go through the same review as local packages
- No dependency resolution added (consistent with AD-7)
- Network dependency at install time (not at browse/list time)
- Version drift is managed — external changes don't propagate without explicit catalog update

## Related Decisions

- [AD-1: Package-based catalog](AD-1-package-catalog.md) — catalog organization
- [AD-2: Canonical format](AD-2-canonical-format.md) — applies to external content too
- [AD-7: No dependency resolution](AD-7-no-dependency-resolution.md) — source is a fetch target, not a dependency
