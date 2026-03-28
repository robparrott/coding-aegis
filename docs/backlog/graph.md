# Dependency Graph

Auto-generated from `bd graph --all --compact`.

```

📊 Dependency graph for coding-aegis-cdb (29 issues, 5 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-b5z ● P2 Phase 2: coding-aegis Skill (Claude Code)
  │   ├── ○ coding-aegis-b5z.2 ● P2 Test Claude Code bootstrap flow
  │   ├── ○ coding-aegis-b5z.3 ● P2 Implement skill catalog browsing
  │   └── ○ coding-aegis-b5z.4 ● P2 Implement package installation
  ├── ○ coding-aegis-b5z.2 ● P2 Test Claude Code bootstrap flow
  ├── ○ coding-aegis-b5z.3 ● P2 Implement skill catalog browsing
  └── ○ coding-aegis-b5z.4 ● P2 Implement package installation

  LAYER 1
  ├── ○ coding-aegis-4d6 ● P2 Phase 4: Renderers / Adaptation
  │   ├── ○ coding-aegis-4d6.1 ● P2 Implement base renderer interface
  │   ├── ○ coding-aegis-4d6.2 ● P2 Implement Cursor adapter
  │   ├── ○ coding-aegis-4d6.3 ● P2 Implement Windsurf adapter
  │   └── ○ coding-aegis-4d6.4 ● P2 Implement Copilot adapter
  ├── ○ coding-aegis-4d6.1 ● P2 Implement base renderer interface
  ├── ○ coding-aegis-4d6.2 ● P2 Implement Cursor adapter
  ├── ○ coding-aegis-4d6.3 ● P2 Implement Windsurf adapter
  ├── ○ coding-aegis-4d6.4 ● P2 Implement Copilot adapter
  ├── ○ coding-aegis-cr7 ● P2 Phase 6: Seed Packages & Quickstarts
  │   ├── ○ coding-aegis-cr7.1 ● P2 Create governance-core required package
  │   ├── ○ coding-aegis-cr7.2 ● P2 Create stub packages per tier
  │   └── ○ coding-aegis-cr7.3 ● P2 Create quickstart packages
  ├── ○ coding-aegis-cr7.1 ● P2 Create governance-core required package
  ├── ○ coding-aegis-cr7.2 ● P2 Create stub packages per tier
  └── ○ coding-aegis-cr7.3 ● P2 Create quickstart packages

  LAYER 2
  ├── ○ coding-aegis-410 ● P2 Phase 5: CLI Tooling
  │   ├── ○ coding-aegis-410.1 ● P2 Catalog structure validation command
  │   ├── ○ coding-aegis-410.2 ● P2 List packages by tier command
  │   ├── ○ coding-aegis-410.3 ● P2 Render package for target tool command
  │   └── ○ coding-aegis-410.4 ● P2 Promote package between tiers command
  ├── ○ coding-aegis-410.1 ● P2 Catalog structure validation command
  ├── ○ coding-aegis-410.2 ● P2 List packages by tier command
  ├── ○ coding-aegis-410.3 ● P2 Render package for target tool command
  └── ○ coding-aegis-410.4 ● P2 Promote package between tiers command

  LAYER 3
  ├── ○ coding-aegis-gmk ● P2 Phase 7: CI & Validation
  │   ├── ○ coding-aegis-gmk.1 ● P2 GitHub Actions workflow for catalog validation
  │   ├── ○ coding-aegis-gmk.2 ● P2 Integration tests
  │   └── ○ coding-aegis-gmk.3 ● P2 Windsurf + Copilot bootstrap mechanisms
  ├── ○ coding-aegis-gmk.1 ● P2 GitHub Actions workflow for catalog validation
  ├── ○ coding-aegis-gmk.2 ● P2 Integration tests
  └── ○ coding-aegis-gmk.3 ● P2 Windsurf + Copilot bootstrap mechanisms

  LAYER 4
  ├── ○ coding-aegis-cdb ● P2 Phase 8: External Package References
  │   ├── ○ coding-aegis-cdb.1 ● P2 Extend pkg.yaml schema with source field
  │   ├── ○ coding-aegis-cdb.2 ● P2 Update CI validation for source field
  │   ├── ○ coding-aegis-cdb.3 ● P2 Implement external fetch in coding-aegis skill
  │   ├── ○ coding-aegis-cdb.4 ● P2 Artifact validation for fetched external content
  │   ├── ○ coding-aegis-cdb.5 ● P2 Create example external package pointer
  │   └── ○ coding-aegis-cdb.6 ● P2 Update docs for external references
  ├── ○ coding-aegis-cdb.1 ● P2 Extend pkg.yaml schema with source field
  ├── ○ coding-aegis-cdb.2 ● P2 Update CI validation for source field
  ├── ○ coding-aegis-cdb.3 ● P2 Implement external fetch in coding-aegis skill
  ├── ○ coding-aegis-cdb.4 ● P2 Artifact validation for fetched external content
  ├── ○ coding-aegis-cdb.5 ● P2 Create example external package pointer
  └── ○ coding-aegis-cdb.6 ● P2 Update docs for external references

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-wpi (7 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-wpi ● P2 Phase 3: Cursor Bootstrap
  │   ├── ○ coding-aegis-wpi.1 ● P2 Create .cursor-plugin/marketplace.json
  │   ├── ○ coding-aegis-wpi.2 ● P2 Create coding-aegis Cursor plugin.json
  │   ├── ○ coding-aegis-wpi.3 ● P2 Create Cursor-native coding-aegis.mdc rule
  │   ├── ○ coding-aegis-wpi.4 ● P2 Register GitHub Enterprise App at Cursor dashboard
  │   ├── ○ coding-aegis-wpi.5 ● P2 Import repo into Cursor Team Marketplace
  │   └── ○ coding-aegis-wpi.6 ● P2 Test Cursor marketplace install flow
  ├── ○ coding-aegis-wpi.1 ● P2 Create .cursor-plugin/marketplace.json
  ├── ○ coding-aegis-wpi.2 ● P2 Create coding-aegis Cursor plugin.json
  ├── ○ coding-aegis-wpi.3 ● P2 Create Cursor-native coding-aegis.mdc rule
  ├── ○ coding-aegis-wpi.4 ● P2 Register GitHub Enterprise App at Cursor dashboard
  ├── ○ coding-aegis-wpi.5 ● P2 Import repo into Cursor Team Marketplace
  └── ○ coding-aegis-wpi.6 ● P2 Test Cursor marketplace install flow

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-avj (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-avj ● P2 Augment beads-sync skill with issue-tracking work…

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-3m9 (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-3m9 ● P2 Resolve multi-tool repository support (AD-11)
```

## Task Index

- [`coding-aegis-cdb`](phase-8-external-package-references.md)
- [`coding-aegis-b5z`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.2`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.3`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.4`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-4d6`](phase-4-renderers---adaptation.md)
- [`coding-aegis-4d6.1`](phase-4-renderers---adaptation.md)
- [`coding-aegis-4d6.2`](phase-4-renderers---adaptation.md)
- [`coding-aegis-4d6.3`](phase-4-renderers---adaptation.md)
- [`coding-aegis-4d6.4`](phase-4-renderers---adaptation.md)
- [`coding-aegis-cr7`](phase-6-seed-packages-&-quickstarts.md)
- [`coding-aegis-cr7.1`](phase-6-seed-packages-&-quickstarts.md)
- [`coding-aegis-cr7.2`](phase-6-seed-packages-&-quickstarts.md)
- [`coding-aegis-cr7.3`](phase-6-seed-packages-&-quickstarts.md)
- [`coding-aegis-410`](phase-5-cli-tooling.md)
- [`coding-aegis-410.1`](phase-5-cli-tooling.md)
- [`coding-aegis-410.2`](phase-5-cli-tooling.md)
- [`coding-aegis-410.3`](phase-5-cli-tooling.md)
- [`coding-aegis-410.4`](phase-5-cli-tooling.md)
- [`coding-aegis-gmk`](phase-7-ci-&-validation.md)
- [`coding-aegis-gmk.1`](phase-7-ci-&-validation.md)
- [`coding-aegis-gmk.2`](phase-7-ci-&-validation.md)
- [`coding-aegis-gmk.3`](phase-7-ci-&-validation.md)
- [`coding-aegis-cdb.1`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.2`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.3`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.4`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.5`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.6`](phase-8-external-package-references.md)
- [`coding-aegis-wpi`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.1`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.2`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.3`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.4`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.5`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.6`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-avj`](standalone.md)
- [`coding-aegis-3m9`](standalone.md)
