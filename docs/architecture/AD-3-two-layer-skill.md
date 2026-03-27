# AD-3: Two-layer skill architecture

**Status**: Accepted

## Decision

Two distinct components serve different purposes:

- **`coding-aegis`** — the rich, full-featured skill that lives in `pkgs/bootstrap/`. It is the primary interface for developers to browse the catalog, install packages, check status, and manage governance. Each coding agent gets this skill in its native format.
- **`coding-aegis-bootstrap`** — the minimal mechanism to get `coding-aegis` installed. Uses each tool's native distribution path.

## Bootstrap Mechanisms Per Tool

| Tool | Bootstrap mechanism | Install commands |
|------|-------------------|-----------------|
| **Claude Code** | Plugin marketplace | `/plugin marketplace add {org}/coding-aegis` then `/plugin install coding-aegis@coding-aegis` |
| **Cursor** | Team Marketplace | Admin imports repo URL at Dashboard → Settings → Plugins; users one-click install from marketplace |
| **Windsurf** | TBD | TBD |
| **Copilot** | TBD | TBD |

## Rationale

Separating the bootstrap mechanism from the full skill keeps the installation path minimal and tool-native, while the rich skill can evolve independently.
