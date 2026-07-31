# Changelog

## 1.0.0 (2026-07-29)

First versioned release. Behaviour unchanged; this brings the skill under the CFOforIT Build Standards charter (v1.8), which the public repo had never enforced.

Recorded classifications and why:

- **`autonomy_tier: draft-for-review`** — it produces a pre-read in chat and offers to save it. It does not write back into the board or circulate anything.
- **`blast_radius: private`** — the pre-read goes to the team that asked for it.
- **`model_tier: sonnet`** — reading an exported board and applying stated thresholds (off track, overdue, unowned, off goal, wrong-direction measures) then ordering the result. Mechanical against explicit rules.
- **`trust_level: external`** — public marketplace skill, run outside the firm on the user's own exported data.

Two honesty rules already in the body and worth naming here, because they are the reason this skill is trustworthy rather than merely useful: it respects a measure's `direction`, so a "lower is better" measure like churn or AR-over-60 going up is never reported as good news; and it says plainly when there are no genuine wins rather than manufacturing a headline, because a fabricated win teaches a team to discount the whole pre-read.
