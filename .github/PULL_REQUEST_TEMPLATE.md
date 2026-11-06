## Summary

<!-- Describe what this PR changes and why. Reference any related issue numbers (e.g., Fixes #12) or FEAT-NN / ADR-NN IDs. -->

## Type of Change

- [ ] Bug fix (`scripts/check_docs.py` or false-positive handling)
- [ ] New reverse-coverage pattern (framework route, ORM table, or config detection)
- [ ] Template / language update (`resources/`)
- [ ] Skill instruction update (`SKILL.md`)
- [ ] Documentation or CI update

## Checklist

- [ ] `python3 -m unittest discover -s tests -v` passes with 0 failures.
- [ ] `python3 scripts/check_docs.py --root .` exits with `0 error(s), 0 warning(s)`.
- [ ] Added or updated unit tests in `tests/test_check_docs.py` (if `scripts/check_docs.py` changed).
- [ ] Updated `docs/FEATURES.md`, `docs/ARCHITECTURE.md`, and `CHANGELOG.md` (`## [Unreleased]`) if behavior changed.
- [ ] Prose follows `SKILL.md` rules (no em dashes, no AI buzzwords, no unverified claims).
