#!/usr/bin/env python3
"""CLI helper for the coding-aegis skill.

Provides structured JSON output for catalog operations so the skill
can delegate filesystem scanning and YAML parsing to a single Bash call
instead of multiple Glob/Read cycles.

Stdlib only — no pip dependencies. Requires Python 3.8+.
"""
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

# Tier scan order (bootstrap excluded from listings)
TIERS = ["required", "best-practices", "optional", "goodies"]

ARTIFACT_TYPE_ORDER = ["rule", "skill", "agent", "mcp", "plugin"]

# Per-tool install path configuration.
# See references/install-rules.md for the full cross-tool mapping.
TOOL_PATHS = {
    "claude":   {"scope_base": ".claude",   "skills_dir": "skills"},
    "codex":    {"scope_base": ".claude",   "skills_dir": ".agents/skills",
                 "skills_base": "."},  # skills install relative to CWD, not scope_base
    "cursor":   {"scope_base": ".cursor",   "skills_dir": "skills"},
    "windsurf": {"scope_base": ".windsurf", "skills_dir": "skills"},
    "copilot":  {"scope_base": ".github",   "skills_dir": "skills"},
}


def _detect_tool():
    """Auto-detect the active coding agent tool from environment signals.

    Detection order (first match wins):
      - CODEX_HOME env var → codex
      - .cursor/ directory in CWD or repo root → cursor
      - .windsurf/ directory in CWD or repo root → windsurf
      - .github/copilot-instructions.md → copilot
      - Default → claude
    """
    # Codex sets CODEX_SANDBOX, CODEX_CI, CODEX_THREAD_ID in its sandbox
    if any(k.startswith("CODEX_") for k in os.environ):
        return "codex"
    cwd = Path.cwd()
    if (cwd / ".cursor").is_dir():
        return "cursor"
    if (cwd / ".windsurf").is_dir():
        return "windsurf"
    if (cwd / ".github" / "copilot-instructions.md").is_file():
        return "copilot"
    return "claude"


# ---------------------------------------------------------------------------
# Minimal YAML parser
# ---------------------------------------------------------------------------
# Handles ONLY the shapes present in pkg.yaml and rule frontmatter:
#   - flat scalar key-value pairs (name: value)
#   - one list-of-dicts (artifacts: [{type: ..., path: ...}])
#   - quoted strings with colons
# This is NOT a general YAML parser.

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

        # Check for key: value at top level (no leading whitespace)
        m = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if not m:
            i += 1
            continue

        key = m.group(1)
        value = m.group(2).strip()

        # If value is empty, check for list or nested dict
        if not value:
            # Peek ahead for list items (- key: val)
            items = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip() or (not next_line[0].isspace() and next_line[0] != ' '):
                    break
                # List item start
                lm = re.match(r'^\s+-\s+(\w[\w-]*):\s*(.*)', next_line)
                if lm:
                    item = {lm.group(1): _unquote(lm.group(2).strip())}
                    i += 1
                    # Collect continuation keys for this item
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
                    # Nested scalar (e.g. source.type, source.repo)
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
    """Remove surrounding quotes from a string."""
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def parse_frontmatter(text):
    """Extract YAML frontmatter from a markdown file.

    Returns (dict, body) where dict is the parsed frontmatter and body
    is everything after the closing ---. Returns ({}, text) if no
    frontmatter found.
    """
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
    """Render a frontmatter dict + body back into markdown text."""
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
# Catalog resolution
# ---------------------------------------------------------------------------

def resolve_catalog(from_path=None):
    """Find the pkgs/ catalog directory by walking up from from_path."""
    start = Path(from_path) if from_path else Path.cwd()
    start = start.resolve()

    # Strategy 1: look for pkgs/required/ starting from CWD and walking up
    p = start
    for _ in range(20):
        candidate = p / "pkgs"
        if candidate.is_dir() and (candidate / "required").is_dir():
            return candidate
        if p.parent == p:
            break
        p = p.parent

    # Strategy 2: check if we're inside pkgs/bootstrap/coding-aegis/
    parts = start.parts
    for i, part in enumerate(parts):
        if part == "pkgs" and i + 2 < len(parts):
            candidate = Path(*parts[: i + 1])
            if (candidate / "required").is_dir():
                return candidate

    return None


# ---------------------------------------------------------------------------
# Helpers
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
            data["artifact_summary"] = compute_artifact_summary(
                data.get("artifacts", [])
            )
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

    # Any types not in the order list
    for t, n in counts.items():
        if t not in ARTIFACT_TYPE_ORDER:
            label = t + "s" if n != 1 else t
            parts.append(f"{n} {label}")

    return ", ".join(parts) if parts else "none"


def compute_target_filename(pkg_name, artifact):
    """Compute the installed filename for a rule/agent artifact."""
    basename = Path(artifact["path"]).stem
    return f"aegis--{pkg_name}--{basename}.md"


def _error(msg):
    """Print error JSON and exit."""
    print(json.dumps({"error": msg}))
    print(msg, file=sys.stderr)
    sys.exit(1)


def _resolve_or_error(args):
    """Resolve catalog from args or error out."""
    cat = resolve_catalog(args.catalog) if args.catalog else resolve_catalog()
    if cat is None:
        _error(
            "Could not locate the coding-aegis package catalog. "
            "Ensure pkgs/ is accessible from the current working directory."
        )
    return cat


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_resolve_catalog(args):
    cat = resolve_catalog(args.from_path)
    if cat is None:
        _error("Could not locate the coding-aegis package catalog.")
    print(json.dumps({"catalog": str(cat)}))


def cmd_list(args):
    cat = _resolve_or_error(args)
    tiers_out = []
    for tier in TIERS:
        packages = scan_tier(cat, tier)
        tiers_out.append({
            "name": tier,
            "packages": [
                {
                    "name": p.get("name"),
                    "version": p.get("version"),
                    "description": p.get("description"),
                    "tier": tier,
                    "artifact_count": p.get("artifact_count", 0),
                    "artifact_summary": p.get("artifact_summary", "none"),
                }
                for p in packages
            ],
        })
    print(json.dumps({"catalog": str(cat), "tiers": tiers_out}, indent=2))


def cmd_show(args):
    cat = _resolve_or_error(args)
    name = args.package

    # Search all tiers + bootstrap
    for tier in TIERS + ["bootstrap"]:
        pkg_yaml = cat / tier / name / "pkg.yaml"
        if pkg_yaml.is_file():
            data = parse_simple_yaml(pkg_yaml.read_text())
            data["tier"] = tier
            data["package_dir"] = str(pkg_yaml.parent)
            data["artifact_summary"] = compute_artifact_summary(
                data.get("artifacts", [])
            )

            # Read README if present
            readme_path = pkg_yaml.parent / "README.md"
            if readme_path.is_file():
                lines = readme_path.read_text().splitlines()
                data["readme"] = "\n".join(lines[:200])
            else:
                data["readme"] = None

            print(json.dumps(data, indent=2))
            return

    _error(f"Package '{name}' not found in the catalog.")


def cmd_install_prep(args):
    cat = _resolve_or_error(args)
    name = args.package
    explicit_tool = getattr(args, "tool", None)
    tool = explicit_tool if explicit_tool else _detect_tool()
    tool_cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])

    # Find the package
    pkg_data = None
    pkg_dir = None
    for tier in TIERS + ["bootstrap"]:
        pkg_yaml = cat / tier / name / "pkg.yaml"
        if pkg_yaml.is_file():
            pkg_data = parse_simple_yaml(pkg_yaml.read_text())
            pkg_data["tier"] = tier
            pkg_dir = pkg_yaml.parent
            break

    if pkg_data is None:
        _error(f"Package '{name}' not found in the catalog.")

    artifacts_out = []
    for artifact in pkg_data.get("artifacts", []):
        a_type = artifact.get("type")
        a_path = artifact.get("path")
        source_path = pkg_dir / a_path

        if not source_path.is_file():
            print(
                f"Warning: artifact {a_path} not found at {source_path}",
                file=sys.stderr,
            )
            continue

        source_text = source_path.read_text()

        if a_type in ("rule", "agent"):
            # Merge managed-by frontmatter
            fm, body = parse_frontmatter(source_text)
            managed_keys = {
                "package": name,
                a_type: Path(a_path).stem,
                "version": pkg_data.get("version", "0.0.0"),
                "tier": pkg_data["tier"],
                "managed-by": "coding-aegis",
            }
            # Preserve description from source if present
            if "description" not in fm:
                managed_keys["description"] = (
                    f"{name} governance — {Path(a_path).stem}"
                )
            merged_fm = merge_frontmatter(fm, managed_keys)
            content = render_frontmatter(merged_fm, body)
            target_filename = compute_target_filename(name, artifact)
            target_subdir = a_type + "s"  # rules/ or agents/

            artifacts_out.append({
                "type": a_type,
                "source_path": str(source_path),
                "target_subdir": target_subdir,
                "target_filename": target_filename,
                "content": content,
            })

        elif a_type == "skill":
            # Skills: copy the entire skill directory.
            # Path varies by tool (e.g. .claude/skills/ vs .agents/skills/).
            skill_name = Path(a_path).parent.name
            skill_dir = pkg_dir / "skills" / skill_name
            skills_prefix = tool_cfg["skills_dir"]
            skill_target = f"{skills_prefix}/{skill_name}"
            # Some tools (Codex) install skills relative to CWD, not scope_base
            skill_base = tool_cfg.get("skills_base")
            if skill_dir.is_dir():
                for f in sorted(skill_dir.rglob("*")):
                    if f.is_file():
                        rel = f.relative_to(skill_dir)
                        entry = {
                            "type": "skill",
                            "source_path": str(f),
                            "target_subdir": skill_target,
                            "target_filename": str(rel),
                            "content": f.read_text(),
                        }
                        if skill_base is not None:
                            entry["base_path"] = skill_base
                        artifacts_out.append(entry)
            else:
                # Single file skill
                entry = {
                    "type": "skill",
                    "source_path": str(source_path),
                    "target_subdir": skill_target,
                    "target_filename": Path(a_path).name,
                    "content": source_text,
                }
                if skill_base is not None:
                    entry["base_path"] = skill_base
                artifacts_out.append(entry)

        else:
            # mcp, plugin, etc. — pass through as-is
            artifacts_out.append({
                "type": a_type,
                "source_path": str(source_path),
                "target_subdir": a_type,
                "target_filename": Path(a_path).name,
                "content": source_text,
            })

    print(json.dumps({
        "name": name,
        "version": pkg_data.get("version"),
        "tier": pkg_data["tier"],
        "tool": tool,
        "scope_base": tool_cfg["scope_base"],
        "artifacts": artifacts_out,
    }, indent=2))


def cmd_status(args):
    cat = _resolve_or_error(args)

    scopes = args.scope
    if not scopes:
        scopes = []
        cwd_claude = Path.cwd() / ".claude"
        if cwd_claude.is_dir():
            scopes.append(str(cwd_claude))
        home_claude = Path.home() / ".claude"
        if home_claude.is_dir():
            scopes.append(str(home_claude))

    # Build catalog index for version comparison
    catalog_index = {}
    for tier in TIERS:
        for pkg in scan_tier(cat, tier):
            catalog_index[pkg["name"]] = pkg

    scopes_out = []
    for scope_path in scopes:
        sp = Path(scope_path)
        label = "Project" if ".claude" in sp.parts and sp.parent == Path.cwd() else "User"

        installed = {}  # pkg_name -> {artifacts: [], version: ...}

        # Scan rules
        rules_dir = sp / "rules"
        if rules_dir.is_dir():
            for f in sorted(rules_dir.glob("aegis--*")):
                if f.is_file():
                    fm, _ = parse_frontmatter(f.read_text())
                    pkg_name = fm.get("package", "unknown")
                    if pkg_name not in installed:
                        installed[pkg_name] = {
                            "installed_version": fm.get("version"),
                            "tier": fm.get("tier"),
                            "artifacts": [],
                        }
                    installed[pkg_name]["artifacts"].append({
                        "type": "rule",
                        "file": f.name,
                    })

        # Scan skills
        skills_dir = sp / "skills"
        if skills_dir.is_dir():
            for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
                skill_name = skill_md.parent.name
                # Try to match to a catalog package
                fm, _ = parse_frontmatter(skill_md.read_text())
                pkg_name = fm.get("package", skill_name)
                if pkg_name not in installed:
                    installed[pkg_name] = {
                        "installed_version": fm.get("version"),
                        "tier": fm.get("tier"),
                        "artifacts": [],
                    }
                installed[pkg_name]["artifacts"].append({
                    "type": "skill",
                    "file": f"skills/{skill_name}/SKILL.md",
                })

        # Cross-reference with catalog
        packages_out = []
        for pkg_name, info in sorted(installed.items()):
            cat_pkg = catalog_index.get(pkg_name)
            cat_version = cat_pkg["version"] if cat_pkg else None
            inst_version = info["installed_version"]

            if cat_version and inst_version:
                status = "current" if cat_version == inst_version else "outdated"
            elif cat_version:
                status = "unknown"
            else:
                status = "untracked"

            summary = compute_artifact_summary(info["artifacts"])
            packages_out.append({
                "name": pkg_name,
                "installed_version": inst_version,
                "catalog_version": cat_version,
                "tier": info.get("tier") or (cat_pkg["tier"] if cat_pkg else None),
                "artifact_summary": summary,
                "status": status,
                "artifacts": info["artifacts"],
            })

        scopes_out.append({
            "label": label,
            "path": str(sp),
            "packages": packages_out,
        })

    print(json.dumps({"scopes": scopes_out}, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="coding-aegis catalog helper"
    )
    sub = parser.add_subparsers(dest="command")

    # resolve-catalog
    p_resolve = sub.add_parser("resolve-catalog", help="Locate pkgs/ directory")
    p_resolve.add_argument("--from", dest="from_path", help="Start search from this path")

    # list
    p_list = sub.add_parser("list", help="List all packages in the catalog")
    p_list.add_argument("--catalog", help="Path to pkgs/ directory")

    # show
    p_show = sub.add_parser("show", help="Show package details")
    p_show.add_argument("package", help="Package name")
    p_show.add_argument("--catalog", help="Path to pkgs/ directory")

    # install-prep
    p_prep = sub.add_parser("install-prep", help="Prepare install artifacts")
    p_prep.add_argument("package", help="Package name")
    p_prep.add_argument("--catalog", help="Path to pkgs/ directory")
    p_prep.add_argument("--tool", default=None,
                        choices=["claude", "codex", "cursor", "windsurf", "copilot"],
                        help="Override auto-detected tool (default: auto-detect from environment)")

    # status
    p_status = sub.add_parser("status", help="Show installed package status")
    p_status.add_argument("--catalog", help="Path to pkgs/ directory")
    p_status.add_argument("--scope", nargs="*", help="Paths to scan for installed files")

    args = parser.parse_args()

    if args.command == "resolve-catalog":
        cmd_resolve_catalog(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "install-prep":
        cmd_install_prep(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
