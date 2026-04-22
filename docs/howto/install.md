# Install Guide

How to install the coding-aegis skill and use it to manage packages, organized by coding-agent tool.

**Command prefix legend:**
- `$ ` — run in a shell (bash/zsh terminal)
- `/coding-aegis ...` — type into the tool's chat or prompt (Claude Code, Cursor, OpenCode, Gemini)
- `$coding-aegis ...` — Codex skill invocation syntax

**Package name format:** `<package-name>` is the bare package name only — e.g. `helloworld` — not a tier-qualified path like `optional/helloworld`.

---

## Claude Code

### Prerequisites

- Claude Code CLI v1.0.33+ (`$ claude --version`)
- GitHub access to the coding-aegis repo

### Install

1. **Add the coding-aegis marketplace**

   ```
   $ claude plugin marketplace add robparrott/coding-aegis
   ```

   > **Alternative:** If you have a local clone, you can also run `/plugin marketplace add /path/to/coding-aegis` from within Claude chat.

   *Expect:* `Successfully added marketplace: robparrott-coding-aegis`

   Verify:
   ```
   $ claude plugin marketplace list
   ```
   Should show: `coding-aegis`

2. **Install the coding-aegis plugin**

   ```
   $ claude plugin install coding-aegis@robparrott-coding-aegis
   ```

   Select the appropriate scope:
   - **User scope** — skill available across all your repositories
   - **Project scope** — skill available to all collaborators in this repository
   - **Local scope** — skill available to you in this repository only

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
   /coding-aegis show <package-name>
   ```

   Packages are listed by tier: `required`, `best-practices`, `optional`, `goodies`. The tiers are informational — choose the packages relevant to your project.

6. **Install a package**

   ```
   /coding-aegis install <package-name>
   ```

   The skill installs rule files to `.claude/rules/` and skill files to `.claude/skills/`. Restart Claude Code to load newly installed skills.

7. **Uninstall a package**

   ```
   /coding-aegis uninstall <package-name>
   ```

   Removes all managed files for the package. Restart Claude Code to unload removed skills.

8. **Check status**

   ```
   /coding-aegis status
   ```

   Shows installed packages, versions, and whether they are current with the catalog.

### Updating

To pick up new packages or updates from the catalog:

```
$ claude plugin marketplace update robparrott-coding-aegis
```

### Troubleshooting

**Plugin says "already installed" but skill is not available**

This can happen when the marketplace was re-registered under a different name or the cached version is stale. Fix by removing both the plugin and the marketplace, then reinstalling:

```
$ claude plugin uninstall coding-aegis@coding-aegis
$ claude plugin marketplace remove coding-aegis
$ claude plugin marketplace add robparrott/coding-aegis
$ claude plugin install coding-aegis@robparrott-coding-aegis
```

Restart Claude Code after reinstalling.

**Skill only works in the coding-aegis repo, not other projects**

The plugin was installed with local (project) scope. Uninstall and reinstall with user scope so it is available across all repositories.

### Removing

```
$ claude plugin uninstall coding-aegis@robparrott-coding-aegis
$ claude plugin marketplace remove robparrott-coding-aegis
```

---

## Cursor

### Prerequisites

- `cursor-agent` CLI installed (`$ brew install cursor-cli` on macOS)
- Authenticated (Cursor account)

> **macOS note:** After `brew install cursor-cli`, clear the quarantine flag:
> ```
> $ xattr -rd com.apple.quarantine "$(brew --prefix)/Caskroom/cursor-cli/<version>/"
> ```
> Substitute the installed version number. See [test-cursor.md](../test/test-cursor.md) for details.

### Install

1. **Clone the coding-aegis repo**

   ```
   $ git clone https://github.com/robparrott/coding-aegis.git /tmp/coding-aegis
   ```

2. **Copy the skill into your target project**

   ```
   $ SKILL_SRC=/tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis
   $ mkdir -p .cursor/skills
   $ cp -r "$SKILL_SRC" .cursor/skills/coding-aegis
   ```

   The skill makes `/coding-aegis` available as an invocable skill in Cursor chat.

   > **Symlinks also work** for personal use: `ln -s "$SKILL_SRC" .cursor/skills/coding-aegis`. Copy is preferred for team repos since symlinks require every contributor to have the same clone path.

3. **Remove the clone**

   The installed skill is self-contained. The clone is only needed during setup.

   ```
   $ rm -rf /tmp/coding-aegis
   ```

### Verify

In a Cursor chat:

```
/coding-aegis list
```

*Expect:* Catalog output listing packages by tier.

### Install a package

```
/coding-aegis install <package-name>
```

### Uninstall a package

```
/coding-aegis uninstall <package-name>
```

### Updating

Re-clone temporarily, copy the updated skill over the existing one, then remove the clone:

```
$ git clone https://github.com/robparrott/coding-aegis.git /tmp/coding-aegis
$ cp -r /tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis .cursor/skills/coding-aegis
$ rm -rf /tmp/coding-aegis
```

### Removing

```
$ rm -rf .cursor/skills/coding-aegis
```

---

## OpenAI Codex

### Prerequisites

- Codex CLI installed and authenticated (`$ codex --version`)
- The coding-aegis repo pushed to GitHub (Codex installs from GitHub, not local paths)

### Install

From within your project directory, ask Codex to install the skill using its built-in `$skill-installer`:

```
$skill-installer install --repo robparrott/coding-aegis --path modules/bootstrap/coding-aegis/skills/coding-aegis
```

The skill installs to `~/.codex/skills/coding-aegis/`. Restart Codex to pick up the new skill.

### Verify

```
$coding-aegis list
$coding-aegis show <package-name>
```

The catalog is fetched automatically from GitHub on first use and cached locally in `.coding-aegis-catalog/`. No local clone needed.

### Install a package

```
$coding-aegis install <package-name>
```

Codex installs packages as:
- **Rules**: appended to `AGENTS.md` as `<!-- aegis:begin -->` / `<!-- aegis:end -->` sections
- **Skills**: copied to `.agents/skills/<name>/`

### Uninstall a package

```
$coding-aegis uninstall <package-name>
```

Removes the `AGENTS.md` section and skill directory.

### Updating

Reinstall the skill from GitHub to pick up updates:

```
$skill-installer install --repo robparrott/coding-aegis --path modules/bootstrap/coding-aegis/skills/coding-aegis
```

Restart Codex after updating.

### Removing

```
$ rm -rf ~/.codex/skills/coding-aegis
```

Restart Codex to unload.

---

## OpenCode

### Prerequisites

- OpenCode CLI installed and authenticated (`$ opencode --version`)
- `git init` in your target project directory (OpenCode requires a git repo)

### Install

1. **Clone the coding-aegis repo**

   ```
   $ git clone https://github.com/robparrott/coding-aegis.git /tmp/coding-aegis
   ```

2. **Copy the skill into your target project**

   ```
   $ SKILL_SRC=/tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis
   $ mkdir -p .opencode/skills
   $ cp -r "$SKILL_SRC" .opencode/skills/coding-aegis
   ```

3. **Remove the clone**

   The installed skill is self-contained. The clone is only needed during setup.

   ```
   $ rm -rf /tmp/coding-aegis
   ```

### Verify

In an OpenCode session:

```
/coding-aegis list
```

*Expect:* Catalog output listing packages by tier.

### Install a package

```
/coding-aegis install <package-name>
```

OpenCode installs packages as:
- **Rules**: appended to `AGENTS.md` as `<!-- aegis:begin -->` / `<!-- aegis:end -->` sections
- **Skills**: copied to `.opencode/skills/<name>/`

### Uninstall a package

```
/coding-aegis uninstall <package-name>
```

### Updating

Re-clone temporarily, copy the updated skill over the existing one, then remove the clone:

```
$ git clone https://github.com/robparrott/coding-aegis.git /tmp/coding-aegis
$ cp -r /tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis .opencode/skills/coding-aegis
$ rm -rf /tmp/coding-aegis
```

### Removing

```
$ rm -rf .opencode/skills/coding-aegis
```

---

## Google Gemini CLI

### Prerequisites

- Gemini CLI installed (`$ gemini --version`)
- Authenticated (`$ gemini auth login`)
- `git init` in your target project directory (Gemini requires a git repo for workspace-scoped skills)

### Install

1. **Clone the repo**

   ```
   $ git clone https://github.com/robparrott/coding-aegis.git /tmp/coding-aegis
   ```

2. **Link the skill** — choose a scope:

   **User scope** (available in all projects):
   ```
   $ gemini skills link /tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis \
     --scope user --consent
   ```

   **Workspace scope** (this project only, run from the project directory):
   ```
   $ gemini skills link /tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis \
     --scope workspace --consent
   ```

3. **Remove the clone** — the installed skill is self-contained:

   ```
   $ rm -rf /tmp/coding-aegis
   ```

### Verify

```
$ gemini skills list
```

Should show: `coding-aegis`

### Install a package

```
/coding-aegis install <package-name>
```

Gemini installs packages as:
- **Rules**: written to `.gemini/rules/aegis--<pkg>--<rule>.md`
- **Skills**: copied to `.gemini/skills/<name>/`

### Uninstall a package

```
/coding-aegis uninstall <package-name>
```

### Updating

Re-clone temporarily, relink at the same scope, then remove the clone:

```
$ git clone https://github.com/robparrott/coding-aegis.git /tmp/coding-aegis
$ gemini skills link /tmp/coding-aegis/modules/bootstrap/coding-aegis/skills/coding-aegis \
  --scope user --consent
$ rm -rf /tmp/coding-aegis
```

Use `--scope workspace` instead if the skill was installed at workspace scope.

### Removing

```
$ gemini skills uninstall coding-aegis --scope user
```

Or, if installed at workspace scope:

```
$ gemini skills uninstall coding-aegis --scope workspace
```

---


## GitHub Copilot

*Stub — to be authored when Copilot bootstrap mechanism is designed.*

---

## Cross-tool notes

- **Skill invocation syntax** differs by tool: Claude Code, Cursor, Gemini, and OpenCode use `/skill-name`; Codex uses `$skill-name`
- **Install paths** are auto-detected — the skill places files where each tool discovers them
- **Catalog access** — fetched automatically from GitHub on first use via `ensure_catalog()`. No local clone required at runtime; the catalog is cached in `.coding-aegis-catalog/` with a 30-second TTL
- **Rules** are installed as markdown files with `managed-by: coding-aegis` frontmatter (rule-based tools) or as `<!-- aegis:begin/end -->` sections in `AGENTS.md` (Codex, OpenCode)
- **Skills** are installed into the tool's discovery path and are immediately invocable without a restart (except Codex)
