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

- Cursor editor
- Local clone of the coding-aegis repo

### Install

From your target project directory, symlink the governance rule and skill into Cursor's project locations:

```bash
mkdir -p .cursor/rules .cursor/skills/coding-aegis
ln -s /path/to/coding-aegis/pkgs/bootstrap/coding-aegis/rules/coding-aegis.mdc .cursor/rules/aegis--coding-aegis.mdc
ln -s /path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis/SKILL.md .cursor/skills/coding-aegis/SKILL.md
```

The `alwaysApply: true` frontmatter causes Cursor to inject the rule into every chat automatically. The skill symlink makes `/coding-aegis` available as an invocable skill. No restart required.

### Verify

Open a Cursor chat and ask: "What governance rules are active?" The agent should reference coding-aegis catalog tiers (required, best-practices, optional, goodies) and the `aegis--` prefix convention.

### Updating

`git pull` in your coding-aegis clone. The symlink picks up changes immediately — no restart needed.

### Removing

```bash
rm .cursor/rules/aegis--coding-aegis.mdc
rm -rf .cursor/skills/coding-aegis
```

---

## OpenAI Codex

### Prerequisites

- Codex CLI installed (`codex --version`)
- Authenticated (`codex login`)

### 1. Install the coding-aegis skill

Codex uses its built-in `$skill-installer` to install skills from GitHub:

```
$skill-installer install --repo <org>/coding-aegis --path pkgs/bootstrap/coding-aegis/skills/coding-aegis
```

The skill is installed to `~/.codex/skills/coding-aegis/`. Restart Codex to pick up new skills.

### 2. Browse the catalog

Use the skill's `$` invocation syntax:

```
$coding-aegis list
$coding-aegis show <package-name>
```

The catalog (`pkgs/`) must be accessible in the current working directory. Clone or symlink the coding-aegis repo, or run from within it.

### 3. Install a package

```
$coding-aegis install <package-name>
```

The skill auto-detects that it's running in Codex and installs:
- Rule files to `.claude/rules/` (cross-tool governance standard)
- Skill files to `.agents/skills/` (Codex discovery path)

### 4. Uninstall a package

```
$coding-aegis uninstall <package-name>
```

### 5. Remove coding-aegis

Delete the skill directory:

```bash
rm -rf ~/.codex/skills/coding-aegis
```

Restart Codex to unload.

---

## Google Gemini CLI

### Prerequisites

- Gemini CLI installed (`gemini --version`)
- Authenticated (Google Cloud credentials)

### 1. Install the coding-aegis skill

Link the skill from a local clone of the repo:

```bash
gemini skills link /path/to/coding-aegis/pkgs/bootstrap/coding-aegis/skills/coding-aegis --scope user --consent
```

Verify:
```bash
gemini skills list
# Should show: coding-aegis [Enabled]
```

### 2. Browse the catalog

Use the skill's slash commands:

```
/coding-aegis list
/coding-aegis show <package-name>
```

The catalog (`pkgs/`) must be accessible in the current working directory.

### 3. Install a package

```
/coding-aegis install <package-name>
```

### 4. Uninstall a package

```
/coding-aegis uninstall <package-name>
```

### 5. Remove coding-aegis

```bash
gemini skills uninstall coding-aegis --scope user
```

---

## Windsurf

*Stub — to be authored when Windsurf bootstrap mechanism is designed.*

---

## GitHub Copilot

*Stub — to be authored when Copilot bootstrap mechanism is designed.*

---

## Cross-tool notes

- **Skill invocation syntax** differs by tool: Claude Code, Cursor, and Gemini use `/skill-name`; Codex uses `$skill-name`
- **Install paths** are auto-detected — the skill places files where each tool discovers them
- **Rules** are markdown files with `managed-by: coding-aegis` frontmatter. The skill only touches files with the `aegis--` prefix
- **Catalog access** — the `pkgs/` directory must be reachable from the working directory. Clone the repo or ensure it's accessible
