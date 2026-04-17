#!/usr/bin/env python3
"""Unit tests for aegis-catalog.py CLI helper.

Uses the helloworld package from the real catalog (pkgs/optional/helloworld/).
Stdlib only (unittest).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "pkgs" / "bootstrap" / "coding-aegis" / "skills" / "coding-aegis" / "aegis-catalog.py"
CATALOG = REPO_ROOT / "pkgs"


def run_cmd(*args, catalog=None, cwd=None):
    """Run aegis-catalog.py with args, return parsed JSON."""
    cmd = [sys.executable, str(SCRIPT)] + list(args)
    if catalog:
        cmd.extend(["--catalog", str(catalog)])
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0 and not result.stdout:
        raise RuntimeError(f"exit {result.returncode}: {result.stderr}")
    return json.loads(result.stdout)


class TestResolveCatalog(unittest.TestCase):

    def test_resolve_from_repo_root(self):
        data = run_cmd("resolve-catalog", "--from", str(REPO_ROOT))
        self.assertIn("catalog", data)
        self.assertTrue(data["catalog"].endswith("/pkgs"))

    def test_resolve_from_nested_dir(self):
        nested = REPO_ROOT / "pkgs" / "goodies"
        data = run_cmd("resolve-catalog", "--from", str(nested))
        self.assertIn("catalog", data)

    def test_resolve_fails_from_tmp(self):
        with tempfile.TemporaryDirectory() as d:
            data = run_cmd("resolve-catalog", "--from", d)
            self.assertIn("error", data)


class TestList(unittest.TestCase):

    def test_list_fixture_catalog(self):
        data = run_cmd("list", catalog=CATALOG)
        self.assertIn("tiers", data)
        tier_names = [t["name"] for t in data["tiers"]]
        self.assertEqual(tier_names, ["required", "best-practices", "optional", "goodies"])

    def test_list_finds_helloworld(self):
        data = run_cmd("list", catalog=CATALOG)
        optional = [t for t in data["tiers"] if t["name"] == "optional"][0]
        names = [p["name"] for p in optional["packages"]]
        self.assertIn("helloworld", names)

    def test_list_package_fields(self):
        data = run_cmd("list", catalog=CATALOG)
        optional = [t for t in data["tiers"] if t["name"] == "optional"][0]
        pkg = [p for p in optional["packages"] if p["name"] == "helloworld"][0]
        self.assertEqual(pkg["version"], "1.0.0")
        self.assertEqual(pkg["tier"], "optional")
        self.assertEqual(pkg["artifact_count"], 2)
        self.assertEqual(pkg["artifact_summary"], "1 rule, 1 skill")

    def test_list_empty_tiers(self):
        data = run_cmd("list", catalog=CATALOG)
        required = [t for t in data["tiers"] if t["name"] == "required"][0]
        self.assertEqual(required["packages"], [])


class TestShow(unittest.TestCase):

    def test_show_test_stub(self):
        data = run_cmd("show", "helloworld", catalog=CATALOG)
        self.assertEqual(data["name"], "helloworld")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["tier"], "optional")
        self.assertEqual(data["author"], "platform-team")
        self.assertEqual(len(data["artifacts"]), 2)

    def test_show_readme(self):
        data = run_cmd("show", "helloworld", catalog=CATALOG)
        self.assertIsNotNone(data["readme"])
        self.assertIn("helloworld", data["readme"])

    def test_show_artifact_summary(self):
        data = run_cmd("show", "helloworld", catalog=CATALOG)
        self.assertEqual(data["artifact_summary"], "1 rule, 1 skill")

    def test_show_not_found(self):
        data = run_cmd("show", "nonexistent", catalog=CATALOG)
        self.assertIn("error", data)


class TestInstallPrep(unittest.TestCase):

    def test_prep_test_stub(self):
        data = run_cmd("install-prep", "helloworld", catalog=CATALOG)
        self.assertEqual(data["name"], "helloworld")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["tier"], "optional")
        self.assertGreaterEqual(len(data["artifacts"]), 2)

    def test_prep_rule_frontmatter(self):
        data = run_cmd("install-prep", "helloworld", catalog=CATALOG)
        rules = [a for a in data["artifacts"] if a["type"] == "rule"]
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        self.assertEqual(rule["target_filename"], "aegis--helloworld--helloworld.md")
        self.assertEqual(rule["target_subdir"], "rules")
        self.assertIn("managed-by: coding-aegis", rule["content"])
        self.assertIn("package: helloworld", rule["content"])
        self.assertIn("version: 1.0.0", rule["content"])
        self.assertIn("tier: optional", rule["content"])

    def test_prep_preserves_source_description(self):
        data = run_cmd("install-prep", "helloworld", catalog=CATALOG)
        rules = [a for a in data["artifacts"] if a["type"] == "rule"]
        rule = rules[0]
        self.assertIn("helloworld governance", rule["content"])

    def test_prep_skill_copy(self):
        data = run_cmd("install-prep", "helloworld", catalog=CATALOG)
        skills = [a for a in data["artifacts"] if a["type"] == "skill"]
        self.assertGreaterEqual(len(skills), 1)
        skill = skills[0]
        self.assertEqual(skill["target_subdir"], "skills/helloworld")
        self.assertIn("SKILL.md", skill["target_filename"])
        self.assertIn("helloworld", skill["content"])

    def test_prep_not_found(self):
        data = run_cmd("install-prep", "nonexistent", catalog=CATALOG)
        self.assertIn("error", data)


class TestInstallPrepCodex(unittest.TestCase):

    def test_codex_rule_targets_agents_md(self):
        """Codex: rule artifact targets AGENTS.md, not a standalone file."""
        with tempfile.TemporaryDirectory() as d:
            data = run_cmd("install-prep", "helloworld", "--tool", "codex", catalog=CATALOG, cwd=d)
            rules = [a for a in data["artifacts"] if a["type"] == "rule"]
            self.assertEqual(len(rules), 1)
            rule = rules[0]
            self.assertEqual(rule.get("target_mode"), "agents-md")
            self.assertTrue(rule["install_path"].endswith("AGENTS.md"))

    def test_codex_rule_content_has_markers(self):
        """Codex: rule content wrapped in aegis:begin/end markers."""
        with tempfile.TemporaryDirectory() as d:
            data = run_cmd("install-prep", "helloworld", "--tool", "codex", catalog=CATALOG, cwd=d)
            rules = [a for a in data["artifacts"] if a["type"] == "rule"]
            rule = rules[0]
            self.assertIn("<!-- aegis:begin package=helloworld rule=helloworld", rule["content"])
            self.assertIn("<!-- aegis:end package=helloworld rule=helloworld -->", rule["content"])

    def test_codex_rule_content_no_frontmatter(self):
        """Codex: rule section content strips YAML frontmatter."""
        with tempfile.TemporaryDirectory() as d:
            data = run_cmd("install-prep", "helloworld", "--tool", "codex", catalog=CATALOG, cwd=d)
            rules = [a for a in data["artifacts"] if a["type"] == "rule"]
            rule = rules[0]
            self.assertNotIn("managed-by: coding-aegis", rule["content"])

    def test_codex_skill_path_unchanged(self):
        """Codex: skill artifacts still go to .agents/skills/, not .claude/skills/."""
        with tempfile.TemporaryDirectory() as d:
            data = run_cmd("install-prep", "helloworld", "--tool", "codex", catalog=CATALOG, cwd=d)
            skills = [a for a in data["artifacts"] if a["type"] == "skill"]
            self.assertGreaterEqual(len(skills), 1)
            for s in skills:
                self.assertIn(".agents/skills", s["install_path"])
                self.assertNotIn(".claude", s["install_path"])


class TestStatus(unittest.TestCase):

    def test_status_empty_scope(self):
        with tempfile.TemporaryDirectory() as d:
            scope = Path(d) / ".claude"
            scope.mkdir()
            data = run_cmd("status", "--scope", str(scope), catalog=CATALOG)
            self.assertIn("scopes", data)
            self.assertEqual(len(data["scopes"]), 1)
            self.assertEqual(data["scopes"][0]["packages"], [])

    def test_status_finds_installed_rule(self):
        with tempfile.TemporaryDirectory() as d:
            scope = Path(d) / ".claude"
            rules_dir = scope / "rules"
            rules_dir.mkdir(parents=True)

            # Write a managed rule file
            (rules_dir / "aegis--helloworld--test-rule.md").write_text(
                "---\n"
                "package: helloworld\n"
                "rule: test-rule\n"
                "version: 1.0.0\n"
                "tier: optional\n"
                "managed-by: coding-aegis\n"
                "---\n\n# Test Rule\n"
            )

            data = run_cmd("status", "--scope", str(scope), catalog=CATALOG)
            pkgs = data["scopes"][0]["packages"]
            self.assertEqual(len(pkgs), 1)
            self.assertEqual(pkgs[0]["name"], "helloworld")
            self.assertEqual(pkgs[0]["status"], "current")
            self.assertEqual(pkgs[0]["installed_version"], "1.0.0")

    def test_status_detects_outdated(self):
        with tempfile.TemporaryDirectory() as d:
            scope = Path(d) / ".claude"
            rules_dir = scope / "rules"
            rules_dir.mkdir(parents=True)

            # Write a rule with an old version
            (rules_dir / "aegis--helloworld--test-rule.md").write_text(
                "---\n"
                "package: helloworld\n"
                "rule: test-rule\n"
                "version: 0.5.0\n"
                "tier: optional\n"
                "managed-by: coding-aegis\n"
                "---\n\n# Test Rule\n"
            )

            data = run_cmd("status", "--scope", str(scope), catalog=CATALOG)
            pkgs = data["scopes"][0]["packages"]
            self.assertEqual(pkgs[0]["status"], "outdated")
            self.assertEqual(pkgs[0]["installed_version"], "0.5.0")
            self.assertEqual(pkgs[0]["catalog_version"], "1.0.0")


class TestUninstallPrep(unittest.TestCase):

    def test_claude_skill_path(self):
        """Claude: skill dir found in .claude/skills/{name}/."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            skill_dir = base / ".claude" / "skills" / "helloworld"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# helloworld\n")
            data = run_cmd("uninstall-prep", "helloworld", "--tool", "claude", cwd=d)
            self.assertEqual(data["tool"], "claude")
            self.assertIn(str(skill_dir), data["dirs_to_remove"])
            self.assertEqual(data["files_to_remove"], [])

    def test_codex_skill_path(self):
        """Codex: skill dir found in .agents/skills/{name}/, not .claude/skills/."""
        with tempfile.TemporaryDirectory() as d:
            skill_dir = Path(d) / ".agents" / "skills" / "helloworld"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# helloworld\n")
            data = run_cmd("uninstall-prep", "helloworld", "--tool", "codex", cwd=d)
            self.assertEqual(data["tool"], "codex")
            self.assertEqual(len(data["dirs_to_remove"]), 1)
            self.assertIn(".agents/skills/helloworld", data["dirs_to_remove"][0])
            for p in data["dirs_to_remove"]:
                self.assertNotIn(".claude", p)

    def test_codex_rule_files_in_agents_rules(self):
        """Codex: rule files in .agents/rules/ are found."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            rules_dir = base / ".agents" / "rules"
            rules_dir.mkdir(parents=True)
            rule_file = rules_dir / "aegis--helloworld--helloworld.md"
            rule_file.write_text("---\npackage: helloworld\nmanaged-by: coding-aegis\n---\n")
            skill_dir = base / ".agents" / "skills" / "helloworld"
            skill_dir.mkdir(parents=True)
            data = run_cmd("uninstall-prep", "helloworld", "--tool", "codex", cwd=d)
            self.assertIn(str(rule_file), data["files_to_remove"])

    def test_not_installed_errors(self):
        """Error JSON returned when nothing found."""
        with tempfile.TemporaryDirectory() as d:
            data = run_cmd("uninstall-prep", "helloworld", "--tool", "claude", cwd=d)
            self.assertIn("error", data)

    def test_codex_agents_md_section_removal(self):
        """Codex: managed AGENTS.md sections removed in-place; file path reported."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            agents_md = base / "AGENTS.md"
            agents_md.write_text(
                "# My Project\n\n"
                "<!-- aegis:begin package=helloworld rule=helloworld version=1.0.0 tier=optional -->\n"
                "Some rule content.\n"
                "<!-- aegis:end package=helloworld rule=helloworld -->\n\n"
                "Other content.\n"
            )
            skill_dir = base / ".agents" / "skills" / "helloworld"
            skill_dir.mkdir(parents=True)
            data = run_cmd("uninstall-prep", "helloworld", "--tool", "codex", cwd=d)
            # Script directly rewrites AGENTS.md and reports file path
            self.assertIn("agents_md_files_rewritten", data)
            self.assertEqual(len(data["agents_md_files_rewritten"]), 1)
            self.assertEqual(data["agents_md_files_rewritten"][0], str(agents_md))
            # Verify the file was actually rewritten
            rewritten = agents_md.read_text()
            self.assertNotIn("aegis:begin", rewritten)
            self.assertNotIn("Some rule content", rewritten)
            self.assertIn("Other content", rewritten)


class TestYamlParser(unittest.TestCase):
    """Test the minimal YAML parser directly."""

    def setUp(self):
        # Import the module
        import importlib.util
        spec = importlib.util.spec_from_file_location("aegis_catalog", str(SCRIPT))
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_simple_scalars(self):
        data = self.mod.parse_simple_yaml("name: foo\nversion: 1.0.0\n")
        self.assertEqual(data["name"], "foo")
        self.assertEqual(data["version"], "1.0.0")

    def test_quoted_value(self):
        data = self.mod.parse_simple_yaml('description: "has: colon"\n')
        self.assertEqual(data["description"], "has: colon")

    def test_artifacts_list(self):
        text = "artifacts:\n  - type: rule\n    path: rules/foo.md\n  - type: skill\n    path: skills/bar/SKILL.md\n"
        data = self.mod.parse_simple_yaml(text)
        self.assertEqual(len(data["artifacts"]), 2)
        self.assertEqual(data["artifacts"][0]["type"], "rule")
        self.assertEqual(data["artifacts"][1]["path"], "skills/bar/SKILL.md")

    def test_em_dash_in_value(self):
        data = self.mod.parse_simple_yaml("description: hello — world\n")
        self.assertEqual(data["description"], "hello — world")


class TestFrontmatter(unittest.TestCase):

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("aegis_catalog", str(SCRIPT))
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_parse_frontmatter(self):
        text = "---\nname: foo\n---\n\n# Body\n"
        fm, body = self.mod.parse_frontmatter(text)
        self.assertEqual(fm["name"], "foo")
        self.assertIn("# Body", body)

    def test_no_frontmatter(self):
        text = "# Just markdown\n"
        fm, body = self.mod.parse_frontmatter(text)
        self.assertEqual(fm, {})
        self.assertEqual(body, text)

    def test_merge_frontmatter(self):
        source = {"description": "original", "globs": "*.md"}
        managed = {"package": "test", "managed-by": "coding-aegis"}
        merged = self.mod.merge_frontmatter(source, managed)
        self.assertEqual(merged["description"], "original")
        self.assertEqual(merged["package"], "test")
        self.assertEqual(merged["globs"], "*.md")

    def test_render_frontmatter(self):
        fm = {"name": "foo", "version": "1.0"}
        result = self.mod.render_frontmatter(fm, "\n# Body\n")
        self.assertTrue(result.startswith("---\n"))
        self.assertIn("name: foo", result)
        self.assertIn("# Body", result)


class TestHelpers(unittest.TestCase):

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("aegis_catalog", str(SCRIPT))
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_compute_artifact_summary(self):
        artifacts = [
            {"type": "rule"}, {"type": "rule"}, {"type": "skill"}
        ]
        self.assertEqual(self.mod.compute_artifact_summary(artifacts), "2 rules, 1 skill")

    def test_compute_artifact_summary_single(self):
        artifacts = [{"type": "skill"}]
        self.assertEqual(self.mod.compute_artifact_summary(artifacts), "1 skill")

    def test_compute_artifact_summary_empty(self):
        self.assertEqual(self.mod.compute_artifact_summary([]), "none")

    def test_compute_target_filename(self):
        artifact = {"type": "rule", "path": "rules/my-rule.md"}
        self.assertEqual(
            self.mod.compute_target_filename("my-pkg", artifact),
            "aegis--my-pkg--my-rule.md"
        )


if __name__ == "__main__":
    unittest.main()
