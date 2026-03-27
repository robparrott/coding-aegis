---
name: fancy-beads
description: Backlog sync for beads (bd) — regenerates docs/backlog/ as navigable markdown from the beads issue database.
---

# Beads Backlog Sync

This skill adds automated backlog sync for repositories using [beads](https://github.com/sttts/beads) (`bd`).

For beads workflow guidance, commands, and session lifecycle, run `bd prime`.

## Backlog Sync

After each task status change (create, close, reopen), run:

```
scripts/sync-backlog.sh
```

This regenerates `docs/backlog/` with:
- **Per-epic files** — Title, status, description, and a task checklist with status icons (`[ ]` open, `[~]` in progress, `[x]` closed, `[!]` blocked)
- **`standalone.md`** — Issues not belonging to any epic
- **`README.md`** — Index with links to all epics and progress counts

Requires `bd` and `python3` on PATH. Clears and regenerates all files in `docs/backlog/` on each run.

> **Do not edit files in `docs/backlog/` manually** — they are overwritten on every sync.

## Future: Dependency Graph

`bd graph` output will be rendered as navigable markdown with hyperlinked task IDs.
