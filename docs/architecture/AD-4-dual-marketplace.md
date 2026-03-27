# AD-4: Dual marketplace registration

**Status**: Accepted

## Decision

This repo simultaneously serves as both a **Claude Code plugin marketplace** and a **Cursor Team Marketplace** via two coexisting plugin manifests.

## Claude Code

`.claude-plugin/marketplace.json` (following [anthropics/skills](https://github.com/anthropics/skills) pattern):

```json
{
  "name": "coding-aegis",
  "metadata": {
    "description": "Engineering organization coding agent governance packages",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "coding-aegis",
      "description": "Browse, install, and manage coding agent governance packages",
      "source": "./",
      "skills": [
        "./pkgs/bootstrap/coding-aegis/skills/coding-aegis"
      ]
    }
  ]
}
```

**Bootstrap flow:**
```
1. /plugin marketplace add {org}/coding-aegis
2. /plugin install coding-aegis@coding-aegis
3. Done — user now has the full coding-aegis skill
```

## Cursor

`.cursor-plugin/marketplace.json` + per-plugin `plugin.json`:

```
.cursor-plugin/
└── marketplace.json          # Lists plugins available in this repo

pkgs/bootstrap/coding-aegis/
├── .cursor-plugin/
│   └── plugin.json           # Cursor plugin metadata for coding-aegis
├── rules/
│   └── coding-aegis.mdc      # Cursor-native rule (tool override)
└── ...
```

`.cursor-plugin/marketplace.json`:
```json
{
  "plugins": [
    {
      "name": "coding-aegis",
      "path": "./pkgs/bootstrap/coding-aegis"
    }
  ]
}
```

`pkgs/bootstrap/coding-aegis/.cursor-plugin/plugin.json`:
```json
{
  "name": "coding-aegis",
  "version": "1.0.0",
  "description": "Browse, install, and manage coding agent governance packages",
  "author": { "name": "platform-team" },
  "rules": "./rules/",
  "skills": "./skills/"
}
```

**Bootstrap flow:**
```
1. Admin: Dashboard → Settings → Plugins → Import → paste repo URL
   (one-time setup, requires GitHub Enterprise App for private repo)
2. User: Open Cursor marketplace → see coding-aegis → one-click install
3. Done — user now has the governance rules/skills in Cursor
```

**Cursor private repo prerequisites:**
- Register GitHub Enterprise App at `https://cursor.com/dashboard?tab=integrations`
- Install the app in the GitHub organization
- Grant the app access to the private governance repository
- Enable auto-refresh for webhook-based updates (optional, has known reliability issues — manual refresh available as fallback)
