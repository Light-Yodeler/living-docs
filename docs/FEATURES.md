# Feature Catalog: `living-docs`

Catalog of features implemented in the `living-docs` skill and verifier, their triggers, exact rules, implementing files, and configuration options. Every feature has a permanent `FEAT-NN` ID.

---

## Module 1: Skill Workflow & Templates

### FEAT-01: Pragmatic 4-File Documentation Workflow
* **Purpose:** Guides AI coding agents to create and maintain accurate project documentation (`README.md`, `docs/FEATURES.md`, `docs/ARCHITECTURE.md`, `CHANGELOG.md`) without file sprawl.
* **Trigger:** Invoked when scaffolding a project, adding/changing a feature, route, database table, or configuration key, or auditing project docs.
* **Behavior & Rules:**
  1. Locates existing documentation files via `find_docs()` before creating new files.
  2. Matches the language of existing documentation (or the user's prompt for new projects) and selects the matching template set from `resources/en/` or `resources/id/`.
  3. Enforces permanent, monotonically increasing IDs (`FEAT-NN` and `ADR-NN`) and translates lifecycle markers consistently (`Removed in vX.Y.Z` / `Dihapus di versi X.Y.Z`, `Superseded by ADR-MM` / `Digantikan oleh ADR-MM`).
* **Touchpoints:**
  * Skill Definition: `SKILL.md`
  * English Templates: `resources/en/README.template.md`, `resources/en/FEATURES.template.md`, `resources/en/ARCHITECTURE.template.md`, `resources/en/CHANGELOG.template.md`
  * Indonesian Templates: `resources/id/README.template.md`, `resources/id/FEATURES.template.md`, `resources/id/ARCHITECTURE.template.md`, `resources/id/CHANGELOG.template.md`
* **Configuration:** None (controlled by target project language and structure).

### FEAT-02: Built-In Anti-Slop Documentation Prose Rules
* **Purpose:** Prevents AI-generated filler, buzzwords, and fabricated technical claims without requiring external skills to be installed.
* **Trigger:** Applied during all documentation drafting and editing steps in `SKILL.md`.
* **Behavior & Rules:**
  1. Requires every identifier, default value, formula, and route to come from source code or command output, using `[TODO: confirm]` (`[TODO: konfirmasi]`) when unverified.
  2. Bans empty AI buzzwords (*robust, seamless, cutting-edge, comprehensive, leverage, delve, empower*) and em dashes (`\u2014`).
  3. Enforces active component-named sentences over actorless passives.
* **Touchpoints:**
  * Skill Rules: `SKILL.md`
  * Automated Dash Check: `scripts/check_docs.py` (`iter_active_lines()`, `main()`)
* **Configuration:** `--allow-em-dash` CLI flag in `scripts/check_docs.py` when the author's voice intentionally uses em dashes.

---

## Module 2: Two-Way Documentation Verifier (`scripts/check_docs.py`)

### FEAT-03: Forward Verification (`Docs -> Code`)
* **Purpose:** Detects broken links, nonexistent file paths, hallucinated `func()` names, and prose violations in Markdown documentation.
* **Trigger:** Executed via `python3 scripts/check_docs.py --root <path>`.
* **Behavior & Rules:**
  1. Scans Markdown files matching `DOC_NAMES` (`README`, `FEATURES`, `CHANGELOG`, `ARCHITECTURE`, `API`, `PRD`, `RUNBOOK`, `ADR`), skipping `*.template.md` and directories in `SKIP_DIRS`.
  2. Reports **Errors (exit code 1)** for em dashes (`\u2014`), broken relative links in `markdown_links()`, missing file paths checked by `path_exists()`, and `func()` inline code spans absent from source files (excluding SQL/runtime built-ins in `BUILTIN_FUNCS`).
  3. Reports **Warnings (exit code 0)** for en dashes (`\u2013`), `/api/...` routes or CSS selectors absent from source, and `CHANGELOG.md` files missing `## [Unreleased]`. <!-- living-docs-ignore -->
* **Touchpoints:**
  * Verifier Script: `scripts/check_docs.py` (`walk()`, `find_docs()`, `load_sources()`, `inline_spans()`, `markdown_links()`, `path_exists()`, `main()`)
  * Test Suite: `tests/test_check_docs.py`
* **Configuration:** `--root`, `--docs`, `--allow-em-dash`.
* **Known Limitations:** `func()` verification uses whole-word regex matching across concatenated source text rather than full AST parsing, so a function name that appears only inside a source comment is treated as present.

### FEAT-04: Multi-Stack Reverse Coverage Check (`Code -> Docs`)
* **Purpose:** Warns when public HTTP endpoints, database tables, or environment variables exist in source code but are never mentioned in documentation.
* **Trigger:** Runs automatically during `scripts/check_docs.py` unless `--skip-reverse` is passed.
* **Behavior & Rules:**
  1. `extract_routes()` scans source files against `ROUTE_PATTERNS` covering Express, Fastify, Hono, Koa, FastAPI, Flask, Go `net/http`, `gorilla/mux`, Gin, Echo, and Fiber.
  2. `extract_tables()` scans source files against `TABLE_PATTERNS` covering SQL `CREATE TABLE` statements and SQLAlchemy `__tablename__` declarations.
  3. `load_sources()` extracts uppercase keys from `.env.example` (if present in the target project) <!-- living-docs-ignore -->.
  4. Emits a `WARN coverage:` line (exit code 0) for each route, table, or env key missing from the combined documentation text.
* **Touchpoints:**
  * Verifier Script: `scripts/check_docs.py` (`extract_routes()`, `extract_tables()`, `load_sources()`)
  * Test Suite: `tests/test_check_docs.py`
* **Configuration:** `--skip-reverse` flag to disable reverse checks.
* **Known Limitations:** File-system routed frameworks (such as Next.js App Router `app/api/*/route.ts` or SvelteKit `+server.ts`) are not yet extracted by `ROUTE_PATTERNS`.

### FEAT-05: False-Positive Escape Hatches
* **Purpose:** Allows authors to suppress false positives on external SDK calls, illustrative examples, or internal routes without deleting valid documentation.
* **Trigger:** Evaluated while parsing Markdown lines and filtering identifiers in `scripts/check_docs.py`.
* **Behavior & Rules:**
  1. `iter_active_lines()` skips lines containing `<!-- living-docs-ignore -->`, lines immediately following `<!-- living-docs-ignore-next-line -->`, and blocks between `<!-- living-docs-ignore-start -->` and `<!-- living-docs-ignore-end -->`.
  2. Files containing `<!-- living-docs-ignore-file -->` skip all forward checks.
  3. `load_ignore_patterns()` loads literal strings, `fnmatch` globs, or regular expressions from `.living-docs-ignore` and `--ignore` CLI arguments, tested via `is_ignored()`.
* **Touchpoints:**
  * Verifier Script: `scripts/check_docs.py` (`iter_active_lines()`, `load_ignore_patterns()`, `is_ignored()`)
  * Test Suite: `tests/test_check_docs.py`
* **Configuration:** `.living-docs-ignore` file at repo root, `--ignore <pattern>` CLI argument.
