# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

Categories used: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

---

## [Unreleased]

### Added
* Bilingual documentation templates in `resources/en/` (English) and `resources/id/` (Indonesian) alongside default English templates in `resources/`.
* Self-contained **Documentation Prose Rules** in `SKILL.md` so the skill works without external skill dependencies.
* Language and status marker translation table (`[TODO: confirm]` / `[TODO: konfirmasi]`, `Removed in vX.Y.Z` / `Dihapus di versi X.Y.Z`, `Superseded by ADR-MM` / `Digantikan oleh ADR-MM`).
* Escape hatches in `scripts/check_docs.py` for false positives: inline HTML comments (`<!-- living-docs-ignore -->`, `<!-- living-docs-ignore-next-line -->`, `<!-- living-docs-ignore-start -->` / `<!-- living-docs-ignore-end -->`, `<!-- living-docs-ignore-file -->`), `.living-docs-ignore` config file, and `--ignore`, `--skip-reverse`, `--allow-em-dash` CLI flags.
* Expanded reverse coverage detection in `scripts/check_docs.py` across Express/Fastify/Hono, FastAPI/Flask, Go `net/http`/Gin/Echo, SQL `CREATE TABLE`, SQLAlchemy `__tablename__`, and `.env.example`.
* Automated unit test suite in `tests/test_check_docs.py`, before-and-after example in `examples/before-and-after.md`, `README.md`, and `LICENSE` (MIT).

### Changed
* Replaced hardcoded environment path in `SKILL.md` with relative `<skill-dir>/scripts/check_docs.py` path for portability across Claude Code, Antigravity, Cursor, and CLI environments.
* Replaced single-domain IoT examples in `SKILL.md` with balanced examples across web APIs, background workers, databases, and optional hardware projects.
* Clarified the **Pragmatic Diataxis Layout** section in `SKILL.md` to explain why `ARCHITECTURE.md` consolidates Reference, ADR, and Runbook in small-to-medium repositories and when to split them.
