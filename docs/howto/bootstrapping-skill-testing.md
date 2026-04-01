# Skill Testing Runbooks (Claude Code)

Validation procedures for coding-aegis authors and maintainers. These runbooks verify that the skill installs and loads correctly in Claude Code during development — they are not end-user documentation.

---

## 1. Test skill from local checkout (no install)

Use `--plugin-dir` to load the skill directly from the working tree. Fastest loop for development — no install/uninstall cycle.

**Prerequisites:** Claude Code CLI installed, local clone of coding-aegis repo.

### Steps

1. **Launch Claude Code with the plugin directory**

   ```
   claude --plugin-dir ./pkgs/bootstrap/coding-aegis
   ```

   *Expect:* Claude Code starts with the coding-aegis skill loaded.

2. **Verify the skill is available**

   ```
   /coding-aegis
   ```

   *Expect:* Skill is listed and responds (even if stub).

3. **Iterate — edit SKILL.md, then reload without restarting**

   ```
   /reload-plugins
   ```

   *Expect:* Changes picked up in the same session.

---

## 2. Install skill via local marketplace

Add the local repo as a marketplace, then install the plugin. Tests the full install flow using the `.claude-plugin/marketplace.json` manifest.

**Prerequisites:** Claude Code CLI installed, local clone of coding-aegis repo.

### Steps

1. **Add the local repo as a marketplace**

   ```
   /plugin marketplace add ./
   ```

   *Expect:* `Successfully added marketplace: coding-aegis` (no plugin count shown).

2. **Install the plugin**

   ```
   /plugin install coding-aegis@coding-aegis
   ```

   *Expect:* `Installed coding-aegis. Restart Claude Code to load new plugins.`

3. **Restart Claude Code** — exit and relaunch to load the plugin.

5. **Verify the skill**

   ```
   /coding-aegis
   ```

   *Expect:* Skill responds.

4. **Check install location**

   ```
   ls ~/.claude/plugins/cache/
   ```

   *Expect:* coding-aegis plugin listed.

5. **Cleanup**

   ```
   /plugin uninstall coding-aegis@coding-aegis
   /plugin marketplace remove coding-aegis
   ```

---

## 3. Install skill from GitHub

Add the GitHub repo as a marketplace and install remotely. Tests the end-to-end flow a real user would follow.

**Prerequisites:** Claude Code CLI installed, coding-aegis repo pushed to GitHub with `.claude-plugin/marketplace.json` at root.

### Steps

1. **Add the GitHub marketplace**

   Replace `robparrott` with the GitHub org or username if different.

   ```
   /plugin marketplace add robparrott/coding-aegis
   ```

   *Expect:* `Successfully added marketplace: robparrott-coding-aegis`

2. **Install the plugin**

   ```
   /plugin install coding-aegis@robparrott-coding-aegis
   ```

   *Expect:* `Installed coding-aegis. Restart Claude Code to load new plugins.`

3. **Restart Claude Code** — exit and relaunch to load the plugin.

4. **Verify the skill**

   ```
   /coding-aegis
   ```

   *Expect:* Skill responds.

5. **List the catalog**

   ```
   /coding-aegis list
   ```

   *Expect:* Packages listed by tier (required, best-practices, optional, goodies).

6. **Show package details**

   ```
   /coding-aegis show pirate-speak
   ```

   *Expect:* Package metadata (tier, description, artifact list) and README content displayed.

7. **Install a package**

   ```
   /coding-aegis install pirate-speak
   ```

   The install command opens a scope picker. Select **"Project"** and hit Enter.

   *Expect:* Files written to `.claude/rules/` (governance rules prefixed `aegis--`) and `.claude/skills/pirate-speak/` (skill artifacts).

8. **Check installed status**

   ```
   /coding-aegis status
   ```

   *Expect:* `pirate-speak` listed as an installed (current) package.

9. **Restart Claude Code** — exit and relaunch to pick up the newly installed skill files.

10. **Verify installed skill is available**

    ```
    /pirate-speak
    ```

    *Expect:* The `/pirate-speak` skill is listed and responds.

11. **Check install location**

    ```
    ls ~/.claude/plugins/cache/
    ```

    *Expect:* coding-aegis plugin listed.

12. **Optionally test project-scoped install**

    ```
    /plugin uninstall coding-aegis@robparrott-coding-aegis
    /plugin install coding-aegis@robparrott-coding-aegis
    ```

    The install command opens a scope picker. Select **"Install for all collaborators on this repository (project scope)"** and hit Enter.

    *Expect:* Plugin reference added to `.claude/settings.local.json` under `enabledPlugins`. The plugin cache still lives at `~/.claude/plugins/cache/`.

13. **Cleanup**

    Remove governance artifacts written by the package install:

    ```
    rm -rf .claude/rules/aegis--* .claude/skills/pirate-speak
    ```

    Then uninstall the plugin and remove the marketplace:

    ```
    /plugin uninstall coding-aegis@robparrott-coding-aegis
    /plugin marketplace remove robparrott-coding-aegis
    ```

---

## 4. Smoke test checklist

Run through these checks regardless of install method.

- [ ] `/coding-aegis` appears in skill list — check via `/plugin` Installed tab
- [ ] Skill responds to invocation — type `/coding-aegis` in a session
- [ ] SKILL.md content renders correctly — verify catalog tiers and install table display
- [ ] No plugin loading errors — `/plugin` Errors tab shows nothing for coding-aegis
- [ ] `/coding-aegis list` shows packages grouped by tier
- [ ] `/coding-aegis show pirate-speak` displays package details and README
- [ ] `/coding-aegis install pirate-speak` writes files to `.claude/rules/` and `.claude/skills/`
- [ ] `/coding-aegis status` shows installed package as current
- [ ] After restart, installed skills (e.g. `/pirate-speak`) are available

---

## 5. Clean-slate testing from an empty directory

Start from an empty temporary directory with no existing project context. This tabula rasa workflow validates the full experience a new user would encounter.

**Prerequisites:** Claude Code CLI installed, coding-aegis repo pushed to GitHub with `.claude-plugin/marketplace.json` at root.

### Steps

1. **Create and enter a clean directory**

   ```
   mkdir -p /tmp/aegis-test && cd /tmp/aegis-test
   ```

2. **Start Claude Code**

   ```
   claude
   ```

   *Expect:* Claude Code launches in `/tmp/aegis-test` with no plugins or skills loaded.

3. **Remove any existing marketplace and plugin registrations**

   Marketplace and plugin registrations are stored in `~/.claude/plugins/` (user-level),
   not in the project directory. If you've tested before, remove stale registrations first:

   ```
   /plugin uninstall coding-aegis@coding-aegis
   /plugin marketplace remove coding-aegis
   ```

   Ignore errors if they don't exist yet.

4. **Register the GitHub marketplace**

   ```
   /plugin marketplace add robparrott/coding-aegis
   ```

   *Expect:* `Successfully added marketplace: robparrott-coding-aegis`

5. **Install the plugin (Project scope)**

   ```
   /plugin install coding-aegis@robparrott-coding-aegis
   ```

   The install command opens a scope picker. Select **"Project"** and hit Enter.

   *Expect:* `Installed coding-aegis. Restart Claude Code to load new plugins.`

6. **Restart Claude Code in the same directory**

   Exit and relaunch:

   ```
   claude
   ```

   *Expect:* Claude Code starts with the coding-aegis skill loaded.

7. **Test catalog commands**

   ```
   /coding-aegis list
   ```

   *Expect:* Packages listed by tier (required, best-practices, optional, goodies).

   ```
   /coding-aegis show pirate-speak
   ```

   *Expect:* Package metadata (tier, description, artifact list) and README content displayed.

   ```
   /coding-aegis install pirate-speak
   ```

   Select **"Project"** scope when prompted.

   *Expect:* Files written to `.claude/rules/` (governance rules prefixed `aegis--`) and `.claude/skills/pirate-speak/` (skill artifacts).

   ```
   /coding-aegis status
   ```

   *Expect:* `pirate-speak` listed as an installed (current) package.

8. **Restart Claude Code again** — exit and relaunch to pick up installed skill files.

   ```
   claude
   ```

9. **Verify the installed skill is available**

   ```
   /pirate-speak
   ```

   *Expect:* The `/pirate-speak` skill is listed and responds.

10. **Cleanup**

   Remove governance artifacts written by the package install:

   ```
   rm -rf .claude/rules/aegis--* .claude/skills/pirate-speak
   ```

   Uninstall the plugin and remove the marketplace:

   ```
   /plugin uninstall coding-aegis@robparrott-coding-aegis
   /plugin marketplace remove robparrott-coding-aegis
   ```

   Optionally delete the temporary directory:

   ```
   rm -rf /tmp/aegis-test
   ```
