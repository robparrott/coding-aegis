---
name: pirate-speak
description: Summon the Jolly Roger — display a pirate-themed ASCII art banner confirming governance is active.
---

# pirate-speak

When invoked, display a pirate-themed ASCII art banner to confirm the pirate-speak governance package is loaded and active.

## Behavior

1. Print the ASCII skull-and-crossbones banner below.
2. Below the banner, print a brief status line: `Pirate governance be ACTIVE, matey! All hands on deck.`
3. List which pirate-speak artifacts are installed:
   - `pirate-speak` rule (always-on pirate dialect)
   - `pirate-readme` rule (README heading guardrail)
   - `pirate-speak` skill (this command)
4. No files are created or modified. Output only.

## Banner

```
    ___
   /   \
  | o o |
  |  _  |
   \___/
  /|   |\
 / |   | \
 __|   |__
|  |   |  |
 \_|   |_/
   |   |
  _|   |_
 |_______|
  \     /
   |   |
   |   |
  /|   |\
 /_|   |_\

  ☠  ARRR!  ☠
  PIRATE-SPEAK
   GOVERNANCE
    ACTIVE
```

## Example

```
> /pirate-speak

    ___
   /   \
  | o o |
  |  _  |
   \___/
  /|   |\
 / |   | \
 __|   |__
|  |   |  |
 \_|   |_/
   |   |
  _|   |_
 |_______|
  \     /
   |   |
   |   |
  /|   |\
 /_|   |_\

  ☠  ARRR!  ☠
  PIRATE-SPEAK
   GOVERNANCE
    ACTIVE

Pirate governance be ACTIVE, matey! All hands on deck.

Installed artifacts:
  ✓ pirate-speak rule (always-on pirate dialect)
  ✓ pirate-readme rule (README heading guardrail)
  ✓ pirate-speak skill (this command)
```
