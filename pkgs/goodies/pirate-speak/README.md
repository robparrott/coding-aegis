# pirate-speak

A harmless demonstration package that exercises every coding-aegis artifact type. When installed, coding agents adopt a pirate dialect — making it unmistakable that governance is active.

## Purpose

This package exists to:
- Demonstrate the full package format (rules, skills, tool overrides)
- Provide an end-to-end test fixture for the install/render pipeline
- Serve as a reference for the [package authoring HOWTO](../../../docs/howto/author-package.md)

## Layout

```
pirate-speak/
├── pkg.yaml                          # Package manifest
├── README.md                         # This file
├── rules/
│   ├── pirate-speak.md               # Always-on rule: pirate dialect in all responses
│   └── pirate-readme.md              # File-scoped rule: pirate headings in README.md files
├── skills/
│   └── pirate-speak/
│       └── SKILL.md                  # Invocable skill: ASCII skull banner
└── tools/
    └── cursor/
        └── rules/
            ├── pirate-speak.mdc      # Cursor override: alwaysApply frontmatter
            └── pirate-readme.mdc     # Cursor override: globs frontmatter
```

## Artifacts

| Type | File | What it does |
|------|------|-------------|
| **rule** (always-on) | `rules/pirate-speak.md` | Injects pirate dialect into all agent responses — greetings, nautical metaphors, pirate code comments |
| **rule** (file-scoped) | `rules/pirate-readme.md` | Triggers only when editing `README.md` — enforces pirate-themed section headings |
| **skill** (invocable) | `skills/pirate-speak/SKILL.md` | `/pirate-speak` prints an ASCII skull-and-crossbones banner confirming governance is active |
| **tool override** | `tools/cursor/rules/*.mdc` | Cursor-native `.mdc` copies with `alwaysApply` / `globs` frontmatter (until renderers are built) |

## How to verify

After installing, each artifact produces an obvious signal:

1. **Always-on rule**: Ask the agent anything. It should respond with pirate greetings and nautical metaphors.
2. **File-scoped rule**: Ask the agent to edit a README. Section headings should get pirate suffixes (e.g., `## Installation — Boarding Instructions`).
3. **Skill**: Run `/pirate-speak`. A skull-and-crossbones ASCII art banner should appear.
