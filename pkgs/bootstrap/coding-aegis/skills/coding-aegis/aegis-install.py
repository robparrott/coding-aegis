#!/usr/bin/env python3
"""coding-aegis install <name> -- install a package and print markdown summary.

Usage: aegis-install.py <name> --scope <project|user>
                        [--catalog PATH] [--tool TOOL]

Writes all artifacts to disk directly. No LLM file-writing needed.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aegis_lib import (
    ensure_catalog, find_package, detect_tool,
    parse_frontmatter, render_frontmatter, merge_frontmatter,
    compute_target_filename, upsert_agents_md_section,
    rebuild_governance_table, resolve_scope_base, skill_install_dir,
    TOOL_PATHS, _die,
)


def main():
    parser = argparse.ArgumentParser(description="Install a coding-aegis package")
    parser.add_argument("package", help="Package name")
    parser.add_argument("--scope", default="project", choices=["project", "user"],
                        help="Install scope (default: project)")
    parser.add_argument("--catalog", help="Path to pkgs/ directory (skips git clone)")
    parser.add_argument("--tool", default=None,
                        choices=["claude", "codex", "cursor", "gemini", "windsurf", "copilot", "opencode"],
                        help="Override auto-detected tool")
    args = parser.parse_args()

    catalog = ensure_catalog(args.catalog)
    tool = args.tool or detect_tool()
    tool_cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])
    scope_base = resolve_scope_base(tool, args.scope)

    pkg, pkg_dir = find_package(catalog, args.package)
    if pkg is None:
        print(
            f"Error: Package '{args.package}' not found in the catalog.\n"
            "Run `/coding-aegis list` to see available packages.",
            file=sys.stderr,
        )
        sys.exit(1)

    name = pkg["name"]
    version = pkg.get("version", "0.0.0")
    tier = pkg["tier"]
    artifacts = pkg.get("artifacts", [])

    if not artifacts:
        print(f"Warning: Package '{name}' has no artifacts to install.")
        sys.exit(0)

    written = []

    for artifact in artifacts:
        a_type = artifact.get("type")
        a_path = artifact.get("path")
        source_path = pkg_dir / a_path

        if not source_path.is_file():
            print(f"Warning: artifact {a_path} not found at {source_path}", file=sys.stderr)
            continue

        source_text = source_path.read_text()

        if a_type in ("rule", "agent"):
            rule_stem = Path(a_path).stem

            if tool in ("codex", "opencode"):
                # Codex + OpenCode: deliver rules as aegis:begin/end sections in AGENTS.md
                _, body = parse_frontmatter(source_text)
                begin = (
                    f"<!-- aegis:begin package={name} rule={rule_stem}"
                    f" version={version} tier={tier} -->"
                )
                end = f"<!-- aegis:end package={name} rule={rule_stem} -->"
                content = begin + "\n" + body.strip() + "\n" + end + "\n"
                amd = Path.cwd() / "AGENTS.md"
                upsert_agents_md_section(content, name, amd)
                written.append({"type": a_type, "install_path": str(amd), "note": "agents-md"})

            else:
                # All other tools: managed file in rules/
                fm, body = parse_frontmatter(source_text)
                managed_keys = {
                    "package": name,
                    a_type: rule_stem,
                    "version": version,
                    "tier": tier,
                    "managed-by": "coding-aegis",
                }
                if "description" not in fm:
                    managed_keys["description"] = f"{name} governance — {rule_stem}"
                merged_fm = merge_frontmatter(fm, managed_keys)
                content = render_frontmatter(merged_fm, body)
                target_filename = compute_target_filename(name, artifact)
                install_path = scope_base / "rules" / target_filename
                os.makedirs(install_path.parent, exist_ok=True)
                install_path.write_text(content)
                written.append({"type": a_type, "install_path": str(install_path)})

        elif a_type == "skill":
            skill_name = Path(a_path).parent.name
            target_dir = skill_install_dir(tool, skill_name, args.scope)
            skill_src_dir = pkg_dir / "skills" / skill_name

            if skill_src_dir.is_dir():
                for f in sorted(skill_src_dir.rglob("*")):
                    if f.is_file():
                        rel = f.relative_to(skill_src_dir)
                        dest = target_dir / rel
                        os.makedirs(dest.parent, exist_ok=True)
                        dest.write_text(f.read_text())
                        written.append({"type": "skill", "install_path": str(dest)})
            else:
                # Single-file skill
                dest = target_dir / Path(a_path).name
                os.makedirs(dest.parent, exist_ok=True)
                dest.write_text(source_text)
                written.append({"type": "skill", "install_path": str(dest)})

        else:
            # mcp, plugin, etc.
            install_path = scope_base / a_type / Path(a_path).name
            os.makedirs(install_path.parent, exist_ok=True)
            install_path.write_text(source_text)
            written.append({"type": a_type, "install_path": str(install_path)})

    # Claude + project scope: rebuild governance table in AGENTS.md
    # (Codex and OpenCode use aegis:begin/end sections instead)
    agents_md_updated = False
    if tool == "claude" and args.scope == "project":
        amd = Path.cwd() / "AGENTS.md"
        if amd.is_file():
            rebuild_governance_table(scope_base, amd)
            agents_md_updated = True

    # Print summary
    lines = [
        f"## Installed: {name} v{version} ({tier})\n",
        f"Tool: {tool}  |  Scope: {args.scope}\n",
        "| # | Type | Installed to |",
        "|---|------|-------------|",
    ]
    for i, w in enumerate(written, 1):
        note = f" *(agents-md)*" if w.get("note") == "agents-md" else ""
        lines.append(f"| {i} | {w['type']} | `{w['install_path']}`{note} |")

    if agents_md_updated:
        lines.append("\nAGENTS.md updated with installed governance rules table.")

    lines.append(
        "\n**Restart your coding tool to load newly installed skills.**"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
