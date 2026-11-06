---
name: living-docs
description: >-
  Creates and maintains project documentation (README, FEATURES catalog, CHANGELOG,
  architecture/API/data-model reference, ADRs, and operational runbooks) so other
  developers can see every feature, why it was built that way, and how to operate it.
  Use when starting a new project, after adding or changing a feature, endpoint, database
  table/column, settings key, sensor/hardware pin, payload field, or config option, and
  when the user asks to document or audit docs.
---

# Living Docs

Keep project documentation true to the code in both directions (every claim in docs exists in
code, and every surface in code is covered in docs). Every fact written must come from the
code, a command output, or the user. Never invent function names, numbers, dates, versions,
or security properties. Write prose following `antislop-copywriting` (load it if not already
loaded).

## Framework Alignment (Diataxis + Docs-as-Code)

| Document | Diataxis Role | Purpose |
| :--- | :--- | :--- |
| `README.md` | Tutorial / Getting Started | Entry point, doc map, directory tree, local setup, test commands |
| `FEATURES.md` | Functional Reference | Catalog of `FEAT-NN` entries: purpose, trigger, exact rule/formula, touchpoints, config, known gaps |
| `ARCHITECTURE.md` (or `SYSTEM_AND_API_DOCUMENTATION.md`) | Technical Reference + Explanation (ADR) + How-To Runbook | System diagram, hardware/env config, API/WS contracts, DB schema, ADRs (`ADR-NN`), deployment/rollback runbook |
| `CHANGELOG.md` | Release History | Keep a Changelog + SemVer (`[Unreleased]`, `Added`, `Changed`, `Fixed`, `Removed`, `Security`) |

## When to run, and what to touch

| Change in this task | README | FEATURES | CHANGELOG | ARCHITECTURE |
| :--- | :---: | :---: | :---: | :---: |
| New project scaffolded | create | create | create | create |
| New user-facing feature | if run steps change | add `FEAT-NN` | `Added` | if API/data touched |
| Behavior of a feature changed | | edit that entry | `Changed` | if API/data touched |
| Bug fixed | | only if documented behavior was wrong | `Fixed` | |
| New/changed endpoint, WS message, payload field | | update touchpoints | `Added`/`Changed` | update contract |
| New table, column, settings key, default value | | update config list | `Added`/`Changed` | update schema |
| New sensor, pin, device, env var | update hardware/setup table | update source list | `Added` | update wiring/config |
| Non-obvious architectural trade-off chosen | | | | add `ADR-NN` |
| Security hardening or known gap found | | update entry honestly | `Security` | |
| Pure refactor, typo, formatting, no behavior change | skip | skip | skip | skip |

Skip silently when the last row applies. Do not create docs for throwaway scripts or one-off experiments.

## Procedure

1. **Locate existing docs.** Search the repo (exclude `node_modules`, `.git`, build output) for
   `README.md`, `FEATURES.md`, `CHANGELOG.md`, and API/architecture/PRD docs. If the project already
   keeps docs in a folder (for example `docs/` or `panel_dashboard/README/`), write there and keep its
   file names. Only for a project with no docs, create `README.md` at the root and the rest in `docs/`.
2. **Match the existing language and style.** Write in the language the existing docs use. For a new
   project, use the language the user writes in.
3. **Collect facts from code before writing.** For each item you are about to document, open or grep
   the source: function names, route paths, table columns, default values, thresholds, pins, `.env.example`
   keys. If a value cannot be found, leave it out or mark it `[TODO: konfirmasi]`. Do not fill gaps with
   plausible guesses.
4. **Write or update using the templates** in `resources/`:
   - [README.template.md](resources/README.template.md): entry point, doc map, directory tree, how to run.
   - [FEATURES.template.md](resources/FEATURES.template.md): one entry per feature, grouped by module.
   - [CHANGELOG.template.md](resources/CHANGELOG.template.md): Keep a Changelog format.
   - [ARCHITECTURE.template.md](resources/ARCHITECTURE.template.md): system diagram, API contract, data model, ADRs (`ADR-NN`), operational runbook.
5. **Feature and ADR IDs.** Use `FEAT-NN` and `ADR-NN`, continuing from the highest existing number.
   Never renumber or reuse an ID. A removed feature keeps its ID with a `Dihapus di versi X` note; a
   superseded decision keeps its ID with `Digantikan oleh ADR-MM`.
6. **Changelog entries.** Add to `## [Unreleased]` unless the user names a version or the project has a
   real version source (`package.json` version, a release tag, or an asset cache-buster bumped in this task).
   Use today's date only when cutting a version. Never backfill history you did not observe; if you must
   reconstruct old history, state that in a note at the top.
7. **Record known gaps.** If you notice a missing safeguard while reading code (plaintext secret, no
   validation, no auth), write it as a known limitation in the feature entry and under `Security` in
   `[Unreleased]`. Do not describe a protection the code does not implement.
8. **Verify (Two-Way Check).** Run the checker from the repo root and fix every error before reporting:
   ```bash
   python3 ~/.gemini/config/skills/living-docs/scripts/check_docs.py --root .
   ```
   It runs both forward checks (Docs -> Code: em/en dashes, broken markdown links, missing file paths,
   unknown `function()` names, unknown CSS selectors/routes) and reverse coverage checks (Code -> Docs:
   routes, SQL tables, and `.env.example` keys present in code but missing from docs).
9. **Report briefly.** List which doc files changed and the IDs or changelog lines added. If deployment
   copies a docs folder (for example via `rsync`), sync it the same way the code was synced.

## Entry quality bar

- **FEATURES (`FEAT-NN`):** A developer who never saw the code can answer what it does for the user,
  what triggers it, the exact rule or formula (`simpan jika |ΔLux| >= delta_lux_threshold, default 50`),
  which files implement it, and which settings change it.
- **ADR (`ADR-NN`):** States the context/constraint, the decision taken, and the trade-off/consequences
  (for example, why GPIO 32 on ADC1 is used instead of ADC2 when Wi-Fi is active).
