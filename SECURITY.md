# Security Policy

## Scope

`cfoforit-openmarketplace` is the public Claude plugin marketplace published by
CFOforIT. It contains skill definitions, a static dashboard app, and a generated copy of
the M&A engine. By design it contains no client data and no credentials.

## Reporting a vulnerability

Report privately to **steve.torres@cfoforit.com**. Please do not open a public issue and
do not disclose publicly before a fix ships.

Include the affected file or skill, reproduction steps, and impact.

Acknowledgement within 2 business days; triage within 5. We will confirm the fix with
you before public disclosure, and credit you unless you'd rather we didn't.

## In scope

- Skill instructions that could cause a user's Claude session to exfiltrate data,
  execute unintended commands, or write outside the intended directory.
- Prompt-injection vectors in skill content or bundled assets.
- Any credential, token, or client-identifying data found committed here.

## Out of scope

- Vulnerabilities in Claude, Claude Code, or Anthropic infrastructure — report those to
  Anthropic.
- Issues that require the user to install a modified fork of this repository.

## Supported versions

Only `main`. Note there are currently no tagged releases, so `main` is what
`/plugin marketplace add` resolves to at any moment.
