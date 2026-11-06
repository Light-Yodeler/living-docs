#!/usr/bin/env python3
"""Two-way verification for project documentation.

Forward checks (Docs -> Code):
- Errors (exit 1):   em dashes, broken markdown links, missing file paths, `func()` names absent from source.
- Warnings (exit 0): en dashes, CSS selectors / API paths absent from source, missing [Unreleased].

Reverse coverage checks (Code -> Docs):
- Warnings (exit 0): API routes, SQL tables, or .env.example keys defined in code but never mentioned in docs.

Usage: python3 check_docs.py --root . [--docs path/to/a.md path/to/b.md]
"""
import argparse
import os
import re
import sys

SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "venv", ".venv",
             "__pycache__", "coverage", ".cache", "backups", "vendor", "target"}
SOURCE_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py", ".ino", ".c", ".cpp",
              ".h", ".hpp", ".go", ".rs", ".java", ".kt", ".swift", ".php", ".rb",
              ".css", ".scss", ".html", ".vue", ".svelte", ".sql", ".sh", ".json",
              ".yaml", ".yml", ".toml", ".conf", ".service", ".env", ".example"}
PATH_EXT = SOURCE_EXT | {".md", ".db", ".txt", ".csv", ".png", ".jpg", ".svg"}
DOC_NAMES = re.compile(r"(README|FEATURES|CHANGELOG|ARCHITECTURE|API|PRD)[^/]*\.md$", re.I)
MAX_BYTES = 2_000_000


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def find_docs(root):
    return sorted(p for p in walk(root) if DOC_NAMES.search(os.path.basename(p)))


def load_sources(root, doc_set):
    chunks, rel_paths, env_keys = [], [], set()
    for path in walk(root):
        rel = os.path.relpath(path, root)
        rel_paths.append(rel.replace(os.sep, "/"))
        if os.path.abspath(path) in doc_set:
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
                if base == ".env.example":
                    for m in re.finditer(r"^([A-Z][A-Z0-9_]+)\s*=", content, re.M):
                        env_keys.add(m.group(1))
        except OSError:
            pass
    return "\n".join(chunks), rel_paths, sorted(env_keys)


def inline_spans(text):
    """Yield (line_no, span) for inline code outside fenced blocks."""
    in_fence = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in re.finditer(r"`([^`\n]+)`", line):
            yield no, m.group(1).strip()


def markdown_links(text):
    """Yield (line_no, target) for markdown links outside fenced blocks."""
    in_fence = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in re.finditer(r"\[[^\]]+\]\(([^)\s]+)\)", line):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--docs", nargs="*")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    docs = [os.path.abspath(d) for d in args.docs] if args.docs else find_docs(root)
    if not docs:
        print("No documentation files found. Create them from the living-docs templates.")
        return 1

    source, rel_paths, env_keys = load_sources(root, set(docs))
    errors, warnings = [], []
    all_docs_text = []

    for doc in docs:
        rel_doc = os.path.relpath(doc, root)
        doc_dir = os.path.dirname(doc)
        with open(doc, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        all_docs_text.append(text)

        for no, line in enumerate(text.splitlines(), 1):
            if "\u2014" in line:
                errors.append(f"{rel_doc}:{no}: em dash found, rewrite with a period, comma, colon, or parentheses")
            elif "\u2013" in line:
                warnings.append(f"{rel_doc}:{no}: en dash found, prefer 'sampai' or a hyphen")

        for no, target in markdown_links(text):
            if target.startswith(("http://", "https://", "mailto:", "file://", "#")):
                continue
            if not path_exists(target, root, doc_dir, rel_paths):
                errors.append(f"{rel_doc}:{no}: broken markdown link `{target}`")

        for no, span in inline_spans(text):
            if " " in span or span.startswith(("http://", "https://")):
                continue
            func = re.fullmatch(r"(?:[A-Za-z_$][\w$]*\.)*([A-Za-z_$][\w$]*)\(\)", span)
            if func:
                name = func.group(1)
                if not re.search(r"\b" + re.escape(name) + r"\b", source):
                    errors.append(f"{rel_doc}:{no}: `{span}` not found in source")
                continue
            if span.startswith("/"):
                route = re.sub(r"[?<{].*$", "", span)
                looks_like_api = route.startswith(("/api", "/ws")) or route.strip("/").count("/") >= 1
                route = re.sub(r"^/api", "", route).rstrip("/")
                if looks_like_api and route and route not in source:
                    warnings.append(f"{rel_doc}:{no}: API path `{span}` not found in source")
                continue
            if re.fullmatch(r"#[0-9A-Fa-f]{3,8}", span):
                continue
            if re.fullmatch(r"[.#][A-Za-z][\w-]*", span):
                if span[1:] not in source:
                    warnings.append(f"{rel_doc}:{no}: selector `{span}` not found in source")
                continue
            ext = os.path.splitext(span.split("?")[0])[1].lower()
            if ext in PATH_EXT and re.fullmatch(r"[\w./-]+", span):
                if not path_exists(span, root, doc_dir, rel_paths):
                    errors.append(f"{rel_doc}:{no}: path `{span}` does not exist")

        if os.path.basename(doc).upper().startswith("CHANGELOG") and "## [Unreleased]" not in text:
            warnings.append(f"{rel_doc}: no '## [Unreleased]' section")

    combined_docs = "\n".join(all_docs_text)

    # Reverse check 1: Express/router endpoints in code must appear in docs
    routes_in_code = set(re.findall(r"\b(?:router|app)\.(?:get|post|put|patch|delete)\(\s*['\"](/[^'\"*]*)['\"]", source))
    for route in sorted(routes_in_code):
        if route not in combined_docs:
            warnings.append(f"coverage: route `{route}` exists in code but is not documented")

    # Reverse check 2: SQL tables in code must appear in docs
    tables_in_code = set(re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][\w]*)", source, re.I))
    for table in sorted(tables_in_code):
        if table not in combined_docs:
            warnings.append(f"coverage: SQL table `{table}` exists in code but is not documented")

    # Reverse check 3: .env.example keys should appear in docs
    for key in env_keys:
        if key not in combined_docs:
            warnings.append(f"coverage: env var `{key}` in .env.example is not documented")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\nChecked {len(docs)} doc file(s): {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
