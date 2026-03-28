# Skill Testing Runbooks

Step-by-step procedures for installing and testing the coding-aegis skill.

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

   Replace `<org>` with the GitHub org or username.

   ```
   /plugin marketplace add <org>/coding-aegis
   ```

   *Expect:* `Successfully added marketplace: ...` (no plugin count shown).

2. **Browse available plugins**

   ```
   /plugin
   ```

   Navigate to the **Discover** tab to confirm the coding-aegis plugin appears.

3. **Install the plugin**

   Marketplace name is derived from `org-repo`.

   ```
   /plugin install coding-aegis@<org>-coding-aegis
   ```

   *Expect:* Plugin installs from remote.

3. **Verify the skill**

   ```
   /coding-aegis
   ```

   *Expect:* Skill responds.

4. **Check install scope** (default is user)

   ```
   ls ~/.claude/plugins/cache/
   ```

   *Expect:* coding-aegis plugin cached.

5. **Optionally test project-scoped install**

   ```
   /plugin uninstall coding-aegis@<org>-coding-aegis
   /plugin install coding-aegis@<org>-coding-aegis --scope project
   ls .claude/plugins/
   ```

   *Expect:* Plugin installed at project level.

6. **Cleanup**

   ```
   /plugin uninstall coding-aegis@<org>-coding-aegis
   /plugin marketplace remove <org>-coding-aegis
   ```

---

## 4. Smoke test checklist

Run through these checks regardless of install method.

- [ ] `/coding-aegis` appears in skill list — check via `/plugin` Installed tab
- [ ] Skill responds to invocation — type `/coding-aegis` in a session
- [ ] SKILL.md content renders correctly — verify catalog tiers and install table display
- [ ] No plugin loading errors — `/plugin` Errors tab shows nothing for coding-aegis
