# Tier System Specification

## Tiers

| Tier | Directory | Enforcement | Bootstrap behavior |
|------|-----------|-------------|-------------------|
| **required** | `modules/required/` | Strict — CI can validate | Auto-installed, cannot opt out |
| **best-practices** | `modules/best-practices/` | Recommended | Installed by default, opt-out with justification |
| **optional** | `modules/optional/` | Opt-in | Listed in catalog, not installed by default |
| **goodies** | `modules/goodies/` | None | Available for browsing |

## Special Directories

`modules/bootstrap/` is a special directory — not a governance tier, but the entry point package(s) that enable everything else.

## Promotion

Promotion = move the package directory to a higher tier via PR. Git history provides full audit trail. CODEOWNERS gates reviews by tier.

## External Packages

External packages (those with a `source` field in `pkg.yaml`) use the identical tier system. The pointer in `modules/<tier>/` is what gets promoted. Tier-gate review for external packages includes inspecting the pinned external content at the declared `source.ref`. See [AD-12](AD-12-external-package-references.md).

See [AD-1](AD-1-package-catalog.md) for the catalog structure decision.
