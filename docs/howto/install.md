# Installing coding-aegis

How to install coding-aegis governance into a target repository, organized by coding-agent tool.

---

## Claude Code

### Prerequisites

- Claude Code CLI v1.0.33+ (`claude --version`)
- GitHub access to the coding-aegis repo

### Steps

1. **Add the coding-aegis marketplace**

   ```
   /plugin marketplace add robparrott/coding-aegis
   ```

   *Expect:* `Successfully added marketplace: robparrott-coding-aegis`

2. **Install the coding-aegis plugin**

   ```
   /plugin install coding-aegis@robparrott-coding-aegis
   ```

   Select the appropriate scope:
   - **User scope** — governance applies across all your repositories
   - **Project scope** — governance applies to this repository for all collaborators
   - **Local scope** — governance applies to you in this repository only

   *Expect:* `Installed coding-aegis. Restart Claude Code to load new plugins.`

3. **Restart Claude Code**

   Exit and relaunch to load the plugin.

4. **Verify the skill is available**

   ```
   /coding-aegis
   ```

   *Expect:* Skill responds with catalog and usage information.

5. **Browse available packages**

   ```
   /coding-aegis list
   ```

   *Expect:* Packages listed by tier (required, best-practices, optional, goodies).

6. **Install governance packages**

   ```
   /coding-aegis install <package-name>
   ```

   Start with `required` tier packages — these are non-negotiable governance. Then review `best-practices` for recommended defaults.

### Updating

To pick up new packages or updates from the catalog:

```
/plugin marketplace update robparrott-coding-aegis
```

### Removing

```
/plugin uninstall coding-aegis@robparrott-coding-aegis
/plugin marketplace remove robparrott-coding-aegis
```

---

## Cursor

*Stub — to be authored when Phase 3 (Cursor Bootstrap) is complete.*

---

## Windsurf

*Stub — to be authored when Windsurf bootstrap mechanism is designed.*

---

## GitHub Copilot

*Stub — to be authored when Copilot bootstrap mechanism is designed.*
