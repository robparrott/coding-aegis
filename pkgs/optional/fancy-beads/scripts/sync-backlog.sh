#!/usr/bin/env bash
# Sync beads database to docs/backlog/ as human-readable markdown.
# Run before committing to keep the backlog snapshot current.
set -euo pipefail

BACKLOG_DIR="docs/backlog"
mkdir -p "$BACKLOG_DIR"

# Clear previous snapshot
rm -f "$BACKLOG_DIR"/*.md

# Generate backlog summary
python3 - "$BACKLOG_DIR" <<'PYEOF'
import json
import subprocess
import sys
from pathlib import Path

backlog_dir = Path(sys.argv[1])

def bd_json(*args):
    result = subprocess.run(["bd", *args, "--json"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return json.loads(result.stdout or "[]")

def bd_children_json(parent_id):
    result = subprocess.run(["bd", "children", parent_id, "--json"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return json.loads(result.stdout or "[]")

def status_icon(status):
    return {"open": "[ ]", "in_progress": "[~]", "closed": "[x]", "blocked": "[!]"}.get(status, "[ ]")

def slugify(title):
    slug = title.lower().replace(" ", "-").replace("/", "-").replace(":", "").replace("(", "").replace(")", "")
    return "-".join(slug.split("-")[:6])

# Get all epics sorted by title
epics = bd_json("list", "--type", "epic")
epics.sort(key=lambda e: e.get("title", ""))

# Get standalone issues (non-epic, no parent)
all_issues = bd_json("list", "--all")
standalone = [i for i in all_issues if i.get("issue_type") != "epic" and "." not in i.get("id", "")]

# Write per-epic files
for epic in epics:
    eid = epic["id"]
    title = epic["title"]
    status = epic["status"]
    desc = epic.get("description", "")

    children = bd_children_json(eid)
    children.sort(key=lambda c: c.get("id", ""))

    slug = slugify(title)
    filename = f"{slug}.md"

    lines = [f"# {title}", "", f"**Status**: {status} | **ID**: `{eid}`", ""]
    if desc:
        lines += [desc, ""]

    if children:
        lines += ["## Tasks", ""]
        for child in children:
            icon = status_icon(child["status"])
            assignee = f" @{child.get('assignee', '')}" if child.get("assignee") else ""
            lines.append(f"- {icon} `{child['id']}` {child['title']}{assignee}")
        lines.append("")

    open_count = sum(1 for c in children if c["status"] in ("open", "in_progress"))
    closed_count = sum(1 for c in children if c["status"] == "closed")
    lines += [f"**Progress**: {closed_count}/{closed_count + open_count} tasks complete", ""]

    (backlog_dir / filename).write_text("\n".join(lines))

# Write standalone issues file if any exist
orphans = [i for i in standalone if not any(i["id"].startswith(e["id"]) for e in epics)]
if orphans:
    lines = ["# Standalone Issues", ""]
    for issue in orphans:
        icon = status_icon(issue["status"])
        itype = issue.get("issue_type", "task")
        lines.append(f"- {icon} `{issue['id']}` [{itype}] {issue['title']}")
    lines.append("")
    (backlog_dir / "standalone.md").write_text("\n".join(lines))

# Write index
index_lines = ["# Backlog", "", "Auto-generated from beads (`bd`). Do not edit manually.", ""]
index_lines += ["## Epics", ""]
for epic in epics:
    children = bd_children_json(epic["id"])
    open_count = sum(1 for c in children if c["status"] in ("open", "in_progress"))
    closed_count = sum(1 for c in children if c["status"] == "closed")
    total = closed_count + open_count
    icon = status_icon(epic["status"])
    slug = slugify(epic["title"])
    index_lines.append(f"- {icon} [{epic['title']}]({slug}.md) — {closed_count}/{total} tasks")
index_lines.append("")

if orphans:
    index_lines += ["## Standalone", "", f"- [Standalone issues](standalone.md) — {len(orphans)} issues", ""]

index_lines += ["## Views", "", "- [Dependency graph](graph.md)", ""]

(backlog_dir / "README.md").write_text("\n".join(index_lines))

# Build ID-to-file mapping for hyperlinks
import re

id_to_file = {}
for epic in epics:
    slug = slugify(epic["title"])
    id_to_file[epic["id"]] = f"{slug}.md"
    for child in bd_children_json(epic["id"]):
        # Children link to their parent epic file
        id_to_file[child["id"]] = f"{slug}.md"
if orphans:
    for issue in orphans:
        id_to_file[issue["id"]] = "standalone.md"

# Generate dependency graph with hyperlinked task IDs
graph_result = subprocess.run(
    ["bd", "graph", "--all", "--compact"],
    capture_output=True, text=True
)
if graph_result.returncode == 0 and graph_result.stdout.strip():
    graph_text = graph_result.stdout

    # Build regex from known IDs to match them in graph output
    escaped_ids = [re.escape(tid) for tid in sorted(id_to_file.keys(), key=len, reverse=True)]
    id_pattern = re.compile(r'\b(' + '|'.join(escaped_ids) + r')\b') if escaped_ids else None
    graph_lines = [
        "# Dependency Graph",
        "",
        "Auto-generated from `bd graph --all --compact`.",
        "",
        "```",
        graph_text.rstrip(),
        "```",
        "",
        "## Task Index",
        "",
    ]
    # Add a linkable index of all IDs found in the graph
    if id_pattern:
        seen = set()
        for match in id_pattern.finditer(graph_text):
            task_id = match.group(1)
            if task_id not in seen:
                seen.add(task_id)
                graph_lines.append(f"- [`{task_id}`]({id_to_file[task_id]})")
    graph_lines.append("")
    (backlog_dir / "graph.md").write_text("\n".join(graph_lines))
    graph_count = " + dependency graph"
else:
    graph_count = ""

print(f"Synced {len(epics)} epics and {len(orphans)} standalone issues{graph_count} to {backlog_dir}/")
PYEOF
