# Contributing to cfoforit-openmarketplace

Thanks for your interest. This repository is the **public mirror** of CFOforIT's Claude
plugin marketplace. Please read this before opening a pull request.

## What is and is not editable here

- Anything under a plugin's `engine/` directory is **generated** from CFOforIT's private
  source repository. Hand-edits are detected and rejected by the mirror-drift check
  there. File an issue instead.
- Skill content and the dashboard app under `app/` accept contributions.

## Standards

Every skill must satisfy the CFOforIT Build Standards charter v1.8: complete SKILL.md
frontmatter and a `CHANGELOG.md` alongside the skill.

## Workflow

1. Fork and branch from `main`.
2. Make your change.
3. `python3 tools/validate_skills.py`
4. `for r in plugins/*/skills/*/evals/runner.py; do python3 "$r"; done`
5. Open a pull request and complete the template.

## Rules

- No client names, client data, credentials, or internal decision-log references.
- No secrets in workflows or skill assets.

## Reporting security issues

See `SECURITY.md`. Do not file security reports as public issues.

## License

Contributions are accepted under the repository's LICENSE (MIT).
