#!/usr/bin/env python3
"""Two-way verification for project documentation.

Forward checks (Docs -> Code):
- Errors (exit 1):   em dashes (unless --allow-em-dash), broken markdown links,
                     missing file paths, `func()` names absent from source.
- Warnings (exit 0): en dashes, CSS selectors / API paths absent from source,
                     missing '## [Unreleased]' in CHANGELOG.

Reverse coverage checks (Code -> Docs):
- Warnings (exit 0): HTTP routes (Express/Fastify/Hono, FastAPI/Flask, Go net/http/Gin/Echo),
                     SQL tables / SQLAlchemy `__tablename__`, or `.env.example` keys
                     defined in code but never mentioned in docs.

Escape hatches for false positives:
- Inline comment on the same line:  `foo()` <!-- living-docs-ignore -->
- Next-line comment:                <!-- living-docs-ignore-next-line -->
- Block comments:                   <!-- living-docs-ignore-start --> ... <!-- living-docs-ignore-end -->
- Whole-file comment:               <!-- living-docs-ignore-file -->
- Project ignore file:              `.living-docs-ignore` at repo root (one pattern or regex per line)
- CLI flags:                        `--ignore <pattern>`, `--skip-reverse`, `--allow-em-dash`

Usage:
  python3 check_docs.py --root . [--docs path/to/a.md ...] [--ignore PATTERN ...]
"""
import argparse
import fnmatch
import os
import re
import sys

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "venv", ".venv",
    "__pycache__", "coverage", ".cache", "backups", "vendor", "target",
    "resources", "examples", "tests", "evals",
}
SOURCE_EXT = {
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".ino", ".c", ".cpp",
    ".h", ".hpp", ".go", ".rs", ".java", ".kt", ".swift", ".php", ".rb",
    ".css", ".scss", ".html", ".vue", ".svelte", ".sql", ".sh", ".json",
    ".yaml", ".yml", ".toml", ".conf", ".service", ".env", ".example",
}
PATH_EXT = SOURCE_EXT | {".md", ".db", ".txt", ".csv", ".png", ".jpg", ".svg"}
DOC_NAMES = re.compile(r"^(README|FEATURES|CHANGELOG|ARCHITECTURE|API|PRD|RUNBOOK|ADR)[^/]*\.md$", re.I)
MAX_BYTES = 2_000_000

BUILTIN_FUNCS = {
    # SQL & database built-ins
    "COUNT", "SUM", "AVG", "MIN", "MAX", "NOW", "COALESCE", "UUID",
    "JSON_EXTRACT", "CAST", "LOWER", "UPPER", "TRIM", "LENGTH", "ROUND",
    "ABS", "RANDOM", "STRFTIME", "DATETIME", "DATE", "IFNULL", "NULLIF",
    # Common language / runtime built-ins
    "main", "init", "setup", "print", "len", "str", "int", "float", "bool",
    "list", "dict", "set", "tuple", "map", "filter", "reduce", "fetch",
    "require", "import", "Date", "Array", "Object", "Promise", "Error",
    "String", "Number", "Boolean", "JSON", "RegExp", "Math", "Symbol",
    "BigInt", "parseInt", "parseFloat", "setTimeout", "setInterval",
    "clearTimeout", "clearInterval", "super", "next",
}

IGNORE_FILE_DIRECTIVE = "<!-- living-docs-ignore-file -->"
IGNORE_START_DIRECTIVE = "<!-- living-docs-ignore-start -->"
IGNORE_END_DIRECTIVE = "<!-- living-docs-ignore-end -->"
IGNORE_NEXT_DIRECTIVE = "<!-- living-docs-ignore-next-line -->"
IGNORE_LINE_DIRECTIVE = "<!-- living-docs-ignore -->"

ROUTE_PATTERNS = [
    # Express, Fastify, Hono, Koa, Gin, Echo, Fiber, Chi
    re.compile(
        r"\b(?:router|app|server|fastify|api|r|e|v1|v2|mux)\."
        r"(?:get|post|put|patch|delete|GET|POST|PUT|PATCH|DELETE)\(\s*['\"](/[^'\"*]*)['\"]"
    ),
    # FastAPI, Flask, APIRouter, Blueprint
    re.compile(
        r"@(?:app|router|bp|api)\."
        r"(?:get|post|put|patch|delete|route)\(\s*['\"](/[^'\"*]*)['\"]"
    ),
    # Go net/http &gorilla/mux HandleFunc
    re.compile(
        r"\b(?:http|mux)\.HandleFunc\(\s*['\"](/[^'\"*]*)['\"]"
    ),
]

TABLE_PATTERNS = [
    re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?([A-Za-z_][\w]*)[`\"']?", re.I),
    re.compile(r"__tablename__\s*=\s*['\"]([A-Za-z_][\w]*)['\"]"),
]


def walk(root, include_all_dirs=False):
    for dirpath, dirnames, filenames in os.walk(root):
        if not include_all_dirs:
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        else:
            dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "__pycache__", ".venv", "venv"}]
        for name in filenames:
            yield os.path.join(dirpath, name)


def find_docs(root):
    return sorted(
        p for p in walk(root)
        if not p.endswith(".template.md") and DOC_NAMES.search(os.path.basename(p))
    )


def load_ignore_patterns(root, cli_ignores):
    patterns = list(cli_ignores or [])
    ignore_path = os.path.join(root, ".living-docs-ignore")
    if os.path.isfile(ignore_path):
        try:
            with open(ignore_path, encoding="utf-8", errors="ignore") as fh:
                for raw in fh:
                    line = raw.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except OSError:
            pass
    return patterns


def is_ignored(token, rel_doc, ignore_patterns):
    for pat in ignore_patterns:
        if pat == token or pat in token:
            return True
        if fnmatch.fnmatch(token, pat) or fnmatch.fnmatch(rel_doc, pat):
            return True
        try:
            if re.search(pat, token):
                return True
        except re.error:
            pass
    return False


def load_sources(root, doc_set):
    chunks, rel_paths, env_keys = [], [], set()
    source_file_count = 0
    for path in walk(root, include_all_dirs=True):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        rel_paths.append(rel)
        if os.path.abspath(path) in doc_set:
            continue
        # Skip test/example/resource/eval directories when indexing production source code
        top_dir = rel.split("/", 1)[0]
        if top_dir in {"resources", "examples", "tests", "evals"}:
            continue
        base = os.path.basename(path)
        ext = os.path.splitext(path)[1].lower()
        if ext not in SOURCE_EXT and not base.startswith(".env"):
            continue
        try:
            if os.path.getsize(path) > MAX_BYTES:
                continue
            with open(path, encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                chunks.append(content)
                if ext in SOURCE_EXT - {".json", ".yaml", ".yml", ".toml", ".md"}:
                    source_file_count += 1
                if base == ".env.example":
                    for m in re.finditer(r"^([A-Z][A-Z0-9_]+)\s*=", content, re.M):
                        env_keys.add(m.group(1))
        except OSError:
            pass
    return "\n".join(chunks), rel_paths, sorted(env_keys), source_file_count > 0


def has_file_ignore_directive(text):
    """Return True if IGNORE_FILE_DIRECTIVE appears outside fenced or inline code."""
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        outside_code = re.sub(r"`[^`\n]+`", "", line)
        if IGNORE_FILE_DIRECTIVE in outside_code:
            return True
    return False


def iter_active_lines(text):
    """Yield (line_no, line, in_fence) for lines not suppressed by ignore comments."""
    in_fence = False
    in_ignore_block = False
    ignore_next = False

    for no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            yield no, line, True
            continue

        if not in_fence:
            outside_code = re.sub(r"`[^`\n]+`", "", line)
            outside_stripped = outside_code.strip()
            if IGNORE_START_DIRECTIVE in outside_code:
                in_ignore_block = True
                continue
            if IGNORE_END_DIRECTIVE in outside_code:
                in_ignore_block = False
                continue
            if in_ignore_block:
                continue
            if IGNORE_NEXT_DIRECTIVE in outside_code or outside_stripped == IGNORE_LINE_DIRECTIVE:
                ignore_next = True
                continue
            if ignore_next:
                ignore_next = False
                continue
            if IGNORE_LINE_DIRECTIVE in outside_code:
                continue

        yield no, line, in_fence


def inline_spans(text):
    """Yield (line_no, span) for inline code outside fenced blocks and ignore directives."""
    for no, line, in_fence in iter_active_lines(text):
        if in_fence:
            continue
        for m in re.finditer(r"`([^`\n]+)`", line):
            yield no, m.group(1).strip()


def markdown_links(text):
    """Yield (line_no, target) for markdown links outside fenced blocks, inline code, and ignore directives."""
    for no, line, in_fence in iter_active_lines(text):
        if in_fence:
            continue
        line_without_code = re.sub(r"`[^`\n]+`", "", line)
        for m in re.finditer(r"\[[^\]]+\]\(([^)\s]+)\)", line_without_code):
            yield no, m.group(1).strip()


def path_exists(span, root, doc_dir, rel_paths):
    clean = span.split("?")[0].split("#")[0].rstrip("/")
    if not clean:
        return True
    for base in (doc_dir, root):
        if os.path.exists(os.path.join(base, clean)):
            return True
    suffix = "/" + re.sub(r"^\./", "", clean)
    return any(("/" + p).endswith(suffix) for p in rel_paths)


def extract_routes(source):
    routes = set()
    for pattern in ROUTE_PATTERNS:
        for match in pattern.findall(source):
            routes.add(match)
    return sorted(routes)


def extract_tables(source):
    tables = set()
    for pattern in TABLE_PATTERNS:
        for match in pattern.findall(source):
            tables.add(match)
    return sorted(tables)


def check_version_consistency(root, docs):
    """Return warning messages if manifest version, CHANGELOG version, or README badge version drift."""
    versions = {}

    version_file = os.path.join(root, "VERSION")
    if os.path.isfile(version_file):
        try:
            with open(version_file, encoding="utf-8") as fh:
                val = fh.read().strip().lstrip("v")
            if re.match(r"^\d+\.\d+\.\d+$", val):
                versions["VERSION"] = val
        except OSError:
            pass

    pkg_json = os.path.join(root, "package.json")
    if os.path.isfile(pkg_json):
        try:
            with open(pkg_json, encoding="utf-8") as fh:
                m = re.search(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"', fh.read())
            if m:
                versions["package.json"] = m.group(1)
        except OSError:
            pass

    for toml_name in ("pyproject.toml", "Cargo.toml"):
        toml_path = os.path.join(root, toml_name)
        if os.path.isfile(toml_path):
            try:
                with open(toml_path, encoding="utf-8") as fh:
                    m = re.search(r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', fh.read(), re.M)
                if m:
                    versions[toml_name] = m.group(1)
            except OSError:
                pass

    for doc in docs:
        base = os.path.basename(doc).upper()
        try:
            with open(doc, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        if base.startswith("CHANGELOG"):
            m = re.search(r"^##\s+\[(\d+\.\d+\.\d+)\]", text, re.M)
            if m:
                versions["CHANGELOG.md"] = m.group(1)
        elif base.startswith("README"):
            m = re.search(r"img\.shields\.io/badge/version-(\d+\.\d+\.\d+)-", text)
            if m:
                versions["README.md"] = m.group(1)

    if len(set(versions.values())) > 1:
        summary = ", ".join(f"{k}={v}" for k, v in versions.items())
        return [f"version: mismatch across files ({summary}); run scripts/bump_version.py to synchronize"]
    return []


def main():
    ap = argparse.ArgumentParser(description="Two-way verification for project documentation.")
    ap.add_argument("--root", default=".", help="Project root directory (default: .)")
    ap.add_argument("--docs", nargs="*", help="Explicit markdown files to check")
    ap.add_argument("--ignore", action="append", default=[], help="Ignore pattern (repeatable)")
    ap.add_argument("--skip-reverse", action="store_true", help="Skip reverse coverage checks (Code -> Docs)")
    ap.add_argument("--allow-em-dash", action="store_true", help="Do not fail on em dashes (—)")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    docs = [os.path.abspath(d) for d in args.docs] if args.docs else find_docs(root)
    if not docs:
        print("No documentation files found. Create them from the living-docs templates.")
        return 1

    ignore_patterns = load_ignore_patterns(root, args.ignore)
    source, rel_paths, env_keys, has_source_files = load_sources(root, set(docs))
    errors, warnings = [], []
    all_docs_text = []

    for doc in docs:
        rel_doc = os.path.relpath(doc, root).replace(os.sep, "/")
        doc_dir = os.path.dirname(doc)
        with open(doc, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        all_docs_text.append(text)

        if has_file_ignore_directive(text) or is_ignored(rel_doc, rel_doc, ignore_patterns):
            continue

        for no, line, in_fence in iter_active_lines(text):
            if in_fence:
                continue
            if not args.allow_em_dash and "\u2014" in line:
                errors.append(
                    f"{rel_doc}:{no}: em dash found, rewrite with a period, comma, colon, or parentheses"
                )
            elif "\u2013" in line:
                warnings.append(
                    f"{rel_doc}:{no}: en dash found, prefer 'to'/'sampai' or a hyphen (-)"
                )

        for no, target in markdown_links(text):
            if target.startswith(("http://", "https://", "mailto:", "file://", "#")):
                continue
            if is_ignored(target, rel_doc, ignore_patterns):
                continue
            if not path_exists(target, root, doc_dir, rel_paths):
                errors.append(f"{rel_doc}:{no}: broken markdown link `{target}`")

        for no, span in inline_spans(text):
            if " " in span or span.startswith(("http://", "https://")):
                continue
            if is_ignored(span, rel_doc, ignore_patterns):
                continue

            func = re.fullmatch(r"(?:[A-Za-z_$][\w$]*\.)*([A-Za-z_$][\w$]*)\(\)", span)
            if func:
                name = func.group(1)
                if name in BUILTIN_FUNCS or name.upper() in BUILTIN_FUNCS:
                    continue
                if has_source_files and not re.search(r"\b" + re.escape(name) + r"\b", source):
                    errors.append(f"{rel_doc}:{no}: `{span}` not found in source")
                continue

            if span.startswith("/"):
                route = re.sub(r"[?<{].*$", "", span)
                looks_like_api = route.startswith(("/api", "/ws")) or route.strip("/").count("/") >= 1
                route_tail = re.sub(r"^/api", "", route).rstrip("/")
                if has_source_files and looks_like_api and route_tail and route_tail not in source:
                    warnings.append(f"{rel_doc}:{no}: API path `{span}` not found in source")
                continue

            if re.fullmatch(r"#[0-9A-Fa-f]{3,8}", span):
                continue

            if re.fullmatch(r"[.#][A-Za-z][\w-]*", span):
                if has_source_files and span[1:] not in source:
                    warnings.append(f"{rel_doc}:{no}: selector `{span}` not found in source")
                continue

            ext = os.path.splitext(span.split("?")[0])[1].lower()
            if ext in PATH_EXT and re.fullmatch(r"[\w./-]+", span):
                if not path_exists(span, root, doc_dir, rel_paths):
                    errors.append(f"{rel_doc}:{no}: path `{span}` does not exist")

        if os.path.basename(doc).upper().startswith("CHANGELOG") and "## [Unreleased]" not in text:
            warnings.append(f"{rel_doc}: no '## [Unreleased]' section")

    if not args.skip_reverse and has_source_files:
        combined_docs = "\n".join(all_docs_text)

        # Reverse check 1: HTTP endpoints in code must appear in docs
        for route in extract_routes(source):
            if not is_ignored(route, "", ignore_patterns) and route not in combined_docs:
                warnings.append(f"coverage: route `{route}` exists in code but is not documented")

        # Reverse check 2: SQL / ORM tables in code must appear in docs
        for table in extract_tables(source):
            if not is_ignored(table, "", ignore_patterns) and table not in combined_docs:
                warnings.append(f"coverage: SQL table `{table}` exists in code but is not documented")

        # Reverse check 3: .env.example keys should appear in docs
        for key in env_keys:
            if not is_ignored(key, "", ignore_patterns) and key not in combined_docs:
                warnings.append(f"coverage: env var `{key}` in .env.example is not documented")

    if not args.skip_reverse:
        warnings.extend(check_version_consistency(root, docs))

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\nChecked {len(docs)} doc file(s): {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
