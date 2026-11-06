# Security Policy

## Supported Versions

Only the latest release on the `main` branch receives security updates.

| Version | Supported |
| :--- | :--- |
| `0.1.x` | Yes |
| `< 0.1.0` | No |

---

## Security Model of `living-docs`

`living-docs` consists of Markdown instructions (`SKILL.md`), documentation templates (`resources/`), and a local verification script (`scripts/check_docs.py`) that uses only the Python 3 standard library.

* `scripts/check_docs.py` reads files inside `--root` and prints verification diagnostics to standard output.
* It makes **no network requests**, executes **no shell subprocesses**, and does **not** modify files on disk.
* Security-relevant bugs in `living-docs` include path traversal outside `--root`, regular expression denial of service (ReDoS) on untrusted input files, or unsafe instructions in `SKILL.md`.

---

## Reporting a Vulnerability

Please **do not** report security vulnerabilities through public GitHub issues.

1. Use [GitHub Private Vulnerability Reporting](https://github.com/Light-Yodeler/living-docs/security/advisories/new) on this repository to submit your report privately.
2. Include the affected file (`scripts/check_docs.py`, `SKILL.md`, or workflow file), a minimal reproduction input, and the potential impact.
3. You will receive an acknowledgment within **72 hours** and a status update or fix timeline within **7 days**.
4. Once a fix is released, we will credit you in the security advisory and `CHANGELOG.md` (unless you prefer to remain anonymous).
