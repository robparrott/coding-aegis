#!/usr/bin/env python3
"""Unit tests for aegis_lib.py shared library.

Run with: python3 -m pytest tests/test_aegis_lib.py -v
      or: python3 tests/test_aegis_lib.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add skill dir to path
SKILL_DIR = Path(__file__).parent.parent.parent / "modules/bootstrap/coding-aegis/skills/coding-aegis"
sys.path.insert(0, str(SKILL_DIR))

import aegis_lib as lib


class TestParseSimpleYaml(unittest.TestCase):
    def test_flat_scalars(self):
        r = lib.parse_simple_yaml("name: foo\nversion: 1.0.0\n")
        self.assertEqual(r["name"], "foo")
        self.assertEqual(r["version"], "1.0.0")

    def test_quoted_value(self):
        r = lib.parse_simple_yaml('description: "Hello, World!"\n')
        self.assertEqual(r["description"], "Hello, World!")

    def test_list_of_dicts(self):
        yaml = "artifacts:\n  - type: rule\n    path: rules/foo.md\n  - type: skill\n    path: skills/foo/SKILL.md\n"
        r = lib.parse_simple_yaml(yaml)
        self.assertEqual(len(r["artifacts"]), 2)
        self.assertEqual(r["artifacts"][0]["type"], "rule")
        self.assertEqual(r["artifacts"][1]["path"], "skills/foo/SKILL.md")

    def test_comments_ignored(self):
        r = lib.parse_simple_yaml("# comment\nname: bar\n")
        self.assertEqual(r["name"], "bar")

    def test_empty_string(self):
        r = lib.parse_simple_yaml("")
        self.assertEqual(r, {})


class TestParseFrontmatter(unittest.TestCase):
    def test_valid_frontmatter(self):
        text = "---\nname: test\nversion: 1.0.0\n---\nbody here"
        fm, body = lib.parse_frontmatter(text)
        self.assertEqual(fm["name"], "test")
        self.assertEqual(fm["version"], "1.0.0")
        self.assertEqual(body.strip(), "body here")

    def test_no_frontmatter(self):
        text = "just body"
        fm, body = lib.parse_frontmatter(text)
        self.assertEqual(fm, {})
        self.assertEqual(body, "just body")

    def test_unclosed_frontmatter(self):
        text = "---\nname: test\nbody"
        fm, body = lib.parse_frontmatter(text)
        self.assertEqual(fm, {})


class TestRenderFrontmatter(unittest.TestCase):
    def test_round_trip(self):
        fm = {"name": "foo", "version": "1.0.0"}
        body = "\n# content\n"
        rendered = lib.render_frontmatter(fm, body)
        self.assertTrue(rendered.startswith("---\n"))
        self.assertIn("name: foo", rendered)
        self.assertIn("# content", rendered)

    def test_quotes_colon_values(self):
        fm = {"description": "foo: bar"}
        rendered = lib.render_frontmatter(fm, "")
        self.assertIn('"foo: bar"', rendered)


class TestMergeFrontmatter(unittest.TestCase):
    def test_managed_keys_win(self):
        source = {"description": "original", "globs": "*.md"}
        managed = {"description": "override", "managed-by": "coding-aegis"}
        merged = lib.merge_frontmatter(source, managed)
        self.assertEqual(merged["description"], "override")
        self.assertEqual(merged["globs"], "*.md")
        self.assertEqual(merged["managed-by"], "coding-aegis")


class TestComputeArtifactSummary(unittest.TestCase):
    def test_mixed(self):
        arts = [{"type": "rule"}, {"type": "skill"}, {"type": "rule"}]
        self.assertEqual(lib.compute_artifact_summary(arts), "2 rules, 1 skill")

    def test_single(self):
        self.assertEqual(lib.compute_artifact_summary([{"type": "skill"}]), "1 skill")

    def test_empty(self):
        self.assertEqual(lib.compute_artifact_summary([]), "none")


class TestResolveScope(unittest.TestCase):
    def test_project_claude(self):
        result = lib.resolve_scope_base("claude", "project")
        self.assertEqual(result, Path.cwd() / ".claude")

    def test_user_claude(self):
        result = lib.resolve_scope_base("claude", "user")
        self.assertEqual(result, Path.home() / ".claude")

    def test_project_codex(self):
        result = lib.resolve_scope_base("codex", "project")
        self.assertEqual(result, Path.cwd() / ".agents")


class TestFindPackage(unittest.TestCase):
    def setUp(self):
        self.catalog = Path(__file__).parent.parent.parent / "modules"

    def test_finds_helloworld(self):
        pkg, pkg_dir = lib.find_package(self.catalog, "helloworld")
        self.assertIsNotNone(pkg)
        self.assertEqual(pkg["name"], "helloworld")
        self.assertEqual(pkg["tier"], "optional")
        self.assertTrue(pkg_dir.is_dir())

    def test_returns_none_for_missing(self):
        pkg, pkg_dir = lib.find_package(self.catalog, "no-such-package")
        self.assertIsNone(pkg)
        self.assertIsNone(pkg_dir)


class TestEnsureCatalog(unittest.TestCase):
    def test_catalog_override(self):
        catalog = Path(__file__).parent.parent.parent / "modules"
        result = lib.ensure_catalog(str(catalog))
        self.assertEqual(result, catalog)
        self.assertTrue(result.is_dir())

    def test_invalid_override_dies(self):
        with self.assertRaises(SystemExit):
            lib.ensure_catalog("/nonexistent/path/to/catalog")


class TestAgentsMdHelpers(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.amd = Path(self.tmpdir) / "AGENTS.md"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_upsert_creates_file(self):
        content = "<!-- aegis:begin package=foo rule=bar version=1 tier=optional -->\n# Foo\n<!-- aegis:end package=foo rule=bar -->\n"
        lib.upsert_agents_md_section(content, "foo", self.amd)
        self.assertTrue(self.amd.is_file())
        self.assertIn("aegis:begin package=foo", self.amd.read_text())

    def test_upsert_replaces_existing(self):
        old = "<!-- aegis:begin package=foo rule=bar version=1 tier=optional -->\nold content\n<!-- aegis:end package=foo rule=bar -->\n"
        self.amd.write_text(old)
        new = "<!-- aegis:begin package=foo rule=bar version=2 tier=optional -->\nnew content\n<!-- aegis:end package=foo rule=bar -->\n"
        lib.upsert_agents_md_section(new, "foo", self.amd)
        text = self.amd.read_text()
        self.assertIn("new content", text)
        self.assertNotIn("old content", text)
        self.assertEqual(text.count("aegis:begin package=foo"), 1)

    def test_strip_removes_section(self):
        content = "before\n<!-- aegis:begin package=foo rule=bar version=1 tier=optional -->\nbody\n<!-- aegis:end package=foo rule=bar -->\nafter\n"
        self.amd.write_text(content)
        changed = lib.strip_agents_md_section("foo", self.amd)
        self.assertTrue(changed)
        text = self.amd.read_text()
        self.assertNotIn("aegis:begin", text)
        self.assertIn("before", text)
        self.assertIn("after", text)

    def test_strip_returns_false_when_absent(self):
        self.amd.write_text("no markers here\n")
        changed = lib.strip_agents_md_section("foo", self.amd)
        self.assertFalse(changed)

    def test_rebuild_governance_table(self):
        # Create a fake rules dir with one aegis-- file
        rules_dir = Path(self.tmpdir) / ".claude" / "rules"
        rules_dir.mkdir(parents=True)
        rule_file = rules_dir / "aegis--foo--myrule.md"
        rule_file.write_text("---\npackage: foo\nrule: myrule\nversion: 1.0.0\ntier: optional\nmanaged-by: coding-aegis\n---\n# Rule\n")
        self.amd.write_text("# AGENTS\n\nSome content.\n")
        scope_base = Path(self.tmpdir) / ".claude"
        lib.rebuild_governance_table(scope_base, self.amd)
        text = self.amd.read_text()
        self.assertIn("## Installed Governance Rules", text)
        self.assertIn("myrule", text)

    def test_rebuild_removes_table_when_no_rules(self):
        self.amd.write_text("# AGENTS\n\n## Installed Governance Rules\n\n| Rule | Package |\n\nMore content.\n")
        scope_base = Path(self.tmpdir) / ".claude"  # no rules/ subdir
        lib.rebuild_governance_table(scope_base, self.amd)
        text = self.amd.read_text()
        self.assertNotIn("## Installed Governance Rules", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
