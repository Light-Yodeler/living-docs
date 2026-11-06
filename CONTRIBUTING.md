# Contributing to `living-docs`

Thank you for your interest in improving `living-docs`. This project keeps documentation verifiable against source code while staying portable across AI coding agents (Claude Code, Google Antigravity, Cursor, Codex, and CLI workflows).

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Ways to Contribute

1. **Expand Reverse Coverage Patterns (`scripts/check_docs.py`):**
   * Add route or data-model extraction patterns in `ROUTE_PATTERNS` or `TABLE_PATTERNS` for frameworks not yet covered (for example, Rails, Spring Boot, Laravel, Rust Actix/Axum, or Prisma models).
   * Every new pattern must include a corresponding unit test in `tests/test_check_docs.py`.
2. **Add Language Template Sets (`resources/<lang>/`):**
   * We currently maintain `resources/en/` (English) and `resources/id/` (Indonesian).
   * To add a new language, provide all four templates (`README.template.md`, `FEATURES.template.md`, `ARCHITECTURE.template.md`, `CHANGELOG.template.md`) and add the status marker translations to the table in `SKILL.md`.
3. **Improve False-Positive Handling:**
   * If a common standard-library or SQL function triggers false positives in forward checks, add it to `BUILTIN_FUNCS` in `scripts/check_docs.py` with a test case.

---

## Development Setup

`living-docs` uses only the **Python 3.8+ standard library**. No third-party packages or virtual environments are required.

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/Light-Yodeler/living-docs.git
   cd living-docs
   ```
2. Run the unit test suite:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
3. Run the two-way documentation verifier against the repository itself:
   ```bash
   python3 scripts/check_docs.py --root .
   ```

---

## Pull Request Checklist

Before submitting a pull request, make sure every item below passes:

* [ ] `python3 -m unittest discover -s tests -v` passes with 0 failures.
* [ ] `python3 scripts/check_docs.py --root .` exits with `0 error(s), 0 warning(s)`.
* [ ] Any new behavior or CLI flag in `scripts/check_docs.py` is documented in `README.md`, `docs/FEATURES.md`, `docs/ARCHITECTURE.md`, and under `## [Unreleased]` in `CHANGELOG.md`.
* [ ] Documentation prose follows the rules in `SKILL.md` (no em dashes, no empty AI buzzwords, and no unverified claims).

---

## License

By contributing to `living-docs`, you agree that your contributions will be licensed under the [MIT License](LICENSE).
