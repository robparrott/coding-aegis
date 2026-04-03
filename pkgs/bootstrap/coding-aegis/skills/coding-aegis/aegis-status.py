#!/usr/bin/env python3
"""coding-aegis status — show installed packages as markdown.

Usage: aegis-status.py [--catalog PATH] [--scope PATH ...]

Outputs final markdown to stdout. No LLM formatting needed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aegis_lib import (
    ensure_catalog, scan_tier, parse_frontmatter,
    compute_artifact_summary, detect_tool, TOOL_PATHS, TIERS, _die,
)


def main():
    parser = argparse.ArgumentParser(description="Show coding-aegis install status")
    parser.add_argument("--catalog", help="Path to pkgs/ directory (skips git clone)")
    parser.add_argument("--scope", nargs="*", help="Scope base paths to scan")
    args = parser.parse_args()

    catalog = ensure_catalog(args.catalog)
    tool = detect_tool()
    tool_cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])

    # Determine scope paths to scan
    scopes = args.scope or []
    if not scopes:
        cwd_scope = Path.cwd() / tool_cfg["scope_base"]
        if cwd_scope.is_dir():
            scopes.append(str(cwd_scope))
        home_scope = Path.home() / tool_cfg["scope_base"]
        if home_scope.is_dir():
            scopes.append(str(home_scope))

    # Build catalog version index
    catalog_index = {}
    for tier in TIERS:
        for pkg in scan_tier(catalog, tier):
            catalog_index[pkg["name"]] = pkg

    if not scopes:
        print("No coding-aegis packages installed. Run `/coding-aegis list` to browse the catalog.")
        return

    lines = ["## coding-aegis status\n"]
    any_found = False

    for scope_path in scopes:
        sp = Path(scope_path)
        label = "Project" if sp.parent == Path.cwd() else "User"
        lines.append(f"\n### {label} ({sp})\n")

        installed = {}

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
                    installed[pkg_name]["artifacts"].append({"type": "rule", "file": f.name})

        # Scan skills
        skills_dir = sp / "skills"
        if skills_dir.is_dir():
            for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
                skill_name = skill_md.parent.name
                fm, _ = parse_frontmatter(skill_md.read_text())
                pkg_name = fm.get("package", skill_name)
                if pkg_name not in installed:
                    installed[pkg_name] = {
                        "installed_version": fm.get("version"),
                        "tier": fm.get("tier"),
                        "artifacts": [],
                    }
                installed[pkg_name]["artifacts"].append({"type": "skill", "file": f"skills/{skill_name}/SKILL.md"})

        if not installed:
            lines.append("(none)\n")
            continue

        any_found = True
        lines.append("| Package | Version | Tier | Artifacts | Status |")
        lines.append("|---------|---------|------|-----------|--------|")
        for pkg_name, info in sorted(installed.items()):
            cat_pkg = catalog_index.get(pkg_name)
            cat_version = cat_pkg["version"] if cat_pkg else None
            inst_version = info["installed_version"] or "?"

            if cat_version and info["installed_version"]:
                status = "current" if cat_version == info["installed_version"] else "outdated"
            elif cat_version:
                status = "unknown"
            else:
                status = "untracked"

            tier = info.get("tier") or (cat_pkg["tier"] if cat_pkg else "?")
            summary = compute_artifact_summary(info["artifacts"])
            lines.append(f"| {pkg_name} | {inst_version} | {tier} | {summary} | {status} |")

    if not any_found:
        print("No coding-aegis packages installed. Run `/coding-aegis list` to browse the catalog.")
        return

    print("\n".join(lines))


if __name__ == "__main__":
    main()
