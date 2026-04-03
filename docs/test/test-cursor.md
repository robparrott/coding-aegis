# Cursor — Test Detail

> Tool-specific details for the Cursor skill install test. For the full test plan, phase definitions, and pass criteria see [testing-spec.md](testing-spec.md).

> **Status: TBD** — Cursor CLI plugin management is not yet documented. This file is a placeholder.

## Install Mechanisms

### T1 — Register Marketplace

TBD. Cursor has a Team Marketplace (`.cursor-plugin/` manifest at repo root per AD-4), but CLI-based registration is not yet documented.

### T2 — Install Skill

TBD. The IDE-based plugin install flow is documented, but headless CLI install is not.

## CLI Invocation

- Binary: `cursor-agent` (Homebrew install); vendor install uses `agent`
- `-p` — headless/print mode (same pattern as Claude)
- `--output-format text` — plain text output
- `--force` or `--yolo` — auto-approve file modifications (exact flag TBD)

## Prompts

TBD. Expected to use `/coding-aegis ...` syntax (same as Claude and Gemini).

## Tool Detection (T2b)

TBD. Cursor likely sets a tool-specific env var or uses a path signal. Update when CLI behavior is confirmed.

## Teardown

TBD. Mirror the Claude teardown pattern once the install mechanism is confirmed.

## Test Script

`tests/test-cursor-skill-install.sh` — not yet written.
