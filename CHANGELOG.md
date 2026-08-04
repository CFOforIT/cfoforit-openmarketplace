# Changelog

Notable changes to the CFOforIT open marketplace. Per-skill history lives in each skill's
own `CHANGELOG.md`. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Repository controls: `CODEOWNERS`, Dependabot, `SECURITY.md`, `CONTRIBUTING.md`,
  pull-request and issue templates, and this changelog.
- Workflow hardening: top-level `permissions: contents: read`, a `concurrency` group,
  and `actions/checkout` SHA-pinned in both jobs.

### Known gap
- **No tagged releases.** `/plugin marketplace add` resolves to whatever `main` is at
  that moment, so consumers have no immutable point to pin or roll back to. Charter
  Rule 17 asks for clean rollback; that is not currently achievable here. Tagging is a
  decision for the maintainer — see the session handoff.

## 2026-07-29

### Added
- `skill-standards-gate`: charter v1.8 validation plus per-skill structural evals on
  every push and pull request to `main`.

### Fixed
- Three `eos-dashboard` skills had been published missing five required frontmatter
  fields each and all three CHANGELOGs — 18 charter errors, previously unchecked.
