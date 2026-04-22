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
- **`graph.md`** — Dependency graph from `bd graph --all --compact` with a task index linking each ID to its backlog file
- **`README.md`** — Index with links to all epics, progress counts, and graph

Requires `bd` and `python3` on PATH. Clears and regenerates all files in `docs/backlog/` on each run.

> **Do not edit files in `docs/backlog/` manually** — they are overwritten on every sync.

