# Dependency Graph

Auto-generated from `bd graph --all --compact`.

```

📊 Dependency graph for coding-aegis-b5z (33 issues, 5 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-b5z ● P2 Phase 2: coding-aegis Skill (Claude Code)
  │   ├── ◐ coding-aegis-b5z.34 ● P1 Fix Codex test: helloworld skill installs to .cla…
  │   ├── ○ coding-aegis-b5z.37 ● P1 Fix uninstall command for Codex: scan .agents/ski…
  │   ├── ○ coding-aegis-b5z.10 ● P2 Add Gemini remote skill install test (git URL)
  │   ├── ○ coding-aegis-b5z.11 ● P2 Update install/testing docs for Claude, Codex, an…
  │   ├── ○ coding-aegis-b5z.36 ● P2 Support local git repo install in Codex test T2
  │   ├── ○ coding-aegis-b5z.42 ● P2 Add local install fallback for Claude test: insta…
  │   └── ○ coding-aegis-b5z.5 ● P2 Add install-required command to coding-aegis skill
  ├── ○ coding-aegis-b5z.10 ● P2 Add Gemini remote skill install test (git URL)
  ├── ○ coding-aegis-b5z.11 ● P2 Update install/testing docs for Claude, Codex, an…
  ├── ◐ coding-aegis-b5z.34 ● P1 Fix Codex test: helloworld skill installs to .cla…
  ├── ○ coding-aegis-b5z.36 ● P2 Support local git repo install in Codex test T2
  ├── ○ coding-aegis-b5z.37 ● P1 Fix uninstall command for Codex: scan .agents/ski…
  ├── ○ coding-aegis-b5z.42 ● P2 Add local install fallback for Claude test: insta…
  └── ○ coding-aegis-b5z.5 ● P2 Add install-required command to coding-aegis skill

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

📊 Dependency graph for coding-aegis-2sv (14 issues, 2 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-2sv ● P1 Cross-tool artifact model refactor
  │   ├── ○ coding-aegis-2sv.15 ● P1 Deliver Codex governance rules via AGENTS.md inst…
  │   ├── ○ coding-aegis-2sv.1 ● P2 Spike: Research Windsurf sub-agent and agent swar…
  │   ├── ○ coding-aegis-2sv.10 ● P2 Create package authoring HOWTO with exemplar
  │   ├── ○ coding-aegis-2sv.12 ● P2 Design AGENTS.md management strategy for installe…
  │   ├── ○ coding-aegis-2sv.2 ● P2 Spike: Research GitHub Copilot agent mode and sub…
  │   ├── ○ coding-aegis-2sv.5 ● P2 Claude Code rules delivery
  │   ├── ○ coding-aegis-2sv.6 ● P2 Windsurf rules delivery
  │   ├── ○ coding-aegis-2sv.7 ● P2 Copilot instructions delivery
  │   ├── ○ coding-aegis-2sv.8 ● P2 Windsurf skills delivery
  │   ├── ○ coding-aegis-2sv.11 ● P3 Add MCP server stub to pirate-speak package
  │   ├── ○ coding-aegis-2sv.13 ● P3 Add AGENTS.md integration to pirate-speak package
  │   ├── ○ coding-aegis-2sv.3 ● P3 Add Codex tool support
  │   └── ○ coding-aegis-2sv.4 ● P3 Add Gemini Code Assist support
  ├── ○ coding-aegis-2sv.1 ● P2 Spike: Research Windsurf sub-agent and agent swar…
  ├── ○ coding-aegis-2sv.10 ● P2 Create package authoring HOWTO with exemplar
  ├── ○ coding-aegis-2sv.11 ● P3 Add MCP server stub to pirate-speak package
  ├── ○ coding-aegis-2sv.12 ● P2 Design AGENTS.md management strategy for installe…
  ├── ○ coding-aegis-2sv.15 ● P1 Deliver Codex governance rules via AGENTS.md inst…
  ├── ○ coding-aegis-2sv.2 ● P2 Spike: Research GitHub Copilot agent mode and sub…
  ├── ○ coding-aegis-2sv.3 ● P3 Add Codex tool support
  ├── ○ coding-aegis-2sv.4 ● P3 Add Gemini Code Assist support
  ├── ○ coding-aegis-2sv.5 ● P2 Claude Code rules delivery
  ├── ○ coding-aegis-2sv.6 ● P2 Windsurf rules delivery
  ├── ○ coding-aegis-2sv.7 ● P2 Copilot instructions delivery
  └── ○ coding-aegis-2sv.8 ● P2 Windsurf skills delivery

  LAYER 1
  └── ○ coding-aegis-2sv.13 ● P3 Add AGENTS.md integration to pirate-speak package

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-bg5 (5 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-bg5 ● P2 coding-aegis Skill UX
  │   ├── ○ coding-aegis-bg5.1 ● P2 Add install-required and install-best-practices c…
  │   ├── ○ coding-aegis-bg5.2 ● P2 Add uninstall command to coding-aegis skill
  │   ├── ○ coding-aegis-bg5.3 ● P2 Update test scripts T7.1 to use skill-mediated un…
  │   └── ○ coding-aegis-z61 ● P2 Design coding-aegis skill UX
  ├── ○ coding-aegis-bg5.1 ● P2 Add install-required and install-best-practices c…
  ├── ○ coding-aegis-bg5.2 ● P2 Add uninstall command to coding-aegis skill
  ├── ○ coding-aegis-bg5.3 ● P2 Update test scripts T7.1 to use skill-mediated un…
  └── ○ coding-aegis-z61 ● P2 Design coding-aegis skill UX

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-wpi (4 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-wpi ● P1 Phase 3: Cursor Bootstrap
  │   ├── ○ coding-aegis-wpi.10 ● P2 Create Cursor test script following user journey …
  │   ├── ○ coding-aegis-wpi.8 ● P2 Test Cursor Remote Rules (Option D) with current …
  │   └── ○ coding-aegis-wpi.9 ● P2 Simplify Cursor local installation process
  ├── ○ coding-aegis-wpi.10 ● P2 Create Cursor test script following user journey …
  ├── ○ coding-aegis-wpi.8 ● P2 Test Cursor Remote Rules (Option D) with current …
  └── ○ coding-aegis-wpi.9 ● P2 Simplify Cursor local installation process

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-lw7 (3 issues, 2 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-ghv ● P2 Create robust coding-agent tool detection utility

  LAYER 1
  ├── ○ coding-aegis-lw7 ● P2 Add tool detection assertion to every skill insta…
  └── ○ coding-aegis-pnv ● P2 Research Windsurf and Copilot tool detection sign…

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-a0q (2 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  ├── ○ coding-aegis-a0q ● P2 External dependency installation for packages
  │   └── ○ coding-aegis-a0q.1 ● P2 Install sttts/beads-skill issue-tracking skill in…
  └── ○ coding-aegis-a0q.1 ● P2 Install sttts/beads-skill issue-tracking skill in…

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-gua (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-gua ● P2 Codex T1: actively register marketplace in test d…

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-c1d (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-c1d ● P2 Suppress tool detection output on implicit runs

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-6pp (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-6pp ● P2 Codex T6/T9: replace local pkgs/ catalog with rem…

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

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-135 (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-135 ● P3 Create conventional-commits best-practices skill

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-400 (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-400 ● P3 Author GitHub Copilot install section in docs/how…

────────────────────────────────────────────────────────────

📊 Dependency graph for coding-aegis-ytb (1 issues, 1 layers)

  Status: ○ open  ◐ in_progress  ● blocked  ✓ closed  ❄ deferred

  LAYER 0 (ready)
  └── ○ coding-aegis-ytb ● P3 Author Windsurf install section in docs/howto/ins…
```

## Task Index

- [`coding-aegis-b5z`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.34`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.37`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.10`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.11`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.36`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.42`](phase-2-coding-aegis-skill-claude.md)
- [`coding-aegis-b5z.5`](phase-2-coding-aegis-skill-claude.md)
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
- [`coding-aegis-cdb`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.1`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.2`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.3`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.4`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.5`](phase-8-external-package-references.md)
- [`coding-aegis-cdb.6`](phase-8-external-package-references.md)
- [`coding-aegis-2sv`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.15`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.1`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.10`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.12`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.2`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.5`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.6`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.7`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.8`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.11`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.13`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.3`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-2sv.4`](cross-tool-artifact-model-refactor.md)
- [`coding-aegis-bg5`](coding-aegis-skill-ux.md)
- [`coding-aegis-bg5.1`](coding-aegis-skill-ux.md)
- [`coding-aegis-bg5.2`](coding-aegis-skill-ux.md)
- [`coding-aegis-bg5.3`](coding-aegis-skill-ux.md)
- [`coding-aegis-z61`](standalone.md)
- [`coding-aegis-wpi`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.10`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.8`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-wpi.9`](phase-3-cursor-bootstrap.md)
- [`coding-aegis-lw7`](standalone.md)
- [`coding-aegis-ghv`](standalone.md)
- [`coding-aegis-pnv`](standalone.md)
- [`coding-aegis-a0q`](external-dependency-installation-for-packages.md)
- [`coding-aegis-a0q.1`](external-dependency-installation-for-packages.md)
- [`coding-aegis-gua`](standalone.md)
- [`coding-aegis-c1d`](standalone.md)
- [`coding-aegis-6pp`](standalone.md)
- [`coding-aegis-avj`](standalone.md)
- [`coding-aegis-3m9`](standalone.md)
- [`coding-aegis-135`](standalone.md)
- [`coding-aegis-400`](standalone.md)
- [`coding-aegis-ytb`](standalone.md)
