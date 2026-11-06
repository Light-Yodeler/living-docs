#!/usr/bin/env python3
"""Unit tests for scripts/bump_version.py and version consistency checks."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BUMP_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts", "bump_version.py")
)
CHECK_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts", "check_docs.py")
)


def run_bump(root, extra_args):
    cmd = [sys.executable, BUMP_SCRIPT, "--root", root] + extra_args
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def run_check(root, extra_args=None):
    cmd = [sys.executable, CHECK_SCRIPT, "--root", root] + (extra_args or [])
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


class BumpVersionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel_path, content):
        full = os.path.join(self.root, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(content)

    def read(self, rel_path):
        with open(os.path.join(self.root, rel_path), encoding="utf-8") as fh:
            return fh.read()

    def test_bump_patch_updates_all_manifests_and_changelog(self):
        self.write("VERSION", "0.1.0\n")
        self.write("package.json", json.dumps({"name": "demo", "version": "0.1.0"}, indent=2))
        self.write("pyproject.toml", '[project]\nname = "demo"\nversion = "0.1.0"\n')
        self.write(
            "README.md",
            "# Demo\n\n[![Release](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)\n",
        )
        self.write(
            "CHANGELOG.md",
            "# Changelog\n\n## [Unreleased]\n\n### Fixed\n* Handle null pointer in parser.\n\n---\n\n## [0.1.0] - 2026-11-01\n\n### Added\n* Initial release.\n",
        )

        res = run_bump(self.root, ["--bump", "patch", "--date", "2026-11-06"])
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("0.1.0 -> 0.1.1", res.stdout)

        self.assertEqual(self.read("VERSION").strip(), "0.1.1")
        self.assertIn('"version": "0.1.1"', self.read("package.json"))
        self.assertIn('version = "0.1.1"', self.read("pyproject.toml"))
        self.assertIn("version-0.1.1-blue.svg", self.read("README.md"))
        cl = self.read("CHANGELOG.md")
        self.assertIn("## [0.1.1] - 2026-11-06", cl)
        self.assertIn("* Handle null pointer in parser.", cl)

        # Verify check_docs.py sees synchronized versions with 0 warnings
        chk = run_check(self.root)
        self.assertEqual(chk.returncode, 0, chk.stdout)
        self.assertIn("0 error(s), 0 warning(s)", chk.stdout)

    def test_auto_bump_infers_minor_and_patch(self):
        self.write("VERSION", "1.2.3\n")
        self.write(
            "CHANGELOG.md",
            "# Changelog\n\n## [Unreleased]\n\n### Added\n* FEAT-02: Export CSV endpoint.\n\n---\n\n## [1.2.3] - 2026-11-01\n",
        )

        res = run_bump(self.root, ["--bump", "auto", "--date", "2026-11-06"])
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("(minor): 1.2.3 -> 1.3.0", res.stdout)
        self.assertEqual(self.read("VERSION").strip(), "1.3.0")

    def test_version_mismatch_warned_by_check_docs(self):
        self.write("VERSION", "0.2.0\n")
        self.write(
            "README.md",
            "# Demo\n\n[![Release](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)\n",
        )
        self.write(
            "CHANGELOG.md",
            "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-11-01\n",
        )

        chk = run_check(self.root)
        self.assertEqual(chk.returncode, 0)
        self.assertIn("version: mismatch across files", chk.stdout)


if __name__ == "__main__":
    unittest.main()
