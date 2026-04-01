#!/usr/bin/env python3
"""Unit tests for aegis-catalog.py CLI helper.

Uses the test-stub fixture package under tests/fixtures/pkgs/
instead of the real catalog. Stdlib only (unittest).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "pkgs" / "bootstrap" / "coding-aegis" / "skills" / "coding-aegis" / "aegis-catalog.py"
FIXTURE_CATALOG = REPO_ROOT / "tests" / "fixtures" / "pkgs"


def run_cmd(*args, catalog=None):
    """Run aegis-catalog.py with args, return parsed JSON."""
    cmd = [sys.executable, str(SCRIPT)] + list(args)
    if catalog:
        cmd.extend(["--catalog", str(catalog)])
    result = subprocess.run(cmd, capture_output=True, text=True)
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
        data = run_cmd("list", catalog=FIXTURE_CATALOG)
        self.assertIn("tiers", data)
        tier_names = [t["name"] for t in data["tiers"]]
        self.assertEqual(tier_names, ["required", "best-practices", "optional", "goodies"])

    def test_list_finds_test_stub(self):
        data = run_cmd("list", catalog=FIXTURE_CATALOG)
        goodies = [t for t in data["tiers"] if t["name"] == "goodies"][0]
        names = [p["name"] for p in goodies["packages"]]
        self.assertIn("test-stub", names)

    def test_list_package_fields(self):
        data = run_cmd("list", catalog=FIXTURE_CATALOG)
        goodies = [t for t in data["tiers"] if t["name"] == "goodies"][0]
        pkg = [p for p in goodies["packages"] if p["name"] == "test-stub"][0]
        self.assertEqual(pkg["version"], "1.0.0")
        self.assertEqual(pkg["tier"], "goodies")
        self.assertEqual(pkg["artifact_count"], 2)
        self.assertEqual(pkg["artifact_summary"], "1 rule, 1 skill")

    def test_list_empty_tiers(self):
        data = run_cmd("list", catalog=FIXTURE_CATALOG)
        required = [t for t in data["tiers"] if t["name"] == "required"][0]
        self.assertEqual(required["packages"], [])


class TestShow(unittest.TestCase):

    def test_show_test_stub(self):
        data = run_cmd("show", "test-stub", catalog=FIXTURE_CATALOG)
        self.assertEqual(data["name"], "test-stub")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["tier"], "goodies")
        self.assertEqual(data["author"], "test-team")
        self.assertEqual(len(data["artifacts"]), 2)

    def test_show_readme(self):
        data = run_cmd("show", "test-stub", catalog=FIXTURE_CATALOG)
        self.assertIsNotNone(data["readme"])
        self.assertIn("test-stub", data["readme"])

    def test_show_artifact_summary(self):
        data = run_cmd("show", "test-stub", catalog=FIXTURE_CATALOG)
        self.assertEqual(data["artifact_summary"], "1 rule, 1 skill")

    def test_show_not_found(self):
        data = run_cmd("show", "nonexistent", catalog=FIXTURE_CATALOG)
        self.assertIn("error", data)


class TestInstallPrep(unittest.TestCase):

    def test_prep_test_stub(self):
        data = run_cmd("install-prep", "test-stub", catalog=FIXTURE_CATALOG)
        self.assertEqual(data["name"], "test-stub")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["tier"], "goodies")
        self.assertGreaterEqual(len(data["artifacts"]), 2)

    def test_prep_rule_frontmatter(self):
        data = run_cmd("install-prep", "test-stub", catalog=FIXTURE_CATALOG)
        rules = [a for a in data["artifacts"] if a["type"] == "rule"]
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        self.assertEqual(rule["target_filename"], "aegis--test-stub--test-rule.md")
        self.assertEqual(rule["target_subdir"], "rules")
        self.assertIn("managed-by: coding-aegis", rule["content"])
        self.assertIn("package: test-stub", rule["content"])
        self.assertIn("version: 1.0.0", rule["content"])
        self.assertIn("tier: goodies", rule["content"])

    def test_prep_preserves_source_description(self):
        data = run_cmd("install-prep", "test-stub", catalog=FIXTURE_CATALOG)
        rules = [a for a in data["artifacts"] if a["type"] == "rule"]
        rule = rules[0]
        self.assertIn("test rule for validation", rule["content"])

    def test_prep_skill_copy(self):
        data = run_cmd("install-prep", "test-stub", catalog=FIXTURE_CATALOG)
        skills = [a for a in data["artifacts"] if a["type"] == "skill"]
        self.assertGreaterEqual(len(skills), 1)
        skill = skills[0]
        self.assertEqual(skill["target_subdir"], "skills/test-stub")
        self.assertIn("SKILL.md", skill["target_filename"])
        self.assertIn("test-stub", skill["content"])

    def test_prep_not_found(self):
        data = run_cmd("install-prep", "nonexistent", catalog=FIXTURE_CATALOG)
        self.assertIn("error", data)


class TestStatus(unittest.TestCase):

    def test_status_empty_scope(self):
        with tempfile.TemporaryDirectory() as d:
            scope = Path(d) / ".claude"
            scope.mkdir()
            data = run_cmd("status", "--scope", str(scope), catalog=FIXTURE_CATALOG)
            self.assertIn("scopes", data)
            self.assertEqual(len(data["scopes"]), 1)
            self.assertEqual(data["scopes"][0]["packages"], [])

    def test_status_finds_installed_rule(self):
        with tempfile.TemporaryDirectory() as d:
            scope = Path(d) / ".claude"
            rules_dir = scope / "rules"
            rules_dir.mkdir(parents=True)

            # Write a managed rule file
            (rules_dir / "aegis--test-stub--test-rule.md").write_text(
                "---\n"
                "package: test-stub\n"
                "rule: test-rule\n"
                "version: 1.0.0\n"
                "tier: goodies\n"
                "managed-by: coding-aegis\n"
                "---\n\n# Test Rule\n"
            )

            data = run_cmd("status", "--scope", str(scope), catalog=FIXTURE_CATALOG)
            pkgs = data["scopes"][0]["packages"]
            self.assertEqual(len(pkgs), 1)
            self.assertEqual(pkgs[0]["name"], "test-stub")
            self.assertEqual(pkgs[0]["status"], "current")
            self.assertEqual(pkgs[0]["installed_version"], "1.0.0")

    def test_status_detects_outdated(self):
        with tempfile.TemporaryDirectory() as d:
            scope = Path(d) / ".claude"
            rules_dir = scope / "rules"
            rules_dir.mkdir(parents=True)

            # Write a rule with an old version
            (rules_dir / "aegis--test-stub--test-rule.md").write_text(
                "---\n"
                "package: test-stub\n"
                "rule: test-rule\n"
                "version: 0.5.0\n"
                "tier: goodies\n"
                "managed-by: coding-aegis\n"
                "---\n\n# Test Rule\n"
            )

            data = run_cmd("status", "--scope", str(scope), catalog=FIXTURE_CATALOG)
            pkgs = data["scopes"][0]["packages"]
            self.assertEqual(pkgs[0]["status"], "outdated")
            self.assertEqual(pkgs[0]["installed_version"], "0.5.0")
            self.assertEqual(pkgs[0]["catalog_version"], "1.0.0")


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
