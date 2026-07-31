# Changelog

## 1.0.0 (2026-07-29)

First public release of the command-center engine.

**What ships:** `ma_engine.validate` (the financial tie-out gate) and `ma_engine.render` (the
self-contained tabbed HTML renderer), plus the portable path config both use.

**What deliberately does not ship:** the diligence request checklist, the internal analysis
workplan, the integration task library, and the strategic-fit rubric. Those are CFOforIT's own
work product — the engine is the machinery, and it renders and validates whatever JSON you hand
it. This split is the reason the plugin can be public at all.

Behaviour worth knowing about, because it is unusual and intentional:

- **A check that cannot run counts as failed.** Absent statements, a missing `role: "cash"` tag,
  or an EBITDA bridge with no period each report "could not run" and fail the gate. A gate that
  returns PASS when it cannot see is worse than no gate, because it is trusted.
- **Cross-statement checks are not self-referential.** The equity rollforward's net income and
  the cash-flow statement's are both checked against the P&L, so a schedule that foots against
  its own invented figure still fails.
- **Tolerance is one dollar**, not a percentage.
- **`prepared_by` defaults to CFOforIT** and must be set to whoever actually produced the page,
  or the footer carries a false attribution.
- **`audience="target"` raises** rather than silently downgrading to a safer build.

`engine/` is generated from the internal repository. A drift check there fails the build whenever
this copy stops matching its source, so what is published is what CFOforIT runs.
