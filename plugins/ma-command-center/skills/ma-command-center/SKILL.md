---
name: ma-command-center
description: "Render a self-contained tabbed HTML command center for an acquisition from your own deal JSON, and run an executable financial tie-out gate over a target's statements before trusting any figure. Trigger on render a command center, build a deal page, validate these financial statements, run a tie-out check, does this balance sheet balance, do these statements tie out, check the retained earnings rollforward, EBITDA bridge check, my add-backs don't foot. Ships the engine, not a diligence checklist — you supply the JSON. Never invents a figure that was not in the input."
version: 1.0.0
autonomy_tier: draft-for-review
blast_radius: private
model_tier: sonnet
model_tier_rationale: "Calling a deterministic validator and a deterministic renderer, then reporting what they returned. The judgment lives in the numbers the user supplies, not in this skill; the arithmetic is Python's."
expected_token_budget: "5K-20K per invocation — reads one deal JSON and reports the gate result. Does not read reference libraries; none ship with this plugin."
trust_level: external
---

# M&A Command Center

Two deterministic tools and a rule about how to report them.

1. **`ma_engine.validate`** — a financial tie-out gate over a target's statements.
2. **`ma_engine.render`** — a self-contained tabbed HTML page from deal JSON.

You supply the JSON. This plugin ships **no** diligence checklist, integration task library, or
scoring rubric.

## The one rule

**Report what the gate returned. Never soften it, never summarise past it, never fill a gap.**

If a figure was not in the input, say "source not provided" — do not produce a plausible number.
If a check failed, name the check and the delta. If the gate could not run a check, say that too;
it is a failure, not a footnote. Someone is going to price an acquisition off this.

## Running the gate

```python
import sys; sys.path.insert(0, "<plugin>/engine")
from ma_engine import validate as V

report = V.validate(detail, hard_stop=False)   # hard_stop=True raises MAError instead
detail["meta"]["validation"] = report.as_snapshot_block()
```

`report.status` is `"pass"` or `"fail"`. `report.blocking_failures` are the checks that must be
explained before any number is used. `report.flags` are non-blocking findings that must still be
shown — a flag nobody sees is the same as no check at all.

What it checks:

- **Balance sheet balances** — Assets = Liabilities + Equity, at every date presented.
- **Cash ties** — balance-sheet cash agrees to ending cash on the cash-flow statement, and
  opening + net change = closing.
- **Retained earnings** — the rollforward foots, its closing balance matches the balance sheet,
  **and its net income matches the P&L's**. That last one matters: a rollforward that foots
  against its own invented net income proves nothing.
- **Detail foots** — revenue, cost of sales and SG&A each sum to their stated totals.
- **Internal arithmetic** — gross profit, EBITDA, EBIT, pre-tax and net income each derive from
  the line above.
- **EBITDA bridge** — add-backs sum into the stated normalized EBITDA, and reported EBITDA
  agrees to the P&L for the bridge's own period.

Two behaviours to understand before you trust it:

- **Tolerance is $1, not a percentage.** A $1,000 difference on $15M revenue (0.007%) fails. In
  diligence a small unexplained difference usually means a whole schedule is wrong.
- **A check that cannot run counts as FAILED.** Missing `statements`, no balance-sheet line
  tagged `role: "cash"`, a bridge with no `period` — each reports "could not run" and fails. A
  gate that returns PASS when it cannot see is worse than no gate, because it is trusted.

`engine/README.md` documents the `statements` shape the gate reads. Match it, or the gate will
tell you which check it could not run — which is the correct outcome, not an error to work around.

## Rendering

```python
from ma_engine.render import render_command_center

html = render_command_center(client, target, docs,
                             audience="client",          # or "firm"
                             prepared_by=client,         # who produced it
                             data_as_of="2026-06-30")
```

`docs` keys, any of which may be absent: `go_no_go`, `diligence_requests`,
`diligence_workplan`, `integration`, `financials_detail`. A missing key renders an honest empty
state rather than a blank tab.

- **`prepared_by`** drives the masthead and the footer. Set it to whoever actually produced the
  page. Left at its default it says CFOforIT, which would be a false attribution on your
  document.
- **`audience`** selects which tabs and sections are built. It changes the **bytes**, not CSS
  visibility — every figure is inlined, so hiding is not a control. `audience="target"` raises
  rather than silently downgrading: showing a seller your own valuation of them needs field-level
  filtering that is not implemented here.
- Every grouped list gets a clickable arrow and an **All / Open only** toggle. The summary tiles
  never move with the filter — they describe the record, not the view — and an active filter says
  "This is not the full list" on the page. Do not screenshot a filtered view as a complete one.

## What must not happen

- [ ] Never write a figure the input did not contain.
- [ ] Never report a gate as passing when `report.status == "fail"`, and never omit `report.flags`.
- [ ] Never pass `audience="firm"` on a page going to someone outside the organisation that
      prepared it — the firm build is stamped INTERNAL and includes the deal team's own workplan.
- [ ] Never edit `engine/` in this plugin. It is generated from CFOforIT's internal repository
      and overwritten on the next sync; a drift check upstream fails when this copy diverges.
      Send fixes as an issue.

## Confidentiality

Nothing here phones home. The engine performs no network access, writes only where you tell it,
and this skill sends nothing anywhere. One deal at a time: a single page covering several targets
would carry every target's pricing in one file, so render one page per target.
