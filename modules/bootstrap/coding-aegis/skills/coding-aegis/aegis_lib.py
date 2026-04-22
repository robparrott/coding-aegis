#!/usr/bin/env python3
"""Shared library for coding-aegis skill scripts.

Provides catalog resolution (sparse git clone with TTL), YAML/frontmatter
parsing, tool detection, and install-path helpers.

Stdlib only — no pip dependencies. Requires Python 3.8+.
"""
import glob
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Import detect_tool from the same skill directory
sys.path.insert(0, str(Path(__file__).parent))
from detect_tool import detect_tool as _detect_tool_fn


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_REPO = "https://github.com/robparrott/coding-aegis.git"
CACHE_DIR = ".coding-aegis-catalog"
CACHE_TTL = 30  # seconds

TIERS = ["required", "best-practices", "optional", "goodies"]
ARTIFACT_TYPE_ORDER = ["rule", "skill", "agent", "mcp", "plugin"]

# Per-tool install path configuration.
# user_scope_base: home-relative path for user scope when it differs from scope_base
#   (e.g. opencode uses ~/.config/opencode for user scope, .opencode for project scope)
TOOL_PATHS = {
    "claude":    {"scope_base": ".claude",   "skills_dir": "skills"},
    "gemini":    {"scope_base": ".gemini",   "skills_dir": "skills",
                  "skills_base": ".gemini"},  # rules → .gemini/rules/, skills → .gemini/skills/
    "codex":     {"scope_base": ".agents",   "skills_dir": ".agents/skills",
                  "skills_base": "."},  # skills install relative to CWD, not scope_base
    "cursor":    {"scope_base": ".cursor",   "skills_dir": "skills", "rule_ext": ".mdc"},
    "windsurf":  {"scope_base": ".windsurf", "skills_dir": "skills"},
    # Copilot: project skills → .github/skills/<name>/SKILL.md
    #          user skills   → ~/.copilot/skills/<name>/SKILL.md
    #          rules (always-on) → .github/copilot-instructions.md (single global file)
    #          rules (file-scoped) → .github/instructions/aegis--<pkg>--<rule>.instructions.md
    # No invocable skill execution in Copilot CLI today (rules-only delivery confirmed).
    # > NEEDS VALIDATION ON COPILOT MACHINE
    "copilot":   {"scope_base": ".github",   "skills_dir": "skills",
                  "user_scope_base": ".copilot",
                  "rule_ext": ".instructions.md"},
    "opencode":  {"scope_base": ".opencode", "skills_dir": "skills",
                  "user_scope_base": ".config/opencode"},
}


# ---------------------------------------------------------------------------
# Tool detection
# ---------------------------------------------------------------------------

def detect_tool():
    """Return the active tool name using detect_tool.py."""
    return _detect_tool_fn()["tool"]


# ---------------------------------------------------------------------------
# Catalog resolution
# ---------------------------------------------------------------------------

def ensure_catalog(catalog_override=None):
    """Return Path to modules/ catalog, cloning/refreshing from GitHub as needed.

    If catalog_override is set, return it directly (for dev/testing).
    Otherwise, maintain a sparse clone of just modules/ in .coding-aegis-catalog/
    in the current working directory, refreshing if the 30-second TTL has expired.
    """
    if catalog_override:
        p = Path(catalog_override)
        if not p.is_dir():
            _die(f"Catalog not found: {catalog_override}")
        return p

    cache_root = Path.cwd() / CACHE_DIR
    ts_file = cache_root / ".cache_ts"

    # Fresh cache — return immediately
    if ts_file.is_file():
        try:
            age = time.time() - float(ts_file.read_text().strip())
            if age < CACHE_TTL:
                pkgs = cache_root / "modules"
                if pkgs.is_dir():
                    return pkgs
        except (ValueError, OSError):
            pass

    if cache_root.is_dir():
        # Stale — pull
        print("Refreshing catalog...", file=sys.stderr)
        result = subprocess.run(
            ["git", "-C", str(cache_root), "pull", "--ff-only", "-q"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            # Pull failed (e.g. diverged) — wipe and re-clone
            import shutil
            shutil.rmtree(str(cache_root))
            _clone_catalog(cache_root)
    else:
        _clone_catalog(cache_root)

    ts_file.write_text(str(time.time()))
    pkgs = cache_root / "modules"
    if not pkgs.is_dir():
        _die("Catalog clone succeeded but modules/ directory not found.")
    return pkgs


def _clone_catalog(cache_root):
    """Perform a sparse shallow clone of just modules/ into cache_root."""
    print("Fetching catalog from GitHub...", file=sys.stderr)
    r1 = subprocess.run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
         GITHUB_REPO, str(cache_root)],
        capture_output=True, text=True
    )
    if r1.returncode != 0:
        _die(f"git clone failed:\n{r1.stderr.strip()}")
    r2 = subprocess.run(
        ["git", "-C", str(cache_root), "sparse-checkout", "set", "modules/"],
        capture_output=True, text=True
    )
    if r2.returncode != 0:
        _die(f"git sparse-checkout failed:\n{r2.stderr.strip()}")


# ---------------------------------------------------------------------------
# Minimal YAML parser
# ---------------------------------------------------------------------------
# Handles ONLY the shapes present in pkg.yaml and rule frontmatter.

def parse_simple_yaml(text):
    """Parse a pkg.yaml-shaped YAML string into a dict."""
    result = {}
    lines = text.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        m = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        value = m.group(2).strip()

        if not value:
            items = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip() or (not next_line[0].isspace() and next_line[0] != ' '):
                    break
                lm = re.match(r'^\s+-\s+(\w[\w-]*):\s*(.*)', next_line)
                if lm:
                    item = {lm.group(1): _unquote(lm.group(2).strip())}
                    i += 1
                    while i < len(lines):
                        cont = lines[i]
                        cm = re.match(r'^\s+(\w[\w-]*):\s*(.*)', cont)
                        if cm and not re.match(r'^\s+-', cont):
                            item[cm.group(1)] = _unquote(cm.group(2).strip())
                            i += 1
                        else:
                            break
                    items.append(item)
                else:
                    nm = re.match(r'^\s+(\w[\w-]*):\s*(.*)', next_line)
                    if nm:
                        if not isinstance(result.get(key), dict):
                            result[key] = {}
                        result[key][nm.group(1)] = _unquote(nm.group(2).strip())
                    i += 1
            if items:
                result[key] = items
            continue

        result[key] = _unquote(value)
        i += 1

    return result


def _unquote(s):
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Extract YAML frontmatter. Returns (dict, body)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break

    if end is None:
        return {}, text

    fm_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1:])
    return parse_simple_yaml(fm_text), body


def render_frontmatter(fm_dict, body):
    """Render frontmatter dict + body back into markdown."""
    lines = ["---"]
    for k, v in fm_dict.items():
        if isinstance(v, str) and (":" in v or '"' in v or v != v.strip()):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body


def merge_frontmatter(source_fm, managed_keys):
    """Merge managed keys into source frontmatter. Managed keys win."""
    merged = dict(source_fm)
    merged.update(managed_keys)
    return merged


# ---------------------------------------------------------------------------
# Catalog helpers
# ---------------------------------------------------------------------------

def scan_tier(catalog, tier):
    """Glob and parse all pkg.yaml files in a tier directory."""
    tier_dir = catalog / tier
    if not tier_dir.is_dir():
        return []

    packages = []
    for pkg_yaml in sorted(tier_dir.glob("*/pkg.yaml")):
        try:
            data = parse_simple_yaml(pkg_yaml.read_text())
            data["tier"] = tier
            data["package_dir"] = str(pkg_yaml.parent)
            data["artifact_summary"] = compute_artifact_summary(data.get("artifacts", []))
            data["artifact_count"] = len(data.get("artifacts", []))
            packages.append(data)
        except Exception as e:
            print(f"Warning: failed to parse {pkg_yaml}: {e}", file=sys.stderr)

    packages.sort(key=lambda p: p.get("name", ""))
    return packages


def compute_artifact_summary(artifacts):
    """Summarize artifacts as '2 rules, 1 skill'."""
    counts = {}
    for a in artifacts:
        t = a.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1

    parts = []
    for t in ARTIFACT_TYPE_ORDER:
        if t in counts:
            n = counts[t]
            label = t + "s" if n != 1 else t
            parts.append(f"{n} {label}")
    for t, n in counts.items():
        if t not in ARTIFACT_TYPE_ORDER:
            label = t + "s" if n != 1 else t
            parts.append(f"{n} {label}")

    return ", ".join(parts) if parts else "none"


def compute_target_filename(pkg_name, artifact, tool=None):
    """Compute the installed filename for a rule/agent artifact.

    Uses the tool's configured rule_ext (e.g. '.mdc' for Cursor) if provided,
    otherwise defaults to '.md'.
    """
    basename = Path(artifact["path"]).stem
    ext = TOOL_PATHS.get(tool, {}).get("rule_ext", ".md")
    return f"aegis--{pkg_name}--{basename}{ext}"


def find_package(catalog, name):
    """Search all tiers + bootstrap for a package by name.

    Returns (pkg_data dict, pkg_dir Path) or (None, None).
    """
    for tier in TIERS + ["bootstrap"]:
        pkg_yaml = catalog / tier / name / "pkg.yaml"
        if pkg_yaml.is_file():
            data = parse_simple_yaml(pkg_yaml.read_text())
            data["tier"] = tier
            data["artifact_summary"] = compute_artifact_summary(data.get("artifacts", []))
            return data, pkg_yaml.parent
    return None, None


# ---------------------------------------------------------------------------
# Install-path helpers
# ---------------------------------------------------------------------------

def resolve_scope_base(tool, scope):
    """Return the absolute scope_base Path for the given tool and scope."""
    cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])
    if scope == "user":
        user_base = cfg.get("user_scope_base", cfg["scope_base"])
        return Path.home() / user_base
    return Path.cwd() / cfg["scope_base"]


def resolve_skill_base(tool):
    """Return the base Path under which skills are installed."""
    cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])
    skills_base = cfg.get("skills_base")
    if skills_base is not None:
        return Path(skills_base).resolve()
    # Falls back to scope_base (project scope)
    return Path.cwd() / cfg["scope_base"]


def skill_install_dir(tool, skill_name, scope="project"):
    """Return the absolute Path of the skill install directory."""
    cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])
    skills_dir = cfg["skills_dir"]
    skills_base = cfg.get("skills_base")
    if skills_base is not None:
        return (Path(skills_base).resolve() / skills_dir / skill_name)
    scope_base = resolve_scope_base(tool, scope)
    return scope_base / skills_dir / skill_name


# ---------------------------------------------------------------------------
# AGENTS.md helpers
# ---------------------------------------------------------------------------

def agents_md_path():
    """Return Path to AGENTS.md in CWD."""
    return Path.cwd() / "AGENTS.md"


def strip_agents_md_section(name, path=None):
    """Remove aegis:begin/end markers for package `name` from AGENTS.md.

    Returns True if the file was modified.
    """
    p = path or agents_md_path()
    if not p.is_file():
        return False
    text = p.read_text()
    pattern = (
        r"<!-- aegis:begin package=" + re.escape(name) + r"[^\n]*-->\n"
        r".*?"
        r"<!-- aegis:end package=" + re.escape(name) + r"[^\n]*-->\n?"
    )
    if re.search(pattern, text, re.DOTALL):
        new_text = re.sub(pattern, "", text, flags=re.DOTALL)
        p.write_text(new_text)
        return True
    return False


def upsert_agents_md_section(content, name, path=None):
    """Insert or replace the aegis:begin/end section for `name` in AGENTS.md.

    If the section already exists it is replaced in-place. Otherwise it is
    appended. Creates the file if it does not exist.
    """
    p = path or agents_md_path()
    existing = p.read_text() if p.is_file() else ""
    pattern = (
        r"<!-- aegis:begin package=" + re.escape(name) + r"[^\n]*-->\n"
        r".*?"
        r"<!-- aegis:end package=" + re.escape(name) + r"[^\n]*-->\n?"
    )
    if re.search(pattern, existing, re.DOTALL):
        new_text = re.sub(pattern, content, existing, flags=re.DOTALL)
    else:
        sep = "\n" if existing and not existing.endswith("\n") else ""
        new_text = existing + sep + content
    p.write_text(new_text)


def rebuild_governance_table(scope_base, agents_md):
    """Rebuild (or remove) the ## Installed Governance Rules section in AGENTS.md.

    Scans scope_base/rules/aegis--* for managed files, builds the table.
    If no files remain, removes the section.
    """
    rules_dir = scope_base / "rules"
    rows = []
    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob("aegis--*")):
            if f.is_file():
                fm, _ = parse_frontmatter(f.read_text())
                rows.append({
                    "rule": fm.get("rule", f.stem),
                    "package": fm.get("package", "unknown"),
                    "version": fm.get("version", "?"),
                    "tier": fm.get("tier", "?"),
                    "file": f"`.claude/rules/{f.name}`",
                })

    if not agents_md.is_file():
        if not rows:
            return
        agents_md.write_text(_governance_section(rows))
        return

    text = agents_md.read_text()
    marker_re = re.compile(
        r"## Installed Governance Rules\n.*?(?=\n## |\Z)", re.DOTALL
    )

    if not rows:
        new_text = marker_re.sub("", text).rstrip() + "\n"
        agents_md.write_text(new_text)
        return

    section = _governance_section(rows)
    if marker_re.search(text):
        new_text = marker_re.sub(section.rstrip(), text)
    else:
        sep = "\n" if not text.endswith("\n") else ""
        new_text = text + sep + section
    agents_md.write_text(new_text)


def _governance_section(rows):
    lines = [
        "## Installed Governance Rules\n",
        "<!-- managed by coding-aegis — do not edit manually -->\n\n",
        "| Rule | Package | Version | Tier | File |\n",
        "|------|---------|---------|------|------|\n",
    ]
    for r in rows:
        lines.append(
            f"| {r['rule']} | {r['package']} | {r['version']} | {r['tier']} | {r['file']} |\n"
        )
    return "".join(lines)


# ---------------------------------------------------------------------------
# Error helper
# ---------------------------------------------------------------------------

def _die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)
