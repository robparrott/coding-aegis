# Install Guide

How to install the coding-aegis skill and use it to manage governance packages, organized by coding-agent tool.

---

## Claude Code

### Prerequisites

- Claude Code CLI v1.0.33+ (`claude --version`)
- GitHub access to the coding-aegis repo (or a local clone)

### Steps

1. **Add the coding-aegis marketplace**

   From GitHub:
   ```
   /plugin marketplace add robparrott/coding-aegis
   ```

   Or from a local clone:
   ```bash
   claude plugin marketplace add /path/to/coding-aegis
   ```

   *Expect:* `Successfully added marketplace: robparrott-coding-aegis`

   Verify:
   ```bash
   claude plugin marketplace list
   # Should show: coding-aegis
   ```

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
   /coding-aegis show <package-name>
   ```

   *Expect:* Packages listed by tier (required, best-practices, optional, goodies).

6. **Install governance packages**

   ```
   /coding-aegis install <package-name>
   ```

   Start with `required` tier packages — these are non-negotiable governance. Then review `best-practices` for recommended defaults.

   The skill installs rule files to `.claude/rules/` and skill files to `.claude/skills/`. Restart Claude Code to load newly installed skills.

7. **Uninstall a governance package**

   ```
   /coding-aegis uninstall <package-name>
   ```

   Removes all governance-managed files for the package. Restart Claude Code to unload removed skills.

8. **Check status**

   ```
   /coding-aegis status
   ```

   Shows installed packages, versions, and whether they're current with the catalog.

### Updating

To pick up new packages or updates from the catalog:

```
/plugin marketplace update robparrott-coding-aegis
```

### Troubleshooting

**Plugin says "already installed" but skill is not available**

This can happen when the marketplace was re-registered under a different name or the cached version is stale. Fix by removing both the plugin and the marketplace, then reinstalling:

```
/plugin uninstall coding-aegis@coding-aegis
/plugin marketplace remove coding-aegis
/plugin marketplace add robparrott/coding-aegis
/plugin install coding-aegis@robparrott-coding-aegis
```

Restart Claude Code after reinstalling.

**Skill only works in the coding-aegis repo, not other projects**

The plugin was installed with local (project) scope. Uninstall and reinstall with user scope so it's available across all repositories.

### Removing

```bash
/plugin uninstall coding-aegis@robparrott-coding-aegis
/plugin marketplace remove robparrott-coding-aegis
```

Or using the CLI directly:
```bash
claude plugin uninstall coding-aegis@coding-aegis --scope user
claude plugin marketplace remove coding-aegis
```

---

## Cursor

### Prerequisites

- `cursor-agent` CLI installed (`brew install cursor-cli` on macOS)
- Authenticated (Cursor account)
- Local clone of the coding-aegis repo

> **macOS note**: After `brew install cursor-cli`, clear the quarantine flag:
> ```bash
> xattr -rd com.apple.quarantine "$(brew --prefix)/Caskroom/cursor-cli/<version>/"
> ```
> Substitute the installed version number. See [test-cursor.md](../test/test-cursor.md) for details.

### Install

Copy the skill directory into your target project:

```bash
SKILL_SRC=/path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis
mkdir -p .cursor/skills
cp -r "$SKILL_SRC" .cursor/skills/coding-aegis
```

The skill makes `/coding-aegis` available as an invocable skill in Cursor chat.

> **Symlinks also work** for personal use: `ln -s "$SKILL_SRC" .cursor/skills/coding-aegis`. Copy is preferred for team repos since symlinks require every contributor to have the same clone path.

### Verify

In a Cursor chat:

```
/coding-aegis list
```

*Expect:* Catalog output listing packages by tier.

### Updating

Pull a fresh copy of the skill directory:

```bash
cp -r /path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis .cursor/skills/coding-aegis
```

### Removing

```bash
rm -rf .cursor/skills/coding-aegis
```

---

## OpenAI Codex

### Prerequisites

- Codex CLI installed and authenticated (`codex --version`)
- The coding-aegis repo pushed to GitHub (Codex installs from GitHub, not local paths)

### 1. Install the coding-aegis skill

From within your project directory, ask Codex to install the skill using its built-in `$skill-installer`:

```
$skill-installer install --repo robparrott/coding-aegis --path pkgs/bootstrap/coding-aegis/skills/coding-aegis
```

The skill installs to `~/.codex/skills/coding-aegis/`. Restart Codex to pick up the new skill.

### 2. Browse the catalog

```
$coding-aegis list
$coding-aegis show <package-name>
```

The catalog is fetched automatically from GitHub on first use and cached locally in `.coding-aegis-catalog/`. No local clone needed.

### 3. Install a package

```
$coding-aegis install <package-name>
```

Codex installs governance packages as:
- **Rules**: appended to `AGENTS.md` as `<!-- aegis:begin -->` / `<!-- aegis:end -->` sections
- **Skills**: copied to `.agents/skills/<name>/`

### 4. Uninstall a package

```
$coding-aegis uninstall <package-name>
```

Removes the `AGENTS.md` section and skill directory.

### 5. Remove coding-aegis

```bash
rm -rf ~/.codex/skills/coding-aegis
```

Restart Codex to unload.

---

## OpenCode

### Prerequisites

- OpenCode CLI installed and authenticated (`opencode --version`)
- Local clone of the coding-aegis repo
- `git init` in your target project directory (OpenCode requires a git repo)

### Install

Copy the skill directory into your target project:

```bash
SKILL_SRC=/path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis
mkdir -p .opencode/skills
cp -r "$SKILL_SRC" .opencode/skills/coding-aegis
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

OpenCode installs governance packages as:
- **Rules**: appended to `AGENTS.md` as `<!-- aegis:begin -->` / `<!-- aegis:end -->` sections
- **Skills**: copied to `.opencode/skills/<name>/`

### Uninstall a package

```
/coding-aegis uninstall <package-name>
```

### Remove coding-aegis

```bash
rm -rf .opencode/skills/coding-aegis
```

---

## Google Gemini CLI

### Prerequisites

- Gemini CLI installed (`gemini --version`)
- Authenticated (Google account via `gemini auth login`)
- Local clone of the coding-aegis repo
- `git init` in your target project directory (Gemini requires a git repo for workspace-scoped skills)

### 1. Install the coding-aegis skill

Choose a scope:

**User scope** (available in all projects):
```bash
gemini skills link /path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis \
  --scope user --consent
```

**Workspace scope** (this project only, from the project directory):
```bash
gemini skills link /path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis \
  --scope workspace --consent
```

Verify:
```bash
gemini skills list
# Should show: coding-aegis
```

### 2. Browse the catalog

```
/coding-aegis list
/coding-aegis show <package-name>
```

The catalog is fetched automatically from GitHub on first use and cached locally in `.coding-aegis-catalog/`. No local clone of the catalog is needed.

### 3. Install a package

```
/coding-aegis install <package-name>
```

Gemini installs governance packages as:
- **Rules**: written to `.gemini/rules/aegis--<pkg>--<rule>.md`
- **Skills**: copied to `.gemini/skills/<name>/`

### 4. Uninstall a package

```
/coding-aegis uninstall <package-name>
```

### 5. Remove coding-aegis

```bash
# Match the scope used during install:
gemini skills uninstall coding-aegis --scope user
# or:
gemini skills uninstall coding-aegis --scope workspace
```

---

## Windsurf

*Stub — to be authored when Windsurf bootstrap mechanism is designed.*

---

## GitHub Copilot

*Stub — to be authored when Copilot bootstrap mechanism is designed.*

---

## Cross-tool notes

- **Skill invocation syntax** differs by tool: Claude Code, Cursor, Gemini, and OpenCode use `/skill-name`; Codex uses `$skill-name`
- **Install paths** are auto-detected — the skill places files where each tool discovers them
- **Catalog access** — fetched automatically from GitHub on first use via `ensure_catalog()`. No local clone required; the catalog is cached in `.coding-aegis-catalog/` with a 30-second TTL
- **Rules** are installed as markdown files with `managed-by: coding-aegis` frontmatter (rule-based tools) or as `<!-- aegis:begin/end -->` sections in `AGENTS.md` (Codex, OpenCode)
- **Skills** are installed into the tool's discovery path and are immediately invocable without a restart (except Codex)
