# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

Categories used: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

---

## [Unreleased]

### Added
* Security policy in `SECURITY.md` with supported versions and private vulnerability reporting steps.
* Automated static security scanning via CodeQL in `.github/workflows/codeql.yml` and weekly GitHub Actions dependency updates in `.github/dependabot.yml`.
* Structured GitHub issue forms (`.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml`), pull request template (`.github/PULL_REQUEST_TEMPLATE.md`), and `.github/CODEOWNERS`.

### Changed
* Expanded the Python test matrix in `.github/workflows/ci.yml` to cover `3.8`, `3.9`, `3.10`, `3.11`, `3.12`, and `3.13`, and added `SECURITY.md` to CI documentation verification.

---

## [0.1.0] - 2026-11-06

### Added
* Bilingual documentation templates in `resources/en/` (English) and `resources/id/` (Indonesian) alongside default English templates in `resources/`.
* Self-contained **Documentation Prose Rules** in `SKILL.md` so the skill works without external skill dependencies (`FEAT-02`).
* Language and status marker translation table (`[TODO: confirm]` / `[TODO: konfirmasi]`, `Removed in vX.Y.Z` / `Dihapus di versi X.Y.Z`, `Superseded by ADR-MM` / `Digantikan oleh ADR-MM`) (`FEAT-01`).
* Escape hatches in `scripts/check_docs.py` for false positives: inline HTML comments (`<!-- living-docs-ignore -->`, `<!-- living-docs-ignore-next-line -->`, `<!-- living-docs-ignore-start -->` / `<!-- living-docs-ignore-end -->`, `<!-- living-docs-ignore-file -->`), `.living-docs-ignore` config file, and `--ignore`, `--skip-reverse`, `--allow-em-dash` CLI flags (`FEAT-05`).
* Expanded reverse coverage detection in `scripts/check_docs.py` across Express/Fastify/Hono, FastAPI/Flask, Go `net/http`/Gin/Echo, SQL `CREATE TABLE`, SQLAlchemy `__tablename__`, and `.env.example` (`FEAT-04`).
* Automated unit test suite in `tests/test_check_docs.py`, before-and-after example in `examples/before-and-after.md`, self-documentation (`README.md`, `docs/FEATURES.md`, `docs/ARCHITECTURE.md`), and `LICENSE` (MIT).
* Community and CI infrastructure: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, GitHub Actions workflow (`.github/workflows/ci.yml`), and status badges in `README.md`.

### Changed
* Replaced hardcoded environment path in `SKILL.md` with relative `<skill-dir>/scripts/check_docs.py` path for portability across Claude Code, Antigravity, Cursor, and CLI environments.
* Replaced single-domain IoT examples in `SKILL.md` with balanced examples across web APIs, background workers, databases, and optional hardware projects.
* Clarified the **Pragmatic Diataxis Layout** section in `SKILL.md` (`ADR-01`) to explain why `ARCHITECTURE.md` consolidates Reference, ADR, and Runbook in small-to-medium repositories and when to split them.
