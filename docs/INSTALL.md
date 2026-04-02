# Install Guide

How to install the coding-aegis skill and use it to manage governance packages. Each section covers one coding agent tool with the exact commands validated by the automated test suite.

## Claude Code

### Prerequisites

- Claude Code installed (`claude --version`)
- Authenticated (`claude auth`)

### 1. Register the marketplace

```bash
claude plugin marketplace add <path-or-url-to-coding-aegis-repo>
```

For a local clone:
```bash
claude plugin marketplace add /path/to/coding-aegis
```

Verify:
```bash
claude plugin marketplace list
# Should show: coding-aegis
```

### 2. Install the coding-aegis skill

```bash
claude plugin install coding-aegis@coding-aegis --scope user
```

Verify:
```bash
claude plugin list
# Should show: coding-aegis@coding-aegis ✔ enabled
```

### 3. Browse the catalog

In Claude Code, use the skill's slash commands:

```
/coding-aegis list
/coding-aegis show <package-name>
```

### 4. Install a package

```
/coding-aegis install <package-name>
```

You'll be asked to choose a scope:
- **Project** — `.claude/` in the current repo (shared via source control)
- **User** — `~/.claude/` in your home directory (all projects)

The skill installs rule files to `.claude/rules/` and skill files to `.claude/skills/`. Restart Claude Code to load newly installed skills.

### 5. Uninstall a package

```
/coding-aegis uninstall <package-name>
```

Removes all governance-managed files for the package. Restart Claude Code to unload removed skills.

### 6. Check status

```
/coding-aegis status
```

Shows installed packages, versions, and whether they're current with the catalog.

### 7. Remove coding-aegis

```bash
claude plugin uninstall coding-aegis@coding-aegis --scope user
claude plugin marketplace remove coding-aegis
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

## Cursor (WIP)

Cursor support is in progress. The Cursor CLI binary is `cursor-agent` (Homebrew) or `agent` (vendor install). See the [test script](../tests/test-cursor-skill-install.sh) for the planned user journey and [Phase 3 backlog](backlog/phase-3-cursor-bootstrap.md) for tracking.

---

## Cross-tool notes

- **Skill invocation syntax** differs by tool: Claude and Gemini use `/skill-name`, Codex uses `$skill-name`
- **Install paths** are auto-detected — the skill places files where each tool discovers them
- **Rules** are markdown files with `managed-by: coding-aegis` frontmatter. The skill only touches files with the `aegis--` prefix
- **Catalog access** — the `pkgs/` directory must be reachable from the working directory. Clone the repo or ensure it's accessible
