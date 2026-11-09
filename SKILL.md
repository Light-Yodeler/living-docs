---
name: living-docs
description: >-
  Creates, verifies, and maintains project documentation (README, FEATURES catalog,
  CHANGELOG, architecture/API/data-model reference, ADRs, and operational runbooks) and
  manages Semantic Versioning (patch/minor/major bumps). Make sure to use this skill
  whenever starting a new project, after adding or changing a feature, endpoint, CLI
  command, database table/column, settings key, hardware pin, or config option, when
  bumping versions or cutting a release, or whenever the user asks to document, update
  README/changelog, or audit docs against the codebase.
license: MIT
compatibility: Python 3.8+ standard library (for scripts/check_docs.py and scripts/bump_version.py)
---

# Living Docs

Keep project documentation true to the code in both directions: every claim in docs must exist in code, and every public surface in code must be covered in docs. Every fact written must come from the source code, a command output, or the user. Never invent function names, numbers, dates, versions, or security guarantees.

## Pragmatic Diataxis Layout (Docs-as-Code)

Strict [Diataxis](https://diataxis.fr/) separates documentation into four distinct trees (Tutorials, How-To Guides, Reference, Explanation). In small-to-medium repositories, strict separation often produces dozens of stub files that quickly go stale.

`living-docs` uses a **pragmatic 4-file baseline** that covers all four Diataxis needs without file sprawl. By default, `ARCHITECTURE.md` consolidates technical reference, ADRs, and the operational runbook into a single file. When a project grows large enough (for example, more than 10 ADRs or multi-service runbooks), split them into dedicated `docs/ADR.md` (or `docs/adr/`) and `docs/RUNBOOK.md` files.

| Document | Diataxis Role | Purpose |
| :--- | :--- | :--- |
| `README.md` | Tutorial / Getting Started | Entry point, doc map, directory tree, local setup, test commands |
| `FEATURES.md` | Functional Reference | Catalog of `FEAT-NN` entries: purpose, trigger, exact rule/formula, touchpoints, config, known gaps |
| `ARCHITECTURE.md` | Technical Reference + Explanation (ADR) + How-To Runbook | System diagram, environment/hardware config, API/event contracts, data model, ADRs (`ADR-NN`), deployment/recovery runbook |
| `CHANGELOG.md` | Release History | Keep a Changelog + SemVer (`[Unreleased]`, `Added`, `Changed`, `Fixed`, `Removed`, `Security`) |

## Documentation Prose Rules (Built-In Anti-Slop)

Follow these prose rules in every document you write or edit (if the `antislop-copywriting` skill is installed in your environment, you may load it for additional examples, but the rules below are self-contained):

1. **Zero fabricated specifics:** Every route, function name, threshold, port, CLI flag, or default value must come from the repository or the user. If a value cannot be verified from source, use the language-appropriate placeholder (`[TODO: confirm]` or `[TODO: konfirmasi]`).
2. **Ban empty AI buzzwords:** Do not write *robust, seamless, cutting-edge, comprehensive, leverage, delve, empower, game-changing, next-level, ecosystem*. Replace claims with concrete mechanisms (`caches session tokens in Redis with a 15-minute TTL`, not `provides a robust caching layer`).
3. **No em dashes (`\u2014`):** Rewrite every em dash using a period, comma, colon, or parentheses. Avoid decorative emojis in headings.
4. **No negative parallelism or signposting:** Do not write *"It's not just X, it's Y"* or *"Let's dive into how X works"*. Start directly with the technical fact.
5. **Name the actor or component:** Prefer active sentences that name the component (`The worker retries failed jobs up to 3 times`) over actorless passives (`Retries are performed`).

## When to Run, and What to Touch

| Change in this task | README | FEATURES | CHANGELOG | ARCHITECTURE |
| :--- | :---: | :---: | :---: | :---: |
| New project scaffolded | create | create | create | create |
| New user-facing feature, script, or CLI capability | update usage, commands & directory tree | add `FEAT-NN` | `Added` | if API/CLI/data touched |
| Behavior of a feature or CLI flag changed | update if shown in `README.md` | edit that entry | `Changed` | if API/CLI/data touched |
| File, script, or folder added/renamed/removed | update directory tree & links | update touchpoints | `Added`/`Changed`/`Removed` | if component layout changed |
| Bug fixed | only if setup/usage example was wrong | only if documented behavior was wrong | `Fixed` | |
| New/changed endpoint, event, CLI command, payload field | update if CLI/endpoint is in `README.md` | update touchpoints | `Added`/`Changed` | update contract |
| New table, column, settings key, default value | update if listed in `README.md` | update config list | `Added`/`Changed` | update schema |
| New env var, external service, or hardware pin/device | update setup table | update source list | `Added` | update config/wiring |
| Non-obvious architectural trade-off chosen | | | | add `ADR-NN` |
| Security hardening or known gap found | update if security/setup notes affected | update entry honestly | `Security` | |
| Version bumped (`PATCH` / `MINOR` / `MAJOR`) | update version badge/refs | | promote `[Unreleased]` -> `[X.Y.Z]` | |
| Pure refactor, typo, formatting, no behavior change | skip | skip | skip | skip |

Skip silently when the last row applies. Do not create docs for throwaway scripts or one-off experiments.

## Procedure

1. **Locate existing docs.** Search the repo (excluding `node_modules`, `.git`, `dist`, `build`, `.venv`) for `README.md`, `FEATURES.md`, `CHANGELOG.md`, and architecture/API docs. If the project already keeps docs in a custom folder (for example `docs/` or `internal/docs/`), write there and preserve its filenames. Only for a project with no docs, create `README.md` at the root and the remaining files in `docs/`.
2. **Match language and translate status markers.** Write in the language the existing docs use; for a brand-new project, match the language the user writes in. Never mix languages between templates and prose. Use the matching template set and markers:

   | Element | English (`en`) | Indonesian (`id`) | Other Languages |
   | :--- | :--- | :--- | :--- |
   | **Template folder** | `resources/en/` (or `resources/`) | `resources/id/` | Translate from `resources/en/` |
   | **Unverified value** | `[TODO: confirm]` | `[TODO: konfirmasi]` | Translate consistently |
   | **Removed feature (`FEAT-NN`)** | `Removed in vX.Y.Z` | `Dihapus di versi X.Y.Z` | Translate consistently |
   | **Superseded ADR (`ADR-NN`)** | `Superseded by ADR-MM` | `Digantikan oleh ADR-MM` | Translate consistently |

3. **Collect facts from code before writing.** Open or grep the source for function names, route paths, table columns, default values, formulas, thresholds, CLI flags, and `.env.example` keys. Do not fill gaps with plausible guesses.
4. **Write or update using the templates** in `resources/en/` (English) or `resources/id/` (Indonesian):
   - `README.template.md`: entry point, doc map, directory tree, local setup, test commands.
   - `FEATURES.template.md`: one `FEAT-NN` entry per feature, grouped by module.
   - `CHANGELOG.template.md`: Keep a Changelog + SemVer format.
   - `ARCHITECTURE.template.md`: system diagram, environment/hardware config, API & event contracts, data model, ADRs (`ADR-NN`), operational runbook.
5. **Always check if `README.md` must be updated.** Never leave a user-visible change documented only inside `docs/` while `README.md` goes stale. Update `README.md` whenever any of the following happen:
   - **Files or folders added, renamed, or deleted:** Update the **Directory Structure** tree and any relative links in `README.md`.
   - **New feature, CLI script, flag, or workflow added/changed:** Add or update the usage section, command examples, or summary table in `README.md`.
   - **Setup, dependencies, environment variables, or test commands changed:** Update the **Running Locally** and **Testing** sections in `README.md`.
   - **Version bumped:** Synchronize the version badge or version references in `README.md` using `scripts/bump_version.py`.
6. **Feature and ADR IDs.** Use `FEAT-NN` and `ADR-NN`, continuing from the highest existing number. Never renumber or reuse an ID. A removed feature keeps its ID with a `Removed in vX.Y.Z` (`Dihapus di versi X.Y.Z`) note; a superseded decision keeps its ID with `Superseded by ADR-MM` (`Digantikan oleh ADR-MM`).
7. **Changelog and Semantic Version Management (`MAJOR.MINOR.PATCH`).**
   - Always record changes under the appropriate Keep a Changelog heading (`Added`, `Changed`, `Fixed`, `Removed`, `Security`).
   - Choose the Semantic Versioning (`X.Y.Z`) increment based on the actual code change:
     | Change Type | Changelog Category | Version Segment | Example |
     | :--- | :--- | :--- | :--- |
     | Bug fix, security patch, or small behavior tweak | `Fixed`, `Security`, `Changed` | **PATCH** (`X.Y.(Z+1)`) | `0.1.0 -> 0.1.1` |
     | New backward-compatible feature (`FEAT-NN`), endpoint, or config key | `Added` | **MINOR** (`X.(Y+1).0`) | `0.1.1 -> 0.2.0` |
     | Breaking API/schema change or removed feature | `Removed`, `Changed` (`BREAKING`) | **MAJOR** (`(X+1).0.0`) | `0.2.0 -> 1.0.0` |
   - **When to stay in `## [Unreleased]` vs. bump the version:**
     - Add entries to `## [Unreleased]` first while work is in progress.
     - When cutting a release, when the user asks to bump the version, or when the project versions every completed fix/feature, run `scripts/bump_version.py` (relative to `<skill-dir>`):
       ```bash
       python3 <skill-dir>/scripts/bump_version.py --root . --bump patch|minor|major|auto
       ```
       `--bump auto` inspects `## [Unreleased]` (`Removed`/`BREAKING` -> major, `Added` -> minor, `Fixed`/`Changed`/`Security` -> patch), updates `VERSION`, `package.json`, `pyproject.toml`, `Cargo.toml`, and `README.md` version badges, and promotes `## [Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD`. Never backfill history you did not observe.
8. **Record known gaps honestly.** If you notice a missing safeguard while reading code (unauthenticated endpoint, plaintext token storage, in-memory state lost on restart, missing input validation), record it under **Known Limitations** in the feature entry and under `Security` in `[Unreleased]`. Never describe a protection the code does not implement.
9. **Verify (Two-Way Check).** Run `scripts/check_docs.py` (resolved relative to this `SKILL.md` directory, `<skill-dir>`) from the target project root and fix every error before reporting:
   ```bash
   python3 <skill-dir>/scripts/check_docs.py --root .
   ```
   - **Forward checks (`Docs -> Code`):** Fails (exit 1) on em dashes, broken markdown links, nonexistent file paths, and `func()` identifiers absent from source code. Warns (exit 0) on en dashes, unknown CSS selectors or `/api/...` paths, and missing `## [Unreleased]`.
   - **Reverse coverage & version checks (`Code <-> Docs`):** Warns (exit 0) when HTTP routes (Express/Fastify/Hono, FastAPI/Flask, Go `net/http`/Gin/Echo), SQL/ORM tables (`CREATE TABLE`, `__tablename__`), or `.env.example` keys exist in source code but are missing from docs, or when version numbers drift across `VERSION`, `package.json`, `pyproject.toml`, `Cargo.toml`, `CHANGELOG.md`, and `README.md` badges.
   - **Handling false positives (Escape Hatches):** When a doc legitimately references an external library function, third-party endpoint, or historical path removed from source, suppress the false positive cleanly instead of deleting accurate prose:
     - Inline comment on the same line: `` `externalHook()` <!-- living-docs-ignore --> ``
     - Next-line comment: `<!-- living-docs-ignore-next-line -->`
     - Block comments: `<!-- living-docs-ignore-start -->` ... `<!-- living-docs-ignore-end -->`
     - Project-wide ignore file: add literal tokens, globs, or regexes (one per line) to `.living-docs-ignore` at the project root, or pass `--ignore <pattern>`.
10. **Report briefly.** List which documentation files changed and the `FEAT-NN` / `ADR-NN` IDs or changelog entries added.

## Entry Quality Bar

- **FEATURES (`FEAT-NN`):** A developer who has never seen the codebase can tell what problem the feature solves, what triggers it, the exact rule or formula (for example, `returns HTTP 429 when requests per IP exceed RATE_LIMIT_MAX (default 60) within a 60s sliding window`, or `retries with delay = base_ms * 2^attempt up to max_retries = 5`), which files and functions implement it, and which configuration keys control it.
- **ADR (`ADR-NN`):** States the concrete context/constraint, the decision taken, and the trade-offs accepted (for example, why cursor-based pagination on `(created_at, id)` was chosen over `OFFSET` pagination for the events feed, or why SQLite in WAL mode was chosen over an external database for single-node deployments).
