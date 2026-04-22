#!/usr/bin/env python3
"""coding-aegis uninstall <name> -- remove a package and print markdown summary.

Usage: aegis-uninstall.py <name> [--scope PATH] [--tool TOOL] [--catalog PATH]

Removes all installed artifacts directly. No LLM file-deletion needed.
When --catalog is supplied, reads pkg.yaml to remove all artifact types
(including mcp, plugin, etc.). Without --catalog, removes rules and skill
only (backward-compatible behaviour).
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aegis_lib import (
    detect_tool, resolve_scope_base, skill_install_dir,
    strip_agents_md_section, rebuild_governance_table,
    find_package,
    TOOL_PATHS, _die,
)


def main():
    parser = argparse.ArgumentParser(description="Uninstall a coding-aegis package")
    parser.add_argument("package", help="Package name")
    parser.add_argument("--scope", default=None,
                        help="Scope base path override (default: auto-detect)")
    parser.add_argument("--tool", default=None,
                        choices=["claude", "codex", "cursor", "gemini", "windsurf", "copilot", "opencode"],
                        help="Override auto-detected tool")
    parser.add_argument("--catalog", default=None,
                        help="Path to modules/ directory; when provided, removes all artifact types")
    args = parser.parse_args()

    name = args.package
    tool = args.tool or detect_tool()
    tool_cfg = TOOL_PATHS.get(tool, TOOL_PATHS["claude"])

    scope_base = Path(args.scope) if args.scope else (Path.cwd() / tool_cfg["scope_base"])

    files_removed = []
    dirs_removed = []
    agents_md_updated = False

    # Remove rule files: aegis--{name}--*.md
    rules_dir = scope_base / "rules"
    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob(f"aegis--{name}--*")):
            if f.is_file():
                f.unlink()
                files_removed.append(str(f))

    # Remove skill directory
    # Compute using same logic as install so the path matches
    skills_base_cfg = tool_cfg.get("skills_base")
    if skills_base_cfg is not None:
        skill_dir = (Path(skills_base_cfg).resolve() / tool_cfg["skills_dir"] / name)
    else:
        skill_dir = scope_base / tool_cfg.get("skills_dir", "skills") / name

    if skill_dir.is_dir():
        try:
            shutil.rmtree(str(skill_dir))
            dirs_removed.append(str(skill_dir))
        except (PermissionError, OSError) as e:
            # Codex workspace-write sandbox blocks rmtree at the syscall level.
            # Note the failure but continue — AGENTS.md stripping still needs to run.
            print(
                f"Warning: could not remove {skill_dir}: {e}\n"
                f"  The directory may need manual removal or danger-full-access sandbox mode.",
                file=sys.stderr,
            )

    # Catalog-based removal: remove non-rule/non-skill artifact types (e.g. mcp)
    # Only runs when --catalog is supplied to avoid unintended git clones.
    if args.catalog:
        pkg, pkg_dir = find_package(Path(args.catalog), name)
        if pkg is not None:
            for artifact in pkg.get("artifacts", []):
                a_type = artifact.get("type")
                a_path = artifact.get("path")
                if a_type in ("rule", "agent", "skill") or not a_path:
                    continue
                target = scope_base / a_type / Path(a_path).name
                if target.is_file():
                    target.unlink()
                    files_removed.append(str(target))
                    # Remove parent dir if now empty
                    try:
                        target.parent.rmdir()
                    except OSError:
                        pass

    # Codex + OpenCode: strip aegis:begin/end sections from AGENTS.md
    if tool in ("codex", "opencode"):
        amd = Path.cwd() / "AGENTS.md"
        if strip_agents_md_section(name, amd):
            agents_md_updated = True

    # Claude + project scope: rebuild or remove governance table,
    # but only if we actually removed something (otherwise it's already accurate).
    if tool == "claude" and not args.scope and files_removed:
        amd = Path.cwd() / "AGENTS.md"
        if amd.is_file():
            rebuild_governance_table(scope_base, amd)
            agents_md_updated = True

    if not files_removed and not dirs_removed and not agents_md_updated:
        print(
            f"Error: Package '{name}' does not appear to be installed in {scope_base}.",
            file=sys.stderr,
        )
        sys.exit(1)

    lines = [f"## Uninstalled: {name}\n", "Removed:"]
    for f in files_removed:
        lines.append(f"- `{f}`")
    for d in dirs_removed:
        lines.append(f"- `{d}/` (directory)")
    if agents_md_updated:
        lines.append("- AGENTS.md updated")

    lines.append("\n**Restart your coding tool to unload removed skills.**")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
