#!/usr/bin/env python3
"""coding-aegis show <name> — print package detail as markdown.

Usage: aegis-show.py <name> [--catalog PATH]

Outputs final markdown to stdout. No LLM formatting needed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aegis_lib import ensure_catalog, find_package, compute_artifact_summary, _die


def main():
    parser = argparse.ArgumentParser(description="Show a coding-aegis package")
    parser.add_argument("package", help="Package name")
    parser.add_argument("--catalog", help="Path to modules/ directory (skips git clone)")
    args = parser.parse_args()

    catalog = ensure_catalog(args.catalog)
    pkg, pkg_dir = find_package(catalog, args.package)

    if pkg is None:
        print(
            f"Error: Package '{args.package}' not found in the catalog.\n"
            f"Run `/coding-aegis list` to see available packages.",
            file=sys.stderr,
        )
        sys.exit(1)

    name = pkg.get("name", args.package)
    version = pkg.get("version", "?")
    tier = pkg.get("tier", "?")
    author = pkg.get("author", "—")
    desc = pkg.get("description", "—")
    artifacts = pkg.get("artifacts", [])

    lines = [
        f"## {name}\n",
        "| Field | Value |",
        "|-------|-------|",
        f"| Name | {name} |",
        f"| Version | {version} |",
        f"| Tier | {tier} |",
        f"| Author | {author} |",
        f"| Description | {desc} |",
        "",
        "### Artifacts\n",
        "| # | Type | Path |",
        "|---|------|------|",
    ]
    for i, a in enumerate(artifacts, 1):
        lines.append(f"| {i} | {a.get('type', '?')} | {a.get('path', '?')} |")

    readme_path = pkg_dir / "README.md"
    lines.append("\n### README\n")
    if readme_path.is_file():
        lines.append(readme_path.read_text().strip())
    else:
        lines.append("(No README)")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
