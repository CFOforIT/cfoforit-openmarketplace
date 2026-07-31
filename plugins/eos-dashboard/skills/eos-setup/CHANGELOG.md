# Changelog

## 1.0.0 (2026-07-29)

First versioned release. The skill itself is unchanged in behaviour; this brings it under the CFOforIT Build Standards charter (v1.8), which it had never been checked against — the public repo carried no standards gate, so nothing caught it.

Recorded classifications and why:

- **`autonomy_tier: draft-for-review`** — it writes a starter file the user imports themselves. It never edits `app/index.html` and never transmits anything.
- **`blast_radius: private`** — output lands on the operator's own machine and reaches no third party. The operator is the leadership team being configured.
- **`model_tier: sonnet`** — a structured interview and a fixed-shape JSON write. The judgment is the user's; the skill's job is to stop them typing into a blank dashboard.
- **`trust_level: external`** — this ships in the public marketplace and is run by people outside the firm on their own data.

Guardrails already in the body, now stated as classifications rather than left implicit: it refuses to re-run against an already-configured dashboard (directing the user to the in-app Setup button instead, so their existing work is not overwritten), and it deliberately does not collect the vision plan — that is `eos-vision`, and mixing the two makes both worse.
