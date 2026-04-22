# coding-aegis Skill Specification

The primary interface to the governance catalog. Lives in `modules/bootstrap/coding-aegis/`.

## Capabilities

- **Browse catalog** — list available packages organized by tier
- **Install packages** — fetch and install individual packages or entire tiers
- **Install external packages** — fetch content from referenced GitHub repos at install time
- **Show status** — what's installed locally vs what's available
- **Check for updates** — compare installed versions to catalog
- **Apply quickstarts** — scaffold new projects from quickstart packages
- **Show governance info** — what's required, what tiers mean, policies
- **Guide new users** — explain what's available, recommend a starting point

## Tool-Specific Behavior

The skill detects the active coding tool at runtime via `detect_tool.py` and adapts its behavior accordingly — installing rules to the correct path, using the right artifact format, and selecting the appropriate scope directory. The detection and per-tool path mappings are specified in [AD-14: Cross-tool artifact model](AD-14-cross-tool-artifact-model.md).

## Interaction Model

The skill communicates dynamically — the catalog will change over time, so the skill reads from the governance repo at runtime rather than hardcoding what's available.

## Related Decisions

- [AD-3: Two-layer skill architecture](AD-3-two-layer-skill.md)
- [AD-4: Dual marketplace registration](AD-4-dual-marketplace.md)
- [AD-6: Equivalent behavior across tools](AD-6-equivalent-behavior.md)
- [AD-12: External package references](AD-12-external-package-references.md)
