#!/usr/bin/env python3
"""Automated Semantic Version (MAJOR.MINOR.PATCH) manager for living-docs.

Responsibilities:
1. Detect current version from VERSION, package.json, pyproject.toml, Cargo.toml, or CHANGELOG.md.
2. Compute next version via --bump (patch | minor | major | auto) or explicit --set X.Y.Z.
   - 'auto' inspects '## [Unreleased]' in CHANGELOG.md:
     * '### Removed' or 'BREAKING' -> major (or minor while major == 0, unless --strict-major)
     * '### Added'                 -> minor
     * '### Fixed' / '### Changed' / '### Security' or fallback -> patch
3. Update all present version files in the project:
   - VERSION
   - package.json
   - pyproject.toml
   - Cargo.toml
   - README.md shields.io version badge (version-X.Y.Z-...)
   - CHANGELOG.md (promotes '## [Unreleased]' items into '## [X.Y.Z] - YYYY-MM-DD')

Usage:
  python3 bump_version.py --root . --bump patch
  python3 bump_version.py --root . --bump auto --message "Fixed: handle null payload"
  python3 bump_version.py --root . --set 1.2.0 --dry-run
"""
import argparse
import datetime
import json
import os
import re
import sys

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
CHANGELOG_VER_RE = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]", re.M)
UNRELEASED_HEADER_RE = re.compile(r"^##\s+\[Unreleased\]\s*$", re.I | re.M)
NEXT_RELEASE_HEADER_RE = re.compile(r"^##\s+\[\d+\.\d+\.\d+\]", re.M)


def parse_semver(ver_str):
    m = SEMVER_RE.match(ver_str.strip().lstrip("v"))
    if not m:
        raise ValueError(f"Invalid semantic version: {ver_str!r} (expected X.Y.Z)")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def format_semver(parts):
    return f"{parts[0]}.{parts[1]}.{parts[2]}"


def find_changelog(root):
    for candidate in ("CHANGELOG.md", os.path.join("docs", "CHANGELOG.md")):
        full = os.path.join(root, candidate)
        if os.path.isfile(full):
            return full
    return None


def detect_current_version(root):
    """Return (version_str, sources_dict) discovered in root."""
    sources = {}

    version_file = os.path.join(root, "VERSION")
    if os.path.isfile(version_file):
        with open(version_file, encoding="utf-8") as fh:
            val = fh.read().strip().lstrip("v")
            if SEMVER_RE.match(val):
                sources["VERSION"] = val

    pkg_json = os.path.join(root, "package.json")
    if os.path.isfile(pkg_json):
        try:
            with open(pkg_json, encoding="utf-8") as fh:
                data = json.load(fh)
            val = str(data.get("version", "")).strip()
            if SEMVER_RE.match(val):
                sources["package.json"] = val
        except (OSError, ValueError):
            pass

    for toml_name in ("pyproject.toml", "Cargo.toml"):
        toml_path = os.path.join(root, toml_name)
        if os.path.isfile(toml_path):
            with open(toml_path, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
            m = re.search(r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', text, re.M)
            if m:
                sources[toml_name] = m.group(1)

    changelog_path = find_changelog(root)
    if changelog_path:
        with open(changelog_path, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        m = CHANGELOG_VER_RE.search(text)
        if m:
            sources["CHANGELOG.md"] = m.group(1)

    for key in ("VERSION", "package.json", "pyproject.toml", "Cargo.toml", "CHANGELOG.md"):
        if key in sources:
            return sources[key], sources

    return "0.1.0", sources


def extract_unreleased_body(changelog_text):
    """Return (body_str, start_idx, end_idx) of content under ## [Unreleased]."""
    m = UNRELEASED_HEADER_RE.search(changelog_text)
    if not m:
        return "", -1, -1
    start = m.end()
    next_rel = NEXT_RELEASE_HEADER_RE.search(changelog_text, start)
    end = next_rel.start() if next_rel else len(changelog_text)
    body = changelog_text[start:end].strip()
    # Strip horizontal rules that separate sections
    body_cleaned = re.sub(r"^\s*---+\s*|\s*---+\s*$", "", body).strip()
    return body_cleaned, start, end


def infer_bump_from_unreleased(unreleased_body, current_major, strict_major=False):
    """Infer 'major', 'minor', or 'patch' from Keep a Changelog headings in [Unreleased]."""
    if not unreleased_body:
        return "patch"
    has_breaking = bool(
        re.search(r"^###\s+Removed\b", unreleased_body, re.I | re.M)
        or re.search(r"\bBREAKING(?:\s+CHANGE)?\b", unreleased_body)
    )
    if has_breaking:
        if current_major == 0 and not strict_major:
            return "minor"
        return "major"
    if re.search(r"^###\s+Added\b", unreleased_body, re.I | re.M):
        return "minor"
    return "patch"


def compute_next_version(current_ver, bump_kind, unreleased_body="", strict_major=False):
    major, minor, patch = parse_semver(current_ver)
    if bump_kind == "auto":
        bump_kind = infer_bump_from_unreleased(unreleased_body, major, strict_major=strict_major)
    if bump_kind == "major":
        return format_semver((major + 1, 0, 0)), bump_kind
    if bump_kind == "minor":
        return format_semver((major, minor + 1, 0)), bump_kind
    if bump_kind == "patch":
        return format_semver((major, minor, patch + 1)), bump_kind
    raise ValueError(f"Unknown bump kind: {bump_kind}")


def format_message_entry(message):
    """Format a CLI --message string into Keep a Changelog section + bullet."""
    msg = message.strip()
    m = re.match(r"^(Added|Changed|Fixed|Removed|Security)\s*:\s*(.+)$", msg, re.I)
    if m:
        category = m.group(1).capitalize()
        item = m.group(2).strip()
    else:
        category = "Fixed"
        item = msg
    return f"### {category}\n* {item}"


def update_changelog_text(changelog_text, new_version, release_date, fallback_message=None):
    """Move [Unreleased] content into ## [new_version] - release_date."""
    unreleased_body, start, end = extract_unreleased_body(changelog_text)
    if not unreleased_body and fallback_message:
        unreleased_body = format_message_entry(fallback_message)
    if not unreleased_body:
        unreleased_body = "### Changed\n* Maintenance release."

    new_section = (
        f"\n\n---\n\n## [{new_version}] - {release_date}\n\n"
        f"{unreleased_body}\n\n---\n\n"
    )

    if start != -1:
        updated = changelog_text[:start] + new_section + changelog_text[end:].lstrip()
        # Collapse duplicate horizontal rules if present
        updated = re.sub(r"(---\s*\n\s*){2,}", "---\n\n", updated)
        return updated

    # If no ## [Unreleased] existed, insert both at the top
    header_block = (
        f"## [Unreleased]\n\n---\n\n"
        f"## [{new_version}] - {release_date}\n\n"
        f"{unreleased_body}\n\n"
    )
    return changelog_text.rstrip() + "\n\n" + header_block


def update_project_files(root, new_version, release_date, message=None, create_version_file=False, dry_run=False):
    touched = []

    # 1. VERSION file
    version_file = os.path.join(root, "VERSION")
    if os.path.isfile(version_file) or create_version_file:
        if not dry_run:
            with open(version_file, "w", encoding="utf-8") as fh:
                fh.write(new_version + "\n")
        touched.append("VERSION")

    # 2. package.json
    pkg_json = os.path.join(root, "package.json")
    if os.path.isfile(pkg_json):
        with open(pkg_json, encoding="utf-8") as fh:
            text = fh.read()
        updated_text, count = re.subn(
            r'("version"\s*:\s*")\d+\.\d+\.\d+(")',
            rf"\g<1>{new_version}\2",
            text,
            count=1,
        )
        if count > 0 and updated_text != text:
            if not dry_run:
                with open(pkg_json, "w", encoding="utf-8") as fh:
                    fh.write(updated_text)
            touched.append("package.json")

    # 3. pyproject.toml / Cargo.toml
    for toml_name in ("pyproject.toml", "Cargo.toml"):
        toml_path = os.path.join(root, toml_name)
        if os.path.isfile(toml_path):
            with open(toml_path, encoding="utf-8") as fh:
                text = fh.read()
            updated_text, count = re.subn(
                r'^(version\s*=\s*["\'])\d+\.\d+\.\d+(["\'])',
                rf"\g<1>{new_version}\2",
                text,
                count=1,
                flags=re.M,
            )
            if count > 0 and updated_text != text:
                if not dry_run:
                    with open(toml_path, "w", encoding="utf-8") as fh:
                        fh.write(updated_text)
                touched.append(toml_name)

    # 4. README.md version badge
    readme_path = os.path.join(root, "README.md")
    if os.path.isfile(readme_path):
        with open(readme_path, encoding="utf-8") as fh:
            text = fh.read()
        updated_text = re.sub(
            r"(img\.shields\.io/badge/version-)\d+\.\d+\.\d+(-[a-z0-9A-Z]+(?:\.svg)?)",
            rf"\g<1>{new_version}\2",
            text,
        )
        if updated_text != text:
            if not dry_run:
                with open(readme_path, "w", encoding="utf-8") as fh:
                    fh.write(updated_text)
            touched.append("README.md")

    # 5. CHANGELOG.md
    changelog_path = find_changelog(root)
    if changelog_path:
        with open(changelog_path, encoding="utf-8") as fh:
            text = fh.read()
        if not re.search(rf"^##\s+\[{re.escape(new_version)}\]", text, re.M):
            updated_text = update_changelog_text(text, new_version, release_date, fallback_message=message)
            if not dry_run:
                with open(changelog_path, "w", encoding="utf-8") as fh:
                    fh.write(updated_text)
            rel_cl = os.path.relpath(changelog_path, root).replace(os.sep, "/")
            touched.append(rel_cl)

    return touched


def main():
    ap = argparse.ArgumentParser(description="Semantic version (MAJOR.MINOR.PATCH) manager for living-docs.")
    ap.add_argument("--root", default=".", help="Project root directory (default: .)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--bump",
        choices=["patch", "minor", "major", "auto"],
        help="Version segment to increment ('auto' inspects ## [Unreleased] in CHANGELOG.md)",
    )
    group.add_argument("--set", dest="set_version", help="Explicit semantic version X.Y.Z to set")
    ap.add_argument(
        "--message",
        help="Changelog entry when ## [Unreleased] is empty (e.g. 'Fixed: handle timeout on retry')",
    )
    ap.add_argument(
        "--date",
        default=datetime.date.today().isoformat(),
        help="Release date in YYYY-MM-DD format (default: today)",
    )
    ap.add_argument(
        "--create-version-file",
        action="store_true",
        help="Create a VERSION file at the project root if one does not exist",
    )
    ap.add_argument(
        "--strict-major",
        action="store_true",
        help="Bump 0.Y.Z -> 1.0.0 on breaking changes in --bump auto (default keeps 0.x and bumps minor)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print planned version change without writing files")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    current_ver, _ = detect_current_version(root)

    changelog_path = find_changelog(root)
    unreleased_body = ""
    if changelog_path:
        with open(changelog_path, encoding="utf-8", errors="ignore") as fh:
            unreleased_body, _, _ = extract_unreleased_body(fh.read())

    if args.set_version:
        parse_semver(args.set_version)
        new_ver = args.set_version.strip().lstrip("v")
        resolved_kind = "explicit"
    else:
        new_ver, resolved_kind = compute_next_version(
            current_ver,
            args.bump,
            unreleased_body=unreleased_body,
            strict_major=args.strict_major,
        )

    touched = update_project_files(
        root,
        new_ver,
        args.date,
        message=args.message,
        create_version_file=args.create_version_file,
        dry_run=args.dry_run,
    )

    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"{prefix}Version bumped ({resolved_kind}): {current_ver} -> {new_ver}")
    if touched:
        print(f"{prefix}Updated files: {', '.join(touched)}")
    else:
        print(f"{prefix}No version files updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
