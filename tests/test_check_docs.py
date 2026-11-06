#!/usr/bin/env python3
"""Unit tests for scripts/check_docs.py."""
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts", "check_docs.py")
)


def run_checker(root, extra_args=None):
    cmd = [sys.executable, SCRIPT_PATH, "--root", root] + (extra_args or [])
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


class CheckDocsTest(unittest.TestCase):
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

    def test_clean_project_passes(self):
        self.write(
            "src/server.py",
            '@app.get("/api/users")\ndef list_users():\n    return []\n',
        )
        self.write(
            "db/schema.sql",
            "CREATE TABLE users (id INTEGER PRIMARY KEY);\n",
        )
        self.write(".env.example", "PORT=8080\n")
        self.write(
            "README.md",
            "# Test App\n\nSee [Features](docs/FEATURES.md).\n",
        )
        self.write(
            "docs/FEATURES.md",
            "# Features\n\nCalls `list_users()` in `src/server.py` on `/api/users` using table `users` and `PORT`.\n"
            "Aggregates rows with `COUNT()` and `NOW()`.\n",
        )
        self.write(
            "docs/CHANGELOG.md",
            "# Changelog\n\n## [Unreleased]\n\n### Added\n* Initial release.\n",
        )

        res = run_checker(self.root)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("0 error(s), 0 warning(s)", res.stdout)

    def test_forward_errors_detected(self):
        self.write("src/app.js", "function realFunc() {}\n")
        self.write(
            "README.md",
            "# Bad Docs \u2014 With Em Dash\n\n"
            "Broken link: [Arch](docs/MISSING.md)\n"
            "Missing path: `src/ghost.js`\n"
            "Missing func: `hallucinatedFunc()`\n",
        )

        res = run_checker(self.root)
        self.assertEqual(res.returncode, 1)
        self.assertIn("em dash found", res.stdout)
        self.assertIn("broken markdown link `docs/MISSING.md`", res.stdout)
        self.assertIn("path `src/ghost.js` does not exist", res.stdout)
        self.assertIn("`hallucinatedFunc()` not found in source", res.stdout)

    def test_inline_and_block_ignore_directives(self):
        self.write("src/app.js", "function realFunc() {}\n")
        self.write(
            "README.md",
            "# Docs\n\n"
            "Same line ignore: `externalFunc()` <!-- living-docs-ignore -->\n"
            "<!-- living-docs-ignore-next-line -->\n"
            "Next line ignore: `nextLineFunc()` and `missing/file.js` \u2014 em dash\n"
            "<!-- living-docs-ignore-start -->\n"
            "Block ignore: `blockFunc()` and [Broken](nope.md) \u2014 em dash\n"
            "<!-- living-docs-ignore-end -->\n"
            "Valid call: `realFunc()` in `src/app.js`.\n",
        )

        res = run_checker(self.root)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("0 error(s), 0 warning(s)", res.stdout)

    def test_ignore_file_and_cli_ignore(self):
        self.write(
            "src/index.ts",
            'app.post("/api/internal/metrics", () => {});\n'
            'app.get("/api/health", () => {});\n',
        )
        self.write(".env.example", "SECRET_INTERNAL_KEY=1\nPUBLIC_PORT=3000\n")
        self.write(
            ".living-docs-ignore",
            "# Ignore internal metrics and secret key\n"
            "/api/internal/*\n"
            "SECRET_INTERNAL_KEY\n"
            "legacyHelper()\n",
        )
        self.write(
            "README.md",
            "# Service\n\nExposes `/api/health` on `PUBLIC_PORT`. Mentions `legacyHelper()` and `cliIgnored()`.\n",
        )

        res = run_checker(self.root, ["--ignore", "cliIgnored()"])
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("0 error(s), 0 warning(s)", res.stdout)

    def test_reverse_coverage_multi_stack(self):
        self.write(
            "src/routes.py",
            '@router.post("/v1/orders")\ndef create_order(): pass\n',
        )
        self.write(
            "src/main.go",
            'package main\nfunc main() { http.HandleFunc("/v1/ping", nil) }\n',
        )
        self.write(
            "src/models.py",
            'class Order:\n    __tablename__ = "orders"\n',
        )
        self.write(".env.example", "REDIS_URL=redis://localhost:6379\n")
        self.write("README.md", "# Minimal Docs\n")

        res = run_checker(self.root)
        self.assertEqual(res.returncode, 0)
        self.assertIn("coverage: route `/v1/orders` exists in code", res.stdout)
        self.assertIn("coverage: route `/v1/ping` exists in code", res.stdout)
        self.assertIn("coverage: SQL table `orders` exists in code", res.stdout)
        self.assertIn("coverage: env var `REDIS_URL` in .env.example", res.stdout)

    def test_markdown_link_syntax_inside_inline_code_ignored(self):
        self.write("src/app.py", "def run(): pass\n")
        self.write(
            "README.md",
            "# Docs\n\nSyntax example: `[label](path/to/nonexistent.md)` calls `run()`.\n",
        )

        res = run_checker(self.root)
        self.assertEqual(res.returncode, 0, res.stdout)
        self.assertIn("0 error(s), 0 warning(s)", res.stdout)


if __name__ == "__main__":
    unittest.main()
