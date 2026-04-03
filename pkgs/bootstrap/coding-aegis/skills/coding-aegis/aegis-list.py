#!/usr/bin/env python3
"""coding-aegis list — print the package catalog as markdown.

Usage: aegis-list.py [--catalog PATH]

Outputs final markdown to stdout. No LLM formatting needed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aegis_lib import ensure_catalog, scan_tier, TIERS, _die


def main():
    parser = argparse.ArgumentParser(description="List coding-aegis packages")
    parser.add_argument("--catalog", help="Path to pkgs/ directory (skips git clone)")
    args = parser.parse_args()

    catalog = ensure_catalog(args.catalog)

    lines = ["## coding-aegis catalog\n"]

    for tier in TIERS:
        lines.append(f"\n### {tier}\n")
        packages = scan_tier(catalog, tier)
        if not packages:
            lines.append("(none)\n")
        else:
            lines.append("| Package | Version | Artifacts | Description |")
            lines.append("|---------|---------|-----------|-------------|")
            for p in packages:
                name = p.get("name", "?")
                version = p.get("version", "?")
                summary = p.get("artifact_summary", "none")
                desc = p.get("description", "")
                lines.append(f"| {name} | {version} | {summary} | {desc} |")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
