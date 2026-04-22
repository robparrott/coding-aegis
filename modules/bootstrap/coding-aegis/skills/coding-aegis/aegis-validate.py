#!/usr/bin/env python3
"""coding-aegis validate-install <name> -- verify a package's artifacts are correctly installed.

Usage: aegis-validate.py <name> [--scope project|user] [--tool TOOL] [--catalog PATH]

Checks each artifact declared in pkg.yaml against what is actually on disk (or in
AGENTS.md for Codex/OpenCode rule delivery).  Exits 0 when all checks pass, 1 when
any check fails.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aegis_lib import (
    detect_tool, ensure_catalog, find_package, resolve_scope_base,
    skill_install_dir, compute_target_filename, parse_frontmatter,
    TOOL_PATHS, _die,
)


def _check_agents_md_section(pkg_name, rule_stem):
    """Return (ok, detail) checking AGENTS.md for an aegis:begin section."""
    amd = Path.cwd() / "AGENTS.md"
    if not amd.is_file():
        return False, "AGENTS.md not found"
    text = amd.read_text()
    pattern = (
        r"<!-- aegis:begin package=" + re.escape(pkg_name)
        + r" rule=" + re.escape(rule_stem) + r"[^\n]*-->"
    )
    if re.search(pattern, text):
        return True, f"AGENTS.md contains aegis:begin package={pkg_name} rule={rule_stem}"
    return False, f"AGENTS.md missing aegis:begin package={pkg_name} rule={rule_stem}"


def _check_rule_file(scope_base, pkg_name, artifact, tool):
    """Return (ok, detail) checking the managed rule file on disk."""
    filename = compute_target_filename(pkg_name, artifact, tool)
    rule_path = scope_base / "rules" / filename
    if not rule_path.is_file():
        return False, f"Missing: `{rule_path}`"
    fm, _ = parse_frontmatter(rule_path.read_text())
    if fm.get("managed-by") != "coding-aegis":
        return False, f"`{rule_path}` exists but frontmatter missing `managed-by: coding-aegis`"
    return True, f"Found: `{rule_path}` (managed-by: coding-aegis)"


def _check_skill_dir(tool, skill_name, scope):
    """Return (ok, detail) checking the skill directory and SKILL.md."""
    skill_dir = skill_install_dir(tool, skill_name, scope)
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return False, f"Missing skill dir: `{skill_dir}`"
    if not skill_md.is_file():
        return False, f"Skill dir exists but SKILL.md missing: `{skill_md}`"
    return True, f"Found: `{skill_dir}/SKILL.md`"


def main():
    parser = argparse.ArgumentParser(description="Validate a coding-aegis package install")
    parser.add_argument("package", help="Package name")
    parser.add_argument("--scope", default="project", choices=["project", "user"],
                        help="Scope to validate (default: project)")
    parser.add_argument("--tool", default=None,
                        choices=["claude", "codex", "cursor", "gemini", "windsurf",
                                 "copilot", "opencode"],
                        help="Override auto-detected tool")
    parser.add_argument("--catalog", help="Path to modules/ directory (skips git clone)")
    args = parser.parse_args()

    name = args.package
    tool = args.tool or detect_tool()
    catalog = ensure_catalog(args.catalog)
    scope_base = resolve_scope_base(tool, args.scope)

    pkg, pkg_dir = find_package(catalog, name)
    if pkg is None:
        _die(f"Package '{name}' not found in catalog.")

    artifacts = pkg.get("artifacts", [])
    version = pkg.get("version", "?")
    tier = pkg.get("tier", "?")

    rows = []  # list of (artifact_label, ok, detail)

    for artifact in artifacts:
        a_type = artifact.get("type")
        a_path = artifact.get("path", "")
        stem = Path(a_path).stem
        label = f"{a_type}: {stem}"

        if a_type in ("rule", "agent"):
            if tool in ("codex", "opencode"):
                ok, detail = _check_agents_md_section(name, stem)
            else:
                ok, detail = _check_rule_file(scope_base, name, artifact, tool)

        elif a_type == "skill":
            skill_name = Path(a_path).parent.name
            ok, detail = _check_skill_dir(tool, skill_name, args.scope)

        else:
            # mcp, plugin, etc. — check generic path
            install_path = scope_base / a_type / Path(a_path).name
            if install_path.is_file():
                ok, detail = True, f"Found: `{install_path}`"
            else:
                ok, detail = False, f"Missing: `{install_path}`"

        rows.append((label, ok, detail))

    all_pass = all(ok for _, ok, _ in rows)
    status_icon = "PASS" if all_pass else "FAIL"

    lines = [
        f"## validate-install: {name} v{version} ({tier})\n",
        f"Tool: {tool}  |  Scope: {args.scope}  |  Status: **{status_icon}**\n",
        "| Artifact | Result | Detail |",
        "|----------|--------|--------|",
    ]
    for label, ok, detail in rows:
        result = "PASS" if ok else "FAIL"
        lines.append(f"| {label} | {result} | {detail} |")

    print("\n".join(lines))

    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
