# Tier System Specification

## Tiers

| Tier | Directory | Enforcement | Bootstrap behavior |
|------|-----------|-------------|-------------------|
| **required** | `pkgs/required/` | Strict — CI can validate | Auto-installed, cannot opt out |
| **best-practices** | `pkgs/best-practices/` | Recommended | Installed by default, opt-out with justification |
| **optional** | `pkgs/optional/` | Opt-in | Listed in catalog, not installed by default |
| **goodies** | `pkgs/goodies/` | None | Available for browsing |

## Special Directories

`pkgs/bootstrap/` is a special directory — not a governance tier, but the entry point package(s) that enable everything else.

## Promotion

Promotion = move the package directory to a higher tier via PR. Git history provides full audit trail. CODEOWNERS gates reviews by tier.

## External Packages

External packages (those with a `source` field in `pkg.yaml`) use the identical tier system. The pointer in `pkgs/<tier>/` is what gets promoted. Tier-gate review for external packages includes inspecting the pinned external content at the declared `source.ref`. See [AD-12](AD-12-external-package-references.md).

See [AD-1](AD-1-package-catalog.md) for the catalog structure decision.
