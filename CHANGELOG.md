# Changelog

Notable changes to the CFOforIT open marketplace. Per-skill history lives in each skill's
own `CHANGELOG.md`. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-08-04

The first tagged release. Every plugin and skill published here already declared `1.0.0`
in its own manifest, so `1.0.0` is what the marketplace as a whole has been shipping — this
release records that fact rather than inventing a new number for it.

### Added
- **Tagged releases.** `v1.0.0` is the first immutable point an outside consumer can pin
  to or roll back to. Until now `/plugin marketplace add CFOforIT/cfoforit-openmarketplace`
  resolved to whatever `main` was that second, including a half-finished commit — which made
  charter Rule 17's "roll back cleanly" unachievable in the one repository outsiders
  actually depend on. A version bump without a matching tag is now a red build
  (`check_release_tag.py`, run from the canonical repo).
- Repository controls: `CODEOWNERS`, Dependabot, `SECURITY.md`, `CONTRIBUTING.md`,
  pull-request and issue templates, and this changelog.
- Workflow hardening: top-level `permissions: contents: read`, a `concurrency` group,
  and `actions/checkout` SHA-pinned in both jobs.

### Changed
- Charter validation moved to the single shared implementation in the canonical repo. The
  local copy of `validate_skills.py` is deleted; it had drifted, and was enforcing charter
  v1.8 minus two rules while reporting clean. See `.github/workflows/skill-standards-gate.yml`
  for where the checks run now, and for the one coverage gap this leaves.

## 2026-07-29

## 2026-07-29

### Added
- `skill-standards-gate`: charter v1.8 validation plus per-skill structural evals on
  every push and pull request to `main`.

### Fixed
- Three `eos-dashboard` skills had been published missing five required frontmatter
  fields each and all three CHANGELOGs — 18 charter errors, previously unchecked.
