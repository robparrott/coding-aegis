# AD-4: Triple marketplace registration

**Status**: Accepted

## Decision

This repo simultaneously serves as a **Claude Code plugin marketplace**, a **Cursor Team Marketplace**, and a **Codex plugin source** via three coexisting plugin manifests.

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
        "./modules/bootstrap/coding-aegis/skills/coding-aegis"
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

modules/bootstrap/coding-aegis/
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
      "path": "./modules/bootstrap/coding-aegis"
    }
  ]
}
```

`modules/bootstrap/coding-aegis/.cursor-plugin/plugin.json`:
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

## Codex

`.codex-plugin/plugin.json` (following [Codex plugin spec](https://developers.openai.com/codex/plugins/build)):

```json
{
  "name": "coding-aegis",
  "version": "1.0.0",
  "description": "Browse, install, and manage coding agent governance packages",
  "author": { "name": "platform-team" },
  "skills": "./modules/bootstrap/coding-aegis/skills/"
}
```

Codex discovers plugins from marketplace JSON files at repo or user level. There is no `codex plugin install` CLI command — plugins are auto-discovered when Codex starts in a directory with a marketplace.

**Marketplace sources (scanned in order):**
- Repo: `$REPO_ROOT/.agents/plugins/marketplace.json`
- Personal: `~/.agents/plugins/marketplace.json`
- Official Plugin Directory (curated, self-serve publishing coming soon)

**Bootstrap flow:**
```
1. Clone/access the coding-aegis repo
2. Create marketplace.json pointing to .codex-plugin/ as a local plugin source
3. Start Codex in the repo — plugin is auto-discovered, skills available
```

**Note:** Self-serve plugin publishing is not yet available. Local and repo-level marketplace registration is the current distribution mechanism for private plugins.
