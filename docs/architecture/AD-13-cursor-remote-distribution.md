# AD-13: Cursor remote plugin distribution options

**Status**: Spike (research complete, decision pending)

## Context

AD-4 originally assumed the Cursor Team Marketplace with a GitHub Enterprise App as the production distribution path. That approach was deferred (wpi.4, wpi.5) because the enterprise setup is heavyweight. This spike researches non-enterprise remote distribution alternatives.

## Constraint

The coding-aegis repo is currently public for development convenience, but production adoption by an engineering org requires a **private repo**. Any distribution path that requires a public repo is not acceptable for production use.

## Options evaluated

### Option E: Local symlink (current path)

Symlink the plugin directory into `~/.cursor/plugins/`.

| Aspect | Detail |
|--------|--------|
| Plan required | None |
| Auth required | Git clone access |
| Private repo | Yes |
| Update flow | `git pull` + restart Cursor |

**Pros:** Works now. No platform dependency. Full privacy.
**Cons:** Per-machine manual setup. No centralized management. Not suitable for broad org rollout.

**Status:** Active. Documented in `docs/howto/install.md`.

### Option D: Remote Rules (GitHub import)

Individual users import rules from a GitHub repo via Cursor Settings → Rules → Remote Rule (GitHub).

| Aspect | Detail |
|--------|--------|
| Plan required | None |
| Auth required | GitHub access to the repo (user's own auth) |
| Private repo | Supported |
| Discoverability | None — manual per-user setup |

**Pros:** Works with private repos. No admin involvement. No plan requirement.
**Cons:** Known bugs as of Cursor 2.6:
- `.mdc` files not imported correctly (Skills/SKILL.md found, but .mdc rules missed)
- Rules download to `~/.cursor/projects/<hash>/rules/` instead of project `.cursor/rules/`
- "Add from GitHub" UI intermittently disappears (requires open project folder)
- Not a plugin-level install — imports rules only, not skills/agents/MCP

**Status:** Needs hands-on investigation. Bugs may be resolved in newer Cursor versions.

### Option C: Team Marketplace with private repo (deferred)

The original AD-4 approach. Requires GitHub Enterprise App registration.

| Aspect | Detail |
|--------|--------|
| Plan required | Team or Enterprise |
| Auth required | GitHub Enterprise App at `cursor.com/dashboard?tab=integrations` |
| Private repo | Yes |
| Discoverability | Org-scoped — visible to team members |

**Pros:** Full privacy. Enterprise-grade access control. Plugin-level install (rules + skills + MCP).
**Cons:** Enterprise app setup overhead. Two-step install (register app, then install in org). Requires paid Team plan (limited to 1 marketplace) or Enterprise plan.

**Status:** Deferred (wpi.4, wpi.5). Revisit if Option D proves unviable.

### Options not viable for production

- **Option A (Public Marketplace):** Requires public repo. Ruled out.
- **Option B (Team Marketplace + public repo):** Requires public repo. Ruled out.

## Decision

1. **Now:** Option E (local symlink) for development and validation.
2. **Next:** Investigate Option D (remote rules) hands-on — test with current Cursor version, document whether known bugs are resolved, and determine if it meets minimum viable distribution needs.
3. **If D works:** Document as the lightweight remote path for small teams / individual contributors.
4. **If D fails:** Revisit Option C (enterprise app) as the production distribution path.

## References

- [Cursor Plugins Docs](https://cursor.com/docs/plugins)
- [Cursor Plugin Reference](https://cursor.com/docs/reference/plugins)
- [Cursor Rules Docs](https://cursor.com/docs/rules)
- [Remote Rules Bug Report](https://forum.cursor.com/t/having-issues-using-cursor-settings-to-import-remote-rules/149132)
- [GitHub Import UI Bug](https://forum.cursor.com/t/rules-from-github-disappeared-add-from-github-option-no-longer-available-cursor-2-5-26/153106)
- [Team Marketplace Setup Guide](https://dredyson.com/complete-beginners-guide-to-cursor-26-team-marketplaces-for-plugins-setup-configuration-and-troubleshooting/)
