# Living Docs (`living-docs`)

[![CI](https://github.com/Light-Yodeler/living-docs/actions/workflows/ci.yml/badge.svg)](https://github.com/Light-Yodeler/living-docs/actions/workflows/ci.yml)
[![Release](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An agent skill and two-way verification tool that keeps project documentation true to the source code in both directions:
1. **Docs -> Code (Forward Check):** Every file path, markdown link, and `function()` identifier written in documentation must exist in the codebase, with zero AI prose filler or hallucinated specifics. <!-- living-docs-ignore -->
2. **Code -> Docs (Reverse Coverage Check):** Every public HTTP route, database table, and `.env.example` variable defined in code is checked for coverage in the documentation. <!-- living-docs-ignore -->

---

## Why `living-docs`?

Most AI-generated documentation suffers from two failure modes:
* **Hallucinated specifics & AI slop:** Invented function names, guessed default values, vague buzzwords (*robust, seamless, cutting-edge*), and unverified security claims.
* **Silent drift:** Endpoints, tables, and environment variables get added in code while `README.md` and architecture docs stay frozen in time.

`living-docs` pairs structured templates (`README.md`, `FEATURES.md`, `ARCHITECTURE.md`, `CHANGELOG.md`) with a zero-dependency Python verifier (`scripts/check_docs.py`) and built-in anti-slop prose rules.

See [`examples/before-and-after.md`](examples/before-and-after.md) for a side-by-side comparison of unchecked AI docs versus verified `living-docs` output.

---

## Pragmatic Diataxis Layout

Strict [Diataxis](https://diataxis.fr/) splits documentation into four separate directory trees (Tutorials, How-To Guides, Reference, Explanation). In small-to-medium repositories, strict separation often leads to fragmented stub files that nobody maintains.

`living-docs` maps the four Diataxis quadrants onto a **compact 4-file baseline**:

| File | Diataxis Role | Contents |
| :--- | :--- | :--- |
| [`README.md`](README.md) | Tutorial / Getting Started | Project overview, documentation map, directory tree, local setup, test commands |
| [`docs/FEATURES.md`](docs/FEATURES.md) | Functional Reference | Catalog of permanent `FEAT-NN` entries: purpose, trigger, exact formula/rules, file touchpoints, config keys, known limitations |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Technical Reference + Explanation (ADR) + How-To Runbook | Mermaid system diagram, env/hardware config, API & event contracts, data model, ADRs (`ADR-NN`), deployment & recovery runbook |
| [`CHANGELOG.md`](CHANGELOG.md) | Release History | Keep a Changelog + SemVer (`[Unreleased]`, `Added`, `Changed`, `Fixed`, `Removed`, `Security`) |

> When a repository grows beyond ~10 ADRs or requires multi-service operational guides, `living-docs` instructs the agent to split `docs/ADR.md` (or `docs/adr/`) and `docs/RUNBOOK.md` into dedicated files. <!-- living-docs-ignore -->

---

## Directory Structure

```text
living-docs/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI (unit tests + self-verification)
├── SKILL.md                          # Main agent skill instructions & built-in prose rules
├── README.md                         # Repository overview, installation, and checker guide
├── CHANGELOG.md                      # Release history of the living-docs skill
├── CONTRIBUTING.md                   # Contribution guide & PR checklist
├── CODE_OF_CONDUCT.md                # Contributor Covenant Code of Conduct
├── LICENSE                           # MIT License
├── docs/
│   ├── FEATURES.md                   # Feature catalog (FEAT-01 .. FEAT-05) for living-docs
│   └── ARCHITECTURE.md               # Architecture, CLI contract, ADRs (ADR-01 .. ADR-03), runbook
├── examples/
│   └── before-and-after.md           # Side-by-side comparison of unchecked vs verified docs
├── resources/
│   ├── README.template.md            # Default (English) README template
│   ├── FEATURES.template.md          # Default (English) FEATURES catalog template
│   ├── ARCHITECTURE.template.md      # Default (English) ARCHITECTURE + ADR + Runbook template
│   ├── CHANGELOG.template.md         # Default (English) CHANGELOG template
│   ├── en/                           # Explicit English templates
│   └── id/                           # Explicit Indonesian templates (Bahasa Indonesia)
├── scripts/
│   └── check_docs.py                 # Two-way documentation verifier (Python 3 standard library)
└── tests/
    └── test_check_docs.py            # Automated unit tests for check_docs.py
```

---

## Installation

### 1. Claude Code
Clone into your global or project skills directory:
```bash
git clone https://github.com/Light-Yodeler/living-docs.git ~/.claude/skills/living-docs
```

### 2. Google Antigravity
Clone into your Antigravity skills config directory:
```bash
git clone https://github.com/Light-Yodeler/living-docs.git ~/.gemini/config/skills/living-docs
```

### 3. Project-Local Skill (Cursor / Codex / Any Agent)
Add as a submodule or copy into `.agent/skills/living-docs/`:
```bash
git submodule add https://github.com/Light-Yodeler/living-docs.git .agent/skills/living-docs
```

---

## Using the Two-Way Checker (`scripts/check_docs.py`)

Requires **Python 3.8+** (uses standard library only, zero external packages).

```bash
python3 scripts/check_docs.py --root /path/to/your/project
```

### What It Checks

| Direction | Check | Severity | Supported Patterns |
| :--- | :--- | :--- | :--- |
| **Docs -> Code** | Em dashes (`\u2014`) in prose | Error (exit 1) | Any un-ignored line outside fenced code blocks (disable with `--allow-em-dash`) |
| **Docs -> Code** | Broken Markdown links | Error (exit 1) | Relative file links `[label](path/to/file.md)` |
| **Docs -> Code** | Missing file paths | Error (exit 1) | Inline code spans with source/doc extensions (e.g. `` `src/app.ts` ``) |
| **Docs -> Code** | Unknown `func()` names | Error (exit 1) | Inline code calls like `walk()`, `find_docs()`, `load_sources()`, `extract_routes()`, `extract_tables()`, `main()` |
| **Docs -> Code** | En dashes, unknown `/api/...` paths or CSS selectors, missing `## [Unreleased]` | Warning (exit 0) | Inline code spans and `CHANGELOG.md` headings | <!-- living-docs-ignore -->
| **Code -> Docs** | Undocumented HTTP routes | Warning (exit 0) | Express, Fastify, Hono, Koa, FastAPI, Flask, Go `net/http`, Gin, Echo, Fiber |
| **Code -> Docs** | Undocumented database tables | Warning (exit 0) | SQL `CREATE TABLE`, SQLAlchemy `__tablename__` |
| **Code -> Docs** | Undocumented env variables | Warning (exit 0) | Keys defined in `.env.example` | <!-- living-docs-ignore -->

### Handling False Positives (Escape Hatches)

When documentation legitimately mentions an external library function, a removed legacy path, or an internal route that should not be flagged, use any of these escape hatches:

1. **Same-line HTML comment:**
   ```markdown
   Calls `externalSdkInit()` <!-- living-docs-ignore --> on startup.
   ```
2. **Next-line HTML comment:**
   ```markdown
   <!-- living-docs-ignore-next-line -->
   Removed in v2.0: `legacyWorker()` in `src/old/worker.ts`.
   ```
3. **Block HTML comments:**
   ```markdown
   <!-- living-docs-ignore-start -->
   Everything inside this block is skipped by check_docs.py.
   <!-- living-docs-ignore-end -->
   ```
4. **Project-wide `.living-docs-ignore` file** (at repo root, one literal, glob, or regex per line):
   ```text
   # Ignore internal debug routes and third-party hooks
   /api/internal/*
   useExternalWidget()
   ```
5. **CLI flags:**
   ```bash
   python3 scripts/check_docs.py --root . --ignore "legacy*" --skip-reverse --allow-em-dash
   ```

---

## Running Tests

Run the unit test suite and self-check this repository:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_docs.py --root .
```

---

## Contributing

Contributions are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before submitting a pull request.

---

## License

Released under the [MIT License](LICENSE).
